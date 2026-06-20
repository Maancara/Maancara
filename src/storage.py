"""Memoria simple de precios en un archivo JSON local.

Guarda el último precio visto de cada producto para poder saber cuándo BAJÓ y
no avisar dos veces de lo mismo.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

_ARCHIVO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "precios.json")


def cargar() -> dict:
    try:
        with open(_ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar(data: dict) -> None:
    with open(_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def registrar(data: dict, producto_id: str, total_cop: float) -> dict:
    """Anota el precio actual y devuelve el registro previo del producto."""
    previo = data.get(producto_id, {})
    historial = previo.get("historial", [])
    historial.append({"fecha": datetime.now().isoformat(timespec="minutes"),
                       "total_cop": total_cop})
    data[producto_id] = {
        "ultimo_cop": total_cop,
        "historial": historial[-50:],  # guardamos los últimos 50 puntos
    }
    return previo
