"""Tasas de cambio (gratis, sin clave).

Baja las tasas desde varias fuentes gratuitas (sin registro). Si el usuario
fijó valores en `config.yaml`, esos mandan. Si no hay internet y no fijaste
nada, usa unas tasas de RESPALDO aproximadas para que la herramienta siga
funcionando (avisando que son aproximadas: ajústalas en config.yaml).

Objetivo: que el programa SIEMPRE pueda calcular y comparar, nunca se quede
"sin tasa".
"""

from __future__ import annotations

import requests

_TIMEOUT = 10

# Fuentes gratuitas y sin clave. Se prueban en orden hasta que una responda.
# Cada una tiene un formato distinto, así que trae su propia función de lectura.
_FUENTES = (
    "https://open.er-api.com/v6/latest/USD",
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
    "https://latest.currency-api.pages.dev/v1/currencies/usd.json",
)

# Último recurso si NO hay internet y NO fijaste tasas en config.yaml.
# Son aproximadas y envejecen; el programa avisa cuando las usa.
_RESPALDO = {"USD_COP": 4000.0, "JPY_COP": 27.0}


def _leer_er_api(data: dict) -> dict | None:
    """Formato open.er-api.com -> {'rates': {'COP': .., 'JPY': ..}}."""
    rates = data.get("rates", {})
    usd_cop = rates.get("COP")
    usd_jpy = rates.get("JPY")
    if not usd_cop or not usd_jpy:
        return None
    return {"USD_COP": float(usd_cop), "JPY_COP": float(usd_cop) / float(usd_jpy)}


def _leer_currency_api(data: dict) -> dict | None:
    """Formato fawazahmed0 currency-api -> {'usd': {'cop': .., 'jpy': ..}}."""
    usd = data.get("usd", {})
    usd_cop = usd.get("cop")
    usd_jpy = usd.get("jpy")
    if not usd_cop or not usd_jpy:
        return None
    return {"USD_COP": float(usd_cop), "JPY_COP": float(usd_cop) / float(usd_jpy)}


def bajar_tasas() -> dict | None:
    """Prueba las fuentes en orden. Devuelve {'USD_COP', 'JPY_COP'} o None."""
    for url in _FUENTES:
        try:
            r = requests.get(url, timeout=_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception:
            continue
        # rates están en base USD: 1 USD = usd_jpy JPY y = usd_cop COP,
        # entonces 1 JPY = usd_cop / usd_jpy COP.
        lector = _leer_er_api if "er-api" in url else _leer_currency_api
        tasas = lector(data)
        if tasas:
            return tasas
    return None


def resolver_tasas(config: dict) -> dict:
    """Combina lo que el usuario fijó en config con lo que se baja de internet.

    Prioridad: (1) valores del config, (2) internet, (3) respaldo aproximado.
    Devuelve siempre {'USD_COP': float, 'JPY_COP': float} — nunca None — para
    que el resto del programa pueda calcular.
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

    # Último recurso: respaldo aproximado, avisando.
    if usd is None or jpy is None:
        print("AVISO: no se pudieron obtener las tasas de cambio; uso valores "
              "aproximados de respaldo. Ajústalos en config.yaml (fx:).")
        if usd is None:
            usd = _RESPALDO["USD_COP"]
        if jpy is None:
            jpy = _RESPALDO["JPY_COP"]

    return {"USD_COP": float(usd), "JPY_COP": float(jpy)}
