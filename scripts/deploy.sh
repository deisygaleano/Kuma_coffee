#!/usr/bin/env bash
# Se ejecuta en el servidor (vía SSH desde el workflow de GitHub Actions,
# o manualmente). Es autocontenido: actualiza el código, respalda la BD,
# reconstruye los contenedores y valida que todo haya quedado corriendo.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Actualizando código..."
git pull origin main

BACKUP_DIR="$HOME/kuma_coffee_backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

DB_CID=$(docker compose ps -q db || true)
if [ -n "$DB_CID" ] && [ "$(docker inspect -f '{{.State.Running}}' "$DB_CID" 2>/dev/null)" = "true" ]; then
  echo "Respaldando base de datos antes del despliegue..."
  set -a
  source .env
  set +a
  docker compose exec -T db mysqldump -u root -p"${DB_ROOT_PASSWORD}" "${DB_NAME}" > "$BACKUP_DIR/backup_${TIMESTAMP}.sql"
  # Conserva solo los últimos 10 backups para no llenar el disco.
  ls -t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | tail -n +11 | xargs -r rm --
  echo "Backup guardado en $BACKUP_DIR/backup_${TIMESTAMP}.sql"
else
  echo "El contenedor db no está corriendo todavía; se omite el backup (primer despliegue)."
fi

echo "Reconstruyendo y desplegando contenedores..."
docker compose up -d --build

echo "Esperando a que los servicios levanten..."
sleep 10

WEB_CID=$(docker compose ps -q web)
if [ "$(docker inspect -f '{{.State.Running}}' "$WEB_CID" 2>/dev/null)" != "true" ]; then
  echo "El contenedor web no quedó corriendo tras el despliegue. Logs:"
  docker compose logs --tail=100 web
  exit 1
fi

DB_CID_AFTER=$(docker compose ps -q db)
if [ -n "$DB_CID_AFTER" ] && [ "$(docker inspect -f '{{.State.Running}}' "$DB_CID_AFTER" 2>/dev/null)" != "true" ]; then
  echo "El contenedor db no quedó corriendo tras el despliegue. Logs:"
  docker compose logs --tail=100 db
  exit 1
fi

echo "Despliegue completado correctamente. Backup previo disponible en $BACKUP_DIR si hace falta restaurar."
