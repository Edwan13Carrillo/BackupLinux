#!/bin/bash

# ─────────────────────────────────────────────
#  yt-dlp Menu Interactivo (Versión Audiófila Real)
#  Autor: hecho con amor (Gemini) - Optimizado
# ─────────────────────────────────────────────

ZEN_PROFILE="$HOME/.config/zen/tbbfmrpu.Default (release)"
DOWNLOAD_DIR="./"
BOLD="\e[1m"
CYAN="\e[36m"
GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
RESET="\e[0m"

# ── Verificar que yt-dlp y ffmpeg estén instalados ──────
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${RED}[ERROR]${RESET} yt-dlp no está instalado. Instálalo con: sudo pacman -S yt-dlp"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[ERROR]${RESET} ffmpeg no está instalado (necesario para carátulas y videos). Instálalo con: sudo pacman -S ffmpeg"
    exit 1
fi

# ── Pedir URL con validación básica ──────────
pedir_url() {
    local url=""
    while [[ -z "$url" ]]; do
        echo -ne "${CYAN}  Pega la URL: ${RESET}" >&2
        read -r url
        if [[ -z "$url" ]]; then
            echo -e "${RED}  La URL no puede estar vacía.${RESET}" >&2
        fi
    done
    echo "$url"
}

# ── Seleccionar calidad de video ─────────────
seleccionar_calidad() {
    echo ""
    echo -e "${BOLD}  Selecciona la calidad de video:${RESET}"
    echo "    1) 1080p (Con audio Premium si está disponible)"
    echo "    2) 720p"
    echo "    3) 480p"
    echo "    4) 360p"
    echo "    5) La mejor disponible"
    echo ""
    echo -ne "${CYAN}  Opción [1-5]: ${RESET}"
    read -r opcion_calidad

    # Se mantiene la lógica del video + audio premium nativo
    case $opcion_calidad in
        1) FORMAT="bestvideo[height<=1080]+141/bestvideo[height<=1080]+bestaudio/best[height<=1080]" ;;
        2) FORMAT="bestvideo[height<=720]+141/bestvideo[height<=720]+bestaudio/best[height<=720]" ;;
        3) FORMAT="bestvideo[height<=480]+bestaudio/best[height<=480]" ;;
        4) FORMAT="bestvideo[height<=360]+bestaudio/best[height<=360]" ;;
        *) FORMAT="bestvideo+141/bestvideo+bestaudio/best" ;;
    esac
}

# ── Separador visual ─────────────────────────
separador() {
    echo -e "${CYAN}  ────────────────────────────────────────${RESET}"
}

# ════════════════════════════════════════════
#  OPCIONES DEL MENÚ
# ════════════════════════════════════════════

descargar_video() {
    echo ""
    separador
    echo -e "${BOLD}  📹 Descargar Video${RESET}"
    separador
    URL=$(pedir_url)
    seleccionar_calidad

    echo ""
    echo -e "${YELLOW}  Descargando video y fusionando con FFmpeg...${RESET}"
    yt-dlp -f "$FORMAT" \
           --cookies-from-browser "firefox:$ZEN_PROFILE" \
           --merge-output-format mkv \
           -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Descarga completada en: $DOWNLOAD_DIR${RESET}"
}

descargar_cancion() {
    echo ""
    separador
    echo -e "${BOLD}  🎵 Descargar Canción / ASMR${RESET}"
    separador
    URL=$(pedir_url)

    echo ""
    echo -e "${YELLOW}  Obteniendo flujo AAC nativo (Copia exacta del servidor)...${RESET}"
    yt-dlp -f "141/bestaudio[ext=m4a]" \
           --cookies-from-browser "firefox:$ZEN_PROFILE" \
           --embed-thumbnail \
           --add-metadata \
           -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Audio de alta fidelidad guardado en: $DOWNLOAD_DIR${RESET}"
}

descargar_playlist_musica() {
    echo ""
    separador
    echo -e "${BOLD}  🎶 Descargar Playlist de Música${RESET}"
    separador
    URL=$(pedir_url)

    echo ""
    echo -e "${YELLOW}  Descargando playlist en formato M4A/AAC nativo...${RESET}"
    yt-dlp -f "141/bestaudio[ext=m4a]" \
           --cookies-from-browser "firefox:$ZEN_PROFILE" \
           --embed-thumbnail \
           --add-metadata \
           --yes-playlist \
           -o "$DOWNLOAD_DIR/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Playlist guardada en: $DOWNLOAD_DIR/${RESET}"
    echo -e "${GREEN}  (Carpeta con el nombre de la playlist, ordenada numéricamente)${RESET}"
}

descargar_playlist_videos() {
    echo ""
    separador
    echo -e "${BOLD}  📂 Descargar Playlist de Videos${RESET}"
    separador
    URL=$(pedir_url)
    seleccionar_calidad

    echo ""
    echo -e "${YELLOW}  Descargando playlist de videos...${RESET}"
    yt-dlp -f "$FORMAT" \
           --cookies-from-browser "firefox:$ZEN_PROFILE" \
           --merge-output-format mkv \
           --yes-playlist \
           -o "$DOWNLOAD_DIR/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Playlist guardada en: $DOWNLOAD_DIR/${RESET}"
    echo -e "${GREEN}  (Carpeta con el nombre de la playlist, ordenada numéricamente)${RESET}"
}

# ════════════════════════════════════════════
#  MENÚ PRINCIPAL
# ════════════════════════════════════════════

mostrar_menu() {
    clear
    echo ""
    echo -e "${BOLD}${CYAN}  ╔══════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}  ║     yt-dlp — Edición Audiófila       ║${RESET}"
    echo -e "${BOLD}${CYAN}  ╚══════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "   ${BOLD}1.${RESET} 📹  Descargar un video"
    echo -e "   ${BOLD}2.${RESET} 🎵  Descargar una canción / ASMR"
    echo -e "   ${BOLD}3.${RESET} 🎶  Descargar playlist de música"
    echo -e "   ${BOLD}4.${RESET} 📂  Descargar playlist de videos"
    echo -e "   ${BOLD}5.${RESET} 🚪  Salir"
    echo ""
    separador
    echo -ne "${CYAN}  Elige una opción [1-5]: ${RESET}"
}

# ── Loop principal ───────────────────────────
while true; do
    mostrar_menu
    read -r opcion

    case $opcion in
        1) descargar_video ;;
        2) descargar_cancion ;;
        3) descargar_playlist_musica ;;
        4) descargar_playlist_videos ;;
        5)
            echo ""
            echo -e "${GREEN}  Hasta luego 👋 Disfruta el ASMR.${RESET}"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}  Opción inválida. Intenta de nuevo.${RESET}"
            ;;
    esac

    echo ""
    echo -ne "${YELLOW}  Presiona Enter para volver al menú...${RESET}"
    read -r
done
