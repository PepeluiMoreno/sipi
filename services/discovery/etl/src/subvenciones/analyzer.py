# -*- coding: utf-8 -*-
"""Analyzer: concesiones BDNS para rehabilitación de inmuebles inmatriculados.

Flujo:
  1. Lee del recurso ODM de concesiones (filtradas a NIF R/G) y, si está
     publicado, el índice de convocatorias para enriquecer la finalidad.
  2. Construye el censo SIPI (entidades religiosas, marcando cuáles tienen
     inmuebles inmatriculados) para el cruce.
  3. Por cada concesión: puntúa con `scoring.evaluar` (NIF + finalidad + bonus de
     censo) y, si es candidata (finalidad = rehabilitación de edificio), crea un
     `Hallazgo` PENDIENTE con `certeza`/`confianza`, idempotente por
     `origen_id = codConcesion`.

El Hallazgo entra en el mismo flujo de comprobación humana que el resto: un
operador lo verifica (transacción `hallazgo.verificar`) y abre/engrosa el
Expediente del inmueble. SIPI no decide: propone con fiabilidad trazable.

Uso:
    python -m subvenciones.analyzer --odm-url http://odmgr_app:8040 --anio 2023
    python -m subvenciones.analyzer --anio 2023 --umbral 70 --dry-run
    python -m subvenciones.analyzer --anio 2023 --informe        # solo cuenta
"""
from __future__ import annotations

import argparse
import logging
import os
from collections import Counter
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .scoring import _norm, evaluar
from . import fuentes

log = logging.getLogger("sipi.etl.subvenciones")

UMBRAL_CIERTO_DEFECTO = 70.0   # fiabilidad (0..100) a partir de la cual: certeza CIERTO
FUENTE = "odmgr:bdns"
ORIGEN_TIPO = "concesion_bdns"

# Bonus de cruce con censo (entidad religiosa conocida)
_BONUS = {
    ("nif", True): (0.25, "censo_nif_inmatriculado"),
    ("nif", False): (0.10, "censo_nif"),
    ("nombre", True): (0.18, "censo_nombre_inmatriculado"),
    ("nombre", False): (0.06, "censo_nombre"),
}


# ---------------------------------------------------------------------------
# Censo SIPI
# ---------------------------------------------------------------------------
class Censo:
    """Índice de entidades religiosas para el cruce, con marca de inmatriculación."""

    def __init__(self, session: Session):
        from sipi_core.db.registry import APP_SCHEMA as S
        rows = session.execute(text(f"""
            SELECT er.id AS id, er.nombre AS nombre, er.nif AS nif,
                   EXISTS (
                       SELECT 1 FROM {S}.inmuebles i
                       JOIN {S}.inmatriculaciones im ON im.inmueble_id = i.id
                       WHERE i.entidad_religiosa_id = er.id
                   ) AS tiene_inmat
            FROM {S}.entidades_religiosas er
            WHERE er.deleted_at IS NULL
        """)).mappings().all()
        self.por_nif: dict[str, tuple[str, bool]] = {}
        self.por_nombre: dict[str, tuple[str, bool]] = {}
        for r in rows:
            ident = (str(r["id"]), bool(r["tiene_inmat"]))
            if r["nif"]:
                self.por_nif[(r["nif"] or "").upper()] = ident
            if r["nombre"]:
                self.por_nombre[_norm(r["nombre"])] = ident
        log.info("Censo: %d entidades religiosas (%d con NIF, %d con inmatriculaciones)",
                 len(rows),
                 sum(1 for r in rows if r["nif"]),
                 sum(1 for r in rows if r["tiene_inmat"]))

    def cruzar(self, nif: str, nombre: str) -> tuple[float, list[str], Optional[str]]:
        """Devuelve (bonus, senales, entidad_religiosa_id) para una concesión."""
        # 1) match exacto por NIF
        ident = self.por_nif.get((nif or "").upper())
        modo = "nif"
        if not ident:
            # 2) match por nombre normalizado (exacto, luego contención)
            modo = "nombre"
            bnorm = _norm(nombre)
            ident = self.por_nombre.get(bnorm)
            if not ident and bnorm:
                for snorm, val in self.por_nombre.items():
                    if bnorm in snorm or snorm in bnorm:
                        ident = val
                        break
        if not ident:
            return 0.0, [], None
        er_id, tiene_inmat = ident
        bonus, senal = _BONUS[(modo, tiene_inmat)]
        return bonus, [senal], er_id


# ---------------------------------------------------------------------------
# Persistencia de Hallazgo (idempotente por codConcesion)
# ---------------------------------------------------------------------------
def _persistir_hallazgo(session: Session, c: "fuentes.ConcesionBDNS", fiab, umbral: float,
                        er_id: Optional[str]) -> bool:
    from sipi_core.models import (
        Hallazgo, EstadoHallazgo, CertezaHallazgo, TipoEventoExpediente,
    )
    # Idempotencia: ¿ya existe un hallazgo para esta concesión?
    ya = session.execute(text(
        "SELECT 1 FROM " + Hallazgo.__table__.schema + ".hallazgos "
        "WHERE fuente = :f AND origen_id = :o LIMIT 1"
    ), {"f": FUENTE, "o": c.cod_concesion}).first()
    if ya:
        return False

    cierto = (fiab.valor * 100) >= umbral
    importe_txt = f"{c.importe:,.0f} €".replace(",", ".") if c.importe else "s/importe"
    titulo = f"{importe_txt} — {c.nombre}"[:255]
    descripcion = " · ".join(t for t in (c.convocatoria, c.instrumento) if t) or None

    h = Hallazgo(
        fuente=FUENTE,
        tipo_evento=TipoEventoExpediente.REHABILITACION_SUBVENCIONADA,
        estado=EstadoHallazgo.PENDIENTE,
        certeza=CertezaHallazgo.CIERTO if cierto else CertezaHallazgo.DUDOSO,
        confianza=round(fiab.valor, 3),
        titulo=titulo,
        descripcion=descripcion,
        datos={
            "cod_concesion": c.cod_concesion,
            "nif": c.nif,
            "beneficiario": c.beneficiario_raw,
            "importe": c.importe,
            "convocatoria": c.convocatoria,
            "numero_convocatoria": c.numero_convocatoria,
            "instrumento": c.instrumento,
            "nivel": [c.nivel1, c.nivel2, c.nivel3],
            "entidad_religiosa_id": er_id,
            "scoring": fiab.detalle,
            "senales": fiab.senales,
        },
        url_evidencia=(c.url_bdns or f"bdns:{c.cod_concesion}")[:500],
        fecha_evento=c.fecha_concesion,
        origen_tipo=ORIGEN_TIPO,
        origen_id=c.cod_concesion,
    )
    session.add(h)
    return True


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def analizar(
    session_factory,
    client,
    anio: Optional[int] = None,
    umbral: float = UMBRAL_CIERTO_DEFECTO,
    dry_run: bool = False,
    solo_informe: bool = False,
    historico: bool = False,
    batch_size: int = 500,
) -> Counter:
    """Recorre las concesiones R/G del recurso ODM, puntúa y crea Hallazgos.

    `session_factory` es un callable que devuelve un context manager de Session
    (sync) de sipi-core. `client` es un `ODMClient`. Con `historico=True` recorre
    todos los hijos por ejercicio de la colección (todo el histórico); si no,
    solo el recurso del año en curso (opcionalmente filtrado por `anio`).
    """
    stats: Counter = Counter()

    with session_factory() as session:
        censo = Censo(session)
        indice_conv = fuentes.construir_indice_convocatorias(client)
        if indice_conv:
            log.info("Índice de convocatorias: %d entradas", len(indice_conv))

        fuente = (fuentes.iter_concesiones_historico(client) if historico
                  else fuentes.iter_concesiones(client, anio=anio))
        n = 0
        for c in fuente:
            stats["leidas"] += 1
            bonus, senales_censo, er_id = censo.cruzar(c.nif, c.nombre)
            fiab = evaluar(
                c.nif, c.nombre, *c.textos_finalidad(indice_conv),
                bonus_censo=bonus, senales_censo=senales_censo,
            )
            if not fiab.es_candidato:
                stats["descartadas_finalidad"] += 1
                continue
            stats["candidatas"] += 1
            stats["cierto" if (fiab.valor * 100) >= umbral else "dudoso"] += 1
            if er_id:
                stats["con_entidad_censo"] += 1

            if solo_informe or dry_run:
                continue

            if _persistir_hallazgo(session, c, fiab, umbral, er_id):
                stats["hallazgos_creados"] += 1
                n += 1
                if n >= batch_size:
                    session.commit()
                    n = 0
            else:
                stats["ya_existian"] += 1

        if not (solo_informe or dry_run):
            session.commit()

    log.info("Subvenciones rehabilitación → %s", dict(stats))
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _session_factory_desde_env():
    url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    if not url:
        raise SystemExit("Falta DATABASE_URL.")
    engine = create_engine(url, pool_pre_ping=True)
    Maker = sessionmaker(bind=engine, autoflush=False, future=True)

    @contextmanager
    def factory():
        s = Maker()
        try:
            yield s
        finally:
            s.close()
    return factory


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(
        description="Concesiones BDNS de rehabilitación → Hallazgos (NIF R/G + inmatriculados)")
    p.add_argument("--odm-url", default=os.getenv("OPENDATAMANAGER_URL", "http://odmgr_app:8040"),
                   help="URL base de OpenDataManager")
    p.add_argument("--odm-token", default=os.getenv("ODM_APP_TOKEN", ""), help="Token M2M de ODM (si aplica)")
    p.add_argument("--anio", type=int, default=None, help="Filtra por año de concesión")
    p.add_argument("--umbral", type=float, default=UMBRAL_CIERTO_DEFECTO,
                   help="Fiabilidad (0..100) a partir de la cual el hallazgo es CIERTO")
    p.add_argument("--dry-run", action="store_true", help="No persiste; solo cuenta")
    p.add_argument("--informe", action="store_true", help="Solo estadísticas (alias de dry-run)")
    p.add_argument("--historico", action="store_true",
                   help="Recorre toda la colección por ejercicio (histórico), no solo el año en curso")
    args = p.parse_args()

    # Cliente ODM (sync, urllib) — reutiliza el del consumidor existente.
    from odm.client import ODMClient
    client = ODMClient(base_url=args.odm_url, app_token=args.odm_token or None)

    analizar(
        _session_factory_desde_env(),
        client,
        anio=args.anio,
        umbral=args.umbral,
        dry_run=args.dry_run,
        solo_informe=args.informe,
        historico=args.historico,
    )


if __name__ == "__main__":
    main()
