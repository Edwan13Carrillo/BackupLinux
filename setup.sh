#!/bin/bash

# ─────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="$SCRIPT_DIR/ansible/inventory.ini"
PLAYBOOK="$SCRIPT_DIR/ansible/playbook.yml"

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
# Verificar dependencias de Ansible
# ─────────────────────────────────────────

check_ansible() {
    if command -v ansible >/dev/null 2>&1 &&
       command -v ansible-playbook >/dev/null 2>&1; then
        print_ok "Ansible ya está instalado."
    else
        print_warn "Ansible no está instalado."

        if ! confirmar "¿Deseas instalar Ansible y ansible-lint?"; then
            print_err "Ansible es necesario para continuar."
            exit 1
        fi

        printf '\n'
        print_info "Instalando Ansible y ansible-lint..."

        if sudo pacman -S --needed --noconfirm ansible ansible-lint; then
            print_ok "Ansible se instaló correctamente."
        else
            print_err "No se pudo instalar Ansible."
            exit 1
        fi
    fi
}

check_ansible_collection() {
    local missing=0

    if ansible-galaxy collection list community.general >/dev/null 2>&1; then
        print_ok "La colección community.general ya está instalada."
    else
        print_info "Instalando la colección Ansible community.general..."

        if ansible-galaxy collection install community.general; then
            print_ok "community.general se instaló correctamente."
        else
            print_err "No se pudo instalar la colección community.general."
            missing=1
        fi
    fi

    if ansible-galaxy collection list ansible.posix >/dev/null 2>&1; then
        print_ok "La colección ansible.posix ya está instalada."
    else
        print_info "Instalando la colección Ansible ansible.posix..."

        if ansible-galaxy collection install ansible.posix; then
            print_ok "ansible.posix se instaló correctamente."
        else
            print_err "No se pudo instalar la colección ansible.posix."
            missing=1
        fi
    fi

    if [ "$missing" -ne 0 ]; then
        return 1
    fi

    return 0
}

# ─────────────────────────────────────────
# Ejecutar Ansible
# ─────────────────────────────────────────

run_playbook() {
    local tags="$1"

    printf '\n'

    # Comprobar que el inventario existe.
    if [ ! -f "$INVENTORY" ]; then
        print_err "No se encontró el inventario de Ansible:"
        echo "    $INVENTORY"
        return 1
    fi

    # Comprobar que el playbook existe.
    if [ ! -f "$PLAYBOOK" ]; then
        print_err "No se encontró el playbook de Ansible:"
        echo "    $PLAYBOOK"
        return 1
    fi

    print_info "Ejecutando Ansible con:"
    printf '    Inventario: %s\n' "$INVENTORY"
    printf '    Playbook:   %s\n' "$PLAYBOOK"
    printf '    Tags:       %s\n' "$tags"
    printf '    Perfil:     %s\n' "$PROFILE"
    printf '\n'

    if ansible-playbook \
        -i "$INVENTORY" \
        "$PLAYBOOK" \
        --tags "$tags" \
        --extra-vars "PROFILE=$PROFILE" \
        --ask-become-pass; then

        print_ok "Ansible terminó correctamente."
        return 0
    fi

    print_err "Ansible encontró un error."

    if [ -f "$SCRIPT_DIR/setupBash.sh" ]; then
        print_warn "Abriendo el respaldo Bash con el perfil: $PROFILE"
        PROFILE="$PROFILE" bash "$SCRIPT_DIR/setupBash.sh"
    else
        print_warn "No se encontró un respaldo Bash ejecutable."
    fi

    return 1
}

# ─────────────────────────────────────────
# Configuración de Tailscale
# ─────────────────────────────────────────

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

    # Comprobar si el equipo ya tiene una sesión activa.
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

# ─────────────────────────────────────────
# Configurar red y firewall
# ─────────────────────────────────────────

setup_network() {
    print_header "Configuración de red y firewall"

    # Primero instalamos Tailscale y UFW.
    if ! run_playbook "network_packages"; then
        return 1
    fi

    # Después levantamos Tailscale, para que tailscale0 exista.
    if ! setup_tailscale; then
        return 1
    fi

    # Finalmente creamos las reglas de UFW.
    if ! run_playbook "firewall"; then
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

    # ── Verificaciones automáticas ──
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

    # Fase 1: paquetes
    print_info "Ejecutando Fase 1 — Paquetes..."

    if ! run_playbook "paquetes"; then
        print_err "La instalación de paquetes falló."
        return 1
    fi

    # Red: primero Tailscale, luego firewall.
    print_info "Configurando Tailscale y firewall..."

    if ! setup_tailscale; then
        print_err "La configuración de Tailscale falló."
        return 1
    fi

    if ! run_playbook "firewall"; then
        print_err "La configuración del firewall falló."
        return 1
    fi

    # Resto de fases.
    print_info "Ejecutando Fase 2 — Dotfiles..."

    if ! run_playbook "dotfiles"; then
        print_err "La Fase 2 falló."
        return 1
    fi

    print_info "Ejecutando Fase 3 — Game Zone..."

    if ! run_playbook "gamezone"; then
        print_err "La Fase 3 falló."
        return 1
    fi

    print_info "Ejecutando Fase 4 — Snapper..."

    if ! run_playbook "snapper"; then
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
        printf '%b\n' "${BLUE}${BOLD}  ║       Setup CachyOS KDE — Post-Install     ║${NC}"
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
                run_playbook "paquetes"
                pause
                ;;

            2)
                run_playbook "dotfiles"
                pause
                ;;

            3)
                run_playbook "gamezone"
                pause
                ;;

            4)
                run_playbook "snapper"
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
    print_err "No corras el script como root directamente."
    print_info "Ejecuta el script con tu usuario normal."
    exit 1
fi

# Verificar que sudo funciona antes de comenzar.
if ! sudo -v; then
    print_err "No se pudo autenticar con sudo."
    exit 1
fi

# Comprobar playbook.
if [ ! -f "$PLAYBOOK" ]; then
    print_err "No se encontró el playbook:"
    echo "    $PLAYBOOK"
    exit 1
fi

# Comprobar inventario.
if [ ! -f "$INVENTORY" ]; then
    print_err "No se encontró el inventario:"
    echo "    $INVENTORY"
    printf '\n'
    print_info "El inventario esperado debe contener, por ejemplo:"
    echo "    localhost ansible_connection=local"
    exit 1
fi

# Comprobar que el inventario realmente contiene localhost.
if ! grep -Eq '^[[:space:]]*localhost([[:space:]]|$)' "$INVENTORY"; then
    print_warn "El inventario existe, pero no parece contener 'localhost'."
    print_info "Contenido actual del inventario:"
    sed 's/^/    /' "$INVENTORY"
    printf '\n'
fi

check_ansible
if ! check_ansible_collection; then
    print_err "No se pudieron preparar las colecciones de Ansible."
    exit 1
fi

seleccionar_perfil
menu

