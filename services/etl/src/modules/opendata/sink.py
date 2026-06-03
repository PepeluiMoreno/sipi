# -*- coding: utf-8 -*-
"""Sumidero de persistencia para los upserts de tablas maestras.

Desacopla la integración con ODM de la decisión de persistencia (que depende de
la consolidación pendiente sobre sipi-core). La integración produce registros ya
mapeados y se los pasa a un `MaestroSink`.

- `LogSink`: no persiste; cuenta y registra (para dry-run y validación).
- `SqlAlchemyMaestroSink`: upsert real contra sipi-core (a completar cuando la
  API/etl consuman sipi-core; importa sipi-core de forma perezosa).
"""
from typing import Protocol, Iterable

__all__ = ["MaestroSink", "LogSink", "SqlAlchemyMaestroSink"]


class MaestroSink(Protocol):
    def upsert(self, tabla: str, registros: Iterable[dict], clave: str) -> int:
        ...


class LogSink:
    """Sink de validación: no toca BD, solo cuenta y guarda una muestra."""
    def __init__(self):
        self.contadores = {}
        self.muestra = {}

    def upsert(self, tabla, registros, clave):
        registros = list(registros)
        self.contadores[tabla] = self.contadores.get(tabla, 0) + len(registros)
        if registros and tabla not in self.muestra:
            self.muestra[tabla] = registros[0]
        return len(registros)


class SqlAlchemyMaestroSink:
    """Upsert real contra sipi-core. Mapea nombre de tabla -> modelo y hace
    insert-or-update por la clave natural.

    Requiere que sipi-core sea consumible (consolidación). Importa de forma
    perezosa para no acoplar el resto del módulo.
    """
    def __init__(self, session_factory, modelo_por_tabla=None):
        self.session_factory = session_factory
        self.modelo_por_tabla = modelo_por_tabla or self._modelos_sipi_core()

    @staticmethod
    def _modelos_sipi_core():
        # Import perezoso; solo se ejecuta si se usa este sink.
        from sipi_core import models as m
        return {
            "comunidades_autonomas": m.ComunidadAutonoma,
            "provincias": m.Provincia,
            "municipios": m.Municipio,
            "administraciones": m.Administracion,
            "notarias": m.Notaria,
        }

    def upsert(self, tabla, registros, clave):
        modelo = self.modelo_por_tabla.get(tabla)
        if modelo is None:
            raise KeyError(f"sin modelo sipi-core para la tabla '{tabla}'")
        n = 0
        s = self.session_factory()
        try:
            for reg in registros:
                k = reg.get(clave)
                existente = s.query(modelo).filter(getattr(modelo, clave) == k).one_or_none()
                if existente:
                    for col, val in reg.items():
                        setattr(existente, col, val)
                else:
                    s.add(modelo(**reg))
                n += 1
            s.commit()
        finally:
            s.close()
        return n
