#!/bin/bash

# ─────────────────────────────────────────────
#  yt-dlp Menu Interactivo
#  Autor: hecho con amor (y Claude)
# ─────────────────────────────────────────────

DOWNLOAD_DIR="$HOME/Música"
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

# ── Pedir URL con validación básica ──────────
pedir_url() {
    local url=""
    while [[ -z "$url" ]]; do
        echo -ne "${CYAN}  Pega la URL: ${RESET}" >&2   # ← stderr
        read -r url
        if [[ -z "$url" ]]; then
            echo -e "${RED}  La URL no puede estar vacía.${RESET}" >&2  # ← stderr
        fi
    done
    echo "$url"  # ← este sí va a stdout (lo que captura $(...))
}

# ── Seleccionar calidad de video ─────────────
seleccionar_calidad() {
    echo ""
    echo -e "${BOLD}  Selecciona la calidad de video:${RESET}"
    echo "    1) 1080p"
    echo "    2) 720p"
    echo "    3) 480p"
    echo "    4) 360p"
    echo "    5) La mejor disponible"
    echo ""
    echo -ne "${CYAN}  Opción [1-5]: ${RESET}"
    read -r opcion_calidad

    case $opcion_calidad in
        1) FORMAT="bestvideo[height<=1080]+bestaudio/best[height<=1080]" ;;
        2) FORMAT="bestvideo[height<=720]+bestaudio/best[height<=720]" ;;
        3) FORMAT="bestvideo[height<=480]+bestaudio/best[height<=480]" ;;
        4) FORMAT="bestvideo[height<=360]+bestaudio/best[height<=360]" ;;
        *) FORMAT="bestvideo+bestaudio/best" ;;
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
    echo -e "${YELLOW}  Descargando video...${RESET}"
    yt-dlp -f "$FORMAT" \
           --merge-output-format mp4 \
           -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Descarga completada en: $DOWNLOAD_DIR${RESET}"
}

descargar_cancion() {
    echo ""
    separador
    echo -e "${BOLD}  🎵 Descargar Canción${RESET}"
    separador
    URL=$(pedir_url)

    echo ""
    echo -e "${YELLOW}  Descargando canción en MP3...${RESET}"
    yt-dlp -x \
           --audio-format mp3 \
           --audio-quality 0 \
           --embed-thumbnail \
           --add-metadata \
           -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Canción guardada en: $DOWNLOAD_DIR${RESET}"
}

descargar_playlist_musica() {
    echo ""
    separador
    echo -e "${BOLD}  🎶 Descargar Playlist de Música${RESET}"
    separador
    URL=$(pedir_url)

    echo ""
    echo -e "${YELLOW}  Descargando playlist de música en MP3...${RESET}"
    yt-dlp -x \
           --audio-format mp3 \
           --audio-quality 0 \
           --embed-thumbnail \
           --add-metadata \
           --yes-playlist \
           -o "$DOWNLOAD_DIR/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Playlist guardada en: $DOWNLOAD_DIR/${RESET}"
    echo -e "${GREEN}  (Carpeta con el nombre de la playlist, ordenada numéricamente)${RESET}"
}

descargar_patreon() {
    echo ""
    separador
    echo -e "${BOLD}  🎨 Descargar Video de Patreon${RESET}"
    separador
    echo -e "${YELLOW}  (Usa tus cookies del navegador para autenticarse)${RESET}"
    echo ""

    # Detectar navegador disponible
    BROWSER=""
    for b in firefox chromium chrome brave; do
        if command -v "$b" &> /dev/null; then
            BROWSER="$b"
            break
        fi
    done

    if [[ -z "$BROWSER" ]]; then
        echo -e "${RED}  No se detectó ningún navegador compatible (firefox, chromium, chrome, brave).${RESET}"
        echo -e "${RED}  Asegúrate de tener uno instalado y haber iniciado sesión en Patreon.${RESET}"
        return
    fi

    echo -e "${GREEN}  Navegador detectado: $BROWSER${RESET}"
    echo ""
    URL=$(pedir_url)
    seleccionar_calidad

    echo ""
    echo -e "${YELLOW}  Descargando video de Patreon...${RESET}"
    yt-dlp -f "$FORMAT" \
           --merge-output-format mp4 \
           --cookies-from-browser "$BROWSER" \
           -o "$HOME/Videos/%(title)s.%(ext)s" \
           "$URL"

    echo ""
    echo -e "${GREEN}  ✔ Video guardado en: $HOME/Videos/${RESET}"
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
           --merge-output-format mp4 \
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
    echo -e "${BOLD}${CYAN}  ║         yt-dlp — Menú Rápido         ║${RESET}"
    echo -e "${BOLD}${CYAN}  ╚══════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "   ${BOLD}1.${RESET} 📹  Descargar un video"
    echo -e "   ${BOLD}2.${RESET} 🎵  Descargar una canción"
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
            echo -e "${GREEN}  Hasta luego 👋${RESET}"
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
