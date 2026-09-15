source /usr/share/cachyos-fish-config/cachyos-config.fish

# overwrite greeting
# potentially disabling fastfetch
#function fish_greeting
#    # smth smth
#end

function bgsddm
    # Comprobar que se pasó exactamente un archivo
    if test (count $argv) -ne 1
        echo "Uso: bgsddm <archivo.mp4>"
        return 1
    end

    set -l video $argv[1]
    set -l video_name (basename "$video")
    set -l target_dir "/usr/share/sddm/themes/sddm-astronaut-theme/Backgrounds"
    set -l conf_file "/usr/share/sddm/themes/sddm-astronaut-theme/Themes/japanese_aesthetic.conf"

    # Comprobar que el archivo de origen existe
    if not test -f "$video"
        echo "Error: no existe el archivo '$video'."
        return 1
    end

    # Comprobar que el formato es compatible
    set -l extension (string lower -- (path extension "$video_name"))

    set -l formatos ".png" ".jpg" ".jpeg" ".webp" ".gif" ".avi" ".mp4" ".mov" ".mkv" ".m4v" ".webm"

    if not contains -- "$extension" $formatos
        echo "Error: formato no compatible: $extension"
        echo "Formatos permitidos: png, jpg, jpeg, webp, gif, avi, mp4, mov, mkv, m4v, webm"
        return 1
    end

    # Comprobar que existen las rutas de destino
    if not test -d "$target_dir"
        echo "Error: no existe el directorio de fondos:"
        echo "$target_dir"
        return 1
    end

    if not test -f "$conf_file"
        echo "Error: no existe el archivo de configuración:"
        echo "$conf_file"
        return 1
    end

    echo "Copiando '$video_name'..."

    sudo cp -- "$video" "$target_dir/$video_name"
    if test $status -ne 0
        echo "Error: no se pudo copiar el vídeo."
        return 1
    end

    # Verificar que realmente se copió
    if not test -f "$target_dir/$video_name"
        echo "Error: el vídeo no aparece en el directorio de destino."
        return 1
    end

    echo "Actualizando configuración..."

    # Sustituir la línea Background= y conservar las comillas
    sudo sed -i "s|^Background=.*|Background=\"Backgrounds/$video_name\"|" "$conf_file"
    if test $status -ne 0
        echo "Error: no se pudo modificar la configuración."
        return 1
    end

    echo "Listo."
    echo "Fondo: Backgrounds/$video_name"
end

function sddmview
    if not type -q sddm-greeter-qt6
        echo "Error: sddm-greeter-qt6 no está instalado."
        return 1
    end

    if not test -d "/usr/share/sddm/themes/sddm-astronaut-theme"
        echo "Error: no existe el tema 'sddm-astronaut-theme'."
        return 1
    end

    echo "Iniciando vista previa del tema..."
    sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/sddm-astronaut-theme
end
