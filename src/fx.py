"""Tasas de cambio (gratis, sin clave).

Baja las tasas de https://open.er-api.com (gratis, sin registro). Si no hay
internet, usa los valores fijos del config (si los pusiste). Todo es opcional y
nunca rompe el programa: si algo falla, devuelve None y el resto del programa
avisa con calma.
"""

from __future__ import annotations

import requests

_API = "https://open.er-api.com/v6/latest/USD"
_TIMEOUT = 10


def bajar_tasas() -> dict | None:
    """Devuelve {'USD_COP': float, 'JPY_COP': float} o None si falla."""
    try:
        r = requests.get(_API, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates", {})
        usd_cop = rates.get("COP")
        usd_jpy = rates.get("JPY")
        if not usd_cop or not usd_jpy:
            return None
        return {
            "USD_COP": float(usd_cop),
            # rates están en base USD: 1 USD = usd_jpy JPY y = usd_cop COP
            # entonces 1 JPY = usd_cop / usd_jpy COP
            "JPY_COP": float(usd_cop) / float(usd_jpy),
        }
    except Exception:
        return None


def resolver_tasas(config: dict) -> dict:
    """Combina lo que el usuario fijó en config con lo que se baja de internet.

    Los valores del config (si no son null) mandan. Lo que falte se intenta
    bajar. Devuelve {'USD_COP': float|None, 'JPY_COP': float|None}.
    """
    fx_cfg = (config or {}).get("fx", {}) or {}
    usd = fx_cfg.get("USD_COP")
    jpy = fx_cfg.get("JPY_COP")

    if usd is None or jpy is None:
        bajadas = bajar_tasas() or {}
        if usd is None:
            usd = bajadas.get("USD_COP")
        if jpy is None:
            jpy = bajadas.get("JPY_COP")

    return {"USD_COP": usd, "JPY_COP": jpy}
