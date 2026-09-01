#!/bin/bash

# ─────────────────────────────────────────
# Setup CachyOS KDE — Versión 100% Bash
# Respaldo sin dependencia de Ansible.
# Traducción directa de ansible/playbook.yml
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────

CONFIG_BK_DIR="$HOME/BackupLinux/linux/configs"
LOCAL_DIR="$HOME/.local/share"
CONFIG_DIR="$HOME/.config"

# ─────────────────────────────────────────
# Colores
# ─────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─────────────────────────────────────────
# Funciones auxiliares
# ─────────────────────────────────────────

print_header() {
    printf '\n'
    printf '%b\n' "${BLUE}${BOLD}  ╔══════════════════════════════════════════════╗${NC}"
    printf '%b\n' "${BLUE}${BOLD}  ║  $1${NC}"
    printf '%b\n' "${BLUE}${BOLD}  ╚══════════════════════════════════════════════╝${NC}"
    printf '\n'
}

print_ok() {
    printf '  %b✓%b %s\n' "$GREEN" "$NC" "$1"
}

print_err() {
    printf '  %b✗%b %s\n' "$RED" "$NC" "$1"
}

print_warn() {
    printf '  %b⚠%b %s\n' "$YELLOW" "$NC" "$1"
}

print_info() {
    printf '  %b→%b %s\n' "$CYAN" "$NC" "$1"
}

pause() {
    printf '\n'
    read -rp "  Presiona Enter para continuar..." _
}

confirmar() {
    local resp
    read -rp "  $1 [s/N]: " resp
    [[ "$resp" =~ ^[sS]$ ]]
}

seleccionar_perfil() {
    case "${PROFILE:-}" in
        plasma|niri)
            export PROFILE
            return 0
            ;;
        "")
            ;;
        *)
            print_warn "El perfil recibido no es válido; selecciona uno de nuevo."
            PROFILE=""
            ;;
    esac

    while true; do
        print_header "Selecciona el entorno de escritorio"
        printf '  %b1.%b KDE Plasma\n' "$BOLD" "$NC"
        printf '  %b2.%b Niri + Noctalia\n' "$BOLD" "$NC"
        printf '\n'

        if ! read -rp "  Elige un perfil: " opcion_perfil; then
            printf '\n'
            print_warn "Entrada finalizada (EOF). Saliendo."
            exit 0
        fi

        case "$opcion_perfil" in
            1) PROFILE="plasma" ;;
            2) PROFILE="niri" ;;
            *)
                print_err "Opción no válida."
                continue
                ;;
        esac

        export PROFILE
        print_ok "Perfil seleccionado: $PROFILE"
        return 0
    done
}

# ─────────────────────────────────────────
# Fase 1 — Paquetes
# ─────────────────────────────────────────

PAQUETES_BASE=(
    discord telegram-desktop zen-browser-bin libreoffice-still libreoffice-still-es
    git fastfetch yt-dlp qbittorrent fuse2 mkvtoolnix-gui prismlauncher
    base-devel yay flatpak python-mutagen tk rsync snapper
    cachyos-snapper-support btrfs-assistant
)

instalar_paquetes_red() {
    print_info "Instalando paquetes de red (tailscale, ufw)..."

    if sudo pacman -S --needed --noconfirm tailscale ufw; then
        print_ok "Paquetes de red instalados."
        return 0
    else
        print_err "Falló la instalación de paquetes de red."
        return 1
    fi
}

instalar_paquetes() {
    print_header "Fase 1 — Paquetes"

    print_info "Instalando paquetes principales..."

    if ! sudo pacman -S --needed --noconfirm "${PAQUETES_BASE[@]}"; then
        print_err "Falló la instalación de paquetes principales."
        return 1
    fi
    print_ok "Paquetes principales instalados."

    if ! instalar_paquetes_red; then
        return 1
    fi

    print_info "Instalando Visual Studio Code (AUR) con yay..."
    # OJO: yay NO se corre con sudo, el mismo escala privilegios cuando
    # necesita instalar el paquete compilado. Si yay no está en PATH
    # todavía, corre esta fase de nuevo después de que termine.
    if yay -S --needed --noconfirm visual-studio-code-bin; then
        print_ok "VS Code instalado."
    else
        print_err "Falló la instalación de VS Code."
        return 1
    fi

    print_info "Agregando el remote de Flathub..."
    if flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo; then
        print_ok "Remote de Flathub agregado."
    else
        print_err "Falló al agregar el remote de Flathub."
        return 1
    fi

    print_info "Instalando Sober (Flatpak)..."
    if flatpak install -y --noninteractive flathub org.vinegarhq.Sober; then
        print_ok "Sober instalado."
    else
        print_err "Falló la instalación de Sober."
        return 1
    fi

    print_ok "Fase 1 completada."
}

# ─────────────────────────────────────────
# Fase 2 — Dotfiles
# ─────────────────────────────────────────

# Formato: origen|destino|delete(0/1)|sudo(0/1)
# Mismos orígenes, destinos y flags que las listas del playbook.
DOTFILES_COMUNES=(
    "$CONFIG_BK_DIR/fonts/|$LOCAL_DIR/fonts/|0|0"
    "$CONFIG_BK_DIR/pixels|/usr/share/plymouth/themes/|1|1"
    "$CONFIG_BK_DIR/local/Bibata-Modern-Ice|$HOME/.icons/|1|0"
    "$CONFIG_BK_DIR/fastfetch/|$CONFIG_DIR/fastfetch/|0|0"
    "$CONFIG_BK_DIR/alacritty/|$CONFIG_DIR/alacritty/|0|0"
    "$CONFIG_BK_DIR/haruna/|$CONFIG_DIR/haruna/|0|0"
)

DOTFILES_PLASMA=(
    "$CONFIG_BK_DIR/local/Layan|$LOCAL_DIR/aurorae/themes/|1|0"
    "$CONFIG_BK_DIR/local/desktoptheme|$LOCAL_DIR/plasma/|1|0"
    "$CONFIG_BK_DIR/local/a2n.kuro|$LOCAL_DIR/plasma/look-and-feel/|0|0"
    "$CONFIG_BK_DIR/Tela|$LOCAL_DIR/icons/|1|0"
    "$CONFIG_BK_DIR/local/org.kde.plasma.clearclock|$LOCAL_DIR/plasma/plasmoids/|1|0"
    "$CONFIG_BK_DIR/local/cachyosTG|$LOCAL_DIR/plasma/look-and-feel/|0|0"
    "$CONFIG_BK_DIR/kdedefaults/|$CONFIG_DIR/kdedefaults/|0|0"
)

# Reservado para futuros dotfiles de Niri + Noctalia.
DOTFILES_NIRI=()

copiar_dotfiles() {
    print_header "Fase 2 — Dotfiles y configuraciones"

    local entrada origen destino delete usa_sudo
    local mkdir_cmd rsync_flags rsync_cmd fallo=0
    local dotfiles=("${DOTFILES_COMUNES[@]}")

    case "$PROFILE" in
        plasma)
            dotfiles+=("${DOTFILES_PLASMA[@]}")
            ;;
        niri)
            dotfiles+=("${DOTFILES_NIRI[@]}")
            ;;
        *)
            print_err "PROFILE inválido: ${PROFILE:-sin definir}"
            return 1
            ;;
    esac

    for entrada in "${dotfiles[@]}"; do
        IFS='|' read -r origen destino delete usa_sudo <<< "$entrada"

        rsync_flags=(-a)
        [ "$delete" = "1" ] && rsync_flags+=(--delete)

        if [ "$usa_sudo" = "1" ]; then
            mkdir_cmd=(sudo mkdir -p "$destino")
            rsync_cmd=(sudo rsync "${rsync_flags[@]}" "$origen" "$destino")
        else
            mkdir_cmd=(mkdir -p "$destino")
            rsync_cmd=(rsync "${rsync_flags[@]}" "$origen" "$destino")
        fi

        print_info "Copiando $(basename "$origen") -> $destino"

        if "${mkdir_cmd[@]}" && "${rsync_cmd[@]}"; then
            print_ok "Copiado: $(basename "$origen")"
        else
            print_err "Falló copiando: $(basename "$origen")"
            fallo=1
        fi
    done

    print_info "Refrescando cache de fuentes..."
    fc-cache -f >/dev/null 2>&1 && print_ok "Cache de fuentes actualizado."

    if [ "$PROFILE" = "plasma" ]; then
        print_warn "Aplica las fuentes en: Ajustes del sistema > Fuentes (Fredoka Medium 12pt / 10pt)."
        print_warn "Ve a: Ajustes del sistema > Aspecto > Tema global y selecciona 'CachyTG' para aplicarlo."
        print_warn "Cierra sesión y vuelve a entrar para que KDE aplique todos los temas."
        print_warn "Agrega el widget Clear Clock al escritorio, reemplaza su config.qml y refresca Plasma con: kquitapp6 plasmashell && kstart5 plasmashell"
    fi

    if [ "$fallo" -eq 0 ]; then
        print_ok "Fase 2 completada."
    else
        print_warn "Fase 2 terminó con algunos errores, revisa arriba."
        return 1
    fi
}

# ─────────────────────────────────────────
# Fase 3 — Game Zone
# ─────────────────────────────────────────

configurar_gamezone() {
    print_header "Fase 3 — Subvolumen Game Zone"

    if [ -e /games ]; then
        print_ok "El subvolumen /games ya existe."
    else
        print_info "Creando subvolumen /games..."
        if sudo btrfs subvolume create /games; then
            print_ok "Subvolumen /games creado."
        else
            print_err "Falló creando el subvolumen /games."
            return 1
        fi
    fi

    local attrs
    attrs="$(lsattr -d /games 2>/dev/null | awk '{print $1}')"

    if [[ "$attrs" == *C* ]]; then
        print_ok "NoCoW ya está activo en /games."
    else
        print_info "Activando NoCoW (chattr +C) en /games..."
        if sudo chattr +C /games; then
            print_ok "NoCoW activado."
        else
            print_err "Falló activando NoCoW."
            return 1
        fi
    fi

    print_info "Asignando propiedad de /games a $USER..."
    if sudo chown "$USER":"$USER" /games; then
        print_ok "Propiedad asignada."
    else
        print_err "Falló asignando propiedad."
        return 1
    fi

    print_ok "Fase 3 completada."
}

# ─────────────────────────────────────────
# Fase 4 — Snapper
# ─────────────────────────────────────────

# Mismos pares clave=valor que la var "snapper_limits" del playbook
SNAPPER_LIMITS=(
    "TIMELINE_LIMIT_HOURLY=0"
    "TIMELINE_LIMIT_DAILY=5"
    "TIMELINE_LIMIT_WEEKLY=1"
    "TIMELINE_LIMIT_MONTHLY=0"
    "TIMELINE_LIMIT_YEARLY=0"
    "NUMBER_LIMIT=0"
    "NUMBER_LIMIT_IMPORTANT=15"
)

configurar_snapper() {
    print_header "Fase 4 — Snapper"

    if [ -f /etc/snapper/configs/root ]; then
        print_ok "La configuración root de Snapper ya existe."
    else
        print_info "Creando configuración root de Snapper..."
        if sudo snapper -c root create-config /; then
            print_ok "Configuración root creada."
        else
            print_err "Falló creando la configuración de Snapper."
            return 1
        fi
    fi

    local par clave valor
    for par in "${SNAPPER_LIMITS[@]}"; do
        clave="${par%%=*}"
        valor="${par#*=}"

        if sudo grep -q "^${clave}=" /etc/snapper/configs/root 2>/dev/null; then
            sudo sed -i "s/^${clave}=.*/${clave}=\"${valor}\"/" /etc/snapper/configs/root
        else
            echo "${clave}=\"${valor}\"" | sudo tee -a /etc/snapper/configs/root >/dev/null
        fi
    done

    print_ok "Límites de Snapper configurados."
    print_warn "Cuando el sistema esté listo, ejecuta: sudo snapper -c root create --description 'Sistema base configurado' para crear un snapshot inicial."
    print_ok "Fase 4 completada."
}

# ─────────────────────────────────────────
# Fase 5 — Red y Firewall
# ─────────────────────────────────────────

# Formato: puerto|proto|interface (interface vacío = sin restringir)
FIREWALL_RULES=(
    "1714:1764|udp|"
    "1714:1764|tcp|"
    "8080|tcp|tailscale0"
    "7884|udp|tailscale0"
    "7889|tcp|tailscale0"
)

setup_tailscale() {
    print_header "Configuración de Tailscale"

    if ! command -v tailscale >/dev/null 2>&1; then
        print_err "Tailscale no está instalado."
        print_info "Ejecuta primero la Fase 1 — Paquetes."
        return 1
    fi

    print_info "Habilitando el servicio tailscaled..."

    if sudo systemctl enable --now tailscaled; then
        print_ok "tailscaled está habilitado y ejecutándose."
    else
        print_err "No se pudo iniciar tailscaled."
        return 1
    fi

    local tailscale_ip
    tailscale_ip="$(sudo tailscale ip -4 2>/dev/null | head -n 1)"

    if [ -n "$tailscale_ip" ]; then
        print_ok "Tailscale ya está conectado."
        printf '    IP de Tailscale: %s\n' "$tailscale_ip"
        return 0
    fi

    printf '\n'
    print_info "Tailscale necesita autenticación."
    print_info "Ejecuta el inicio de sesión y selecciona GitHub como proveedor."
    printf '\n'

    if sudo tailscale up; then
        tailscale_ip="$(sudo tailscale ip -4 2>/dev/null | head -n 1)"

        if [ -n "$tailscale_ip" ]; then
            print_ok "Tailscale se conectó correctamente."
            printf '    IP de Tailscale: %s\n' "$tailscale_ip"
            return 0
        fi

        print_warn "tailscale up terminó, pero no se pudo obtener la IP."
        print_info "Puedes comprobar el estado con: sudo tailscale status"
        return 1
    else
        print_err "No se pudo conectar Tailscale."
        return 1
    fi
}

configurar_firewall() {
    print_header "Reglas de firewall"

    local regla puerto proto interface cmd fallo=0

    for regla in "${FIREWALL_RULES[@]}"; do
        IFS='|' read -r puerto proto interface <<< "$regla"

        if [ -n "$interface" ]; then
            cmd=(sudo ufw allow in on "$interface" to any port "$puerto" proto "$proto")
            print_info "Permitiendo ${proto}/${puerto} vía ${interface}..."
        else
            cmd=(sudo ufw allow in to any port "$puerto" proto "$proto")
            print_info "Permitiendo ${proto}/${puerto}..."
        fi

        if "${cmd[@]}"; then
            print_ok "Regla aplicada: ${proto}/${puerto}"
        else
            print_err "Falló la regla: ${proto}/${puerto}"
            fallo=1
        fi
    done

    print_info "Habilitando UFW..."
    if sudo ufw --force enable; then
        print_ok "UFW habilitado."
    else
        print_err "Falló habilitando UFW."
        fallo=1
    fi

    [ "$fallo" -eq 0 ]
}

setup_network() {
    print_header "Configuración de red y firewall"

    if ! instalar_paquetes_red; then
        return 1
    fi

    if ! setup_tailscale; then
        return 1
    fi

    if ! configurar_firewall; then
        return 1
    fi

    print_ok "Red y firewall configurados correctamente."
}

# ─────────────────────────────────────────
# Resumen y verificaciones
# ─────────────────────────────────────────

resumen_manual() {
    print_header "Pasos manuales pendientes"

    printf '  Los siguientes pasos %bno se pueden automatizar%b y deben hacerse a mano:\n\n' "$BOLD" "$NC"

    printf '  %bKDE — Sistema%b\n' "$YELLOW" "$NC"
    echo "    • SDDM: cambiar fondo de pantalla"
    echo "    • Efectos del escritorio: ventanas tambaleantes en 1"
    echo "    • Luz nocturna: activar"
    echo "    • Atajo Meta+T para Alacritty"
    printf '\n'

    printf '  %bApps manuales%b\n' "$YELLOW" "$NC"
    echo "    • Prism Launcher: seleccionar Java 17"
    echo "    • Descargar SmartVideo para el fondo de pantalla"
    echo '    • Snapshot maestra: sudo snapper -c root create --description "Sistema base configurado"'
    printf '\n'

    echo "  Reinicia el sistema después de completar estos pasos para que todo quede aplicado correctamente."
    printf '\n'

    print_header "Verificaciones"

    printf '  %b→%b  Subvolumen /games:\n' "$CYAN" "$NC"
    sudo btrfs subvolume list / || true

    if sudo btrfs subvolume list / | grep -q "games"; then
        print_ok "Subvolumen /games encontrado."
    else
        print_err "Subvolumen /games NO encontrado."
    fi

    printf '\n'
    printf '  %b→%b  Atributo NoCoW en /games:\n' "$CYAN" "$NC"
    lsattr -d /games 2>/dev/null || print_err "No se pudo leer /games"

    printf '\n'
    printf '  %b→%b  Configuraciones de Snapper (debe aparecer solo '"'"'root'"'"'):\n' "$CYAN" "$NC"
    sudo snapper list-configs 2>/dev/null || true

    printf '\n'
    printf '  %b→%b  Límites de Snapper (valores esperados entre paréntesis):\n' "$CYAN" "$NC"

    if sudo test -f /etc/snapper/configs/root; then
        sudo grep -E 'TIMELINE_LIMIT|NUMBER_LIMIT' /etc/snapper/configs/root |
        while read -r line; do
            key=$(echo "$line" | cut -d= -f1)
            value=$(echo "$line" | cut -d= -f2)

            case "$key" in
                TIMELINE_LIMIT_DAILY)   expected='"5"' ;;
                TIMELINE_LIMIT_WEEKLY)  expected='"1"' ;;
                TIMELINE_LIMIT_HOURLY)  expected='"0"' ;;
                TIMELINE_LIMIT_MONTHLY) expected='"0"' ;;
                TIMELINE_LIMIT_YEARLY)  expected='"0"' ;;
                NUMBER_LIMIT)           expected='"0"' ;;
                NUMBER_LIMIT_IMPORTANT) expected='"15"' ;;
                *)                      expected="?" ;;
            esac

            if [ "$value" = "$expected" ]; then
                printf '    %b✔%b  %s=%s (esperado: %s)\n' \
                    "$GREEN" "$NC" "$key" "$value" "$expected"
            else
                printf '    %b✘%b  %s=%s (esperado: %s)\n' \
                    "$RED" "$NC" "$key" "$value" "$expected"
            fi
        done
    else
        print_warn "/etc/snapper/configs/root todavía no existe."
    fi

    printf '\n'
    printf '  %b→%b  Tailscale:\n' "$CYAN" "$NC"

    local tailscale_ip
    tailscale_ip="$(sudo tailscale ip -4 2>/dev/null | head -n 1)"

    if [ -n "$tailscale_ip" ]; then
        print_ok "Tailscale conectado: $tailscale_ip"
    else
        print_warn "Tailscale no aparece conectado."
    fi

    printf '\n'
    printf '  %b→%b  Firewall UFW:\n' "$CYAN" "$NC"
    sudo ufw status || true
}

# ─────────────────────────────────────────
# Pasos manuales de inicio
# ─────────────────────────────────────────

pasos_inicio() {
    print_header "Pasos manuales de inicio"

    printf '  Los siguientes pasos %bson de inicio%b y deben hacerse a mano:\n\n' "$BOLD" "$NC"

    printf '  %bCachyOS Hello%b\n' "$YELLOW" "$NC"
    echo "    • Ananicy Cpp: Habilitado"
    echo "    • Cachy Update: Habilitado"
    echo "    • Systemd-oomd: Deshabilitado"
    echo "    • Bpfutune: Deshabilitado"
    echo "    • Bluetooth: Habilitado"
    echo "    • Evaluar mirrors (Colombia)"
    echo "    • Instalar paquetes de gaming (Wine, Proton, drivers)"
    printf '\n'

    print_header "Comandos importantes"

    printf '  Los siguientes comandos %bson de referencia%b a futuro:\n\n' "$BOLD" "$NC"

    echo "    • Listar snapshots:"
    echo "      sudo snapper -c root list"
    printf '\n'

    echo "    • Borrar snapshots:"
    echo "      sudo snapper -c root delete <número>"
    printf '\n'

    echo "    • Ver espacio de las snapshots:"
    echo "      sudo bash -c 'btrfs filesystem du -s /.snapshots/*/snapshot'"
    printf '\n'

    printf '  %b⚠%b  El campo '"'"'Total'"'"' incluye espacio compartido entre snapshots y parece mayor de lo real.\n' "$YELLOW" "$NC"
    echo "      Ignorar 'Total'. El espacio real es el 'Set shared'"
    echo "      (compartido entre todas) más el 'Exclusive' de cada snapshot"
    echo "      (lo que ocupa de forma única)."
}

# ─────────────────────────────────────────
# Correr todo
# ─────────────────────────────────────────

run_all() {
    print_header "Ejecutando todas las fases"

    print_info "Ejecutando Fase 1 — Paquetes..."
    if ! instalar_paquetes; then
        print_err "La instalación de paquetes falló."
        return 1
    fi

    print_info "Configurando Tailscale y firewall..."
    if ! setup_tailscale; then
        print_err "La configuración de Tailscale falló."
        return 1
    fi

    if ! configurar_firewall; then
        print_err "La configuración del firewall falló."
        return 1
    fi

    print_info "Ejecutando Fase 2 — Dotfiles..."
    if ! copiar_dotfiles; then
        print_err "La Fase 2 falló."
        return 1
    fi

    print_info "Ejecutando Fase 3 — Game Zone..."
    if ! configurar_gamezone; then
        print_err "La Fase 3 falló."
        return 1
    fi

    print_info "Ejecutando Fase 4 — Snapper..."
    if ! configurar_snapper; then
        print_err "La Fase 4 falló."
        return 1
    fi

    printf '\n'
    print_ok "Todas las fases terminaron correctamente."
}

# ─────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────

menu() {
    while true; do
        clear
        printf '\n'
        printf '%b\n' "${BLUE}${BOLD}  ╔══════════════════════════════════════════════╗${NC}"
        printf '%b\n' "${BLUE}${BOLD}  ║   Setup CachyOS KDE — Bash (sin Ansible)   ║${NC}"
        printf '%b\n' "${BLUE}${BOLD}  ╚══════════════════════════════════════════════╝${NC}"
        printf '\n'

        printf '  %b1.%b Fase 1 — Paquetes\n' "$BOLD" "$NC"
        printf '  %b2.%b Fase 2 — Dotfiles y configuraciones\n' "$BOLD" "$NC"
        printf '  %b3.%b Fase 3 — Subvolumen Game Zone\n' "$BOLD" "$NC"
        printf '  %b4.%b Fase 4 — Snapper\n' "$BOLD" "$NC"
        printf '  %b5.%b Fase 5 — Red y Firewall\n' "$BOLD" "$NC"
        printf '  %b6.%b Correr todo de una\n' "$BOLD" "$NC"
        printf '  %b7.%b Ver pasos manuales pendientes\n' "$BOLD" "$NC"
        printf '  %b0.%b Salir\n' "$BOLD" "$NC"
        printf '\n'

        if ! read -rp "  Elige una opción: " opcion; then
            printf '\n'
            print_warn "Entrada finalizada (EOF). Saliendo."
            exit 0
        fi

        case "$opcion" in

            1)
                instalar_paquetes
                pause
                ;;

            2)
                copiar_dotfiles
                pause
                ;;

            3)
                configurar_gamezone
                pause
                ;;

            4)
                configurar_snapper
                pause
                ;;

            5)
                setup_network
                pause
                ;;

            6)
                if confirmar "¿Correr todas las fases?"; then
                    run_all
                else
                    print_info "Cancelado."
                fi

                pause
                ;;

            7)
                resumen_manual
                pause
                ;;

            0)
                printf '\n'
                printf '  %b¡Hasta luego!%b\n\n' "$GREEN" "$NC"
                exit 0
                ;;

            *)
                print_err "Opción no válida."
                sleep 1
                ;;
        esac
    done
}

# ─────────────────────────────────────────
# Verificaciones iniciales
# ─────────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
    print_err "No corras el script como root directamente. Usa tu usuario normal."
    exit 1
fi

if ! sudo -v; then
    print_err "No se pudo obtener privilegios de sudo."
    exit 1
fi

seleccionar_perfil
menu
