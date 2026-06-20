"""Cálculo del "costo total puesto en Colombia".

Esta es la parte de verdad valiosa: convierte cualquier precio extranjero a
pesos colombianos sumando casillero e impuestos, para poder comparar de forma
justa entre Colombia, Amazon US y Amazon Japón.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Desglose:
    total_cop: float
    producto_cop: float
    envio_cop: float
    impuestos_cop: float
    nota: str = ""


def _a_cop(precio: float, moneda: str, tasas: dict) -> float | None:
    moneda = (moneda or "").upper()
    if moneda == "COP":
        return precio
    if moneda == "USD":
        t = tasas.get("USD_COP")
        return precio * t if t else None
    if moneda == "JPY":
        t = tasas.get("JPY_COP")
        return precio * t if t else None
    return None


def calcular(
    precio: float,
    moneda: str,
    peso_kg: float,
    config: dict,
    tasas: dict,
) -> Desglose | None:
    """Devuelve el desglose en COP, o None si falta una tasa de cambio."""
    imp = (config or {}).get("importacion", {}) or {}

    producto_cop = _a_cop(precio, moneda, tasas)
    if producto_cop is None:
        return None

    # Compra local en Colombia: sin envío internacional ni impuestos de importación.
    if (moneda or "").upper() == "COP" or not peso_kg:
        return Desglose(
            total_cop=producto_cop,
            producto_cop=producto_cop,
            envio_cop=0.0,
            impuestos_cop=0.0,
            nota="compra local (sin importación)",
        )

    usd_cop = tasas.get("USD_COP")
    if not usd_cop:
        return None

    # --- Envío / casillero (se cotiza en USD por kilo) ---
    casillero_usd = imp.get("casillero_usd_por_kg", 0.0) * peso_kg
    casillero_usd += imp.get("manejo_usd", 0.0)
    envio_cop = casillero_usd * usd_cop

    # --- Impuestos de importación ---
    precio_usd = precio if (moneda or "").upper() == "USD" else producto_cop / usd_cop
    de_minimis = imp.get("de_minimis_usd", 0.0) or 0.0
    if de_minimis and precio_usd <= de_minimis:
        impuestos_cop = 0.0
        nota = f"bajo de-minimis (<= US${de_minimis:.0f}): sin impuestos"
    else:
        base = producto_cop + envio_cop
        iva = imp.get("iva", 0.0) or 0.0
        arancel = imp.get("arancel", 0.0) or 0.0
        impuestos_cop = base * (iva + arancel)
        nota = f"importado (IVA {iva*100:.0f}% + arancel {arancel*100:.0f}%)"

    total = producto_cop + envio_cop + impuestos_cop
    return Desglose(
        total_cop=total,
        producto_cop=producto_cop,
        envio_cop=envio_cop,
        impuestos_cop=impuestos_cop,
        nota=nota,
    )
