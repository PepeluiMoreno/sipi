# -*- coding: utf-8 -*-
"""Mapeo declarativo: dataset de ODM -> tabla maestra de SIPI.

Cada `MapeoMaestro` dice de qué dataset de ODM (su `query_name` en la API de
datos) se alimenta una tabla maestra de SIPI, qué campos coger, cómo renombrarlos
a las columnas de SIPI y cuál es la clave natural para el upsert.

OJO: los nombres de campo del lado ODM (`origen`) son los esperados según
`seed_resources.py`, pero **deben confirmarse contra el schema real del dataset**
(`ODMClient.list_datasets()` da los `fields` exactos). Por eso van marcados.
"""
from dataclasses import dataclass, field

__all__ = ["MapeoMaestro", "MAPEOS"]


@dataclass
class MapeoMaestro:
    dataset_query_name: str        # queryName del dataset en la API de datos de ODM
    tabla_sipi: str                # tabla maestra destino en SIPI (esquema app)
    columnas: dict                 # {campo_odm: columna_sipi}
    clave_natural: str             # columna_sipi usada como clave para upsert
    descripcion: str = ""
    confirmado: bool = False       # True cuando los campos se han verificado contra el dataset real

    @property
    def campos_origen(self):
        return list(self.columnas.keys())


# Mapeos iniciales (geografía + actores con resource ya sembrado en ODM).
# `confirmado=False` => nombres de campo a verificar con list_datasets().
MAPEOS = [
    MapeoMaestro(
        dataset_query_name="geoComunidades",
        tabla_sipi="comunidades_autonomas",
        columnas={"codigo": "codigo_ine", "nombre": "nombre"},
        clave_natural="codigo_ine",
        descripcion="INE -> Comunidades Autónomas",
    ),
    MapeoMaestro(
        dataset_query_name="geoProvincias",
        tabla_sipi="provincias",
        columnas={"codigo": "codigo_ine", "nombre": "nombre", "codigoComunidad": "codigo_comunidad"},
        clave_natural="codigo_ine",
        descripcion="INE -> Provincias",
    ),
    MapeoMaestro(
        dataset_query_name="geoMunicipios",
        tabla_sipi="municipios",
        columnas={"codigo": "codigo_ine", "nombre": "nombre", "codigoProvincia": "codigo_provincia"},
        clave_natural="codigo_ine",
        descripcion="INE (codmun) -> Municipios",
    ),
    MapeoMaestro(
        dataset_query_name="dir3Unidades",
        tabla_sipi="administraciones",
        columnas={"codigo": "codigo_oficial", "denominacion": "nombre", "nivelAdmin": "ambito",
                  "codigoPadre": "codigo_padre"},
        clave_natural="codigo_oficial",
        descripcion="DIR3 -> Administraciones",
    ),
    MapeoMaestro(
        dataset_query_name="notarios",
        tabla_sipi="notarias",
        columnas={"codigoNotaria": "codigo_oficial", "nombre": "nombre", "municipio": "municipio_nombre"},
        clave_natural="codigo_oficial",
        descripcion="Guía Notarial (CGN) -> Notarías",
    ),
]
