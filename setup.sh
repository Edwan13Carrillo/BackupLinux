#!/bin/bash
#
# ============================================================
#   setup.sh — Automatización post-instalación CachyOS KDE
# ============================================================
#
# Requiere bash (usa arrays, [[ ]], process substitution).
# No es POSIX sh a propósito: este script solo corre en CachyOS,
# donde bash siempre está disponible.

set -Eeuo pipefail

# ─────────────────────────────────────────
# Colores
# ─────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─────────────────────────────────────────
# Utilidades de salida
# ─────────────────────────────────────────
# Nota: se usa printf en vez de echo -e. Los códigos de color van con
# %b (interpreta los \033 de las variables) y el texto del usuario con
# %s (nunca se interpreta como formato, aunque contenga backslashes).

print_header() {
  printf '\n'
  printf '%b\n' "${BLUE}${BOLD}══════════════════════════════════════${NC}"
  printf '%b\n' "${BLUE}${BOLD}  $1${NC}"
  printf '%b\n' "${BLUE}${BOLD}══════════════════════════════════════${NC}"
  printf '\n'
}

print_ok()   { printf '  %b✔%b  %s\n' "$GREEN" "$NC" "$1"; }
print_warn() { printf '  %b⚠%b  %s\n' "$YELLOW" "$NC" "$1"; }
print_info() { printf '  %b→%b  %s\n' "$CYAN" "$NC" "$1"; }
print_err()  { printf '  %b✘%b  %s\n' "$RED" "$NC" "$1"; }

pause() {
  printf '\n'
  read -rp "  Presiona Enter para continuar..." _
  printf '\n'
}

# Ojo: acepta exactamente "s"/"S" para sí, cualquier otra cosa es "no".
# Es intencional — simple y sin ambigüedad.
confirmar() {
  local resp
  read -rp "  $1 [s/N]: " resp
  [[ "$resp" =~ ^[sS]$ ]]
}

# Reporta en qué línea y comando reventó el script (gracias a set -e).
on_error() {
  local exit_code=$?
  printf '\n  %b✘ Error (código %s) en línea %s: %s%b\n\n' \
    "${RED}${BOLD}" "$exit_code" "$LINENO" "$BASH_COMMAND" "$NC"
}
trap on_error ERR

# ─────────────────────────────────────────
# Rutas base (relativas al repo)
# ─────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/linux/configs"
FONTS_DIR="$SCRIPT_DIR/linux/fonts"

# ─────────────────────────────────────────
# Logging — guarda toda la sesión en un archivo, sin dejar de
# mostrarla en pantalla.
# ─────────────────────────────────────────

LOG_DIR="$HOME/.local/state/setup-cachyos"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/setup-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1
print_info "Esta sesión se está guardando en: $LOG_FILE"

# ─────────────────────────────────────────
# Fase 1 — Paquetes
# ─────────────────────────────────────────

fase_paquetes() {
  print_header "Fase 1 — Paquetes"

  print_info "Actualizando sistema..."
  sudo pacman -Syu --noconfirm

  print_info "Instalando paquetes desde repositorio oficial..."
  sudo pacman -S --noconfirm --needed \
    discord \
    telegram-desktop \
    zen-browser-bin \
    libreoffice-still \
    libreoffice-still-es \
    git \
    fastfetch \
    yt-dlp \
    qbittorrent \
    fuse2 \
    mkvtoolnix-gui \
    prismlauncher \
    base-devel \
    yay \
    flatpak \
    rsync

  print_ok "Paquetes base instalados."

  print_info "Instalando Visual Studio Code (AUR)..."
  yay -S --noconfirm visual-studio-code-bin
  print_ok "VSCode instalado."

  print_info "Configurando el remoto de Flathub..."
  flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  print_ok "Flathub configurado."

  print_info "Instalando Sober/Roblox (Flatpak)..."
  flatpak install -y flathub org.vinegarhq.Sober
  print_ok "Sober instalado."

}

# ─────────────────────────────────────────
# Fase 2 — Dotfiles y configuraciones
# ─────────────────────────────────────────
#
# copiar_config: copia una carpeta o archivo del repo hacia el sistema.
#
#   $1 descripcion  → texto para los mensajes
#   $2 origen       → ruta dentro del repo
#   $3 destino      → carpeta destino (no incluye el nombre final)
#   $4 modo         → file   : copia un solo archivo
#                     subvol : la carpeta origen se copia completa,
#                              con su propio nombre, dentro de destino.
#                              Se sincroniza EXACTO (borra lo que sobre
#                              en destino/<nombre>). Úsalo para carpetas
#                              que el repo controla por completo
#                              (temas, iconos, cursores, plymouth...).
#                     merge  : el CONTENIDO de origen se mezcla directo
#                              dentro de destino, sin borrar nada que ya
#                              esté ahí. Úsalo para configs de apps que
#                              también escriben su propio estado
#                              (fastfetch, alacritty, haruna, kdedefaults).
#   $5 usar_sudo    → "sudo" si la copia requiere privilegios, vacío si no

copiar_config() {
  local descripcion="$1" origen="$2" destino="$3" modo="$4" usar_sudo="$5"
  local -a runner=()
  [ -n "$usar_sudo" ] && runner=(sudo)

  if [ ! -e "$origen" ]; then
    print_err "No se encontró: $origen"
    return 1
  fi

  print_info "Copiando $descripcion..."

  local ok=1
  case "$modo" in
    file)
      "${runner[@]}" mkdir -p "$destino" || ok=0
      if [ "$ok" = "1" ]; then
        "${runner[@]}" cp -f "$origen" "$destino/" || ok=0
      fi
      ;;
    subvol)
      local nombre destino_final
      nombre="$(basename "$origen")"
      destino_final="$destino/$nombre"
      "${runner[@]}" mkdir -p "$destino" || ok=0
      if [ "$ok" = "1" ]; then
        if [ "$RSYNC_OK" = "1" ]; then
          "${runner[@]}" rsync -a --delete "$origen/" "$destino_final/" || ok=0
        else
          "${runner[@]}" rm -rf "$destino_final"
          "${runner[@]}" cp -r "$origen" "$destino/" || ok=0
        fi
      fi
      ;;
    merge)
      "${runner[@]}" mkdir -p "$destino" || ok=0
      if [ "$ok" = "1" ]; then
        if [ "$RSYNC_OK" = "1" ]; then
          "${runner[@]}" rsync -a "$origen/" "$destino/" || ok=0
        else
          "${runner[@]}" cp -r "$origen/." "$destino/" || ok=0
        fi
      fi
      ;;
    *)
      print_err "Modo desconocido '$modo' para $descripcion"
      return 1
      ;;
  esac

  if [ "$ok" = "1" ]; then
    print_ok "$descripcion copiado."
  else
    print_err "Falló la copia de: $descripcion"
    return 1
  fi
}

fase_dotfiles() {
  print_header "Fase 2 — Dotfiles y configuraciones"

  if command -v rsync >/dev/null 2>&1; then
    RSYNC_OK=1
  else
    RSYNC_OK=0
    print_warn "rsync no está instalado; se usará 'cp -r' como respaldo (sin limpiar archivos obsoletos)."
    print_warn "Instálalo con: sudo pacman -S rsync"
  fi

  # descripcion|origen|destino|modo|sudo
  local -a dotfiles=(
    "Decoraciones de ventanas (Aurorae) Layan|$CONFIGS_DIR/local/Layan|$HOME/.local/share/aurorae/themes|subvol|"
    "Esquema de colores ArchDark|$CONFIGS_DIR/local/ArchDark.colors|$HOME/.local/share/color-schemes|file|"
    "Temas de Plasma (desktoptheme)|$CONFIGS_DIR/local/desktoptheme|$HOME/.local/share/plasma|subvol|"
    "Look and feel (Kuro)|$CONFIGS_DIR/local/a2n.kuro|$HOME/.local/share/plasma/look-and-feel|subvol|"
    "Pantalla de arranque (pixels)|$CONFIGS_DIR/pixels|/usr/share/plymouth/themes|subvol|sudo"
    "Iconos Tela|$CONFIGS_DIR/Tela|$HOME/.local/share/icons|subvol|"
    "Cursores Bibata-Modern-Ice|$CONFIGS_DIR/local/Bibata-Modern-Ice|$HOME/.icons|subvol|"
    "Tema global (cachyosTG)|$CONFIGS_DIR/local/cachyosTG|$HOME/.local/share/plasma/look-and-feel|subvol|"
    "Configuración de KDE (kdedefaults)|$CONFIGS_DIR/kdedefaults|$HOME/.config/kdedefaults|merge|"
    "Fastfetch|$CONFIGS_DIR/fastfetch|$HOME/.config/fastfetch|merge|"
    "Alacritty|$CONFIGS_DIR/alacritty|$HOME/.config/alacritty|merge|"
    "Haruna|$CONFIGS_DIR/haruna|$HOME/.config/haruna|merge|"
    "Widget Clear Clock|$CONFIGS_DIR/org.kde.plasma.clearclock|$HOME/.local/share/plasma/plasmoids|subvol|"
  )

  local entry descripcion origen destino modo usar_sudo
  for entry in "${dotfiles[@]}"; do
    IFS='|' read -r descripcion origen destino modo usar_sudo <<< "$entry"
    copiar_config "$descripcion" "$origen" "$destino" "$modo" "$usar_sudo" || true
  done

  # ── Acciones posteriores a la copia ──

  if [ -d "$CONFIGS_DIR/pixels" ]; then
    print_info "Activando pantalla de arranque (pixels)..."
    if sudo plymouth-set-default-theme -R pixels; then
      print_ok "Plymouth configurado con el tema pixels."
    else
      print_err "No se pudo activar Plymouth. Hazlo manualmente: sudo plymouth-set-default-theme -R pixels"
    fi
  fi

  if [ -d "$CONFIGS_DIR/local/cachyosTG" ]; then
    print_warn "Ve a: Ajustes del sistema > Aspecto > Tema global y selecciona 'CachyTG' para aplicarlo."
  fi

  if [ -d "$CONFIGS_DIR/kdedefaults" ]; then
    print_warn "Cierra sesión y vuelve a entrar para que KDE aplique todos los temas."
  fi

  if [ -d "$CONFIGS_DIR/org.kde.plasma.clearclock" ]; then
    print_warn "Agrega el widget Clear Clock al escritorio, reemplaza su config.qml y luego refresca Plasma:"
    print_warn "kquitapp6 plasmashell && kstart5 plasmashell"
  fi
}

# ─────────────────────────────────────────
# Fase 3 — Fuentes
# ─────────────────────────────────────────

fase_fuentes() {
  print_header "Fase 3 — Fuentes"

  shopt -s nullglob
  local fuentes=("$FONTS_DIR"/*.ttf "$FONTS_DIR"/*.otf)
  shopt -u nullglob

  if [ -d "$FONTS_DIR" ] && [ ${#fuentes[@]} -gt 0 ]; then
    print_info "Instalando fuentes..."
    mkdir -p ~/.local/share/fonts

    cp "${fuentes[@]}" ~/.local/share/fonts/

    fc-cache -f > /dev/null 2>&1

    print_ok "Fuentes instaladas: ${#fuentes[@]} archivo(s)."
    print_warn "Aplica las fuentes en: Ajustes del sistema > Fuentes (Fredoka Medium 12pt / 10pt)."
  else
    print_err "No se encontraron archivos .ttf ni .otf en $FONTS_DIR"
  fi
}

# ─────────────────────────────────────────
# Fase 4 — Subvolumen Game Zone (Btrfs)
# ─────────────────────────────────────────

fase_gamezone() {
  print_header "Fase 4 — Subvolumen Game Zone (Btrfs)"

  if ! command -v btrfs >/dev/null 2>&1; then
    print_err "El comando 'btrfs' no está disponible. Esta fase requiere btrfs-progs."
    return 1
  fi

  if [ "$(findmnt -no FSTYPE /)" != "btrfs" ]; then
    print_err "La raíz (/) no está en Btrfs. Esta fase no aplica en este sistema."
    return 1
  fi

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

# ─────────────────────────────────────────
# Fase 5 — Snapper (Snapshots)
# ─────────────────────────────────────────

fase_snapper() {
  print_header "Fase 5 — Snapper (Snapshots)"

  print_info "Instalando snapper..."
  sudo pacman -S --noconfirm --needed snapper cachyos-snapper-support btrfs-assistant

  if sudo snapper list-configs 2>/dev/null | grep -q '^root '; then
    print_warn "La configuración 'root' de Snapper ya existe. Se omite la creación."
  else
    print_info "Creando configuración root..."
    sudo snapper -c root create-config /
  fi

  print_info "Ajustando límites en /etc/snapper/configs/root..."
  sudo sed -i \
    -e 's/^TIMELINE_LIMIT_HOURLY=.*/TIMELINE_LIMIT_HOURLY="0"/' \
    -e 's/^TIMELINE_LIMIT_DAILY=.*/TIMELINE_LIMIT_DAILY="5"/' \
    -e 's/^TIMELINE_LIMIT_WEEKLY=.*/TIMELINE_LIMIT_WEEKLY="1"/' \
    -e 's/^TIMELINE_LIMIT_MONTHLY=.*/TIMELINE_LIMIT_MONTHLY="0"/' \
    -e 's/^TIMELINE_LIMIT_YEARLY=.*/TIMELINE_LIMIT_YEARLY="0"/' \
    -e 's/^NUMBER_LIMIT=.*/NUMBER_LIMIT="0"/' \
    -e 's/^NUMBER_LIMIT_IMPORTANT=.*/NUMBER_LIMIT_IMPORTANT="15"/' \
    /etc/snapper/configs/root

  print_ok "Snapper configurado."
  print_warn "Cuando el sistema esté completamente listo, crea la snapshot maestra:"
  print_warn "snapper -c root create --description \"Sistema base configurado\""
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
  echo "    • Prism Launcher: Seleccionar Java 17"
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

  printf '  %b→%b  Atributo NoCoW en /games:\n' "$CYAN" "$NC"
  lsattr -d /games 2>/dev/null || print_err "No se pudo leer /games"

  printf '\n'
  printf '  %b→%b  Configuraciones de Snapper (debe aparecer solo '"'"'root'"'"'):\n' "$CYAN" "$NC"
  sudo snapper list-configs 2>/dev/null || true

  printf '\n'
  printf '  %b→%b  Límites de Snapper (valores esperados entre paréntesis):\n' "$CYAN" "$NC"
  sudo grep -E 'TIMELINE_LIMIT|NUMBER_LIMIT' /etc/snapper/configs/root | while read -r line; do
    key=$(echo "$line" | cut -d= -f1)
    value=$(echo "$line" | cut -d= -f2)
    case "$key" in
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
      printf '    %b✔%b  %s=%s (esperado: %s)\n' "$GREEN" "$NC" "$key" "$value" "$expected"
    else
      printf '    %b✘%b  %s=%s (esperado: %s)\n' "$RED" "$NC" "$key" "$value" "$expected"
    fi
  done || true
}

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
  echo "      Ignorar 'Total'. El espacio real es el 'Set shared' (compartido entre todas)"
  echo "      más el 'Exclusive' de cada snapshot (lo que ocupa de forma única)."
}

# ─────────────────────────────────────────
# Menú principal
# ─────────────────────────────────────────

menu() {
  while true; do
    clear
    pasos_inicio
    pause

    clear
    printf '\n'
    printf '%b\n' "${BLUE}${BOLD}  ╔══════════════════════════════════════╗${NC}"
    printf '%b\n' "${BLUE}${BOLD}  ║   Setup CachyOS KDE — Post-Install  ║${NC}"
    printf '%b\n' "${BLUE}${BOLD}  ╚══════════════════════════════════════╝${NC}"
    printf '\n'
    printf '  %b1.%b Fase 1 — Paquetes\n' "$BOLD" "$NC"
    printf '  %b2.%b Fase 2 — Dotfiles y configuraciones\n' "$BOLD" "$NC"
    printf '  %b3.%b Fase 3 — Fuentes\n' "$BOLD" "$NC"
    printf '  %b4.%b Fase 4 — Subvolumen Game Zone\n' "$BOLD" "$NC"
    printf '  %b5.%b Fase 5 — Snapper\n' "$BOLD" "$NC"
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
      1) fase_paquetes; pause ;;
      2) fase_dotfiles; pause ;;
      3) fase_fuentes; pause ;;
      4) fase_gamezone; pause ;;
      5) fase_snapper; pause ;;
      6)
        if confirmar "¿Correr todas las fases?"; then
          fase_paquetes; pause
          fase_dotfiles; pause
          fase_fuentes; pause
          fase_gamezone; pause
          fase_snapper; pause
          resumen_manual
        else
          print_info "Cancelado."
        fi
        ;;
      7) resumen_manual; pause ;;
      0) printf '\n'; printf '  %b¡Hasta luego!%b\n\n' "$GREEN" "$NC"; exit 0 ;;
      *) print_err "Opción no válida." ;;
    esac
  done
}

# ─────────────────────────────────────────
# Verificación inicial
# ─────────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
  print_err "No corras el script como root directamente. Usa tu usuario normal."
  exit 1
fi

if ! sudo -v; then
  print_err "No se pudo obtener privilegios de sudo."
  exit 1
fi

menu
