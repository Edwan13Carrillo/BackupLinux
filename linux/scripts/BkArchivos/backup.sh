#!/bin/bash

#========================================#
#          CONFIGURACIÓN GENERAL          #
#========================================#

USB="/run/media/$USER/MattUsb"
#PC="$HOME"
PC="$HOME/tmp/origen"

CARPETAS=("Documentos" "Descargas")

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

    if [ ! -d "$USB" ]; then

        read -p "📁 Ruta de la USB: " RUTA

        if [[ ! -d "$RUTA" && -n "$RUTA" && "$RUTA" != /run/media/* ]]; then
            echo -e "${RED}✖ La ruta ingresada no existe o no es válida.${RESET}"
            inicio
            return
        fi

        USB="$RUTA"
        return

    else
        echo -e "${GREEN}✓ USB detectada:${RESET} $USB"
        return
    fi
}

inicio

#========================================#
#             RESPALDAR                  #
#========================================#

respaldar() {

    echo
    echo -e "${BOLD}${YELLOW}⚠ Se copiarán los datos desde la PC hacia la USB.${RESET}"

    read -p "¿Deseas continuar? (s/n): " ELECCION

    if [ "$ELECCION" == "s" ]; then

        for CARPETA in "${CARPETAS[@]}"; do

            echo
            echo -e "${CYAN}────────────────────────────────────────${RESET}"
            echo -e "${BOLD}${CYAN}📁 Sincronizando: $CARPETA${RESET}"
            echo -e "${CYAN}────────────────────────────────────────${RESET}"

            mkdir -p "$USB/Backup/$CARPETA/"

            rsync -av --delete \
                --exclude='qbit/' \
                --exclude='BackupLinux/' \
                --exclude='*.m4a' \
                "$PC/$CARPETA/" "$USB/Backup/$CARPETA/"

        done

        rm -rf "$USB/Backup/zen.tar.gz"
        rm -rf "$USB/Backup/hayase.tar.gz"

        tar -czf "$USB/Backup/zen.tar.gz" -C "$PC/.config" zen
        tar -czf "$USB/Backup/hayase.tar.gz" -C "$PC/.config" hayase

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

    echo
    echo -e "${BOLD}${YELLOW}⚠ Antes de continuar, abre y cierra Zen Browser.${RESET}"
    echo

    read -p "¿Restaurar los datos desde la USB hacia la PC? (s/n): " ELECCION

    if [ "$ELECCION" == "s" ]; then

        for CARPETA in "${CARPETAS[@]}"; do

            echo
            echo -e "${CYAN}────────────────────────────────────────${RESET}"
            echo -e "${BOLD}${CYAN}📁 Sincronizando: $CARPETA${RESET}"
            echo -e "${CYAN}────────────────────────────────────────${RESET}"

            rsync -av --delete "$USB/Backup/$CARPETA/" "$PC/$CARPETA/"

        done

        tar -xzf "$USB/Backup/zen.tar.gz" -C "$PC/"
        tar -xzf "$USB/Backup/hayase.tar.gz" -C "$PC/"

        rsync -av --delete "$PC/zen/" "$PC/.config/zen/"
        rsync -av --delete "$PC/hayase/" "$PC/.config/hayase/"

        rm -rf "$PC/zen/"
        rm -rf "$PC/hayase/"

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

    read -p "Selecciona una opción: " OPCION

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
