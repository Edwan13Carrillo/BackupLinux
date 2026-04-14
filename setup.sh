#!/bin/bash

# ============================================================
#   setup.sh — Automatización post-instalación CachyOS KDE
# ============================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Rutas base (relativas al repo)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/linux/configs"
FONTS_DIR="$SCRIPT_DIR/linux/fonts"

# ─────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────

print_header() {
  echo ""
  echo -e "${BLUE}${BOLD}══════════════════════════════════════${NC}"
  echo -e "${BLUE}${BOLD}  $1${NC}"
  echo -e "${BLUE}${BOLD}══════════════════════════════════════${NC}"
  echo ""
}

print_ok()   { echo -e "  ${GREEN}✔${NC}  $1"; }
print_warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
print_info() { echo -e "  ${CYAN}→${NC}  $1"; }
print_err()  { echo -e "  ${RED}✘${NC}  $1"; }

pause() {
  echo ""
  read -rp "  Presiona Enter para continuar..."
  echo ""
}

confirmar() {
  read -rp "  $1 [s/N]: " resp
  [[ "$resp" =~ ^[sS]$ ]]
}

# ─────────────────────────────────────────
# Fases
# ─────────────────────────────────────────

fase_paquetes() {
  print_header "Fase 1 — Paquetes"

  print_info "Actualizando sistema..."
  sudo pacman -Syu --noconfirm

  print_info "Instalando paquetes desde repositorio oficial..."
  sudo pacman -S --noconfirm --needed \
    discord \
    protonvpn \
    vlc \
    telegram-desktop \
    zen-browser-bin \
    git \
    fastfetch \
    base-devel \
    yay

  print_ok "Paquetes base instalados."

  print_info "Instalando Visual Studio Code (AUR)..."
  yay -S --noconfirm visual-studio-code-bin
  print_ok "VSCode instalado."

  print_info "Instalando Sober/Roblox (Flatpak)..."
  flatpak install -y sober
  print_ok "Sober instalado."

  print_warn "Prism Launcher: instalación manual. Recuerda seleccionar Java 17 dentro de la app."
}

fase_dotfiles() {
  print_header "Fase 2 — Dotfiles y configuraciones"

  # Fastfetch
  if [ -d "$CONFIGS_DIR/fastfetch" ]; then
    print_info "Copiando configuración de Fastfetch..."
    mkdir -p ~/.config/fastfetch
    cp -r "$CONFIGS_DIR/fastfetch/." ~/.config/fastfetch/
    print_ok "Fastfetch configurado."
  else
    print_err "No se encontró la carpeta fastfetch en $CONFIGS_DIR"
  fi

  # Konsole
  if [ -d "$CONFIGS_DIR/konsole" ]; then
    print_info "Copiando perfil de Konsole..."
    mkdir -p ~/.local/share/konsole
    cp -r "$CONFIGS_DIR/konsole/." ~/.local/share/konsole/
    print_ok "Perfil de Konsole copiado."
    print_warn "Abre Konsole > Ajustes > Gestionar perfiles y márcalo como predeterminado."
  else
    print_err "No se encontró la carpeta konsole en $CONFIGS_DIR"
  fi

  # Widget Clear Clock
  #if [ -d "$CONFIGS_DIR/widget" ]; then
  #  print_info "Copiando widget Clear Clock..."
  #  mkdir -p ~/.local/share/plasma/plasmoids
  #  cp -r "$CONFIGS_DIR/widget/." ~/.local/share/plasma/plasmoids/
  #  print_ok "Widget copiado."
  #  print_warn "Agrega el widget al escritorio, reemplaza su config.qml y luego refresca Plasma:"
  #  print_warn "kquitapp6 plasmashell && kstart5 plasmashell"
  #else
  #  print_err "No se encontró la carpeta widget en $CONFIGS_DIR"
  #fi
}

#fase_fuentes() {
#  print_header "Fase 3 — Fuentes"
#
#  if [ -d "$FONTS_DIR" ] && [ "$(ls -A "$FONTS_DIR"/*.ttf 2>/dev/null)" ]; then
#    print_info "Instalando fuentes..."
#    mkdir -p ~/.local/share/fonts
#    cp "$FONTS_DIR"/*.ttf ~/.local/share/fonts/
#    fc-cache -fv > /dev/null 2>&1
#    print_ok "Fuentes instaladas: $(ls "$FONTS_DIR"/*.ttf | wc -l) archivo(s)."
#    print_warn "Aplica las fuentes en: Ajustes del sistema > Fuentes (Fredoka Medium 12pt / 10pt)."
#  else
#    print_err "No se encontraron archivos .ttf en $FONTS_DIR"
#  fi
#}

fase_gamezone() {
  print_header "Fase 4 — Subvolumen Game Zone (Btrfs)"

  if [ -d "/games" ]; then
    print_warn "El subvolumen /games ya existe. Saltando."
    return
  fi

  print_info "Creando subvolumen /games..."
  sudo btrfs subvolume create /games
  sudo chattr +C /games
  sudo chown "$USER":"$USER" /games
  print_ok "Subvolumen /games creado con NoCoW habilitado."
}

fase_snapper() {
  print_header "Fase 5 — Snapper (Snapshots)"

  print_info "Instalando snapper..."
  sudo pacman -S --noconfirm --needed snapper snapper-support btrfs-assistant

  print_info "Creando configuración root..."
  sudo snapper -c root create-config /

  print_info "Ajustando límites en /etc/snapper/configs/root..."
  sudo sed -i 's/^DAILY_LIMIT=.*/DAILY_LIMIT="5"/' /etc/snapper/configs/root
  sudo sed -i 's/^WEEKLY_LIMIT=.*/WEEKLY_LIMIT="1"/' /etc/snapper/configs/root
  sudo sed -i 's/^MONTHLY_LIMIT=.*/MONTHLY_LIMIT="0"/' /etc/snapper/configs/root
  sudo sed -i 's/^YEARLY_LIMIT=.*/YEARLY_LIMIT="0"/' /etc/snapper/configs/root
  sudo sed -i 's/^HOURLY_LIMIT=.*/HOURLY_LIMIT="0"/' /etc/snapper/configs/root
  sudo sed -i 's/^NUMBER_LIMIT=.*/NUMBER_LIMIT="0"/' /etc/snapper/configs/root

  print_ok "Snapper configurado."
  print_warn "Cuando el sistema esté completamente listo, crea la snapshot maestra:"
  print_warn "snapper -c root create --description \"Sistema base configurado\""
}

resumen_manual() {
  print_header "Pasos manuales pendientes"

  echo -e "  Los siguientes pasos ${BOLD}no se pueden automatizar${NC} y deben hacerse a mano:\n"

  echo -e "  ${YELLOW}CachyOS Hello${NC}"
  echo "    • Ananicy Cpp: Habilitado"
  echo "    • Cachy Update: Habilitado"
  echo "    • Systemd-oomd: Deshabilitado"
  echo "    • Bpfutune: Deshabilitado"
  echo "    • Bluetooth: Habilitado"
  echo "    • Evaluar mirrors (Colombia)"
  echo "    • Instalar paquetes de gaming (Wine, Proton, drivers)"
  echo ""
  echo -e "  ${YELLOW}KDE — Apariencia${NC}"
  echo "    • Tema global: Layan"
  echo "    • Colores: ArchDark"
  echo "    • Estilo de aplicaciones: Brisa"
  echo "    • Estilo de Plasma: Arch-round"
  echo "    • Decoraciones de ventanas: Layan"
  echo "    • Iconos: Tela Dark"
  echo "    • Cursores: Bibata-Modern-Ice"
  echo "    • Splash screen: Kuro"
  echo "    • Fuentes: Fredoka Medium 12pt (10pt para pequeños)"
  echo ""
  echo -e "  ${YELLOW}KDE — Sistema${NC}"
  echo "    • SDDM: cambiar fondo de pantalla"
  echo "    • Efectos del escritorio: ventanas tambaleantes en 1"
  echo "    • Luz nocturna: activar"
  echo "    • Atajo Meta+T para Konsole"
  echo "    • Konsole: marcar perfil como predeterminado"
  echo ""
  echo -e "  ${YELLOW}Apps manuales${NC}"
  echo "    • Prism Launcher: instalar y seleccionar Java 17"
  echo "    • Snapshot maestra de Snapper (cuando el sistema esté listo)"
  echo ""
}

# ─────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────

menu() {
  clear
  echo ""
  echo -e "${BLUE}${BOLD}  ╔══════════════════════════════════════╗${NC}"
  echo -e "${BLUE}${BOLD}  ║   Setup CachyOS KDE — Post-Install  ║${NC}"
  echo -e "${BLUE}${BOLD}  ╚══════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${BOLD}1.${NC} Correr todo de una"
  echo -e "  ${BOLD}2.${NC} Fase 1 — Paquetes"
  echo -e "  ${BOLD}3.${NC} Fase 2 — Dotfiles y configuraciones"
  echo -e "  ${BOLD}4.${NC} Fase 3 — Fuentes"
  echo -e "  ${BOLD}5.${NC} Fase 4 — Subvolumen Game Zone"
  echo -e "  ${BOLD}6.${NC} Fase 5 — Snapper"
  echo -e "  ${BOLD}7.${NC} Ver pasos manuales pendientes"
  echo -e "  ${BOLD}0.${NC} Salir"
  echo ""
  read -rp "  Elige una opción: " opcion

  case $opcion in
    1)
      if confirmar "¿Correr todas las fases?"; then
        fase_paquetes; pause
        fase_dotfiles; pause
        fase_fuentes; pause
        fase_gamezone; pause
        fase_snapper; pause
        resumen_manual
      fi
      ;;
    2) fase_paquetes; pause ;;
    3) fase_dotfiles; pause ;;
    4) fase_fuentes; pause ;;
    5) fase_gamezone; pause ;;
    6) fase_snapper; pause ;;
    7) resumen_manual; pause ;;
    0) echo ""; echo -e "  ${GREEN}¡Hasta luego!${NC}"; echo ""; exit 0 ;;
    *) print_err "Opción no válida." ;;
  esac

  menu
}

# ─────────────────────────────────────────
# Verificación inicial
# ─────────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
  print_err "No corras el script como root directamente. Usa tu usuario normal."
  exit 1
fi

menu
