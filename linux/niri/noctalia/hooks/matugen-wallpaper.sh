#!/usr/bin/env bash
set -Eeuo pipefail

trap 'notify-send -u critical "matugen-wallpaper" "Falló al generar el tema (revisá $LOCKFILE o corré el script a mano)"' ERR

[ -z "${NOCTALIA_WALLPAPER_PATH:-}" ] && exit 1

LOCKFILE="/tmp/matugen-wallpaper.lock"

exec 200>"$LOCKFILE"
flock -n 200 || exit 0   # ya hay una instancia corriendo -> se sale sin ruido, no es un error

matugen image "$NOCTALIA_WALLPAPER_PATH" --source-color-index 0
