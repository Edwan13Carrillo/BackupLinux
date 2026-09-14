#!/bin/bash

#========================================#
#          CONFIGURACIÓN GENERAL          #
#========================================#

# Se pueden sobrescribir al ejecutar el script para hacer pruebas controladas.
USB="${USB:-/run/media/$USER/MattUsb}"
PC="${PC:-$HOME}"
#PC="$HOME/tmp/origen"

CARPETAS=("Documentos" "Descargas")

# Cada entrada tiene el formato: origen|destino_dentro_del_backup
# Para añadir una carpeta o aplicación basta con añadir una línea aquí.
RUTAS_RESPALDO=(
    "$PC/${CARPETAS[0]}|${CARPETAS[0]}"
    "$PC/${CARPETAS[1]}|${CARPETAS[1]}"
    "$PC/.config/zen|apps/zen"
    "$PC/.config/hayase|apps/hayase"
    "$PC/.config/qbittorrent|apps/qbittorrent"

    "$PC/.local/share/Prism Launcher|apps/Prism Launcher"
    "$PC/.local/share/lutris|apps/lutris"

    # La carpeta del tema en sí es tolerante (si falta, se omite con aviso);
    # lo que de verdad se exige que exista es "temes/" — ver REQUISITOS_ESTRICTOS.
    "$PC/.Steam/steam/millenium/temes/neko-ui|apps/millennium/neko-ui"

    "$PC/.config/niri|apps/niri"
    "$PC/.config/quickshell|apps/quickshell"
)

# Formato: origen|destino_dentro_del_backup|estricto
# A diferencia de RUTAS_RESPALDO, cada entrada es un ARCHIVO puntual (no una
# carpeta): se copia con cp, nunca con rsync --delete, así que jamás se borra
# nada más dentro de la carpeta real de destino, ni al respaldar ni al
# restaurar (p. ej. no toca el resto de "scripts" de mpv ni del ".vscode").
# El tercer campo, "si", hace que si el archivo no existe se detenga todo
# el respaldo en vez de solo omitir esa entrada; vacío = advertir y omitir.
ARCHIVOS_RESPALDO=(
    "$PC/.vscode/argv.json|vscode/argv.json|"
    "$PC/.config/mpv/scripts/skip_confirm.lua|apps/mpv/scripts/skip_confirm.lua|"

    # El archivo en sí es tolerante (si falta, se omite con aviso);
    # lo que de verdad se exige que exista es la carpeta del plugin —
    # ver REQUISITOS_ESTRICTOS.
    "$PC/.local/state/noctalia/plugins/materialized/community/better-clock/widget.luau|apps/noctalia/better-clock/widget.luau|"
)

# Formato: ruta|descripción
# Carpetas "contenedoras" que deben existir ANTES de continuar (se revisan
# antes de crear temporales o copiar nada). No son lo que se respalda —
# son la señal de que Millennium / el plugin de Noctalia están instalados —
# lo que sí se respalda (p. ej. la carpeta neko-ui puntual, o el widget.luau)
# vive en RUTAS_RESPALDO / ARCHIVOS_RESPALDO y es tolerante si falta.
REQUISITOS_ESTRICTOS=(
    "$PC/.Steam/steam/millenium/temes|Millennium (carpeta de temas)"
    "$PC/.local/state/noctalia/plugins/materialized/community/better-clock|Plugin better-clock de Noctalia"
)

# Formato: nombre|gestor|paquete_o_id_flatpak|destino_dentro_del_backup
# El cuarto campo se usa para omitir una configuración si se elige continuar
# sin la aplicación. Hayase no aparece aquí: es AppImage y no se valida.
APLICACIONES_VALIDAR=(
    "Zen|yay|zen-browser-bin|apps/zen"
    "qBittorrent|pacman|qbittorrent|apps/qbittorrent"
    "PrismLauncher|pacman|prismlauncher|apps/Prism Launcher"
    "Lutris|pacman|lutris|apps/lutris"
)

APLICACIONES_FALTANTES=()
DESTINOS_OMITIDOS=()

NOMBRE_ARCHIVO="backup.tar.gz"
NOMBRE_CIFRADO="$NOMBRE_ARCHIVO.gpg"
# Por defecto se usa el disco de $HOME, no el tmpfs limitado de /tmp.
# TMPDIR permite usar otra ubicación de forma explícita para pruebas.
DIRECTORIO_TEMPORAL_BASE="${TMPDIR:-$HOME/.cache/backup-usb-tmp}"
TEMPORAL_RAIZ=""
TEMPORAL_USB=""

#========================================#
#               COLORES                  #
#========================================#

RESET="\e[0m"
BOLD="\e[1m"

RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
CYAN="\e[36m"
WHITE="\e[97m"

#========================================#
#       TEMPORALES Y VALIDACIONES        #
#========================================#

limpiar_temporales() {
    local estado=$?

    if [ -n "$TEMPORAL_RAIZ" ] && [ -d "$TEMPORAL_RAIZ" ]; then
        rm -rf -- "$TEMPORAL_RAIZ"
    fi

    if [ -n "$TEMPORAL_USB" ] && [ -e "$TEMPORAL_USB" ]; then
        rm -f -- "$TEMPORAL_USB"
    fi

    TEMPORAL_RAIZ=""
    TEMPORAL_USB=""
    return "$estado"
}

trap limpiar_temporales EXIT
trap 'exit 130' INT TERM

crear_temporal() {
    mkdir -p "$DIRECTORIO_TEMPORAL_BASE" || {
        echo -e "${RED}✖ No se pudo crear el directorio para temporales: $DIRECTORIO_TEMPORAL_BASE${RESET}"
        return 1
    }

    if [ ! -d "$DIRECTORIO_TEMPORAL_BASE" ] || [ ! -w "$DIRECTORIO_TEMPORAL_BASE" ]; then
        echo -e "${RED}✖ No se puede escribir en el directorio temporal: $DIRECTORIO_TEMPORAL_BASE${RESET}"
        return 1
    fi

    TEMPORAL_RAIZ=$(mktemp -d "$DIRECTORIO_TEMPORAL_BASE/backup-usb.XXXXXX") || {
        echo -e "${RED}✖ No se pudo crear el directorio temporal.${RESET}"
        return 1
    }
}

validar_dependencias() {
    local dependencia

    for dependencia in rsync tar gpg mktemp find; do
        if ! command -v "$dependencia" >/dev/null 2>&1; then
            echo -e "${RED}✖ Falta la dependencia requerida: $dependencia${RESET}"
            return 1
        fi
    done
}

validar_usb() {
    if [ ! -d "$USB" ] || [ ! -r "$USB" ] || [ ! -w "$USB" ]; then
        echo -e "${RED}✖ La USB no está disponible para lectura y escritura: $USB${RESET}"
        return 1
    fi
}

# Revisa primero REQUISITOS_ESTRICTOS (carpetas que deben existir sí o sí),
# y de paso también las rutas "estrictas" que puedan quedar sueltas en
# RUTAS_RESPALDO (sin prefijo "apps/") y ARCHIVOS_RESPALDO (marcadas "si").
# Todo esto corre antes de crear temporales o copiar nada.
validar_rutas_estrictas() {
    local requisito ruta descripcion entrada_archivo

    for requisito in "${REQUISITOS_ESTRICTOS[@]}"; do
        ruta="${requisito%%|*}"
        descripcion="${requisito#*|}"

        if [ ! -d "$ruta" ]; then
            echo -e "${RED}✖ No existe: $ruta${RESET}"
            echo -e "${YELLOW}  ($descripcion no está instalado/configurado en esta PC)${RESET}"
            return 1
        fi
    done

    for ruta in "${RUTAS_RESPALDO[@]}"; do
        separar_ruta "$ruta" || return 1
        destino_de_aplicacion "$DESTINO" && continue

        if [ ! -d "$ORIGEN" ]; then
            echo -e "${RED}✖ No existe la ruta de origen: $ORIGEN${RESET}"
            return 1
        fi
    done

    for entrada_archivo in "${ARCHIVOS_RESPALDO[@]}"; do
        separar_archivo "$entrada_archivo" || return 1
        [ "$ARCHIVO_ESTRICTO" = "si" ] || continue

        if [ ! -f "$ARCHIVO_ORIGEN" ]; then
            echo -e "${RED}✖ No existe: $ARCHIVO_ORIGEN${RESET}"
            return 1
        fi
    done
}

validar_destino_relativo() {
    local destino="$1"

    case "$destino" in
        ""|/*|..|../*|*/..|*/../*|*//*)
            echo -e "${RED}✖ Destino inválido en RUTAS_RESPALDO: $destino${RESET}"
            return 1
            ;;
    esac
}

separar_ruta() {
    local ruta="$1"

    ORIGEN="${ruta%%|*}"
    DESTINO="${ruta#*|}"

    if [ "$ORIGEN" = "$DESTINO" ]; then
        echo -e "${RED}✖ Entrada inválida en RUTAS_RESPALDO: $ruta${RESET}"
        return 1
    fi

    validar_destino_relativo "$DESTINO"
}

separar_archivo() {
    local entrada="$1"
    local resto

    ARCHIVO_ORIGEN="${entrada%%|*}"
    resto="${entrada#*|}"
    ARCHIVO_DESTINO="${resto%%|*}"
    ARCHIVO_ESTRICTO="${resto#*|}"

    if [ "$ARCHIVO_ORIGEN" = "$ARCHIVO_DESTINO" ]; then
        echo -e "${RED}✖ Entrada inválida en ARCHIVOS_RESPALDO: $entrada${RESET}"
        return 1
    fi

    validar_destino_relativo "$ARCHIVO_DESTINO"
}

separar_aplicacion() {
    local aplicacion="$1"

    APP_NOMBRE="${aplicacion%%|*}"
    aplicacion="${aplicacion#*|}"
    APP_GESTOR="${aplicacion%%|*}"
    aplicacion="${aplicacion#*|}"
    APP_PAQUETE="${aplicacion%%|*}"
    APP_DESTINO="${aplicacion#*|}"
}

aplicacion_instalada() {
    local gestor="$1"
    local paquete="$2"

    case "$gestor" in
        yay|pacman)
            command -v pacman >/dev/null 2>&1 && pacman -Q "$paquete" >/dev/null 2>&1
            ;;
        flatpak)
            command -v flatpak >/dev/null 2>&1 && flatpak info "$paquete" >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

buscar_aplicaciones_faltantes() {
    local aplicacion

    APLICACIONES_FALTANTES=()
    for aplicacion in "${APLICACIONES_VALIDAR[@]}"; do
        separar_aplicacion "$aplicacion"
        if ! aplicacion_instalada "$APP_GESTOR" "$APP_PAQUETE"; then
            APLICACIONES_FALTANTES+=("$aplicacion")
        fi
    done
}

instalar_aplicacion() {
    local aplicacion="$1"

    separar_aplicacion "$aplicacion"
    echo -e "${CYAN}Instalando $APP_NOMBRE...${RESET}"

    case "$APP_GESTOR" in
        yay)
            command -v yay >/dev/null 2>&1 || {
                echo -e "${RED}✖ No está instalado yay; no se puede instalar $APP_NOMBRE.${RESET}"
                return 1
            }
            yay -S --needed "$APP_PAQUETE"
            ;;
        pacman)
            command -v pacman >/dev/null 2>&1 || {
                echo -e "${RED}✖ No está instalado pacman; no se puede instalar $APP_NOMBRE.${RESET}"
                return 1
            }
            sudo pacman -S --needed "$APP_PAQUETE"
            ;;
        flatpak)
            command -v flatpak >/dev/null 2>&1 || {
                echo -e "${RED}✖ No está instalado flatpak; no se puede instalar $APP_NOMBRE.${RESET}"
                return 1
            }
            flatpak install --user flathub "$APP_PAQUETE"
            ;;
        *)
            echo -e "${RED}✖ Gestor no reconocido para $APP_NOMBRE.${RESET}"
            return 1
            ;;
    esac
}

destino_omitido() {
    local destino="$1"
    local destino_omitido

    for destino_omitido in "${DESTINOS_OMITIDOS[@]}"; do
        [ "$destino" = "$destino_omitido" ] && return 0
    done

    return 1
}

destino_de_aplicacion() {
    case "$1" in
        apps/*) return 0 ;;
        *) return 1 ;;
    esac
}

validar_aplicaciones_para_respaldo() {
    local aplicacion opcion

    DESTINOS_OMITIDOS=()
    buscar_aplicaciones_faltantes

    [ "${#APLICACIONES_FALTANTES[@]}" -eq 0 ] && return 0

    echo
    echo -e "${BOLD}${YELLOW}⚠ Faltan las siguientes aplicaciones:${RESET}"
    for aplicacion in "${APLICACIONES_FALTANTES[@]}"; do
        separar_aplicacion "$aplicacion"
        echo -e " ${YELLOW}•${RESET} $APP_NOMBRE"
    done

    while true; do
        echo
        echo -e " ${GREEN}1)${RESET} Instalar las aplicaciones faltantes y continuar"
        echo -e " ${GREEN}2)${RESET} Continuar sin las configuraciones de las aplicaciones faltantes"
        echo -e " ${GREEN}3)${RESET} Salir"
        read -r -p "Selecciona una opción: " opcion

        case "$opcion" in
            1)
                for aplicacion in "${APLICACIONES_FALTANTES[@]}"; do
                    instalar_aplicacion "$aplicacion" || {
                        echo -e "${RED}✖ No se iniciará el backup porque una instalación falló.${RESET}"
                        return 1
                    }
                done

                buscar_aplicaciones_faltantes
                if [ "${#APLICACIONES_FALTANTES[@]}" -ne 0 ]; then
                    echo -e "${RED}✖ Algunas aplicaciones siguen sin estar instaladas; no se iniciará el backup.${RESET}"
                    return 1
                fi
                return 0
                ;;
            2)
                for aplicacion in "${APLICACIONES_FALTANTES[@]}"; do
                    separar_aplicacion "$aplicacion"
                    [ -n "$APP_DESTINO" ] && DESTINOS_OMITIDOS+=("$APP_DESTINO")
                done
                return 0
                ;;
            3)
                echo -e "${BOLD}${GREEN}👋 ¡Hasta luego!${RESET}"
                exit 0
                ;;
            *)
                echo -e "${RED}✖ Opción inválida.${RESET}"
                ;;
        esac
    done
}

limpiar_backup_usb() {
    local directorio_backup="$USB/Backup"

    mkdir -p "$directorio_backup" || {
        echo -e "${RED}✖ No se pudo crear $directorio_backup.${RESET}"
        return 1
    }

    # Se eliminan los formatos anteriores solo después de haber cifrado bien
    # el nuevo respaldo. Así, al finalizar, Backup contiene solo el .gpg.
    find "$directorio_backup" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + || {
        echo -e "${RED}✖ No se pudo limpiar el respaldo anterior de la USB.${RESET}"
        return 1
    }
}

guardar_cifrado_en_usb() {
    local archivo_cifrado="$1"
    local destino_final="$USB/Backup/$NOMBRE_CIFRADO"

    mkdir -p "$USB/Backup" || {
        echo -e "${RED}✖ No se pudo crear la carpeta Backup en la USB.${RESET}"
        return 1
    }

    # Primero se copia el archivo ya cifrado a un nombre temporal en la USB.
    # El cambio al nombre final es un movimiento dentro de la misma unidad.
    TEMPORAL_USB=$(mktemp "$USB/.backup-usb.XXXXXX") || {
        echo -e "${RED}✖ No se pudo crear un archivo temporal en la USB.${RESET}"
        return 1
    }

    if ! mv -f -- "$archivo_cifrado" "$TEMPORAL_USB"; then
        echo -e "${RED}✖ No se pudo copiar el respaldo cifrado a la USB.${RESET}"
        return 1
    fi

    if ! limpiar_backup_usb; then
        return 1
    fi

    if ! mv -f -- "$TEMPORAL_USB" "$destino_final"; then
        echo -e "${RED}✖ No se pudo guardar el respaldo cifrado en la USB.${RESET}"
        return 1
    fi

    TEMPORAL_USB=""
}

#========================================#
#             ENCABEZADO                 #
#========================================#

echo
echo -e "${BOLD}${CYAN}========================================${RESET}"
echo -e "${BOLD}${CYAN}          BACKUP USB MANAGER${RESET}"
echo -e "${BOLD}${CYAN}========================================${RESET}"
echo

#========================================#
#       VALIDACIÓN DEL MODO DE USO       #
#========================================#

if [ "$PC" == "$HOME" ]; then
    echo -e "${BOLD}${RED}========================================${RESET}"
    echo -e "${BOLD}${RED}🚨 MODO REAL${RESET}"
    echo -e "${RED}Se sincronizará la carpeta:${RESET}"
    echo -e "${BOLD}${WHITE}$PC${RESET}"
    echo -e "${BOLD}${RED}========================================${RESET}"
else
    echo -e "${BOLD}${YELLOW}========================================${RESET}"
    echo -e "${BOLD}${YELLOW}⚠️  MODO PRUEBA${RESET}"
    echo -e "${YELLOW}Se sincronizará la carpeta:${RESET}"
    echo -e "${BOLD}${WHITE}$PC${RESET}"
    echo -e "${BOLD}${YELLOW}========================================${RESET}"
fi

echo

#========================================#
#         DETECCIÓN DE LA USB            #
#========================================#

inicio() {
    while [ ! -d "$USB" ]; do
        read -r -p "📁 Ruta de la USB: " RUTA

        if [ -z "$RUTA" ] || [ ! -d "$RUTA" ]; then
            echo -e "${RED}✖ La ruta ingresada no existe o no es válida.${RESET}"
            continue
        fi

        USB="$RUTA"
    done

    if [ ! -r "$USB" ] || [ ! -w "$USB" ]; then
        echo -e "${RED}✖ No hay permisos de lectura y escritura en la USB: $USB${RESET}"
        return 1
    fi

    echo -e "${GREEN}✓ USB detectada:${RESET} $USB"
}

inicio || exit 1

#========================================#
#             RESPALDAR                  #
#========================================#

respaldar() {
    local ruta stage archivo archivo_cifrado entrada_archivo

    echo
    echo -e "${BOLD}${YELLOW}⚠ Se copiarán los datos desde la PC hacia la USB.${RESET}"

    read -r -p "¿Deseas continuar? (s/n): " ELECCION

    if [ "$ELECCION" == "s" ]; then
        validar_dependencias && validar_usb || return 1
        validar_rutas_estrictas || return 1
        validar_aplicaciones_para_respaldo || return 1
        crear_temporal || return 1

        stage="$TEMPORAL_RAIZ/contenido"
        archivo="$TEMPORAL_RAIZ/$NOMBRE_ARCHIVO"
        archivo_cifrado="$TEMPORAL_RAIZ/$NOMBRE_CIFRADO"
        mkdir -p "$stage" || {
            echo -e "${RED}✖ No se pudo preparar el contenido temporal.${RESET}"
            return 1
        }

        for ruta in "${RUTAS_RESPALDO[@]}"; do
            separar_ruta "$ruta" || return 1

            if destino_omitido "$DESTINO"; then
                echo -e "${YELLOW}⚠ Se omite la configuración de $DESTINO porque su aplicación no está instalada.${RESET}"
                continue
            fi

            if [ ! -d "$ORIGEN" ]; then
                if destino_de_aplicacion "$DESTINO"; then
                    echo -e "${YELLOW}⚠ No existe la configuración de $DESTINO; se omite.${RESET}"
                    continue
                fi
                echo -e "${RED}✖ No existe la ruta de origen: $ORIGEN${RESET}"
                return 1
            fi

            echo
            echo -e "${CYAN}────────────────────────────────────────${RESET}"
            echo -e "${BOLD}${CYAN}📁 Copiando al temporal: $DESTINO${RESET}"
            echo -e "${CYAN}────────────────────────────────────────${RESET}"

            mkdir -p "$stage/$DESTINO" || return 1

            if [[ "$DESTINO" == "${CARPETAS[0]}" || "$DESTINO" == "${CARPETAS[1]}" ]]; then
                rsync -av --delete \
                    --exclude='BackupLinux/' \
                    --exclude='juegosLutris/' \
                    --exclude='*.mkv' \
                    --exclude='*.m4a' \
                    "$ORIGEN/" "$stage/$DESTINO/" || {
                        echo -e "${RED}✖ Falló la copia temporal de: $ORIGEN${RESET}"
                        return 1
                    }
            else
                rsync -av --delete "$ORIGEN/" "$stage/$DESTINO/" || {
                    echo -e "${RED}✖ Falló la copia temporal de: $ORIGEN${RESET}"
                    return 1
                }
            fi
        done

        for entrada_archivo in "${ARCHIVOS_RESPALDO[@]}"; do
            separar_archivo "$entrada_archivo" || return 1

            if [ ! -f "$ARCHIVO_ORIGEN" ]; then
                if [ "$ARCHIVO_ESTRICTO" = "si" ]; then
                    echo -e "${RED}✖ No existe: $ARCHIVO_ORIGEN${RESET}"
                    return 1
                fi
                echo -e "${YELLOW}⚠ No existe el archivo: $ARCHIVO_ORIGEN; se omite.${RESET}"
                continue
            fi

            echo
            echo -e "${CYAN}────────────────────────────────────────${RESET}"
            echo -e "${BOLD}${CYAN}📄 Copiando al temporal: $ARCHIVO_DESTINO${RESET}"
            echo -e "${CYAN}────────────────────────────────────────${RESET}"

            mkdir -p "$stage/$(dirname "$ARCHIVO_DESTINO")" || return 1
            cp -f -- "$ARCHIVO_ORIGEN" "$stage/$ARCHIVO_DESTINO" || {
                echo -e "${RED}✖ Falló la copia temporal de: $ARCHIVO_ORIGEN${RESET}"
                return 1
            }
        done

        echo -e "${CYAN}📦 Creando el único archivo $NOMBRE_ARCHIVO...${RESET}"
        tar -czf "$archivo" -C "$stage" . || {
            echo -e "${RED}✖ Falló la creación de $NOMBRE_ARCHIVO.${RESET}"
            return 1
        }

        echo -e "${CYAN}🔐 GPG solicitará la contraseña del respaldo de forma segura.${RESET}"
        gpg --symmetric --cipher-algo AES256 --output "$archivo_cifrado" "$archivo" || {
            echo -e "${RED}✖ Falló el cifrado. El respaldo anterior de la USB no se modificó.${RESET}"
            return 1
        }

        if [ ! -s "$archivo_cifrado" ]; then
            echo -e "${RED}✖ El archivo cifrado no se creó correctamente.${RESET}"
            return 1
        fi

        # El .tar.gz se conserva hasta que GPG haya terminado sin errores.
        guardar_cifrado_en_usb "$archivo_cifrado" || return 1

        echo
        echo -e "${GREEN}========================================${RESET}"
        echo -e "${BOLD}${GREEN}✓ Respaldo finalizado correctamente.${RESET}"
        echo -e "${GREEN}========================================${RESET}"

    elif [ "$ELECCION" == "n" ]; then
        menu

    else
        echo -e "${RED}✖ Opción inválida.${RESET}"
        respaldar
    fi
}

#========================================#
#             RESTAURAR                  #
#========================================#

restaurar() {
    local ruta archivo archivo_extraido origen_temporal entrada_archivo

    echo
    echo -e "${BOLD}${YELLOW}⚠ Antes de continuar, abre y cierra Zen Browser.${RESET}"
    echo

    read -r -p "¿Restaurar los datos desde la USB hacia la PC? (s/n): " ELECCION

    if [ "$ELECCION" == "s" ]; then
        validar_dependencias && validar_usb || return 1

        archivo="$USB/Backup/$NOMBRE_CIFRADO"
        if [ ! -f "$archivo" ] || [ ! -r "$archivo" ]; then
            echo -e "${RED}✖ No se encontró el respaldo cifrado: $archivo${RESET}"
            return 1
        fi

        crear_temporal || return 1
        archivo_extraido="$TEMPORAL_RAIZ/$NOMBRE_ARCHIVO"
        origen_temporal="$TEMPORAL_RAIZ/contenido"
        mkdir -p "$origen_temporal" || return 1

        echo -e "${CYAN}🔐 GPG solicitará la contraseña del respaldo de forma segura.${RESET}"
        if ! gpg --decrypt --output "$archivo_extraido" "$archivo"; then
            echo -e "${RED}✖ No se pudo descifrar el respaldo: contraseña incorrecta o archivo corrupto.${RESET}"
            return 1
        fi

        if ! tar -tzf "$archivo_extraido" >/dev/null; then
            echo -e "${RED}✖ El archivo descifrado no es un backup.tar.gz válido.${RESET}"
            return 1
        fi

        if ! tar -xzf "$archivo_extraido" --no-same-owner --no-same-permissions -C "$origen_temporal"; then
            echo -e "${RED}✖ Falló la extracción del respaldo.${RESET}"
            return 1
        fi

        for ruta in "${RUTAS_RESPALDO[@]}"; do
            separar_ruta "$ruta" || return 1

            if [ ! -d "$origen_temporal/$DESTINO" ]; then
                if destino_de_aplicacion "$DESTINO"; then
                    echo -e "${YELLOW}⚠ No hay configuración de $DESTINO en este respaldo; se omite.${RESET}"
                    continue
                fi
                echo -e "${RED}✖ Falta la ruta esperada en el respaldo: $DESTINO${RESET}"
                return 1
            fi

            echo
            echo -e "${CYAN}────────────────────────────────────────${RESET}"
            echo -e "${BOLD}${CYAN}📁 Restaurando: $DESTINO${RESET}"
            echo -e "${CYAN}────────────────────────────────────────${RESET}"

            mkdir -p "$ORIGEN" || {
                echo -e "${RED}✖ No se pudo preparar el destino: $ORIGEN${RESET}"
                return 1
            }

            rsync -av --delete "$origen_temporal/$DESTINO/" "$ORIGEN/" || {
                echo -e "${RED}✖ Falló la restauración de: $DESTINO${RESET}"
                return 1
            }
        done

        for entrada_archivo in "${ARCHIVOS_RESPALDO[@]}"; do
            separar_archivo "$entrada_archivo" || return 1

            if [ ! -f "$origen_temporal/$ARCHIVO_DESTINO" ]; then
                if [ "$ARCHIVO_ESTRICTO" = "si" ]; then
                    echo -e "${RED}✖ Falta el archivo esperado en el respaldo: $ARCHIVO_DESTINO${RESET}"
                    return 1
                fi
                echo -e "${YELLOW}⚠ No hay $ARCHIVO_DESTINO en este respaldo; se omite.${RESET}"
                continue
            fi

            echo
            echo -e "${CYAN}────────────────────────────────────────${RESET}"
            echo -e "${BOLD}${CYAN}📄 Restaurando: $ARCHIVO_DESTINO${RESET}"
            echo -e "${CYAN}────────────────────────────────────────${RESET}"

            mkdir -p "$(dirname "$ARCHIVO_ORIGEN")" || {
                echo -e "${RED}✖ No se pudo preparar el destino: $ARCHIVO_ORIGEN${RESET}"
                return 1
            }

            cp -f -- "$origen_temporal/$ARCHIVO_DESTINO" "$ARCHIVO_ORIGEN" || {
                echo -e "${RED}✖ Falló la restauración de: $ARCHIVO_DESTINO${RESET}"
                return 1
            }
        done

        echo
        echo -e "${GREEN}========================================${RESET}"
        echo -e "${BOLD}${GREEN}✓ Restauración finalizada correctamente.${RESET}"
        echo -e "${GREEN}========================================${RESET}"

    elif [ "$ELECCION" == "n" ]; then
        menu

    else
        echo -e "${RED}✖ Opción inválida.${RESET}"
        restaurar
    fi
}

#========================================#
#                MENÚ                    #
#========================================#

menu() {
    echo
    echo -e "${BOLD}${CYAN}========================================${RESET}"
    echo -e "${BOLD}${CYAN}                MENÚ${RESET}"
    echo -e "${BOLD}${CYAN}========================================${RESET}"

    echo -e " ${GREEN}1)${RESET} 📤 Respaldar  (PC → USB)"
    echo -e " ${GREEN}2)${RESET} 📥 Restaurar (USB → PC)"
    echo -e " ${GREEN}3)${RESET} ❌ Salir"
    echo

    read -r -p "Selecciona una opción: " OPCION

    case "$OPCION" in
        1)
            respaldar
            ;;
        2)
            restaurar
            ;;
        3)
            echo -e "${BOLD}${GREEN}👋 ¡Hasta luego!${RESET}"
            exit 0
            ;;
        *)
            echo -e "${RED}✖ Opción inválida.${RESET}"
            menu
            ;;
    esac
}

menu