#!/usr/bin/env python3
"""
00_extraer_excel.py — Extracción: Excel CEE → CSVs por CCAA

Lee el Excel de inmatriculaciones de la CEE y genera un CSV por cada
hoja (comunidad autónoma), normalizando texto, expandiendo comillas y
filtrando totalizadores.

Uso:
    python scripts/00_extraer_excel.py --input data/input/Inmatriculaciones_CEE.xlsx
    python scripts/00_extraer_excel.py --input /ruta/al/excel.xlsx --output data/csv/
"""

import argparse
import os
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Provincias españolas principales para detectar CCAA multiprovinciales
# ---------------------------------------------------------------------------
PROVINCIAS_PRINCIPALES = {
    'ALAVA', 'ALBACETE', 'ALICANTE', 'ALMERIA', 'AVILA', 'BADAJOZ', 'BARCELONA',
    'BURGOS', 'CACERES', 'CADIZ', 'CASTELLON', 'CIUDAD REAL', 'CORDOBA', 'A CORUÑA',
    'CUENCA', 'GIRONA', 'GRANADA', 'GUADALAJARA', 'GUIPUZCOA', 'HUELVA', 'HUESCA',
    'JAEN', 'LEON', 'LLEIDA', 'LUGO', 'MALAGA', 'OURENSE', 'PALENCIA', 'PONTEVEDRA',
    'SALAMANCA', 'SEGOVIA', 'SEVILLA', 'SORIA', 'TARRAGONA', 'TERUEL', 'TOLEDO',
    'VALENCIA', 'VALLADOLID', 'VIZCAYA', 'ZAMORA', 'ZARAGOZA',
}


def normalizar_texto(texto):
    """Elimina acentos y caracteres diacríticos del texto."""
    if pd.isna(texto):
        return texto
    texto_nfd = unicodedata.normalize('NFD', str(texto))
    return ''.join(c for c in texto_nfd if unicodedata.category(c) != 'Mn')


def es_comilla(valor):
    if pd.isna(valor):
        return False
    return str(valor).strip() in ('"', '\\"')


def es_provincia_multiprovincial(texto):
    if not texto:
        return False
    texto_upper = str(texto).upper().strip()
    if 'Nº' in texto or 'NÚM' in texto_upper:
        return False
    return texto_upper in PROVINCIAS_PRINCIPALES


def es_totalizador(registro_val):
    if pd.isna(registro_val):
        return False
    return 'TOTAL' in str(registro_val).strip().upper()


def es_valor_booleano(valor):
    if pd.isna(valor):
        return False
    return str(valor).strip().upper() in {'SI', 'SÍ', 'NO', '0', '1', '0.0', '1.0'}


def convertir_a_booleano(valor):
    if pd.isna(valor):
        return None
    v = str(valor).strip().upper()
    if v in {'SI', 'SÍ', '1', '1.0'}:
        return True
    if v in {'NO', '0', '0.0'}:
        return False
    return None


def convertir_templo_dependencias(valor):
    if pd.isna(valor):
        return False
    v = str(valor).strip().upper()
    if v in {'', 'NAN'}:
        return False
    if v in {'SI', 'SÍ'}:
        return True
    return str(valor).strip()


def limpiar_comillas_externas(texto):
    if pd.isna(texto):
        return texto
    texto = str(texto).strip()
    if len(texto) >= 2 and texto[0] == '"' and texto[-1] == '"':
        texto = texto[1:-1].strip()
    return texto


def capitalizar_palabra(palabra):
    if not palabra:
        return palabra
    if '-' in palabra:
        return '-'.join(capitalizar_palabra(p) for p in palabra.split('-'))
    if "'" in palabra:
        return "'".join(capitalizar_palabra(p) for p in palabra.split("'"))
    return palabra.capitalize()


def capitalizar_toponimos(texto):
    if pd.isna(texto):
        return texto
    texto = limpiar_comillas_externas(texto)
    texto = str(texto)

    palabras = texto.split()
    palabras_may = sum(
        1 for p in palabras
        if len(p.replace('Nº', '').replace('nº', '')) > 1
        and not p.replace('Nº', '').replace('nº', '').isdigit()
        and p.replace('Nº', '').replace('nº', '').isupper()
    )
    total_sig = sum(
        1 for p in palabras
        if len(p.replace('Nº', '').replace('nº', '')) > 1
        and not p.replace('Nº', '').replace('nº', '').isdigit()
    )

    if not total_sig:
        debe = texto.isupper() or texto.islower()
    else:
        debe = palabras_may / total_sig > 0.5 or texto.isupper() or texto.islower()

    if not debe:
        return texto

    minusculas = {'de', 'del', 'la', 'el', 'los', 'las', 'y', 'e', 'o', 'u',
                  'a', 'en', 'con', 'por', 'para', 'sobre', 'bajo', 'entre', 'sin'}
    resultado = []
    for i, palabra in enumerate(palabras):
        pl = palabra.lower()
        if pl in {'nº'} or palabra == 'Nº':
            resultado.append('Nº')
        elif palabra.isdigit():
            resultado.append(palabra)
        elif i == 0:
            resultado.append(capitalizar_palabra(palabra))
        elif pl in minusculas:
            resultado.append(pl)
        else:
            resultado.append(capitalizar_palabra(palabra))
    return ' '.join(resultado)


def procesar_excel(excel_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    xls = pd.ExcelFile(excel_path)
    hojas = [s for s in xls.sheet_names if s != 'Hoja1']
    print(f"Procesando {len(hojas)} hojas...\n")

    estadisticas = []

    for sheet in hojas:
        print(f"  {sheet}...")
        df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
        comunidad_autonoma = str(df.iloc[0, 0]).strip()
        headers = list(df.iloc[1].values)
        df_raw = df.iloc[2:].reset_index(drop=True)

        # Detectar si es multiprovincial
        es_multi = False
        for _, row in df_raw.iterrows():
            col0, col1 = row.iloc[0], row.iloc[1]
            if pd.isna(col1) or str(col1).strip() in ('', '0'):
                if pd.notna(col0) and not es_comilla(col0):
                    if es_provincia_multiprovincial(str(col0).strip()):
                        es_multi = True
                        break

        provincia_actual = None if es_multi else comunidad_autonoma
        registro_actual = None
        filas = []

        for idx, row in df_raw.iterrows():
            col0, col1 = row.iloc[0], row.iloc[1]

            if pd.isna(col1) or str(col1).strip() in ('', '0'):
                if pd.notna(col0) and not es_comilla(col0):
                    texto = str(col0).strip()
                    if texto:
                        if es_multi and es_provincia_multiprovincial(texto):
                            provincia_actual = texto
                        else:
                            registro_actual = texto
                continue

            fila = {}
            for ci, header in enumerate(headers):
                if pd.isna(header):
                    continue
                valor = row.iloc[ci] if ci < len(row) else None
                if es_comilla(valor):
                    for pi in range(idx - 1, -1, -1):
                        pv = df_raw.iloc[pi, ci] if ci < len(df_raw.iloc[pi]) else None
                        if pd.notna(pv) and not es_comilla(pv):
                            valor = pv
                            break
                fila[str(header)] = valor

            if 'REGISTRO' in fila:
                if pd.isna(fila['REGISTRO']) or es_comilla(fila['REGISTRO']):
                    fila['REGISTRO'] = registro_actual

            if es_totalizador(fila.get('REGISTRO')):
                continue

            fila['Comunidad Autónoma'] = comunidad_autonoma
            fila['Provincia'] = provincia_actual
            filas.append(fila)

        df_final = pd.DataFrame(filas)

        # Normalizar el nombre de la columna de título (las hojas alternan 'Titulo'/'Título';
        # si no, Tenerife se quedaba sin denominación al cargar).
        for _alt in ('Título', 'TÍTULO', 'TITULO'):
            if _alt in df_final.columns and 'Titulo' not in df_final.columns:
                df_final = df_final.rename(columns={_alt: 'Titulo'})

        cols = ['Comunidad Autónoma', 'Provincia']
        for c in df_final.columns:
            if c not in cols and c not in ('Nº Orden', 'Total'):
                cols.append(c)
        df_final = df_final[cols].dropna(axis=1, how='all')

        if 'Templo y dependencias complementarias' in df_final.columns:
            df_final['Templo y dependencias complementarias'] = (
                df_final['Templo y dependencias complementarias'].apply(convertir_templo_dependencias)
            )

        for col in df_final.columns:
            if col in ('Comunidad Autónoma', 'Provincia', 'REGISTRO',
                       'Templo y dependencias complementarias'):
                continue
            muestra = df_final[col].dropna().head(200)
            if len(muestra) > 0 and all(es_valor_booleano(v) for v in muestra):
                df_final[col] = df_final[col].apply(convertir_a_booleano)

        for col in df_final.columns:
            if df_final[col].dtype == 'object' and col != 'Templo y dependencias complementarias':
                df_final[col] = df_final[col].apply(capitalizar_toponimos)

        for col in ('Comunidad Autónoma', 'Provincia', 'REGISTRO', 'Municipio'):
            if col in df_final.columns:
                df_final[col] = df_final[col].apply(normalizar_texto)

        # ── Denominación (refinamiento en la etapa de TRANSFORMACIÓN) ───────────────
        # Si la fila no trae Título, se compone una denominación legible a partir de
        # Tipo + Municipio (p. ej. "Solar en Ademuz", "Iglesia parroquial en …"), ya
        # capitalizados/normalizados arriba. Así el seeding nunca deja denominaciones
        # vacías ni genéricas de una sola palabra. El enriquecimiento con OSM/Wikidata
        # es una pasada posterior (cuando esos datos estén cargados).
        if 'Titulo' in df_final.columns:
            def _denominacion(r):
                tit = r.get('Titulo')
                if pd.notna(tit) and str(tit).strip():
                    return str(tit).strip()
                tipo = str(r.get('Tipo') or '').strip()
                muni = str(r.get('Municipio') or '').strip()
                base = tipo if tipo else 'Inmueble'
                return f"{base} en {muni}" if muni else base
            df_final['Titulo'] = df_final.apply(_denominacion, axis=1)

        for prov, count in df_final['Provincia'].value_counts().items():
            estadisticas.append({
                'Comunidad Autónoma': comunidad_autonoma,
                'Provincia': prov,
                'Número de inmatriculaciones': count,
            })

        csv_name = sheet.strip().replace(' ', '_').replace('/', '-') + '.csv'
        df_final.to_csv(output_dir / csv_name, index=False, encoding='utf-8-sig')
        print(f"    → {csv_name} ({len(df_final)} filas)")

    pd.DataFrame(estadisticas).sort_values(
        ['Comunidad Autónoma', 'Provincia']
    ).to_csv(output_dir / 'estadisticas_por_provincia.csv', index=False, encoding='utf-8-sig')

    print(f"\n✓ {len(hojas)} CSVs generados en {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Extrae Excel CEE → CSVs por CCAA")
    parser.add_argument("--input", type=Path, required=True,
                        help="Ruta al Excel (Inmatriculaciones_CEE.xlsx)")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent.parent.parent / "data" / "csv",
                        help="Directorio de salida para los CSVs (default: data/csv/)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: No se encuentra {args.input}")
        sys.exit(1)

    procesar_excel(args.input, args.output)


if __name__ == "__main__":
    main()
