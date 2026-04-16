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
    vlc \
    telegram-desktop \
    zen-browser-bin \
    libreoffice-still \
    libreoffice-still-es \
    git \
    alacritty \
    fastfetch \
    base-devel \
    yay

  print_ok "Paquetes base instalados."

  print_info "Instalando Visual Studio Code (AUR)..."
  yay -S --noconfirm visual-studio-code-bin
  print_ok "VSCode instalado."

  print_info "Instalando Sober/Roblox (Flatpak)..."
  flatpak install flathub org.vinegarhq.Sober
  print_ok "Sober instalado."

  print_warn "Prism Launcher: instalación manual. Recuerda seleccionar Java 17 dentro de la app."
}

fase_dotfiles() {
  print_header "Fase 2 — Dotfiles y configuraciones"
  # ── Temas KDE (primero los archivos, luego la config) ──

  # Aurorae (decoraciones de ventanas)
  if [ -d "$CONFIGS_DIR/local/Layan" ]; then
    print_info "Copiando tema de decoraciones Layan..."
    mkdir -p ~/.local/share/aurorae/themes
    cp -r "$CONFIGS_DIR/local/Layan/" ~/.local/share/aurorae/themes/
    print_ok "Decoraciones Layan copiadas."
  else
    print_err "No se encontró la carpeta aurorae/Layan en $CONFIGS_DIR"
  fi

  # Color scheme
  if [ -f "$CONFIGS_DIR/local/ArchDark.colors" ]; then
    print_info "Copiando esquema de colores ArchDark..."
    mkdir -p ~/.local/share/color-schemes
    cp "$CONFIGS_DIR/local/ArchDark.colors" ~/.local/share/color-schemes/
    print_ok "Colores ArchDark copiados."
  else
    print_err "No se encontró ArchDark.colors en $CONFIGS_DIR"
  fi

  # Plasma desktop theme
  if [ -d "$CONFIGS_DIR/local/desktoptheme" ]; then
    print_info "Copiando temas de Plasma (Arch-round, Layan)..."
    mkdir -p ~/.local/share/plasma/desktoptheme
    cp -r "$CONFIGS_DIR/local/desktoptheme/" ~/.local/share/plasma/
    print_ok "Temas de Plasma copiados."
  else
    print_err "No se encontró la carpeta desktoptheme en $CONFIGS_DIR"
  fi

  # Look and feel (splash screen Kuro)
  if [ -d "$CONFIGS_DIR/local/a2n.kuro/" ]; then
    print_info "Copiando look and feel (Kuro)..."
    mkdir -p ~/.local/share/plasma/look-and-feel
    cp -r "$CONFIGS_DIR/local/a2n.kuro/" ~/.local/share/plasma/look-and-feel/
    print_ok "Look and feel copiado (Kuro)."
  else
    print_err "No se encontró la carpeta a2n.kuro en $CONFIGS_DIR"
  fi

  # Pantalla de arranque (Pixels)
  if [ -d "$CONFIGS_DIR/pixels/" ]; then
    print_info "Copiando pantalla de arranque (pixels)..."
    sudo cp -r "$CONFIGS_DIR/pixels/" /usr/share/plymouth/themes/
    print_ok "Pantalla de arranque copiado (pixels)."
  else
    print_err "No se encontró la carpeta pixels en $CONFIGS_DIR"
  fi

  # Iconos Tela Dark
  if [ -d "$CONFIGS_DIR/Tela" ]; then
    print_info "Copiando iconos Tela..."
    mkdir -p ~/.local/share/icons
    cp -r "$CONFIGS_DIR/Tela/" ~/.local/share/icons/
    print_ok "Iconos Tela copiados."
  else
    print_err "No se encontró la carpeta icons/Tela en $CONFIGS_DIR"
  fi

  # Cursores Bibata
  if [ -d "$CONFIGS_DIR/local/Bibata-Modern-Ice" ]; then
    print_info "Copiando cursores Bibata-Modern-Ice..."
    mkdir -p ~/.icons
    cp -r "$CONFIGS_DIR/local/Bibata-Modern-Ice/" ~/.icons/
    print_ok "Cursores copiados."
  else
    print_err "No se encontró la carpeta cursors/Bibata-Modern-Ice en $CONFIGS_DIR"
  fi

  # Tema global
  if [ -d "$CONFIGS_DIR/local/cachyosTG" ]; then
    print_info "Copiando tema global..."
    cp -r "$CONFIGS_DIR/local/cachyosTG/" ~/.local/share/plasma/look-and-feel/
    print_ok "Tema global copiado."
    print_warn "Ve a: Ajustes del sistema > Aspecto > Tema global y selecciona 'CachyTG' para aplicarlo."
  else
    print_err "No se encontró la carpeta cursors/Bibata-Modern-Ice en $CONFIGS_DIR"
  fi

  # kdedefaults (al final, cuando ya están los temas)
  if [ -d "$CONFIGS_DIR/kdedefaults" ]; then
    print_info "Aplicando configuración de KDE..."
    mkdir -p ~/.config/kdedefaults
    cp -r "$CONFIGS_DIR/kdedefaults/." ~/.config/kdedefaults/
    print_ok "Configuración de KDE aplicada."
    print_warn "Cierra sesión y vuelve a entrar para que KDE aplique todos los temas."
  else
    print_err "No se encontró la carpeta kdedefaults en $CONFIGS_DIR"
  fi

  # ── Aplicaciones ──

  # Fastfetch
  if [ -d "$CONFIGS_DIR/fastfetch" ]; then
    print_info "Copiando configuración de Fastfetch..."
    mkdir -p ~/.config/fastfetch
    cp -r "$CONFIGS_DIR/fastfetch/." ~/.config/fastfetch/
    print_ok "Fastfetch configurado."
  else
    print_err "No se encontró la carpeta fastfetch en $CONFIGS_DIR"
  fi

  # Alacritty
  if [ -d "$CONFIGS_DIR/alacritty" ]; then
    print_info "Copiando configuración de Alacritty..."
    mkdir -p ~/.config/alacritty
    cp -r "$CONFIGS_DIR/alacritty/." ~/.config/alacritty/
    print_ok "Alacritty configurado."
  else
    print_err "No se encontró la carpeta alacritty en $CONFIGS_DIR"
  fi

  # Widget Clear Clock
  if [ -d "$CONFIGS_DIR/org.kde.plasma.clearclock" ]; then
    print_info "Copiando widget Clear Clock..."
    mkdir -p ~/.local/share/plasma/plasmoids
    cp -r "$CONFIGS_DIR/org.kde.plasma.clearclock/" ~/.local/share/plasma/plasmoids/
    print_ok "Widget copiado."
    print_warn "Agrega el widget al escritorio, reemplaza su config.qml y luego refresca Plasma:"
    print_warn "kquitapp6 plasmashell && kstart5 plasmashell"
  else
    print_err "No se encontró la carpeta widget en $CONFIGS_DIR"
  fi
}

fase_fuentes() {
  print_header "Fase 3 — Fuentes"

  shopt -s nullglob
  local fuentes=("$FONTS_DIR"/*.ttf "$FONTS_DIR"/*.otf)
  shopt -u nullglob

  if [ -d "$FONTS_DIR" ] && [ ${#fuentes[@]} -gt 0 ]; then
    print_info "Instalando fuentes..."
    mkdir -p ~/.local/share/fonts
    
    cp "${fuentes[@]}" ~/.local/share/fonts/
    
    fc-cache -fv > /dev/null 2>&1
    
    print_ok "Fuentes instaladas: ${#fuentes[@]} archivo(s)."
    print_warn "Aplica las fuentes en: Ajustes del sistema > Fuentes (Fredoka Medium 12pt / 10pt)."
  else
    print_err "No se encontraron archivos .ttf ni .otf en $FONTS_DIR"
  fi
}

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
  sudo pacman -S --noconfirm --needed snapper cachyos-snapper-support btrfs-assistant

  print_info "Creando configuración root..."
  sudo snapper -c root create-config /

  print_info "Ajustando límites en /etc/snapper/configs/root..."
  sudo sed -i 's/^TIMELINE_LIMIT_DAILY=.*/TIMELINE_LIMIT_DAILY="5"/' /etc/snapper/configs/root
  sudo sed -i 's/^TIMELINE_LIMIT_WEEKLY=.*/TIMELINE_LIMIT_WEEKLY="1"/' /etc/snapper/configs/root
  sudo sed -i 's/^TIMELINE_LIMIT_MONTHLY=.*/TIMELINE_LIMIT_MONTHLY="0"/' /etc/snapper/configs/root
  sudo sed -i 's/^TIMELINE_LIMIT_YEARLY=.*/TIMELINE_LIMIT_YEARLY="0"/' /etc/snapper/configs/root
  sudo sed -i 's/^TIMELINE_LIMIT_HOURLY=.*/TIMELINE_LIMIT_HOURLY="0"/' /etc/snapper/configs/root
  sudo sed -i 's/^NUMBER_LIMIT=.*/NUMBER_LIMIT="0"/' /etc/snapper/configs/root

  print_ok "Snapper configurado."
  print_warn "Cuando el sistema esté completamente listo, crea la snapshot maestra:"
  print_warn "snapper -c root create --description \"Sistema base configurado\""
}

resumen_manual() {
  print_header "Pasos manuales pendientes"

  echo -e "  Los siguientes pasos ${BOLD}no se pueden automatizar${NC} y deben hacerse a mano:\n"

  echo -e "  ${YELLOW}KDE — Sistema${NC}"
  echo "    • SDDM: cambiar fondo de pantalla"
  echo "    • Efectos del escritorio: ventanas tambaleantes en 1"
  echo "    • Luz nocturna: activar"
  echo "    • Atajo Meta+T para Alacritty"
  echo ""
  echo -e "  ${YELLOW}Apps manuales${NC}"
  echo "    • Prism Launcher: instalar y seleccionar Java 17"
  echo '    • Snapshot maestra: sudo snapper -c root create --description "Sistema base configurado"'
  echo ""
  echo "  Reinicia el sistema después de completar estos pasos para que todo quede aplicado correctamente."
  echo ""

  # ── Verificaciones automáticas ──
  print_header "Verificaciones"

  # Subvolumen Game Zone
  echo -e "  ${CYAN}→${NC}  Subvolumen /games:"
  sudo btrfs subvolume list /
  if sudo btrfs subvolume list / | grep -q "games"; then
    print_ok "Subvolumen /games encontrado."
  else
    print_err "Subvolumen /games NO encontrado."
  fi

  # Subvolumen
  echo -e "  ${CYAN}→${NC}  Atributo NoCoW en /games:"
  lsattr -d /games 2>/dev/null || print_err "No se pudo leer /games"

  # Snapper configs
  echo ""
  echo -e "  ${CYAN}→${NC}  Configuraciones de Snapper (debe aparecer solo 'root'):"
  sudo snapper list-configs 2>/dev/null

  # Límites con valores esperados al lado
  echo ""
  echo -e "  ${CYAN}→${NC}  Límites de Snapper (valores esperados entre paréntesis):"
  sudo grep -E 'TIMELINE_LIMIT|NUMBER_LIMIT' /etc/snapper/configs/root | while read -r line; do
    key=$(echo "$line" | cut -d= -f1)
    value=$(echo "$line" | cut -d= -f2)
    case $key in
      TIMELINE_LIMIT_DAILY)   expected='"5"'  ;;
      TIMELINE_LIMIT_WEEKLY)  expected='"1"'  ;;
      TIMELINE_LIMIT_HOURLY)  expected='"0"'  ;;
      TIMELINE_LIMIT_MONTHLY) expected='"0"'  ;;
      TIMELINE_LIMIT_YEARLY)  expected='"0"'  ;;
      NUMBER_LIMIT)           expected='"0"'  ;;
      NUMBER_LIMIT_IMPORTANT) expected='"15"' ;;
      *) expected="?" ;;
    esac
    if [ "$value" = "$expected" ]; then
      echo -e "    ${GREEN}✔${NC}  $key=$value (esperado: $expected)"
    else
      echo -e "    ${RED}✘${NC}  $key=$value (esperado: $expected)"
    fi
  done
}

pasos_inicio() {
  print_header "Pasos manuales de inicio"

  echo -e "  Los siguientes pasos ${BOLD}son de inicio${NC} y deben hacerse a mano:\n"

  echo -e "  ${YELLOW}CachyOS Hello${NC}"
  echo "    • Ananicy Cpp: Habilitado"
  echo "    • Cachy Update: Habilitado"
  echo "    • Systemd-oomd: Deshabilitado"
  echo "    • Bpfutune: Deshabilitado"
  echo "    • Bluetooth: Habilitado"
  echo "    • Evaluar mirrors (Colombia)"
  echo "    • Instalar paquetes de gaming (Wine, Proton, drivers)"
  echo ""

  # ── Comandos importantes ──
  print_header "Comandos importantes"
  
  echo -e "  Los siguientes comandos ${BOLD}son de referencia${NC} a futuro:\n"
  echo "    • Listar snapshots:"
  echo "      sudo snapper -c root list"
  echo ""
  echo "    • Borrar snapshots:"
  echo "      sudo snapper -c root delete <número>"
  echo ""
  echo "    • Ver espacio de las snapshots:"
  echo "      sudo bash -c 'btrfs filesystem du -s /.snapshots/*/snapshot'"
  echo ""
  echo -e "  ${YELLOW}⚠${NC}  El campo 'Total' incluye espacio compartido entre snapshots y parece mayor de lo real."
  echo "      Ignorar 'Total'. El espacio real es el 'Set shared' (compartido entre todas)"
  echo "      más el 'Exclusive' de cada snapshot (lo que ocupa de forma única)."
}

# ─────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────

menu() {
  clear
  pasos_inicio
  pause

  clear
  echo ""
  echo -e "${BLUE}${BOLD}  ╔══════════════════════════════════════╗${NC}"
  echo -e "${BLUE}${BOLD}  ║   Setup CachyOS KDE — Post-Install  ║${NC}"
  echo -e "${BLUE}${BOLD}  ╚══════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${BOLD}1.${NC} Fase 1 — Paquetes"
  echo -e "  ${BOLD}2.${NC} Fase 2 — Dotfiles y configuraciones"
  echo -e "  ${BOLD}3.${NC} Fase 3 — Fuentes"
  echo -e "  ${BOLD}4.${NC} Fase 4 — Subvolumen Game Zone"
  echo -e "  ${BOLD}5.${NC} Fase 5 — Snapper"
  echo -e "  ${BOLD}6.${NC} Correr todo de una"
  echo -e "  ${BOLD}7.${NC} Ver pasos manuales pendientes"
  echo -e "  ${BOLD}0.${NC} Salir"
  echo ""
  read -rp "  Elige una opción: " opcion

  case $opcion in
    1) fase_paquetes; pause ;;
    2) fase_dotfiles; pause ;;
    3) fase_fuentes; pause ;;
    4) fase_gamezone; pause ;;
    5) fase_snapper; pause ;;
    6) resumen_manual; pause ;;
    7)
      if confirmar "¿Correr todas las fases?"; then
        fase_paquetes; pause
        fase_dotfiles; pause
        fase_fuentes; pause
        fase_gamezone; pause
        fase_snapper; pause
        resumen_manual
      fi
      ;;
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
