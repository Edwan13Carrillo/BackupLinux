#!/bin/bash

# ─────────────────────────────────────────────
#  Descargador de videos de Patreon
#  Usa las cookies de Firefox automáticamente
# ─────────────────────────────────────────────

ZEN_PROFILE="$HOME/.config/zen/megquvp9.Default (release)"
DOWNLOAD_DIR="./"
BOLD="\e[1m"
CYAN="\e[36m"
GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
RESET="\e[0m"

# ── Verificar que yt-dlp esté instalado ──────
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${RED}[ERROR]${RESET} yt-dlp no está instalado. Instálalo con: sudo pacman -S yt-dlp"
    exit 1
fi

# ── Crear carpeta destino si no existe ───────
mkdir -p "$DOWNLOAD_DIR"

# ── Cabecera ─────────────────────────────────
clear
echo ""
echo -e "${BOLD}${CYAN}  ╔══════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}  ║       Patreon Downloader 🎬           ║${RESET}"
echo -e "${BOLD}${CYAN}  ╚══════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Carpeta destino: ${CYAN}$DOWNLOAD_DIR${RESET}"
echo -e "  Autenticación:   ${CYAN}Cookies de Firefox${RESET}"
echo ""
echo -e "  ${CYAN}────────────────────────────────────────${RESET}"

# ── Pedir URL ────────────────────────────────
URL=""
while [[ -z "$URL" ]]; do
    echo -ne "${CYAN}  Pega la URL del video de Patreon: ${RESET}"
    read -r URL
    if [[ -z "$URL" ]]; then
        echo -e "${RED}  La URL no puede estar vacía.${RESET}"
    fi
done

FORMAT="bestvideo+bestaudio/best"

# ── Descarga ──────────────────────────────────
echo ""
echo -e "${YELLOW}  Descargando video...${RESET}"
echo ""

yt-dlp \
    --cookies-from-browser "firefox:$ZEN_PROFILE" \
    -f "$FORMAT" \
    --merge-output-format mp4 \
    --embed-thumbnail \
    --add-metadata \
    -o "$DOWNLOAD_DIR/%(creator)s - %(title)s.%(ext)s" \
    "$URL"

# ── Resultado ─────────────────────────────────
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}  ✔ Video guardado ${RESET}"
    echo ""
else
    echo ""
    echo -e "${RED}  ✘ Algo salió mal. Verifica que:${RESET}"
    echo -e "${RED}    - Tengas sesión activa de Patreon en Firefox${RESET}"
    echo -e "${RED}    - Firefox esté cerrado o al menos no en uso activo${RESET}"
    echo -e "${RED}    - La URL sea de un video al que estés suscrito${RESET}"
    echo ""
fi
