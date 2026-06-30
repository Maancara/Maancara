"""El bot: revisa todos los productos de la lista de deseos, calcula el costo
total puesto en Colombia, lo muestra en pantalla y avisa cuando un precio baja
de tu umbral.

Uso:
    python -m src.monitor              # revisa y muestra
    python -m src.monitor --solo-ver   # no manda alertas (solo imprime)
"""

from __future__ import annotations

import os
import sys

import yaml

from . import fx, notify, storage
from .landed_cost import calcular
from .stores import colombia

_RAIZ = os.path.dirname(os.path.dirname(__file__))


def _ruta(nombre: str) -> str:
    return os.path.join(_RAIZ, nombre)


def _cargar_yaml(ruta: str) -> dict:
    with open(ruta, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def cargar_config() -> dict:
    if os.path.exists(_ruta("config.yaml")):
        return _cargar_yaml(_ruta("config.yaml"))
    print("AVISO: no existe config.yaml. Copia config.example.yaml -> config.yaml")
    return _cargar_yaml(_ruta("config.example.yaml"))


def _moneda_de(mercado: str) -> str:
    return {"colombia": "COP", "amazon_us": "USD", "amazon_jp": "JPY"}.get(
        mercado, "COP"
    )


def _precio_de_producto(p: dict):
    """Devuelve (precio, moneda) o (None, None) si no se pudo obtener."""
    mercado = p.get("mercado")
    if mercado == "colombia":
        url = p.get("url", "")
        if not url or "pega-aqui" in url:
            return None, None
        res = colombia.leer_precio(url)
        if res is None:
            return None, None
        return res.precio, res.moneda
    # Amazon US / JP: precio puesto a mano (ver README, se usa Keepa/CamelCamelCamel)
    precio = p.get("precio_manual")
    if precio is None:
        return None, None
    return float(precio), _moneda_de(mercado)


def revisar(solo_ver: bool = False) -> int:
    config = cargar_config()
    watch = _cargar_yaml(_ruta("watchlist.yaml"))
    productos = watch.get("productos", []) or []

    tasas = fx.resolver_tasas(config)
    print(f"Tasas: 1 USD = {tasas.get('USD_COP')} COP | "
          f"1 JPY = {tasas.get('JPY_COP')} COP\n")

    db = storage.cargar()
    alertas = 0

    for p in productos:
        pid = p.get("id", "?")
        nombre = p.get("nombre", pid)
        precio, moneda = _precio_de_producto(p)

        if precio is None:
            print(f"• {nombre}: (no se pudo leer el precio — revisa la URL/datos)")
            continue

        d = calcular(precio, moneda, float(p.get("peso_kg") or 0), config, tasas)
        if d is None:
            print(f"• {nombre}: falta tasa de cambio, no se pudo calcular")
            continue

        umbral = p.get("umbral_cop")
        previo = storage.registrar(db, pid, d.total_cop)
        ultimo = previo.get("ultimo_cop")

        flecha = ""
        if ultimo is not None:
            if d.total_cop < ultimo:
                flecha = f"  ↓ bajó (antes {ultimo:,.0f})"
            elif d.total_cop > ultimo:
                flecha = f"  ↑ subió (antes {ultimo:,.0f})"

        print(f"• {nombre}")
        print(f"    precio: {precio:,.2f} {moneda}  ->  TOTAL en Colombia: "
              f"{d.total_cop:,.0f} COP   [{d.nota}]{flecha}")
        if umbral:
            print(f"    umbral: {umbral:,.0f} COP")

        # ¿Alertamos? Cuando está por debajo del umbral Y bajó respecto a la
        # última vez (o es la primera vez que lo vemos por debajo).
        # Si el producto no tiene umbral, no hay nada que comparar.
        bajo_umbral = umbral is not None and d.total_cop <= umbral
        bajo_antes = umbral is not None and ultimo is not None and ultimo <= umbral
        if bajo_umbral and not bajo_antes:
            alertas += 1
            msg = (
                f"💰 <b>{nombre}</b>\n"
                f"Total puesto en Colombia: <b>{d.total_cop:,.0f} COP</b>\n"
                f"(umbral: {umbral:,.0f} COP)\n"
                f"{d.nota}"
            )
            if solo_ver:
                print("    >>> [solo-ver] se habría enviado alerta")
            else:
                notify.enviar(config, msg)
                print("    >>> alerta enviada")

    storage.guardar(db)
    print(f"\nListo. Productos revisados: {len(productos)}. Alertas: {alertas}.")
    return alertas


if __name__ == "__main__":
    revisar(solo_ver="--solo-ver" in sys.argv)
