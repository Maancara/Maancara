"""Pruebas que corren SIN internet (parseo de precios y cálculo de costos).

Correr con:   python -m pytest -q     o     python tests/test_logica.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.landed_cost import calcular  # noqa: E402
from src.stores.colombia import _a_numero, extraer_precio_de_html  # noqa: E402

# --------------------------------------------------------------------------- #
# Parseo de números colombianos
# --------------------------------------------------------------------------- #
def test_numeros_colombianos():
    assert _a_numero("1.299.900") == 1299900.0
    assert _a_numero("$ 1.299.900") == 1299900.0
    assert _a_numero("79.99") == 79.99          # decimal real
    assert _a_numero("1299900") == 1299900.0
    assert _a_numero("1,299,900") == 1299900.0  # estilo USA
    assert _a_numero(6500) == 6500.0


# --------------------------------------------------------------------------- #
# Extraer precio desde HTML con JSON-LD (como hacen Éxito/Falabella/Alkosto)
# --------------------------------------------------------------------------- #
HTML_JSONLD = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"TV 55",
 "offers":{"@type":"Offer","price":"1299900","priceCurrency":"COP"}}
</script>
</head><body>...</body></html>
"""

HTML_META = """
<html><head>
<meta property="og:title" content="Audifonos X">
<meta property="product:price:amount" content="159900">
<meta property="product:price:currency" content="COP">
</head><body>...</body></html>
"""


def test_jsonld():
    r = extraer_precio_de_html(HTML_JSONLD)
    assert r is not None
    assert r.precio == 1299900.0
    assert r.moneda == "COP"
    assert r.nombre == "TV 55"


def test_metatags():
    r = extraer_precio_de_html(HTML_META)
    assert r is not None
    assert r.precio == 159900.0
    assert r.nombre == "Audifonos X"


def test_sin_precio():
    assert extraer_precio_de_html("<html><body>nada</body></html>") is None


# --------------------------------------------------------------------------- #
# Costo total puesto en Colombia
# --------------------------------------------------------------------------- #
CONFIG = {
    "importacion": {
        "casillero_usd_por_kg": 12.0,
        "manejo_usd": 5.0,
        "iva": 0.19,
        "arancel": 0.0,
        "de_minimis_usd": 200.0,
    }
}
TASAS = {"USD_COP": 4000.0, "JPY_COP": 27.0}


def test_compra_local_colombia():
    d = calcular(1299900, "COP", 0, CONFIG, TASAS)
    assert d.total_cop == 1299900
    assert d.envio_cop == 0
    assert d.impuestos_cop == 0


def test_amazon_us_bajo_de_minimis():
    # 79.99 USD, 0.5 kg -> bajo US$200 => sin impuestos
    d = calcular(79.99, "USD", 0.5, CONFIG, TASAS)
    producto = 79.99 * 4000
    envio = (12.0 * 0.5 + 5.0) * 4000
    assert round(d.producto_cop) == round(producto)
    assert round(d.envio_cop) == round(envio)
    assert d.impuestos_cop == 0
    assert "de-minimis" in d.nota


def test_amazon_us_con_impuestos():
    # 300 USD supera el de-minimis => paga IVA
    d = calcular(300.0, "USD", 1.0, CONFIG, TASAS)
    producto = 300.0 * 4000
    envio = (12.0 * 1.0 + 5.0) * 4000
    impuestos = (producto + envio) * 0.19
    assert round(d.impuestos_cop) == round(impuestos)


def test_amazon_japon():
    d = calcular(6500, "JPY", 0.8, CONFIG, TASAS)
    assert round(d.producto_cop) == round(6500 * 27.0)
    assert d.total_cop > d.producto_cop  # suma envío


def test_falta_tasa():
    d = calcular(50, "USD", 1.0, CONFIG, {"USD_COP": None, "JPY_COP": None})
    assert d is None


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASÓ  {nombre}")
            except AssertionError as e:
                fallos += 1
                print(f"FALLÓ {nombre}: {e}")
    sys.exit(1 if fallos else 0)
