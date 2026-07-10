#!/bin/bash

# ─────────────────────────────────────────────
#  yt-dlp GUI (Versión Audiófila con YAD)
#  Autor: Tú + Gemini
# ─────────────────────────────────────────────

# ── Verificar dependencias ──────
for req in yad yt-dlp ffmpeg; do
    if ! command -v $req &> /dev/null; then
        if [ "$req" = "yad" ]; then
            echo -e "\e[31m[ERROR]\e[0m Te falta 'yad' para la interfaz gráfica. Instálalo con: sudo pacman -S yad"
            exit 1
        fi
        yad --error --text="<big><b>Falta una dependencia: $req</b></big>\n\nInstálala antes de continuar." --title="Error de dependencias" --width=300
        exit 1
    fi
done

# Buscamos el perfil de Zen dinámicamente
ZEN_PROFILE_DIR=$(find "$HOME/.config/zen" -maxdepth 1 -type d -name "*.Default*" | head -n 1)

if [[ -z "$ZEN_PROFILE_DIR" ]]; then
    yad --error --text="<big><b>¡Uy!</b></big>\n\nParece que Zen Browser no está por aquí." --title="Falta Zen" --width=300
    exit 1
fi

# ── Bucle principal de la GUI ──────
while true; do
    # Mostrar el formulario principal (¡Aquí está la magia corregida con "!" en lugar de "^")
    FORM_DATA=$(yad --title="yt-dlp Edición Audiófila" \
        --form \
        --width=450 \
        --window-icon="browser-download" \
        --image="browser-download" \
        --text="<big><b>Gestor de Descargas</b></big>\nLlena los datos, elige tu veneno y dale a descargar." \
        --field="URL:" "" \
        --field="¿Qué quieres hacer hoy?":CB "📹 Descargar Video (YouTube)!🎵 Descargar Canción / ASMR!🎶 Descargar Playlist de Música!📂 Descargar Playlist de Videos!💰 Descargar de Patreon" \
        --field="Calidad de Video (Si aplica)":CB "1080p!720p!480p!360p!Mejor disponible" \
        --field="Carpeta de destino":DIR "$PWD" \
        --button="Salir y tocar pasto:1" \
        --button="Descargar:0")

    RET=$?

    # Si el usuario presiona "Salir" o cierra la ventana
    if [ $RET -ne 0 ]; then
        exit 0
    fi

    # Extraer los datos del formulario (yad separa los campos con '|')
    URL=$(echo "$FORM_DATA" | awk -F'|' '{print $1}')
    TIPO=$(echo "$FORM_DATA" | awk -F'|' '{print $2}')
    CALIDAD_STR=$(echo "$FORM_DATA" | awk -F'|' '{print $3}')
    DOWNLOAD_DIR=$(echo "$FORM_DATA" | awk -F'|' '{print $4}')

    # Validación de la URL
    if [[ -z "$URL" ]]; then
        yad --warning --text="La URL no se pone sola, capo.\nEscribe algo la próxima vez." --title="Advertencia" --width=300
        continue
    fi

    # Lógica de formato de calidad (solo para videos)
    FORMAT=""
    if [[ "$TIPO" == *"Video"* || "$TIPO" == *"Patreon"* ]]; then
        case "$CALIDAD_STR" in
            "1080p") FORMAT="bestvideo[height<=1080]+141/bestvideo[height<=1080]+bestaudio/best[height<=1080]" ;;
            "720p")  FORMAT="bestvideo[height<=720]+141/bestvideo[height<=720]+bestaudio/best[height<=720]" ;;
            "480p")  FORMAT="bestvideo[height<=480]+bestaudio/best[height<=480]" ;;
            "360p")  FORMAT="bestvideo[height<=360]+bestaudio/best[height<=360]" ;;
            *)       FORMAT="bestvideo+141/bestvideo+bestaudio/best" ;;
        esac
    fi

    # Preparar el comando de yt-dlp según la opción elegida
    case "$TIPO" in
        "📹 Descargar Video (YouTube)")
            CMD=(yt-dlp -f "$FORMAT" --cookies-from-browser "firefox:$ZEN_PROFILE_DIR" --merge-output-format mkv -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" "$URL")
            MSG="Descargando video y fusionando con FFmpeg..."
            ;;
        "🎵 Descargar Canción / ASMR")
            CMD=(yt-dlp -f "141/bestaudio" -x --audio-format m4a --cookies-from-browser "firefox:$ZEN_PROFILE_DIR" --embed-thumbnail --add-metadata -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" "$URL")
            MSG="Extrayendo audio AAC (Sin pérdida de calidad)..."
            ;;
        "🎶 Descargar Playlist de Música")
            CMD=(yt-dlp -f "141/bestaudio" -x --audio-format m4a --cookies-from-browser "firefox:$ZEN_PROFILE_DIR" --embed-thumbnail --add-metadata --yes-playlist -o "$DOWNLOAD_DIR/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" "$URL")
            MSG="Acaparando música... Descargando playlist entera."
            ;;
        "📂 Descargar Playlist de Videos")
            CMD=(yt-dlp -f "$FORMAT" --cookies-from-browser "firefox:$ZEN_PROFILE_DIR" --merge-output-format mkv --yes-playlist -o "$DOWNLOAD_DIR/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" "$URL")
            MSG="Vaciando los servidores de YouTube..."
            ;;
        "💰 Descargar de Patreon")
            FORMAT="bestvideo+bestaudio/best"
            CMD=(yt-dlp --cookies-from-browser "firefox:$ZEN_PROFILE_DIR" -f "$FORMAT" --merge-output-format mp4 --embed-thumbnail --add-metadata -o "$DOWNLOAD_DIR/%(creator)s - %(title)s.%(ext)s" "$URL")
            MSG="Saqueando el contenido premium de Patreon..."
            ;;
    esac

    # Ejecutar yt-dlp mostrando una barra de progreso de yad
    "${CMD[@]}" 2>&1 | yad --progress --pulsate --title="Trabajando..." \
        --text="<big><b>$MSG</b></big>\n\n<b>Destino:</b> $DOWNLOAD_DIR\n<i>Espera pacientemente...</i>" \
        --auto-close --auto-kill --width=450 --button="Cancelar:1"

    # Capturar el código de salida de yt-dlp (es el primer elemento en PIPESTATUS)
    RET_DL=${PIPESTATUS[0]}

    if [ $RET_DL -eq 0 ]; then
        yad --info --text="<big><b>✔ ¡Listazo!</b></big>\n\nTu archivo fue guardado con éxito en:\n<i>$DOWNLOAD_DIR</i>" --title="Éxito" --width=350
    else
        yad --error --text="<big><b>✘ F. Algo petó.</b></big>\n\nVerifica que:\n- La URL sea correcta.\n- Tengas la sesión abierta en Zen Browser.\n- El navegador esté cerrado por si las moscas." --title="Error de descarga" --width=350
    fi

done
