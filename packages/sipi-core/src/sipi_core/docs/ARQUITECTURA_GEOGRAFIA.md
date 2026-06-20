# Arquitectura: Distribución Territorial de España

## Decisión arquitectónica

La jerarquía territorial de España **no es homogénea** en todo el Estado. Existen entidades
administrativas específicas de ciertas regiones que no encajan en una jerarquía lineal fija:

- **Galicia**: parroquia (entidad entre municipio y ELM, con identidad administrativa propia)
- **Asturias / Navarra**: concejo
- **Cataluña / Aragón**: comarca
- **Todo el Estado**: mancomunidades (agrupan municipios, no se subordinan a uno solo)
- **Canarias**: cabildo (nivel equivalente a Diputación pero con naturaleza distinta)
- **Ceuta / Melilla**: ciudad autónoma que es simultáneamente CCAA y municipio

Por este motivo se descarta un modelo de 4 tablas fijas (CCAA → Provincia → Municipio → ELM)
en favor de **una tabla recursiva `unidades_territoriales`**.

Adicionalmente, los inmuebles pueden estar ubicados en entidades sub-municipales (ELM,
parroquias), por lo que estas entidades son necesarias como referencia de localización,
no solo como dato estadístico.

---

## Modelo de datos: `unidades_territoriales`

```python
class UnidadTerritorial(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "unidades_territoriales"

    parent_id:      UUID → self (nullable — None indica raíz, i.e. CCAA)
    tipo:           str  # ver valores válidos abajo
    nivel:          int  # 1=CCAA, 2=Provincia, 3=Municipio, 4+=sub-municipal
    codigo:         str  # clave de negocio INE o CNIG (nullable para tipos sin código)
    codigo_padre:   str  # código INE del padre (para reconstrucción si se pierde el UUID)
    nombre:         str
    nombre_oficial: str  (nullable)
    latitud:        float (nullable)
    longitud:       float (nullable)
```

### Valores de `tipo`

| tipo | nivel | Fuente | Notas |
|---|---|---|---|
| `ccaa` | 1 | INE | 17 CCAA + 2 ciudades autónomas |
| `provincia` | 2 | INE | 52 provincias |
| `municipio` | 3 | CNIG Nomenclátor | ~8.200 municipios |
| `parroquia` | 4 | CNIG Nomenclátor | Galicia, Asturias |
| `elm` | 4 | CNIG Nomenclátor | Entidad Local Menor |
| `nucleo` | 4 | CNIG Nomenclátor | Núcleo de población |
| `diseminado` | 4 | CNIG Nomenclátor | Diseminado |
| `concejo` | 4 | CNIG Nomenclátor | Asturias, Navarra |

Los tipos `mancomunidad` y `comarca` son agrupaciones administrativas sin ubicación física propia,
por lo que **no son relevantes para la localización de inmuebles** y se excluyen del modelo.

---

## Fuentes de datos (vía OpenDataManager)

La tabla `unidades_territoriales` se nutre exclusivamente desde **ODMGR** a través de dos recursos:

### Recurso 1: España - CCAA y Provincias (INE)
- **Fetcher**: API REST
- **Fuentes**:
  - CCAA: `https://servicios.ine.es/wstempus/jsCache/ES/VALORES_VARIABLE/70`
  - Provincias: `https://servicios.ine.es/wstempus/jsCache/ES/VALORES_VARIABLE/20`
- **Target ODMGR**: `core.geo_territorio`
- **Campos clave**: `Codigo` (2 dígitos), `Nombre`, `FK_JerarquiaPadres` (ID interno INE)

### Recurso 2: España - Entidades de Población (CNIG)
- **Fetcher**: File Download (CSV)
- **Fuente**: CNIG Nomenclátor Geográfico (Centro de Descargas IGN)
  - URL: `https://centrodedescargas.cnig.es/CentroDescargas/nomenclator-geografico-municipios-entidades-poblacion`
- **Target ODMGR**: `core.geo_territorio` (misma tabla, `tipo` diferencia los registros)
- **Código jerárquico**: 11 dígitos → `CPRO(2) + CMUN(3) + ENTIDAD(6)`
  - El padre se deriva directamente de los primeros N dígitos del código
  - Municipio padre: `codigo[:5]`, Provincia padre: `codigo[:2]`

### Tabla staging ODMGR: `core.geo_territorio`

```
codigo          string   — clave INE o CNIG (clave de negocio)
codigo_padre    string   — código del padre (null para CCAA)
tipo            string   — ccaa | provincia | municipio | elm | parroquia | nucleo | ...
nivel           int      — 1=CCAA, 2=Provincia, 3=Municipio, 4+=sub-municipal
nombre          string
nombre_oficial  string   (nullable)
latitud         float    (nullable, solo CNIG)
longitud        float    (nullable, solo CNIG)
```

---

## Carga en SIPI-ETL: `cargar_geografia.py`

El script lee `geo_territorio` desde ODMGR (GraphQL data API, paginado) y carga
`unidades_territoriales` en orden ascendente de `nivel`:

```
Paso 1 — nivel=1 (CCAA):
  → INSERT unidades_territoriales(tipo='ccaa', parent_id=null, codigo=Codigo)
  → Construir: codigo_map { codigo: sipi_uuid }

Paso 2 — nivel=2 (Provincias):
  → Resolver FK_JerarquiaPadres[0].Id → ine_id_map → ccaa_uuid
  → INSERT unidades_territoriales(tipo='provincia', parent_id=ccaa_uuid)
  → Extender codigo_map

Paso 3 — nivel=3 (Municipios, desde CNIG):
  → codigo_padre = codigo[:2]  → prov_uuid desde codigo_map
  → INSERT unidades_territoriales(tipo='municipio', parent_id=prov_uuid)
  → Extender codigo_map

Paso 4 — nivel>=4 (ELM, Parroquias, Núcleos, desde CNIG):
  → codigo_padre = codigo[:5]  → municipio_uuid desde codigo_map
  → INSERT unidades_territoriales(tipo=tipo_cnig, parent_id=mun_uuid)
```

### Nota sobre FKs

Todas las FK en SIPI son **UUID**. El `codigo` INE/CNIG es una clave de negocio
que facilita el lookup durante la carga del ETL y la vinculación con fuentes externas
(catastro, registros de la propiedad, notarías…), pero nunca se usa como FK en la BD.

Los demás modelos que referencian una entidad territorial (Inmueble, Administracion,
Notaria, RegistroPropiedad…) apuntan a `unidades_territoriales.id` (UUID).

---

## Estado de implementación

- [ ] Refactor `sipi_core/models/geografia.py`: reemplazar 4 tablas por `UnidadTerritorial`
- [ ] Migración Alembic: drop tablas antiguas, create `unidades_territoriales`
- [ ] Actualizar FKs en todos los modelos relacionados
- [ ] Crear recurso ODMGR: España - CCAA y Provincias (INE)
- [ ] Crear recurso ODMGR: España - Entidades de Población (CNIG)
- [ ] Reescribir `cargar_geografia.py` en SIPI-ETL
