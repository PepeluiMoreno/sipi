"""Pipeline consumer-side de desacralizaciones.

Detecta en el texto de los boletines diocesanos / CEE los decretos de
"reducción a uso profano" (c. 1222 §2), extrae {iglesia, municipio, diócesis,
fecha}, los enlaza al Inmueble del inventario y vuelca el cambio de estado de
uso (religioso -> profano), dejando el decreto como Documento/FuenteDocumental.
Ese cambio de estado es la señal que eleva la prioridad de la vigilancia de
portales.

ODM produce el texto (fetcher recipe-per-diócesis); aquí va SOLO el ensamblaje.
"""
from .detector import detectar_desacralizaciones, Desacralizacion

__all__ = ["detectar_desacralizaciones", "Desacralizacion"]
