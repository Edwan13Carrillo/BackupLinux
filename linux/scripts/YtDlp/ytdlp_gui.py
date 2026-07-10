#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  yt-dlp GUI (Versión Audiófila con Tkinter)
#  Migrado desde Bash + yad
# ─────────────────────────────────────────────

import os
import sys
import re
import json
import shutil
import queue
import threading
import subprocess
import configparser
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# ── Directorio de trabajo: todo se descarga aquí, sin excepciones ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# ── Formatos yt-dlp ──
VIDEO_FORMATS = {
    "1080p": "bestvideo[height<=1080]+141/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":  "bestvideo[height<=720]+141/bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "Mejor disponible": "bestvideo+141/bestvideo+bestaudio/best",
}
AUDIO_FORMAT = "141/bestaudio"
PATREON_FORMAT = "bestvideo+bestaudio/best"

PROGRESS_RE = re.compile(r"(\d{1,3}(?:\.\d)?)%")


# ───────────────────────── Helpers ─────────────────────────

def check_dependencies():
    """Devuelve la lista de binarios que faltan."""
    return [exe for exe in ("yt-dlp", "ffmpeg") if shutil.which(exe) is None]


def is_zen_running():
    """
    Devuelve True si detecta un proceso de Zen Browser corriendo.
    Zen puede llamarse 'zen', 'zen-browser' o 'zen-bin' según cómo esté instalado.
    Usamos pgrep -i para cubrir variantes de mayúsculas/minúsculas.
    """
    try:
        result = subprocess.run(
            ["pgrep", "-i", "-x", "zen"],
            capture_output=True,
        )
        if result.returncode == 0:
            return True
        result2 = subprocess.run(
            ["pgrep", "-i", "zen-browser"],
            capture_output=True,
        )
        return result2.returncode == 0
    except FileNotFoundError:
        # Si pgrep no existe (raro en Linux, pero por si acaso)
        return False


def _has_moz_cookies(profile_dir: Path) -> bool:
    """
    Verifica que cookies.sqlite exista Y que realmente contenga la tabla moz_cookies.
    Abre el archivo en modo inmutable (read-only) para no interferir con el navegador.
    """
    db = profile_dir / "cookies.sqlite"
    if not db.is_file():
        return False
    try:
        # uri=True + immutable=1 → SQLite no intenta escribir ni crear WAL propio
        conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True, timeout=3)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='moz_cookies'"
        )
        found = cur.fetchone() is not None
        conn.close()
        return found
    except Exception:
        return False


def _zen_is_running(profile_dir: Path) -> bool:
    """
    Detecta si Zen Browser tiene el perfil bloqueado (.parentlock existe y está locked).
    Un lock activo significa que el navegador está abierto → peligro de corrupción WAL.
    """
    lock_file = profile_dir / ".parentlock"
    if not lock_file.exists():
        return False
    try:
        import fcntl
        with open(lock_file, "r") as fh:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fh, fcntl.LOCK_UN)
                return False  # Se pudo bloquear → el navegador NO lo tiene
            except OSError:
                return True   # No se pudo bloquear → navegador abierto
    except Exception:
        return False


def _candidates_from_ini(base: Path):
    """
    Lee installs.ini y profiles.ini para obtener los perfiles en orden de prioridad:
    primero el perfil activo real, luego todos los demás.
    """
    result = []

    # installs.ini (Firefox 67+ / Zen): apunta directamente al perfil activo
    installs = base / "installs.ini"
    if installs.is_file():
        cfg = configparser.ConfigParser()
        cfg.read(installs)
        for section in cfg.sections():
            path_val = cfg.get(section, "Default", fallback="")
            if path_val:
                p = (base / path_val) if not Path(path_val).is_absolute() else Path(path_val)
                if p.is_dir() and p not in result:
                    result.append(p)

    # profiles.ini: primero Default=1, después todos los demás
    profiles = base / "profiles.ini"
    if profiles.is_file():
        cfg = configparser.ConfigParser()
        cfg.read(profiles)
        sections = [s for s in cfg.sections() if s.lower().startswith("profile")]
        # Default=1 primero
        for section in sections:
            if cfg.get(section, "Default", fallback="0") == "1":
                path_val = cfg.get(section, "Path", fallback="")
                is_rel  = cfg.get(section, "IsRelative", fallback="1") == "1"
                if path_val:
                    p = (base / path_val) if is_rel else Path(path_val)
                    if p.is_dir() and p not in result:
                        result.append(p)
        # Resto
        for section in sections:
            path_val = cfg.get(section, "Path", fallback="")
            is_rel   = cfg.get(section, "IsRelative", fallback="1") == "1"
            if path_val:
                p = (base / path_val) if is_rel else Path(path_val)
                if p.is_dir() and p not in result:
                    result.append(p)

    return result


def find_zen_profile():
    """
    Busca el perfil de Zen Browser activo con cookies válidas (tabla moz_cookies real).
    Orden de búsqueda: installs.ini → profiles.ini → glob *.Default* → cualquier carpeta.
    Además detecta si el navegador está abierto y corta antes de causar problemas.
    Devuelve (Path_del_perfil, None) si todo bien, o (None, mensaje_error) si hay problema.
    """
    base = Path.home() / ".config" / "zen"
    if not base.is_dir():
        return None, (
            "No encontré ~/.config/zen.\n"
            "¿Tienes Zen Browser instalado en esta máquina?"
        )

    # Candidatos en orden de prioridad
    candidates = _candidates_from_ini(base)

    # Fallback: glob
    glob_dirs = sorted(base.glob("*.Default*"))
    if not glob_dirs:
        glob_dirs = sorted(p for p in base.iterdir() if p.is_dir())
    for p in glob_dirs:
        if p not in candidates:
            candidates.append(p)

    if not candidates:
        return None, (
            "No encontré ninguna carpeta de perfil dentro de ~/.config/zen.\n"
            "Abre Zen y déjalo cargar al menos una vez."
        )

    # Buscar el primero con moz_cookies válido
    for profile in candidates:
        if not _has_moz_cookies(profile):
            continue

        # Perfil válido encontrado — ¿está el navegador abierto?
        if _zen_is_running(profile):
            return None, (
                "Encontré tu perfil de Zen Browser con cookies, pero el navegador "
                "está abierto en este momento.\n\n"
                "⚠ Abrir cookies.sqlite mientras el navegador corre puede corromper "
                "la base de datos (modo WAL de SQLite).\n\n"
                "Cierra Zen completamente y vuelve a intentarlo."
            )

        return profile, None

    # Hay perfiles pero ninguno tiene moz_cookies válido
    any_sqlite = any((p / "cookies.sqlite").is_file() for p in candidates)
    if any_sqlite:
        return None, (
            "Encontré cookies.sqlite en el perfil de Zen, pero la tabla moz_cookies "
            "no existe o no es accesible.\n\n"
            "Esto puede pasar si:\n"
            "• Zen estaba abierto cuando corriste el script (prueba cerrarlo primero).\n"
            "• El perfil encontrado es secundario y no tiene sesión iniciada.\n\n"
            "Cierra Zen completamente, ábrelo de nuevo, inicia sesión en YouTube y "
            "ciérralo antes de usar el script."
        )

    return None, (
        "Encontré la carpeta de Zen Browser, pero ningún perfil tiene cookies.sqlite.\n\n"
        "Abre Zen, inicia sesión en YouTube (y Patreon si aplica) al menos una vez,\n"
        "ciérralo y vuelve a intentarlo."
    )


def sanitize_filename(name):
    if not name:
        return "sin_titulo"
    invalid = '<>:"/\\|?*'
    cleaned = "".join(c for c in name if c not in invalid).strip().rstrip(".")
    return cleaned[:150] if cleaned else "sin_titulo"


def resolve_entry_url(entry):
    """En modo --flat-playlist, 'url' a veces ya es la URL completa, a veces no."""
    u = entry.get("url")
    if isinstance(u, str) and u.startswith("http"):
        return u
    vid = entry.get("id")
    if vid:
        return f"https://www.youtube.com/watch?v={vid}"
    return u or ""


def cookie_args(profile_dir):
    return ["--cookies-from-browser", f"firefox:{profile_dir}"]


# ───────────────────────── Constructores de comandos ─────────────────────────

def build_video_cmd(url, quality, out_template, profile_dir):
    fmt = VIDEO_FORMATS.get(quality, VIDEO_FORMATS["Mejor disponible"])
    return ["yt-dlp", "-f", fmt, *cookie_args(profile_dir),
            "--merge-output-format", "mkv", "-o", out_template, url]


def build_audio_cmd(url, out_template, profile_dir):
    return ["yt-dlp", "-f", AUDIO_FORMAT, "-x", "--audio-format", "m4a",
            *cookie_args(profile_dir), "--embed-thumbnail", "--add-metadata",
            "-o", out_template, url]


def build_patreon_cmd(url, out_template, profile_dir):
    return ["yt-dlp", *cookie_args(profile_dir), "-f", PATREON_FORMAT,
            "--merge-output-format", "mp4", "--embed-thumbnail", "--add-metadata",
            "-o", out_template, url]


# ───────────────────────── Ejecución / streaming ─────────────────────────

def run_and_stream(cmd, log_queue, prefix=""):
    """Corre un comando, manda cada línea a la cola y parsea el % de progreso."""
    log_queue.put(("log", f"$ {' '.join(cmd)}"))
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True,
        )
    except FileNotFoundError:
        log_queue.put(("error", "No encontré el ejecutable 'yt-dlp'. ¿Está en el PATH?"))
        return 1

    for line in process.stdout:
        line = line.rstrip("\n")
        if not line:
            continue
        log_queue.put(("log", f"{prefix}{line}" if prefix else line))
        m = PROGRESS_RE.search(line)
        if m:
            try:
                log_queue.put(("progress", float(m.group(1))))
            except ValueError:
                pass

    process.wait()
    return process.returncode


# ───────────────────────── Hilos de trabajo ─────────────────────────

def analyze_playlist_thread(url, profile_dir, log_queue):
    cmd = ["yt-dlp", "-J", "--flat-playlist", *cookie_args(profile_dir), url]
    log_queue.put(("status", "Analizando la playlist..."))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        log_queue.put(("error", "No encontré el ejecutable 'yt-dlp'. ¿Está en el PATH?"))
        return
    except subprocess.TimeoutExpired:
        log_queue.put(("error", "yt-dlp tardó demasiado analizando la playlist. Intenta de nuevo."))
        return

    if result.returncode != 0:
        detalle = (result.stderr or "").strip()[-800:]
        log_queue.put(("error", f"yt-dlp falló al analizar la playlist:\n\n{detalle}"))
        return

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        log_queue.put(("error", "La respuesta de yt-dlp no se pudo interpretar (JSON inválido)."))
        return

    entries = [e for e in data.get("entries", []) if e]
    if not entries:
        log_queue.put(("error", "La playlist está vacía o no se encontraron videos."))
        return

    playlist_title = data.get("title") or "Playlist"
    log_queue.put(("playlist_ready", playlist_title, entries))


def download_single_thread(option, url, quality, profile_dir, log_queue):
    out_template = os.path.join(SCRIPT_DIR, "%(title)s.%(ext)s")

    if option == 1:
        cmd = build_video_cmd(url, quality, out_template, profile_dir)
        msg = "Descargando video y fusionando con FFmpeg..."
    elif option == 2:
        cmd = build_audio_cmd(url, out_template, profile_dir)
        msg = "Extrayendo audio (prioridad: formato 141, AAC 256kbps)..."
    elif option == 5:
        cmd = build_patreon_cmd(url, out_template, profile_dir)
        msg = "Descargando contenido de Patreon..."
    else:
        log_queue.put(("error", "Opción inválida."))
        return

    log_queue.put(("status", msg))
    rc = run_and_stream(cmd, log_queue)

    if rc == 0:
        log_queue.put(("done", True, SCRIPT_DIR))
    else:
        log_queue.put(("error",
            "yt-dlp terminó con error. Revisa el registro.\n\n"
            "Verifica que:\n"
            "• La URL sea correcta.\n"
            "• Tengas sesión iniciada en Zen Browser.\n"
            "• Zen esté CERRADO (cookies.sqlite se bloquea si el navegador está abierto)."
        ))


def download_playlist_thread(option, quality, playlist_title, selected_entries, profile_dir, log_queue):
    folder = sanitize_filename(playlist_title)
    full_dir = os.path.join(SCRIPT_DIR, folder)
    os.makedirs(full_dir, exist_ok=True)

    padding = 2 if option == 3 else 3
    total = len(selected_entries)
    overall_ok = True

    for idx, entry in enumerate(selected_entries, start=1):
        index_str = str(idx).zfill(padding)
        title = sanitize_filename(entry.get("title", f"item_{idx}"))
        out_template = os.path.join(full_dir, f"{index_str} - {title}.%(ext)s")
        video_url = resolve_entry_url(entry)
        prefix = f"[{idx}/{total}] "

        log_queue.put(("status", f"{prefix}{entry.get('title', '')}"))
        log_queue.put(("progress", 0))

        if not video_url:
            log_queue.put(("log", f"⚠ {prefix}sin URL resoluble, me la salto."))
            overall_ok = False
            continue

        if option == 3:
            cmd = build_video_cmd(video_url, quality, out_template, profile_dir)
        else:
            cmd = build_audio_cmd(video_url, out_template, profile_dir)

        rc = run_and_stream(cmd, log_queue, prefix=prefix)
        if rc != 0:
            overall_ok = False
            log_queue.put(("log", f"⚠ Falló: {entry.get('title', '(sin título)')}"))

    log_queue.put(("done", overall_ok, full_dir))


# ───────────────────────── Ventana de selección de playlist ─────────────────────────

class PlaylistSelectorWindow(tk.Toplevel):
    def __init__(self, parent, playlist_title, entries, on_confirm):
        super().__init__(parent)
        self.title(f"Selecciona pistas — {playlist_title}")
        self.geometry("520x560")
        self.minsize(420, 400)
        self.entries = entries
        self.on_confirm = on_confirm
        self.vars = []

        ttk.Label(
            self, text=f"📂 {playlist_title}  ({len(entries)} elementos)",
            font=("", 11, "bold"), wraplength=480,
        ).pack(pady=(12, 6), padx=10, anchor="w")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10)
        ttk.Button(btn_frame, text="Marcar todo", command=self.select_all).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="Desmarcar todo", command=self.deselect_all).pack(side="left")

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.list_frame = ttk.Frame(canvas)

        self.list_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for entry in entries:
            var = tk.BooleanVar(value=True)
            title = entry.get("title") or "(sin título)"
            ttk.Checkbutton(self.list_frame, text=title, variable=var).pack(anchor="w", pady=1)
            self.vars.append(var)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=10, pady=10)
        ttk.Button(footer, text="Cancelar", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="Descargar seleccionados", command=self.confirm).pack(side="right")

    def select_all(self):
        for v in self.vars:
            v.set(True)

    def deselect_all(self):
        for v in self.vars:
            v.set(False)

    def confirm(self):
        selected = [e for e, v in zip(self.entries, self.vars) if v.get()]
        if not selected:
            messagebox.showwarning(
                "Sin selección", "No marcaste nada, ¿pa' qué le diste a descargar? 😅"
            )
            return
        self.destroy()
        self.on_confirm(selected)


# ───────────────────────── App principal ─────────────────────────

class App:
    OPTIONS = [
        (1, "🎥 Video individual de YouTube"),
        (2, "🎵 Música / ASMR individual de YouTube"),
        (3, "📂 Playlist de Video de YouTube"),
        (4, "🎶 Playlist de Música / ASMR de YouTube"),
        (5, "💰 Video de Patreon"),
    ]

    def __init__(self, root, profile_dir):
        self.root = root
        self.profile_dir = profile_dir
        self.log_queue = queue.Queue()
        self.busy = False
        self._pending_opt = None
        self._pending_quality = None
        self._pending_title = None

        self._build_ui()
        self._poll_queue()

    # ── UI ──
    def _build_ui(self):
        self.root.title("yt-dlp GUI 🎧 — Edición Tkinter")
        self.root.geometry("620x680")
        self.root.minsize(560, 600)

        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Gestor de Descargas yt-dlp", font=("", 14, "bold")).pack(anchor="w")
        ttk.Label(
            main, text=f"Todo se guarda en: {SCRIPT_DIR}", foreground="#666"
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(main, text="URL:").pack(anchor="w")
        self.url_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.url_var).pack(fill="x", pady=(0, 10))

        ttk.Label(main, text="¿Qué quieres hacer?").pack(anchor="w")
        self.option_var = tk.IntVar(value=1)
        opt_frame = ttk.Frame(main)
        opt_frame.pack(fill="x", pady=(0, 10))
        for val, text in self.OPTIONS:
            ttk.Radiobutton(
                opt_frame, text=text, value=val, variable=self.option_var,
                command=self._on_option_change,
            ).pack(anchor="w")

        self.quality_frame = ttk.Frame(main)
        ttk.Label(self.quality_frame, text="Calidad máxima de video:").pack(anchor="w")
        self.quality_var = tk.StringVar(value="Mejor disponible")
        ttk.Combobox(
            self.quality_frame, textvariable=self.quality_var, state="readonly",
            values=list(VIDEO_FORMATS.keys()),
        ).pack(fill="x")
        self.quality_frame.pack(fill="x", pady=(0, 10))

        self.action_btn = ttk.Button(main, text="Descargar", command=self._on_action)
        self.action_btn.pack(fill="x", pady=(0, 10))

        self.status_var = tk.StringVar(value="Listo para la acción.")
        ttk.Label(main, textvariable=self.status_var, foreground="#444").pack(anchor="w")
        self.progress = ttk.Progressbar(main, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(5, 10))

        ttk.Label(main, text="Registro:").pack(anchor="w")
        log_frame = ttk.Frame(main)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=12, state="disabled",
                                 font=("Consolas", 9), wrap="word")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        self._on_option_change()

    def _on_option_change(self):
        opt = self.option_var.get()
        if opt in (1, 3):
            self.quality_frame.pack(fill="x", pady=(0, 10), before=self.action_btn)
        else:
            self.quality_frame.pack_forget()
        self.action_btn.config(text="Analizar Playlist" if opt in (3, 4) else "Descargar")

    def _log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_busy(self, busy):
        self.busy = busy
        self.action_btn.config(state="disabled" if busy else "normal")

    # ── Acciones ──
    def _on_action(self):
        if self.busy:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(
                "Falta la URL", "La URL no se pone sola, capo. Pégala y dale otra vez."
            )
            return

        # ── Zen Browser debe estar cerrado antes de tocar cookies.sqlite ──
        # Si Zen está abierto, el archivo está en modo WAL (transacciones pendientes).
        # yt-dlp copiaría un SQLite inconsistente → error "no such table: moz_cookies".
        # Peor aún: cuando Zen reabre y detecta el WAL corrupto, hace rollback
        # y puede limpiar cookies recientes. Bloqueamos AQUÍ para evitar eso.
        if is_zen_running():
            messagebox.showerror(
                "Zen Browser está abierto",
                "Cierra Zen Browser antes de descargar.\n\n"
                "¿Por qué? yt-dlp necesita leer cookies.sqlite, pero mientras Zen\n"
                "está corriendo ese archivo tiene transacciones pendientes (modo WAL).\n\n"
                "Si se lee en ese estado:\n"
                "  • yt-dlp falla con 'no such table: moz_cookies'\n"
                "  • Al reabrir Zen puede detectar inconsistencia y hacer rollback,\n"
                "    borrándote cookies recientes.\n\n"
                "Cierra Zen, dale OK aquí e intenta de nuevo.",
            )
            return

        opt = self.option_var.get()
        quality = self.quality_var.get()

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self._set_busy(True)
        self.progress.stop()

        if opt in (3, 4):
            self.status_var.set("Analizando la playlist, dame un toque...")
            self.progress.config(mode="indeterminate")
            self.progress.start(10)
            self._pending_opt = opt
            self._pending_quality = quality
            threading.Thread(
                target=analyze_playlist_thread,
                args=(url, self.profile_dir, self.log_queue),
                daemon=True,
            ).start()
        else:
            self.status_var.set("Descargando...")
            self.progress.config(mode="determinate")
            self.progress["value"] = 0
            threading.Thread(
                target=download_single_thread,
                args=(opt, url, quality, self.profile_dir, self.log_queue),
                daemon=True,
            ).start()

    def _on_playlist_confirm(self, selected_entries):
        self._set_busy(True)
        self.status_var.set(f"Descargando {len(selected_entries)} elementos...")
        self.progress.config(mode="determinate", value=0)
        threading.Thread(
            target=download_playlist_thread,
            args=(self._pending_opt, self._pending_quality, self._pending_title,
                  selected_entries, self.profile_dir, self.log_queue),
            daemon=True,
        ).start()

    # ── Cola de eventos (hilo -> UI) ──
    def _poll_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                kind = msg[0]

                if kind == "log":
                    self._log(msg[1])

                elif kind == "status":
                    self.status_var.set(msg[1])

                elif kind == "progress":
                    if str(self.progress["mode"]) != "determinate":
                        self.progress.stop()
                        self.progress.config(mode="determinate")
                    self.progress["value"] = msg[1]

                elif kind == "playlist_ready":
                    _, title, entries = msg
                    self.progress.stop()
                    self.progress.config(mode="determinate", value=0)
                    self._set_busy(False)
                    self._pending_title = title
                    self.status_var.set(
                        f"Playlist analizada: {len(entries)} elementos. Elige cuáles quieres."
                    )
                    PlaylistSelectorWindow(self.root, title, entries, self._on_playlist_confirm)

                elif kind == "error":
                    self.progress.stop()
                    self.progress.config(mode="determinate", value=0)
                    self._set_busy(False)
                    self.status_var.set("Algo petó. Revisa el registro.")
                    self._log(f"✘ ERROR: {msg[1]}")
                    messagebox.showerror("Error", msg[1])

                elif kind == "done":
                    ok, location = msg[1], msg[2]
                    self.progress.stop()
                    self.progress.config(mode="determinate", value=100 if ok else 0)
                    self._set_busy(False)
                    if ok:
                        self.status_var.set("¡Listazo! Descarga completa.")
                        self._log(f"✔ Terminado. Guardado en: {location}")
                        messagebox.showinfo(
                            "Éxito", f"Descarga completa.\nGuardado en:\n{location}"
                        )
                    else:
                        self.status_var.set("Terminó con errores. Revisa el registro.")
                        messagebox.showwarning(
                            "Con errores",
                            "Algunas descargas fallaron. Revisa el registro para más detalles.",
                        )
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


# ───────────────────────── Main ─────────────────────────

def main():
    root = tk.Tk()
    root.withdraw()

    missing = check_dependencies()
    if missing:
        messagebox.showerror(
            "Faltan dependencias",
            f"Te falta(n): {', '.join(missing)}.\nInstálalos antes de continuar.",
        )
        root.destroy()
        sys.exit(1)

    profile_dir, err = find_zen_profile()
    if err:
        messagebox.showerror("Sin cookies de Zen Browser", err)
        root.destroy()
        sys.exit(1)

    root.deiconify()
    App(root, str(profile_dir))
    root.mainloop()


if __name__ == "__main__":
    main()
