"""Tests del detector de beneficio religioso/filo-religioso."""
from sipi_core.vigilancia.detector import (
    evaluar_concesion, evaluar_convocatoria, evaluar_licitacion, extraer_nif,
)


def test_nif_letra_r_es_alerta_directa():
    d = evaluar_concesion({"beneficiario": "R4100345D ARZOBISPADO DE SEVILLA",
                           "convocatoria": "Ayudas genéricas 2026"})
    assert d.veredicto == "alerta" and d.score == 1.0
    assert d.nif == "R4100345D" and any(s.startswith("nif:R") for s in d.senales)


def test_lexico_entidad_sin_nif():
    d = evaluar_concesion({"beneficiario": "HERMANDAD DE NTRA. SRA. DEL ROCÍO",
                           "convocatoria": "Subvenciones culturales"})
    assert d.veredicto in ("alerta", "revision") and d.score >= 0.8


def test_objeto_filo_religioso_en_licitacion_con_constructora_laica():
    d = evaluar_licitacion(
        objeto="Obras de rehabilitación de la cubierta de la Iglesia de San Miguel",
        adjudicatario="B11223344 CONSTRUCCIONES PÉREZ SL",
    )
    assert d.veredicto == "alerta"
    assert any(s.startswith("objeto:") for s in d.senales)


def test_calle_de_la_iglesia_no_puntua():
    d = evaluar_licitacion(objeto="Reurbanización de la calle de la Iglesia y aceras adyacentes")
    assert d.veredicto == "sin_indicios"


def test_persona_fisica_enmascarada_neutra():
    d = evaluar_concesion({"beneficiario": "***1886** ISAURA MARIA AGUINAGA SUBERVIOLA",
                           "convocatoria": "Ayudas para la descarbonización del sector residencial"})
    assert d.veredicto == "sin_indicios" and d.nif is None


def test_corroboracion_entidad_mas_objeto_refuerza():
    d = evaluar_concesion({"beneficiario": "G21345678 ASOCIACIÓN HERMANAS DE LA CRUZ",
                           "convocatoria": "Restauración del retablo mayor"})
    assert d.veredicto == "alerta"


def test_convocatoria_semana_santa():
    d = evaluar_convocatoria({"descripcion": "Subvenciones a cofradías para la Semana Santa 2026"})
    assert d.veredicto == "alerta"


def test_convocatoria_laica_sin_indicios():
    d = evaluar_convocatoria({"descripcion": "Cheque formación dirigido a personas desempleadas"})
    assert d.veredicto == "sin_indicios"


def test_extraer_nif():
    assert extraer_nif("Q2866001G CARITAS ESPAÑOLA") == "Q2866001G"
    assert extraer_nif("***1886** PERSONA FISICA") is None
