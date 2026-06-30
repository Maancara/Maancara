"""Pruebas que corren SIN internet (parseo de precios y cálculo de costos).

Correr con:   python -m pytest -q     o     python tests/test_logica.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src import storage  # noqa: E402
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


# --------------------------------------------------------------------------- #
# Memoria de precios (manejo del archivo precios.json)
# --------------------------------------------------------------------------- #
def test_storage_registrar_y_previo():
    # Primera vez: no hay registro previo.
    db = {}
    previo = storage.registrar(db, "p1", 100000.0)
    assert previo == {}
    assert db["p1"]["ultimo_cop"] == 100000.0
    assert len(db["p1"]["historial"]) == 1

    # Segunda vez: el previo conserva el precio anterior (no se contamina) y el
    # historial crece.
    previo = storage.registrar(db, "p1", 95000.0)
    assert previo["ultimo_cop"] == 100000.0
    assert db["p1"]["ultimo_cop"] == 95000.0
    assert len(db["p1"]["historial"]) == 2


def test_storage_historial_se_recorta_a_50():
    db = {}
    for i in range(60):
        storage.registrar(db, "p1", float(i))
    assert len(db["p1"]["historial"]) == 50
    # Conserva los más recientes.
    assert db["p1"]["historial"][-1]["total_cop"] == 59.0


def test_storage_round_trip(tmp_path=None):
    import json
    import tempfile

    carpeta = tempfile.mkdtemp()
    archivo = os.path.join(carpeta, "precios.json")
    original = storage._ARCHIVO
    storage._ARCHIVO = archivo
    try:
        # Archivo inexistente -> diccionario vacío.
        assert storage.cargar() == {}
        # Guardar y volver a leer.
        db = {"p1": {"ultimo_cop": 123.0, "historial": []}}
        storage.guardar(db)
        assert storage.cargar() == db
        # Archivo corrupto -> no rompe, devuelve {}.
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("{ esto no es json valido ")
        assert storage.cargar() == {}
        # Verifica que el guardado dejó JSON válido (no temporales sueltos).
        storage.guardar(db)
        with open(archivo, encoding="utf-8") as f:
            assert json.load(f) == db
        assert [n for n in os.listdir(carpeta) if n.startswith(".precios-")] == []
    finally:
        storage._ARCHIVO = original


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
