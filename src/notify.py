"""Alertas: Telegram (recomendado) y correo (opcional).

Ambos son gratis. Telegram es lo más fácil y confiable de montar (ver README).
Si están deshabilitados en config, simplemente no hace nada.
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

import requests


def enviar(config: dict, mensaje: str) -> None:
    """Manda el aviso por los canales que estén habilitados."""
    _telegram(config, mensaje)
    _correo(config, mensaje)


def _telegram(config: dict, mensaje: str) -> None:
    tg = (config or {}).get("telegram", {}) or {}
    if not tg.get("habilitado"):
        return
    token = tg.get("bot_token")
    chat_id = tg.get("chat_id")
    if not token or not chat_id or "PEGA" in str(token):
        print("[telegram] habilitado pero falta bot_token/chat_id en config.yaml")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"},
            timeout=15,
        )
        r.raise_for_status()
    except Exception as e:
        print(f"[telegram] no se pudo enviar: {e}")


def _correo(config: dict, mensaje: str) -> None:
    c = (config or {}).get("correo", {}) or {}
    if not c.get("habilitado"):
        return
    try:
        msg = MIMEText(mensaje, "plain", "utf-8")
        msg["Subject"] = "Ofertas Maancara: ¡bajó un precio!"
        msg["From"] = c.get("usuario", "")
        msg["To"] = c.get("destino", "")
        with smtplib.SMTP(c["smtp_host"], int(c["smtp_port"]), timeout=20) as s:
            s.starttls()
            s.login(c["usuario"], c["password"])
            s.send_message(msg)
    except Exception as e:
        print(f"[correo] no se pudo enviar: {e}")
