# -*- coding: utf-8 -*-
"""Banco de experimentos del descubrimiento.

Permite ejecutar la fusión con distintas `DiscoveryConfig` y comparar el efecto,
para ajustar pesos/umbrales con evidencia en vez de a ojo.

- `proxies(resumen)`: métricas-proxy de una ejecución (no exigen verdad de
  referencia): reparto de bandas, geo-confirmación, nº de hallazgos, cobertura.
- `comparar(...)`: ejecuta varias configs sobre los mismos datos y las pone en
  paralelo.
- `barrido(...)`: varía UN parámetro sobre una lista de valores.
- `evaluar(matches, gold)`: precisión/recall/F1 SI hay una muestra etiquetada
  a mano (la verdad de referencia sale de la cola de revisión).
"""
from copy import deepcopy
from dataclasses import replace

from .config import DiscoveryConfig
from .seed import run_fusion

__all__ = ["proxies", "comparar", "barrido", "evaluar"]


def proxies(resumen: dict) -> dict:
    """Extrae métricas-proxy numéricas del resumen, de forma defensiva."""
    out = {}
    for k, v in (resumen or {}).items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = v
        elif isinstance(v, dict):  # p.ej. {'ALTA': 83, 'MEDIA': 40, ...}
            for kk, vv in v.items():
                if isinstance(vv, (int, float)) and not isinstance(vv, bool):
                    out[f"{k}.{kk}"] = vv
    return out


def comparar(csv_dir, osm_json, configs: dict, **run_kwargs) -> dict:
    """Ejecuta `run_fusion` con cada config nombrada y devuelve {nombre: proxies}.

    `configs`: {"nombre": DiscoveryConfig, ...}. `run_kwargs` se pasa a run_fusion
    (provincia, ccaa, osm_boundaries...).
    """
    resultados = {}
    for nombre, cfg in configs.items():
        _, resumen = run_fusion(csv_dir, osm_json, config=cfg, **run_kwargs)
        resultados[nombre] = proxies(resumen)
    _imprimir_tabla(resultados)
    return resultados


def barrido(csv_dir, osm_json, base: DiscoveryConfig, parametro: str, valores, **run_kwargs) -> dict:
    """Varía un único `parametro` de `base` sobre `valores` y compara."""
    base = base or DiscoveryConfig()
    configs = {}
    for v in valores:
        cfg = replace(base, **{parametro: v}) if not isinstance(getattr(base, parametro), dict) \
            else _replace_dict(base, parametro, v)
        configs[f"{parametro}={v}"] = cfg
    return comparar(csv_dir, osm_json, configs, **run_kwargs)


def _replace_dict(base, parametro, v):
    cfg = deepcopy(base)
    setattr(cfg, parametro, v)
    return cfg


def evaluar(matches, gold_pairs, cee_key=lambda c: getattr(c, "registro", id(c)),
            osm_key=lambda o: getattr(o, "osm_id", id(o))) -> dict:
    """Precisión/recall/F1 de los matches frente a una muestra etiquetada.

    `gold_pairs`: conjunto de pares verdaderos {(clave_cee, clave_osm), ...}.
    Solo cuenta predicciones en banda ALTA/MEDIA. Requiere etiquetas reales.
    """
    pred = set()
    for m in matches:
        if m.osm is not None and m.band in ("ALTA", "MEDIA"):
            pred.add((cee_key(m.cee), osm_key(m.osm)))
    gold = set(gold_pairs)
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(prec, 4),
            "recall": round(rec, 4), "f1": round(f1, 4)}


def _imprimir_tabla(resultados: dict) -> None:
    if not resultados:
        return
    claves = sorted({k for d in resultados.values() for k in d})
    nombres = list(resultados)
    w = max([len(k) for k in claves] + [10])
    print(f"{'metrica'.ljust(w)} | " + " | ".join(n[:14].rjust(14) for n in nombres))
    print("-" * (w + 3 + 17 * len(nombres)))
    for k in claves:
        fila = [str(resultados[n].get(k, "")).rjust(14) for n in nombres]
        print(f"{k.ljust(w)} | " + " | ".join(fila))
