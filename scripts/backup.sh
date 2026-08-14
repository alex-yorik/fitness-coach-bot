#!/bin/bash
# Резервное копирование SQLite БД через атомарный sqlite backup API.
# Запуск: cron (root) или вручную. Конфигурация — переменными окружения.
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/fitness-coach/backups}"
DB_PATH="${DB_PATH:-/opt/fitness-coach/data/database.db}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

DST="$BACKUP_DIR/db-$(date +%F).db"

python3 - "$DB_PATH" "$DST" <<'PY'
import os
import sqlite3
import sys

src, dst = sys.argv[1], sys.argv[2]
sqlite3.connect(src).backup(sqlite3.connect(dst))
os.chmod(dst, 0o600)
PY

find "$BACKUP_DIR" -name 'db-*.db' -mtime "+$RETENTION_DAYS" -delete
