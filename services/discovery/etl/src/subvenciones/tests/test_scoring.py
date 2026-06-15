# -*- coding: utf-8 -*-
"""Casos de prueba del scorer (deterministas, sin BD ni red)."""
from subvenciones.scoring import (
    clasificar_nif, detectar_finalidad_rehab, nombre_es_religioso, evaluar,
)


def _check(cond, msg):
    print(("OK  " if cond else "FALLO ") + msg)
    assert cond, msg


# --- NIF -------------------------------------------------------------------
_check(clasificar_nif("R0800012H").clase == "religiosa", "NIF R → religiosa")
_check(clasificar_nif("R0800012H").en_alcance, "NIF R en alcance")
_check(clasificar_nif("G41000000").clase == "asociacion_fundacion", "NIF G → asoc/fundación")
_check(not clasificar_nif("B12345678").en_alcance, "NIF B fuera de alcance")
_check(not clasificar_nif("").en_alcance, "NIF vacío fuera de alcance")

# --- Finalidad: positivos --------------------------------------------------
f = detectar_finalidad_rehab("Rehabilitación de la cubierta de la iglesia parroquial de San Mateo")
_check(f.es_rehab_edificio, "rehab cubierta iglesia → edificio")
_check("rehabilitacion" in f.senales and "templo" in f.senales, "señales rehab+templo")

f = detectar_finalidad_rehab("Conservación y restauración del retablo de la ermita")
_check(f.es_rehab_edificio, "conservación retablo ermita → edificio")

f = detectar_finalidad_rehab("Restauración de bien de interés cultural (BIC): consolidación estructural")
_check(f.es_rehab_edificio, "restauración BIC → edificio")

# --- Finalidad: vetos ------------------------------------------------------
f = detectar_finalidad_rehab("Programa de rehabilitación psicosocial de personas con enfermedad mental")
_check(f.vetada and not f.es_rehab_edificio, "veto rehab psicosocial")

f = detectar_finalidad_rehab("Subvención para reinserción laboral y rehabilitación de drogodependientes")
_check(f.vetada, "veto drogodependientes")

# --- Finalidad: insuficiente (acción sin contexto de edificio) -------------
f = detectar_finalidad_rehab("Subvención nominativa para actividades culturales")
_check(not f.es_rehab_edificio, "actividades culturales → no edificio")

# --- Nombre religioso / gremio secular ------------------------------------
_check(nombre_es_religioso("Parroquia de Santa María"), "parroquia → religioso")
_check(nombre_es_religioso("Hermandad de Nuestra Señora del Rocío"), "hermandad mariana → religioso")
_check(not nombre_es_religioso("Cofradía de Pescadores de Barbate"), "cofradía pescadores → NO religioso")
_check(not nombre_es_religioso("Sociedad Gastronómica La Tasca"), "gastronómica → NO religioso")

# --- Evaluación combinada --------------------------------------------------
# Religiosa (R) + rehab de templo + bonus de censo inmatriculado → alta fiabilidad CIERTO
e = evaluar("R4100001A", "Parroquia de San Juan",
            "Rehabilitación de la torre campanario de la iglesia",
            bonus_censo=0.25, senales_censo=["censo_nif_inmatriculado"])
_check(e.es_candidato, "candidato: R + rehab templo")
_check(e.valor >= 0.70, f"fiabilidad alta ({e.valor}) → CIERTO")
_check("censo_nif_inmatriculado" in e.senales, "señal de censo presente")

# Fundación (G) confesional + rehab patrimonio, sin censo → candidato pero menor
e = evaluar("G41000000", "Fundación Diocesana de Patrimonio",
            "Conservación del patrimonio histórico-artístico del templo")
_check(e.es_candidato, "candidato: G confesional + rehab")
_check("nombre_religioso" in e.senales, "refuerzo nombre religioso en G")

# G de gremio secular con rehab de edificio → candidato por finalidad, pero sin
# refuerzo religioso (la fiabilidad debe ser menor que el caso confesional)
e_gremio = evaluar("G11000000", "Cofradía de Pescadores de Conil",
                   "Rehabilitación de la cubierta del edificio sede")
_check("nombre_religioso" not in e_gremio.senales, "gremio secular: sin refuerzo religioso")

# NIF fuera de alcance → nunca candidato
e = evaluar("B12345678", "Constructora SA", "Rehabilitación de iglesia")
_check(not e.es_candidato and e.valor == 0.0, "NIF B → no candidato")

# Finalidad vetada anula aunque el NIF sea R
e = evaluar("R0800012H", "Cáritas Diocesana",
            "Rehabilitación psicosocial e inserción laboral de personas sin hogar")
_check(not e.es_candidato, "R + finalidad vetada → no candidato")

print("\nTodos los casos pasan.")


# --- selección de recursos por ejercicio (colección histórica) ----------------
from sipi_core.modules.discovery.subvenciones import recursos_por_ejercicio

_RES = [
    {"id": "a", "name": "BDNS · Concesiones 2024"},
    {"id": "b", "name": "BDNS · Concesiones 2025-03"},
    {"id": "c", "name": "BDNS · Concesiones 2025-12"},
    {"id": "d", "name": "BDNS · Concesiones 2022"},
    {"id": "e", "name": "BDNS · Concesiones (histórico por ejercicio)"},  # la colección padre, NO hija
    {"id": "f", "name": "BDNS · Convocatorias 2024"},                      # otra etiqueta
    {"id": "g", "name": "BDNS - Concesiones de Subvenciones"},             # recurso plano legacy
]
_sel = recursos_por_ejercicio(_RES, "Concesiones")
_ids = [i for i, _, _ in _sel]
_check(_ids == ["c", "b", "a", "d"], f"hijos por ejercicio, recientes primero: {_ids}")
_check(all(x not in _ids for x in ("e", "f", "g")), "excluye colección, otra etiqueta y legacy")

print("\nTodos los casos (incl. colección) pasan.")
