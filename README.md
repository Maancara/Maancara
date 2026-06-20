# Maancara — Buscador y vigilante de ofertas (Colombia · USA · Japón)

Herramienta **personal y gratis** que corre en tu PC. Vigila los productos que tú
elijas y te **avisa por Telegram (o correo)** cuando bajan de precio, comparando el
**costo total puesto en Colombia** entre Colombia, Amazon US y Amazon Japón
(incluyendo dólar/yen, casillero e impuestos).

> En palabras simples: tú armas tu **lista de deseos** y la herramienta te dice
> *dónde* y *cuándo* comprar más barato.

---

## 🧠 ¿Cómo funciona? (las dos piezas)

1. **El bot** (`src/monitor.py`): un programa que se ejecuta cada cierto tiempo,
   revisa los precios y te manda el aviso. Hace la **vigilancia automática**.
2. **Claude Code** (la IA con la que chateas): la usas para **buscar a pedido**
   ("búscame este producto en los 3 mercados") y para **arreglar el bot** si una
   tienda cambia su página. Tú no programas: le pides.

---

## 🚀 Puesta en marcha (una sola vez)

1. Instala [Python 3.11+](https://www.python.org/downloads/) (marca *"Add to PATH"*).
2. Abre una terminal en esta carpeta e instala las librerías:
   ```
   pip install -r requirements.txt
   ```
3. Crea tu archivo de configuración personal:
   ```
   cp config.example.yaml config.yaml      # en Windows:  copy config.example.yaml config.yaml
   ```
   `config.yaml` lleva tus datos privados y **no se sube a internet**.

---

## 🛒 Tu lista de deseos (`watchlist.yaml`)

Aquí pones lo que quieres vigilar. Dos tipos de producto:

- **Tiendas de Colombia** (Éxito, Alkosto, Olímpica, Falabella…): pega la **URL**
  de la página del producto. El bot lee el precio solo.
- **Amazon US / Japón**: ver la sección de abajo. Pones el precio actual a mano en
  `precio_manual` y lo actualizas cuando Keepa/CamelCamelCamel te avise.

Para cada producto defines `umbral_cop`: el precio (total, puesto en Colombia) por
debajo del cual quieres que te avise.

---

## ▶️ Usarlo

- Ver precios ahora (sin mandar alertas):
  ```
  python -m src.monitor --solo-ver
  ```
- Revisión normal (manda alertas si algo bajó del umbral):
  ```
  python -m src.monitor
  ```
  o con los atajos: `scripts/run_once.sh` (Mac/Linux) · `scripts\run_once.bat` (Windows).

### Vigilancia automática (que revise solo)
- **Windows**: *Programador de tareas* → tarea nueva → que ejecute `scripts\run_once.bat`
  cada 6–12 horas.
- **Mac/Linux**: `crontab -e` y agrega (ejemplo, 2 veces al día):
  ```
  0 9,21 * * *  /ruta/a/Maancara/scripts/run_once.sh
  ```

---

## 🔔 Alertas por Telegram (gratis, recomendado)

1. En Telegram, habla con **@BotFather** → `/newbot` → te da un **bot_token**.
2. Escríbele algo a tu nuevo bot, luego abre en el navegador:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` y copia tu **chat_id**.
3. Pon `habilitado: true`, el `bot_token` y el `chat_id` en `config.yaml`.

(El correo es opcional; instrucciones en `config.example.yaml`. Con Gmail necesitas
una *"contraseña de aplicación"*, no tu clave normal.)

---

## 🇺🇸🇯🇵 Amazon US y Japón (sin pagar y estable)

Amazon bloquea a los robots, así que **no reinventamos la rueda**: usa herramientas
gratis que ya hacen el trabajo y mandan alertas:

- **Keepa** (keepa.com): historial de precios y alertas gratis para Amazon US, Japón
  y otros 9 países. Extensión de navegador.
- **CamelCamelCamel** (camelcamelcamel.com): alertas de bajada de precio **por correo**
  (Amazon US).

Flujo: pones tu alerta en Keepa/CamelCamelCamel → cuando te avisen un precio nuevo,
lo escribes en `precio_manual` de ese producto en `watchlist.yaml`. Así Maancara lo
compara con Colombia y Japón incluyendo casillero e impuestos.

> El **casillero** (Aeropost, etc.) es un servicio que contratas aparte; aquí solo
> calculamos su costo. Ajusta las tarifas e impuestos en `config.yaml`.

---

## 🔎 Búsqueda "a pedido"

¿Quieres descubrir un producto nuevo? Pídeselo a **Claude Code** en lenguaje natural
("búscame un monitor 27\" en Éxito, Alkosto y Amazon, y compárame el costo puesto en
Colombia"). Si te gusta, dile que lo agregue a `watchlist.yaml` para vigilarlo.

---

## ✅ Probar que todo está bien

```
python tests/test_logica.py
```
Prueba el lector de precios y el cálculo de costos **sin necesitar internet**.

---

## ⚠️ Límites honestos

- Vigila tu **lista de deseos**, no "todo internet". Para descubrir cosas nuevas usas
  la búsqueda a pedido con Claude Code.
- Si una tienda de Colombia cambia su página y deja de leerse, dile a Claude Code que
  arregle `src/stores/colombia.py`. No es "cero mantenimiento", pero se arregla rápido.
- Las tasas de cambio e impuestos son configurables; revísalos de vez en cuando.
- Uso **personal** y de baja frecuencia (respetuoso con las tiendas).
