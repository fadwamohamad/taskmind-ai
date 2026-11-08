#!/usr/bin/env bash
set -euo pipefail
DB_SRC="${1:-/opt/taskmind/taskmind.db}"
BACKUP_DIR="${2:-/opt/taskmind/backups}"
mkdir -p "$BACKUP_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"
if [ -f "$DB_SRC" ]; then
  cp "$DB_SRC" "$BACKUP_DIR/taskmind-$stamp.db"
  echo "Backup written: $BACKUP_DIR/taskmind-$stamp.db"
else
  echo "No database at $DB_SRC" >&2
  exit 1
fi
# Keep last 7 backups
ls -1t "$BACKUP_DIR/taskmind-"*.db 2>/dev/null | tail -n +8 | xargs -r rm --
