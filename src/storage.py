"""Memoria simple de precios en un archivo JSON local.

Guarda el último precio visto de cada producto para poder saber cuándo BAJÓ y
no avisar dos veces de lo mismo.

El guardado es ATÓMICO: primero escribimos en un archivo temporal y luego lo
movemos sobre el definitivo. Así, si el programa se corta a la mitad, nunca
queda un `precios.json` corrupto y no se pierde el historial.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime

_ARCHIVO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "precios.json")


def cargar() -> dict:
    """Lee la memoria de precios. Si el archivo no existe o está dañado,
    devuelve un diccionario vacío sin romper el programa."""
    try:
        with open(_ARCHIVO, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    # Nos aseguramos de devolver siempre un diccionario.
    return data if isinstance(data, dict) else {}


def guardar(data: dict) -> None:
    """Escribe la memoria de precios de forma atómica (temporal + reemplazo)."""
    carpeta = os.path.dirname(_ARCHIVO) or "."
    os.makedirs(carpeta, exist_ok=True)
    # Archivo temporal en la MISMA carpeta para que os.replace sea atómico.
    fd, tmp = tempfile.mkstemp(prefix=".precios-", suffix=".tmp", dir=carpeta)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, _ARCHIVO)  # reemplazo atómico
    except Exception:
        # Si algo falla, no dejamos basura temporal tirada.
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def registrar(data: dict, producto_id: str, total_cop: float) -> dict:
    """Anota el precio actual y devuelve el registro previo del producto.

    No modifica el registro previo: trabaja sobre una copia del historial para
    que el valor devuelto siga reflejando el estado anterior (lo usa el monitor
    para saber si el precio subió o bajó).
    """
    previo = data.get(producto_id, {})
    historial = list(previo.get("historial", []))  # copia, no mutar el previo
    historial.append({"fecha": datetime.now().isoformat(timespec="minutes"),
                       "total_cop": total_cop})
    data[producto_id] = {
        "ultimo_cop": total_cop,
        "historial": historial[-50:],  # guardamos los últimos 50 puntos
    }
    return previo
