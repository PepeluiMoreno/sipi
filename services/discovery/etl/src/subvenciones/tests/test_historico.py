"""Test de iter_concesiones_historico con un cliente ODM simulado.

Fija: unión de los hijos por ejercicio de la colección, dedup por codConcesion
(anual + mensual del mismo año conviviendo), filtrado a NIF R/G y orden de
recursos de más reciente a más antiguo.
"""
import re
from subvenciones import fuentes

_FALLOS = 0


def _check(cond, msg):
    global _FALLOS
    print(("OK  " if cond else "FALLO  ") + msg)
    if not cond:
        _FALLOS += 1


class FakeODM:
    """Implementa lo que usa el lector: _post_json (resources/datasets) e iter_jsonl."""

    def __init__(self, resources, recs):
        self._resources = resources       # [{id,name}]
        self._recs = recs                 # {resource_id: [registros]}

    def _post_json(self, path, body):
        q = body["query"]
        if "resources {" in q:
            return {"data": {"resources": self._resources}}
        if "datasets(" in q:
            rid = re.search(r'resourceId:"([^"]+)"', q).group(1)
            return {"data": {"datasets": [{
                "id": f"ds-{rid}", "majorVersion": 1, "minorVersion": 0,
                "patchVersion": 0, "createdAt": "2026-01-01",
                "recordCount": len(self._recs.get(rid, []))}]}}
        return {"data": {}}

    def iter_jsonl(self, dataset_id):
        rid = dataset_id[len("ds-"):]
        yield from self._recs.get(rid, [])


def _c(cod, nif, fecha):
    return {"codConcesion": cod, "beneficiario": f"{nif} Parroquia de Prueba",
            "fechaConcesion": fecha, "importe": 1000.0,
            "convocatoria": "Rehabilitación de templo"}


RESOURCES = [
    {"id": "col", "name": "BDNS · Concesiones (histórico por ejercicio)"},  # padre
    {"id": "m202503", "name": "BDNS · Concesiones 2025-03"},                 # mensual
    {"id": "y2025", "name": "BDNS · Concesiones 2025"},                      # anual
    {"id": "y2024", "name": "BDNS · Concesiones 2024"},
    {"id": "otro", "name": "BDNS · Convocatorias 2025"},                     # otra etiqueta
]
RECS = {
    "m202503": [_c("C1", "R1234567A", "2025-03-10"),    # dup con y2025
                _c("C2", "R7654321B", "2025-03-12"),
                _c("P1", "12345678Z", "2025-03-15")],   # persona física → fuera
    "y2025":   [_c("C1", "R1234567A", "2025-03-10"),    # mismo codConcesion → dedup
                _c("C3", "G1111111H", "2025-07-01")],
    "y2024":   [_c("C4", "R2222222C", "2024-05-05")],
}

cods = [c.cod_concesion for c in fuentes.iter_concesiones_historico(FakeODM(RESOURCES, RECS))]
_check(sorted(cods) == ["C1", "C2", "C3", "C4"], f"unión R/G de todos los hijos: {sorted(cods)}")
_check(cods.count("C1") == 1, "dedup por codConcesion entre mensual y anual")
_check("P1" not in cods, "persona física (NIF no R/G) descartada")
_check(cods[0] in ("C1", "C2"), f"empieza por el hijo más reciente (2025-03): {cods[0]}")

print("\nTodos los casos pasan." if _FALLOS == 0 else f"\n{_FALLOS} FALLOS")
raise SystemExit(1 if _FALLOS else 0)
