# Extracción: Notarías (CGN)

**Código:** E5b
**Fuente:** Consejo General del Notariado (CGN)
**URL buscador:** `https://www.notariado.org/portal/Elige%20a%20tu%20notario%20orden`
**Script:** `extract/notarios/descargar_notarios_cgn.py`
**Salida:** `data/input/notarios/notarios_cgn_raw.csv`

---

## Descripción

El CGN publica un buscador de notarías en su web pública. El formulario permite
buscar por nombre, apellidos, código postal, municipio e idioma de trabajo.

El portal carga hasta ~835 resultados por consulta en el DOM del cliente y los
filtra mediante JavaScript (no hay llamadas AJAX por búsqueda). Para obtener
cobertura completa se itera por la capital de cada provincia (51 consultas en
total) y se deduplican los resultados por `nombre_notario + municipio`.

### Alternativa ODM

`extract/notarios/descargar_notarios.py` (E5) consume el mismo directorio pero
vía OpenDataManager, que gestiona la extracción automática. Usar E5b cuando
ODM no esté disponible o se quiera refrescar datos directamente.

---

## Parámetros del formulario

| Parámetro     | Tipo         | Descripción                          |
|---------------|--------------|--------------------------------------|
| `Nombre`      | texto libre  | Nombre del notario                   |
| `Apellidos`   | texto libre  | Apellidos del notario                |
| `CodigoPostal`| texto (5 d.) | Código postal de la notaría          |
| `Poblacion`   | texto libre  | Municipio (búsqueda parcial, POST)   |
| `Idioma`      | selección    | Idioma de trabajo del notario        |

**Form id:** `pbwg_form-eligetunotario`
**Método:** POST vía jQuery al mismo URL
**Validación JS:** requiere al menos un campo relleno (`checkInput()`)

---

## Estructura HTML de resultados

Los ítems de resultado tienen **clase numérica** (`.1`, `.2`, … hasta `.835`).
El contenedor de paginación es `#zzoz_pagination` (librería bootpag, lado cliente).
El script intenta localizar los ítems en este orden:

1. Contenedor con `id="zzoz_resultsContainer"` o clase que contenga `result`
2. Elementos con clase numérica en todo el documento
3. `div`/`li` cuyo texto contenga la palabra "notaría" / "notario"

### Campos extraídos por regex

| Campo          | Patrón                                      |
|----------------|---------------------------------------------|
| `nombre_notario` | Primera etiqueta `<strong>`, `<b>`, `<h2>`  |
| `codigo_postal`  | `\b\d{5}\b`                                 |
| `telefono`       | `9\d{8}` ó `6\d{8}` ó `+34…`               |
| `email`          | patrón estándar `user@domain.tld`           |
| `numero_protocolo` | `Nº \d+` ó `Protocolo \d+`               |
| `url_notaria`    | `<a href>` dentro del ítem                  |

---

## Ejecución

```bash
cd SIPI-ETL

# Descarga completa (51 provincias)
python extract/notarios/descargar_notarios_cgn.py

# Solo una provincia (para pruebas)
python extract/notarios/descargar_notarios_cgn.py --provincia Madrid

# Dry-run (no guarda CSV)
python extract/notarios/descargar_notarios_cgn.py --dry-run

# Con Playwright (si el HTML sin JS no contiene resultados)
pip install playwright && playwright install chromium
python extract/notarios/descargar_notarios_cgn.py --playwright

# Ajustar delay entre peticiones
python extract/notarios/descargar_notarios_cgn.py --delay 1.0
```

---

## Limitaciones conocidas

- **Cobertura parcial por municipio:** solo se consultan las 51 capitales de
  provincia. Notarías en municipios pequeños pueden no aparecer. Segunda pasada
  con lista completa de municipios si se detectan huecos.
- **JS rendering:** si el servidor exige JavaScript para renderizar resultados,
  usar `--playwright`. El flag activa `PlaywrightSync` con Chromium headless.
- **Sin paginación servidor:** todos los resultados están en el DOM; la
  paginación (`#zzoz_pagination`) es puramente visual/cliente.
- **Álava / Vitoria-Gasteiz:** puede requerir el nombre en euskera
  (`Gasteiz`) si la búsqueda por "Vitoria-Gasteiz" no devuelve resultados.

---

## Pipeline completa

```
E5b  extract/notarios/descargar_notarios_cgn.py   → data/input/notarios/notarios_cgn_raw.csv
T5   transform/notarios/transformar_notarios.py    → data/output/notarios/notarios.csv
L5   load/cargar_notarios.py                       → sipi.notarias
```

---

## TODO

- [ ] Validar que los resultados contienen datos reales (posible JS-only render)
- [ ] Si JS-only: configurar el recurso ODM en lugar de usar este script
- [ ] Segunda pasada por municipios no-capital para cobertura completa
- [ ] Implementar T5 (`transformar_notarios.py`) y L5 (`cargar_notarios.py`)
