#!/bin/bash

# ─────────────────────────────────────────
# Setup CachyOS KDE — Versión 100% Bash
# Respaldo sin dependencia de Ansible.
# Traducción directa de ansible/playbook.yml
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────

BK_COMMON="$HOME/BackupLinux/linux/common"
BK_NIRI="$HOME/BackupLinux/linux/niri"
BK_PLASMA="$HOME/BackupLinux/linux/plasma"
ASSETS_DIR="$HOME/BackupLinux/assets"
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
    base-devel paru flatpak python-mutagen tk rsync snapper
    cachyos-snapper-support btrfs-assistant
    alacritty baobab gnome-text-editor
)

# Paquetes exclusivos del perfil Plasma
PAQUETES_PLASMA=(
    haruna
)

# Paquetes exclusivos del perfil Niri + Noctalia (repos oficiales / CachyOS)
PAQUETES_NIRI=(
    matugen quickshell
    gnome-keyring libsecret
    mpv jq curl openbsd-netcat mpv-mpris
    bitwarden-cli
)

# Paquetes exclusivos del perfil Niri que solo existen en AUR
PAQUETES_NIRI_AUR=(
    sddm-astronaut-theme millennium
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

instalar_uosc() {
    print_info "Instalando uosc para mpv..."

    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/tomasklaen/uosc/HEAD/installers/unix.sh)"; then
        print_ok "uosc instalado."
        return 0
    else
        print_err "Falló la instalación de uosc."
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

    if [ "$PROFILE" = "niri" ]; then
        print_info "Instalando paquetes específicos de Niri..."
        if ! sudo pacman -S --needed --noconfirm "${PAQUETES_NIRI[@]}"; then
            print_err "Falló la instalación de paquetes de Niri."
            return 1
        fi
        print_ok "Paquetes de Niri instalados."

        if ! instalar_uosc; then
            return 1
        fi

        print_info "Instalando sddm-astronaut-theme y millennium (AUR) con paru..."
        if paru -S --needed --noconfirm "${PAQUETES_NIRI_AUR[@]}"; then
            print_ok "Paquetes AUR de Niri instalados."
        else
            print_err "Falló la instalación de paquetes AUR de Niri."
            return 1
        fi
    fi

    if [ "$PROFILE" = "plasma" ]; then
        print_info "Instalando paquetes específicos de Plasma..."
        if ! sudo pacman -S --needed --noconfirm "${PAQUETES_PLASMA[@]}"; then
            print_err "Falló la instalación de paquetes de Plasma."
            return 1
        fi
        print_ok "Paquetes de Plasma instalados."
    fi

    if ! instalar_paquetes_red; then
        return 1
    fi

    print_info "Instalando Visual Studio Code (AUR) con paru..."
    # OJO: paru NO se corre con sudo, el mismo escala privilegios cuando
    # necesita instalar el paquete compilado. Si paru no está en PATH
    # todavía, corre esta fase de nuevo después de que termine.
    if paru -S --needed --noconfirm visual-studio-code-bin; then
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

    print_info "Configurando Zen como navegador predeterminado..."
    if xdg-settings set default-web-browser zen.desktop; then
        print_ok "Zen configurado como navegador predeterminado."
    else
        print_warn "No se pudo configurar Zen como predeterminado (hazlo manual si hace falta)."
    fi

    print_ok "Fase 1 completada."
}

# ─────────────────────────────────────────
# Fase 2 — Dotfiles
# ─────────────────────────────────────────

# Formato: origen|destino|delete(0/1)|sudo(0/1)
# Mismos orígenes, destinos y flags que las listas del playbook.
DOTFILES_COMUNES=(
    "$BK_COMMON/fonts/|$LOCAL_DIR/fonts/|0|0"
    "$BK_COMMON/Starlord|/usr/share/plymouth/themes/|1|1"
    "$BK_COMMON/Bibata-Modern-Ice|$HOME/.icons/|1|0"
    "$BK_COMMON/fastfetch/|$CONFIG_DIR/fastfetch/|0|0"
    "$BK_COMMON/alacritty/|$CONFIG_DIR/alacritty/|0|0"
)

DOTFILES_PLASMA=(
    "$BK_PLASMA/Layan|$LOCAL_DIR/aurorae/themes/|1|0"
    "$BK_PLASMA/desktoptheme|$LOCAL_DIR/plasma/|1|0"
    "$BK_PLASMA/a2n.kuro|$LOCAL_DIR/plasma/look-and-feel/|0|0"
    "$BK_PLASMA/Tela|$LOCAL_DIR/icons/|1|0"
    "$BK_PLASMA/org.kde.plasma.clearclock|$LOCAL_DIR/plasma/plasmoids/|1|0"
    "$BK_PLASMA/cachyosTG|$LOCAL_DIR/plasma/look-and-feel/|0|0"
    "$BK_PLASMA/kdedefaults/|$CONFIG_DIR/kdedefaults/|0|0"
    "$BK_PLASMA/ArchDark.colors|$LOCAL_DIR/color-schemes/|0|0"
    "$BK_PLASMA/haruna/|$CONFIG_DIR/haruna/|0|0"
)

DOTFILES_NIRI=(
    "$BK_NIRI/matugen|$CONFIG_DIR/|1|0"
    "$BK_NIRI/noctalia|$CONFIG_DIR/|1|0"
    "$BK_NIRI/niri/|$CONFIG_DIR/niri/|1|0"
    "$BK_NIRI/quickshell/wallpaper-picker|$CONFIG_DIR/quickshell/|1|0"
    "$BK_NIRI/sddm/metadata.desktop|/usr/share/sddm/themes/sddm-astronaut-theme/|0|1"
    "$BK_NIRI/sddm/japanese_aesthetic.conf|/usr/share/sddm/themes/sddm-astronaut-theme/Themes/|0|1"
    "$ASSETS_DIR/icons/archlinu.png|/usr/share/icons/|0|1"
    "$BK_NIRI/mimeapps.list|$CONFIG_DIR/|0|0"
    "$BK_NIRI/mpv/skip_confirm.lua|$CONFIG_DIR/mpv/scripts/|0|0"
)

configurar_sddm_theme() {
    print_info "Activando sddm-astronaut-theme en SDDM..."

    if sudo mkdir -p /etc/sddm.conf.d &&
       printf '[Theme]\nCurrent=sddm-astronaut-theme\n' | sudo tee /etc/sddm.conf.d/theme.conf >/dev/null; then
        print_ok "SDDM configurado para usar sddm-astronaut-theme."
        return 0
    else
        print_err "Falló activando el tema de SDDM."
        return 1
    fi
}

configurar_symlinks_zen() {
    print_info "Configurando symlinks de Zen (necesarios para el plugin de YouTube Music)..."
    local ok=1

    if [ -L "$HOME/.zen" ] || [ -e "$HOME/.zen" ]; then
        print_ok "~/.zen ya existe."
    else
        if ln -s "$CONFIG_DIR/zen" "$HOME/.zen"; then
            print_ok "Symlink ~/.zen creado."
        else
            print_err "Falló creando ~/.zen"
            ok=0
        fi
    fi

    if [ -L /usr/local/bin/zen ] || [ -e /usr/local/bin/zen ]; then
        print_ok "/usr/local/bin/zen ya existe."
    else
        if sudo ln -s /usr/bin/zen-browser /usr/local/bin/zen; then
            print_ok "Symlink /usr/local/bin/zen creado."
        else
            print_err "Falló creando /usr/local/bin/zen"
            ok=0
        fi
    fi

    [ "$ok" = "1" ]
}

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

    print_info "Activando el tema de Plymouth (Starlord)..."
    if sudo plymouth-set-default-theme -R Starlord; then
        print_ok "Plymouth configurado con el tema Starlord."
    else
        print_err "No se pudo activar Plymouth. Actívalo manualmente: sudo plymouth-set-default-theme -R Starlord"
        fallo=1
    fi

    if [ "$PROFILE" = "plasma" ]; then
        print_warn "Aplica las fuentes en: Ajustes del sistema > Fuentes (Fredoka Medium 12pt / 10pt)."
        print_warn "Ve a: Ajustes del sistema > Aspecto > Tema global y selecciona 'CachyTG' para aplicarlo."
        print_warn "Cierra sesión y vuelve a entrar para que KDE aplique todos los temas."
        print_warn "Agrega el widget Clear Clock al escritorio, reemplaza su config.qml y refresca Plasma con: kquitapp6 plasmashell && kstart5 plasmashell"
    fi

    if [ "$PROFILE" = "niri" ]; then
        chmod +x "$CONFIG_DIR/noctalia/hooks/matugen-wallpaper.sh" 2>/dev/null || true

        if ! configurar_sddm_theme; then
            fallo=1
        fi

        if ! configurar_symlinks_zen; then
            fallo=1
        fi

        print_warn "Abre Noctalia y cambia de wallpaper una vez para activar el pipeline de matugen (borde de Niri)."
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

    local qbit_dir="$HOME/Documentos/qbit"

    if [ -d "$qbit_dir" ]; then
        print_ok "La carpeta $qbit_dir ya existe."
    else
        print_info "Creando $qbit_dir..."
        if mkdir -p "$qbit_dir"; then
            print_ok "Carpeta creada."
        else
            print_err "Falló creando $qbit_dir."
            return 1
        fi
    fi

    local attrs_qbit
    attrs_qbit="$(lsattr -d "$qbit_dir" 2>/dev/null | awk '{print $1}')"

    if [[ "$attrs_qbit" == *C* ]]; then
        print_ok "NoCoW ya está activo en $qbit_dir."
    else
        print_info "Activando NoCoW (chattr +C) en $qbit_dir..."
        if chattr +C "$qbit_dir"; then
            print_ok "NoCoW activado en $qbit_dir."
        else
            print_err "Falló activando NoCoW en $qbit_dir."
            return 1
        fi
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

pendientes_manuales() {
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

    if [ "$PROFILE" = "niri" ]; then
        printf '\n'
        echo "    • Millennium (Steam): ya se instaló el paquete. Abre Steam y activa el tema NEVKO-UI a mano."
        echo "      La copia del CSS de NEVKO-UI se maneja en otro script aparte, no aquí."
        printf '\n'
        echo "    • Bitwarden: corre 'bw login' para iniciar sesión (es interactivo, no se automatiza)."
        echo "      Revisa en la extensión/CLI que el timeout del vault sea 15 min y el clear clipboard 30 seg."
        echo "      Funciona en el launcher escribiendo '/bw'."
        printf '\n'
        echo "    • Better Clock (Noctalia): abre Noctalia y activa el plugin community/better-clock"
        echo "      desde Settings → Plugins. Cuando ya exista la carpeta, copia:"
        echo "        cp \"$BK_NIRI/widget.luau\" \\"
        echo "          ~/.local/state/noctalia/plugins/materialized/community/better-clock/widget.luau"
    fi
    printf '\n'

    echo "  Reinicia el sistema después de completar estos pasos para que todo quede aplicado correctamente."
    printf '\n'
}

verificaciones() {
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
    printf '  %b→%b  Atributo NoCoW en ~/Documentos/qbit:\n' "$CYAN" "$NC"
    lsattr -d "$HOME/Documentos/qbit" 2>/dev/null || print_err "No se pudo leer ~/Documentos/qbit"

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

    if [ "$PROFILE" = "niri" ]; then
        printf '\n'
        printf '  %b→%b  Symlink de Zen:\n' "$CYAN" "$NC"

        local zen_path
        zen_path="$(command -v zen 2>/dev/null || true)"

        if [ "$zen_path" = "/usr/local/bin/zen" ]; then
            print_ok "command -v zen -> $zen_path"
        else
            print_err "command -v zen -> ${zen_path:-no encontrado} (se esperaba /usr/local/bin/zen)"
        fi

        printf '\n'
        printf '  %b→%b  Perfiles de Zen (revisa a ojo, no se edita por script):\n' "$CYAN" "$NC"

        if [ -f "$CONFIG_DIR/zen/profiles.ini" ]; then
            cat "$CONFIG_DIR/zen/profiles.ini"
        else
            print_warn "No se encontró $CONFIG_DIR/zen/profiles.ini todavía."
        fi
    fi
}

resumen_manual() {
    pendientes_manuales
    verificaciones
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