# -*- coding: utf-8 -*-
"""Parámetros del proceso de descubrimiento, externalizados para investigación.

Todos los pesos y umbrales del pipeline viven aquí (no incrustados en la lógica),
para poder modificarlos, ejecutar experimentos y comparar resultados sin tocar
el código. Los valores por defecto son los validados sobre Pontevedra.

Se serializa a/desde JSON para registrar cada ejecución con su configuración y
para lanzar barridos de parámetros desde el banco de experimentos (experimento.py).
"""
import json
from dataclasses import dataclass, asdict, field, fields

__all__ = ["DiscoveryConfig"]


@dataclass
class DiscoveryConfig:
    # --- Emparejamiento (entity resolution CEE x OSM) ---
    peso_nombre: float = 0.78            # peso de la similitud de nombre en el score de match
    peso_tipo: float = 0.22              # peso de la compatibilidad de tipo
    bonus_municipio: float = 0.10        # bonus si coincide addr:city (modo province-wide)
    umbral_alta: float = 0.72            # banda ALTA (auto-fusión, solo si geo-confirmado)
    umbral_media: float = 0.50           # banda MEDIA (revisión)

    # --- Similitud de nombre ---
    peso_jaccard: float = 0.6            # Jaccard de tokens
    peso_secuencia: float = 0.4          # ratio de secuencia (difflib)

    # --- Bloqueo ---
    cap_token_distintivo_ratio: float = 0.25    # un token bloquea si df <= ratio*N
    tolerancia_proximidad_grados: float = 0.03  # rescate por cercanía en reverse-geocoding (~3 km)

    # --- Clasificador de religiosidad (scoring multi-señal) ---
    # OJO: la secularización NO es una penalización; es un evento valioso del
    # historial. Aquí solo van señales POSITIVAS de religiosidad.
    pesos_religiosidad: dict = field(default_factory=lambda: {
        "titularidad": 0.40,
        "uso_catastral": 0.25,
        "uso_osm": 0.20,
        "tipo": 0.15,
        "ontologia_wd": 0.10,
        "advocacion": 0.05,
    })
    umbral_religioso: float = 0.60           # confirmado
    umbral_religioso_revision: float = 0.35  # probable -> revisión

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_mapping(cls, data: dict) -> "DiscoveryConfig":
        """Construye desde un dict (p. ej. el JSONB del perfil de BD).

        Ignora claves desconocidas y respeta los defaults para las ausentes.
        DB-first: el servicio de descubrimiento carga el perfil activo y lo pasa
        por aqui; si no hay perfil, usa DiscoveryConfig() (defaults del codigo).
        """
        validos = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (data or {}).items() if k in validos})

    @classmethod
    def from_json(cls, path: str) -> "DiscoveryConfig":
        with open(path, encoding="utf-8") as f:
            return cls(**json.load(f))
