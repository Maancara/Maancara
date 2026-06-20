"""Lector de precios para tiendas de Colombia (Éxito, Alkosto, Olímpica,
Falabella, etc.).

Estrategia estable y poco intrusiva: en vez de "adivinar" leyendo el diseño de
la página (que cambia seguido), leemos los DATOS ESTRUCTURADOS que casi todas
las tiendas grandes incluyen para Google:

  1) JSON-LD  <script type="application/ld+json"> ... "@type": "Product" ...
  2) Si no hay, metatags tipo  <meta property="product:price:amount">

Esto funciona igual en Éxito, Alkosto, Falabella, etc. sin código por tienda.
Si una tienda cambia y deja de funcionar, le pides a Claude Code que la arregle.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

_TIMEOUT = 15
_HEADERS = {
    # Nos identificamos como un navegador normal; uso personal y de baja frecuencia.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-CO,es;q=0.9",
}


@dataclass
class PrecioTienda:
    precio: float
    moneda: str  # normalmente "COP"
    nombre: str | None = None


def leer_precio(url: str) -> PrecioTienda | None:
    """Descarga la página y devuelve el precio, o None si no se pudo."""
    try:
        r = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
    except Exception:
        return None
    return extraer_precio_de_html(r.text)


def extraer_precio_de_html(html: str) -> PrecioTienda | None:
    """Separa la lógica de parseo para poder probarla sin internet."""
    soup = BeautifulSoup(html, "html.parser")

    # --- 1) JSON-LD ---
    for tag in soup.find_all("script", type="application/ld+json"):
        if not tag.string and not tag.text:
            continue
        crudo = tag.string or tag.text
        for nodo in _iter_json_objs(crudo):
            precio = _precio_desde_jsonld(nodo)
            if precio is not None:
                return precio

    # --- 2) Metatags ---
    precio_meta = _meta(soup, "product:price:amount") or _meta(soup, "og:price:amount")
    moneda_meta = (
        _meta(soup, "product:price:currency")
        or _meta(soup, "og:price:currency")
        or "COP"
    )
    if precio_meta:
        valor = _a_numero(precio_meta)
        if valor is not None:
            nombre = _meta(soup, "og:title")
            return PrecioTienda(precio=valor, moneda=moneda_meta, nombre=nombre)

    return None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _iter_json_objs(crudo: str):
    """Carga un bloque JSON-LD y va devolviendo cada objeto (maneja listas y
    @graph)."""
    try:
        data = json.loads(crudo)
    except Exception:
        return
    pendientes = [data]
    while pendientes:
        actual = pendientes.pop()
        if isinstance(actual, list):
            pendientes.extend(actual)
        elif isinstance(actual, dict):
            if "@graph" in actual and isinstance(actual["@graph"], list):
                pendientes.extend(actual["@graph"])
            yield actual


def _precio_desde_jsonld(nodo: dict) -> PrecioTienda | None:
    tipo = nodo.get("@type")
    tipos = tipo if isinstance(tipo, list) else [tipo]
    if "Product" not in tipos:
        return None
    offers = nodo.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None
    precio = offers.get("price") or offers.get("lowPrice")
    valor = _a_numero(precio)
    if valor is None:
        return None
    moneda = offers.get("priceCurrency") or "COP"
    return PrecioTienda(precio=valor, moneda=moneda, nombre=nodo.get("name"))


def _meta(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find(
        "meta", attrs={"name": prop}
    )
    if tag and tag.get("content"):
        return tag["content"]
    return None


def _a_numero(valor) -> float | None:
    """Convierte '1.299.900' o '1299900.00' o 1299900 a float COP."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip()
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None
    # Si tiene coma y punto, asumimos el último separador como decimal.
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # Coma sola: en COP suele ser separador de miles -> quitarla.
        s = s.replace(",", "")
    else:
        # Punto(s): si hay varios o agrupa de a 3, es separador de miles.
        partes = s.split(".")
        if len(partes) > 2 or (len(partes) == 2 and len(partes[1]) == 3):
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None
