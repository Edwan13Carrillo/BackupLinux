# BackupLinux 🐧

> Mi respaldo personal de **CachyOS** — con dos sabores, **KDE Plasma** o **Niri + Noctalia** — para cuando el sistema explota y hay que volver a armar todo sin querer llorar.

---

## ¿Qué hay aquí?

| Carpeta | Contenido |
|---|---|
| `setup.sh` | El jefe. Arma todo: paquetes, dotfiles, fuentes, subvolumen de juegos, Snapper, red/firewall y más |
| `linux/common/` | Dotfiles compartidos por los dos perfiles: Alacritty, Fastfetch, fuentes (Fredoka, Okami, Earth Theory), cursores Bibata, tema de arranque Plymouth (Starlord) |
| `linux/plasma/` | Dotfiles exclusivos de KDE Plasma: temas Aurorae y look-and-feel, iconos Tela, Haruna, esquema de color, `kdedefaults`, etc. |
| `linux/niri/` | Dotfiles exclusivos de Niri + Noctalia: config de Niri, Noctalia, matugen, Quickshell, tema de SDDM, scripts de mpv, etc. |
| `linux/scripts/yt-dlp/` | Script para descargar videos/audio con yt-dlp |
| `linux/scripts/organizar/` | Scripts en Python para organizar ASMR, música, anime y PDFs |
| `gaming/notes/` | Configs y parámetros de Steam para distintos juegos |
| `gaming/mc_skins/` | Skins de Minecraft |
| `assets/wallpapers/` | Fondos de pantalla |
| `assets/icons/` | Iconos, incluyendo los personalizados (ej. el del launcher de Noctalia) |
| `docs/` | Guía completa de reinstalación (PDF) + notas y extras |

---

## Fase 0 — Instalación de CachyOS

Antes de correr `setup.sh` necesitás el sistema ya instalado así. Es clave para que `limine` arranque bien — no te lo saltes ni cambies el orden.

**Tabla de particiones:** GPT

**Partición EFI**
- Tamaño: 4092 MiB
- Sistema de archivos: FAT32
- Punto de montaje: `/boot`
- Flag: `boot`

**Partición raíz**
- Tamaño: resto del disco
- Sistema de archivos: Btrfs
- Punto de montaje: `/`

**Contraseñas:** una distinta para el usuario y otra para root. No las repitas.

> 📄 La guía completa (post-instalación, temas de KDE, snapshots, etc.) está en `docs/`.

---

## Perfiles: Plasma o Niri + Noctalia

Lo primero que pide `setup.sh` al correrlo es elegir un perfil:

1. **KDE Plasma**
2. **Niri + Noctalia**

Los paquetes y dotfiles de `linux/common/` se instalan siempre, sin importar el perfil. El resto (`linux/plasma/` o `linux/niri/`) depende de cuál elijas. Se puede correr el script de nuevo para elegir el otro perfil — no queda "pegado" a la primera elección.

---

## Reinstalación rápida

```bash
git clone https://github.com/Edwan13Carrillo/BackupLinux.git
cd BackupLinux
chmod +x setup.sh
./setup.sh
```

El script tiene un menú interactivo: puedes instalar todo de una o ir eligiendo qué configurar.

> 📄 Ver `docs/` para la guía completa de reinstalación.

---

## Scripts destacados

### 🎬 `linux/scripts/yt-dlp/ytdlp.sh`
Descarga videos o audio desde YouTube y otras plataformas. Sin drama.

### 🗂️ `linux/scripts/organizar/`
Sistema de organización automática de archivos. Dejás los archivos que quieras ordenar en la carpeta `orden/` y el `main.py` se encarga del resto. Organiza:
- 🎵 Música
- 🎧 ASMR
- 📚 PDFs (Mangas, manhwas específicamente)

---

## Notas

- Los archivos sensibles (contraseñas, tokens) **nunca** se suben aquí. Obvio.
- Este repo es personal, así que si algo no tiene sentido para ti, tiene todo el sentido para mí.
- Fuentes de anime, listas para Hayase, y soluciones a problemas típicos (KDE Connect, Bluetooth) están aparte en [`docs/notas.md`](docs/notas.md), para no inflar este README con cosas que no son parte del setup en sí.