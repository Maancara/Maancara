#!/usr/bin/env bash
# Ejecuta una revisión de precios. Úsalo a mano o desde cron (Mac/Linux).
cd "$(dirname "$0")/.." || exit 1
python3 -m src.monitor "$@"
