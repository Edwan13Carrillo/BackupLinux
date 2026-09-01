#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  yt-dlp GUI (Versión Windows con Tkinter)
# ─────────────────────────────────────────────

import os
import sys
import re
import json
import shutil
import queue
import platform
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# ── Directorio de trabajo: todo se descarga aquí, sin excepciones ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# ── Evita que se abra una ventanita de consola negra al lanzar yt-dlp/ffmpeg ──
# (solo aplica en Windows; en otros sistemas queda en 0 y no hace nada)
CREATIONFLAGS = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

# ── Formatos yt-dlp ──
VIDEO_FORMATS = {
    "1080p": "bestvideo[height<=1080]+141/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":  "bestvideo[height<=720]+141/bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "Mejor disponible": "bestvideo+141/bestvideo+bestaudio/best",
}
AUDIO_FORMAT = "141/bestaudio"

# ── Navegadores desde los que yt-dlp puede sacar cookies (todos soportados en Windows) ──
BROWSER_LABELS = {
    "Ninguna (sin cookies)": None,
    "Chrome": "chrome",
    "Firefox": "firefox",
    "Edge": "edge",
    "Brave": "brave",
    "Opera": "opera",
    "Vivaldi": "vivaldi",
}

PROGRESS_RE = re.compile(r"(\d{1,3}(?:\.\d)?)%")


# ───────────────────────── Helpers ─────────────────────────

def check_dependencies():
    """Devuelve la lista de binarios que faltan."""
    return [exe for exe in ("yt-dlp", "ffmpeg") if shutil.which(exe) is None]


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


def cookie_args(browser_label):
    """
    Traduce la opción elegida en el combo a los flags de yt-dlp.
    yt-dlp sabe encontrar solito el perfil por defecto de cada navegador
    en Windows, así que no hace falta buscar ni tocar ningún archivo.
    Si el usuario elige "Ninguna", no se manda ningún flag de cookies.
    """
    key = BROWSER_LABELS.get(browser_label)
    if not key:
        return []
    return ["--cookies-from-browser", key]


# ───────────────────────── Constructores de comandos ─────────────────────────

def build_video_cmd(url, quality, out_template, browser_label):
    fmt = VIDEO_FORMATS.get(quality, VIDEO_FORMATS["Mejor disponible"])
    return ["yt-dlp", "-f", fmt, *cookie_args(browser_label),
            "--merge-output-format", "mkv", "-o", out_template, url]


def build_audio_cmd(url, out_template, browser_label):
    return ["yt-dlp", "-f", AUDIO_FORMAT, "-x", "--audio-format", "m4a",
            *cookie_args(browser_label), "--embed-thumbnail", "--add-metadata",
            "-o", out_template, url]


# ───────────────────────── Ejecución / streaming ─────────────────────────

def run_and_stream(cmd, log_queue, prefix=""):
    """Corre un comando, manda cada línea a la cola y parsea el % de progreso."""
    log_queue.put(("log", f"$ {' '.join(cmd)}"))
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True,
            creationflags=CREATIONFLAGS,
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

def analyze_playlist_thread(url, browser_label, log_queue):
    cmd = ["yt-dlp", "-J", "--flat-playlist", *cookie_args(browser_label), url]
    log_queue.put(("status", "Analizando la playlist..."))
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180,
            creationflags=CREATIONFLAGS,
        )
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


def download_single_thread(option, url, quality, browser_label, log_queue):
    out_template = os.path.join(SCRIPT_DIR, "%(title)s.%(ext)s")

    if option == 1:
        cmd = build_video_cmd(url, quality, out_template, browser_label)
        msg = "Descargando video y fusionando con FFmpeg..."
    elif option == 2:
        cmd = build_audio_cmd(url, out_template, browser_label)
        msg = "Extrayendo audio (prioridad: formato 141, AAC 256kbps)..."
    else:
        log_queue.put(("error", "Opción inválida."))
        return

    log_queue.put(("status", msg))
    rc = run_and_stream(cmd, log_queue)

    if rc == 0:
        log_queue.put(("done", True, SCRIPT_DIR))
    else:
        extra = (
            "• Si activaste cookies, revisa que el navegador elegido tenga sesión "
            "iniciada en YouTube.\n"
            if browser_label != "Ninguna (sin cookies)" else ""
        )
        log_queue.put(("error",
            "yt-dlp terminó con error. Revisa el registro.\n\n"
            "Verifica que:\n"
            "• La URL sea correcta.\n"
            f"{extra}"
        ))


def download_playlist_thread(option, quality, playlist_title, selected_entries, keep_numbering, browser_label, log_queue):
    folder = sanitize_filename(playlist_title)
    full_dir = os.path.join(SCRIPT_DIR, folder)
    os.makedirs(full_dir, exist_ok=True)

    padding = 2 if option == 3 else 3
    total = len(selected_entries)
    overall_ok = True

    for idx, entry in enumerate(selected_entries, start=1):
        index_str = str(idx).zfill(padding)
        title = sanitize_filename(entry.get("title", f"item_{idx}"))
        filename = f"{index_str} - {title}" if keep_numbering else title
        out_template = os.path.join(full_dir, f"{filename}.%(ext)s")
        video_url = resolve_entry_url(entry)
        prefix = f"[{idx}/{total}] "

        log_queue.put(("status", f"{prefix}{entry.get('title', '')}"))
        log_queue.put(("progress", 0))

        if not video_url:
            log_queue.put(("log", f"⚠ {prefix}sin URL resoluble, me la salto."))
            overall_ok = False
            continue

        if option == 3:
            cmd = build_video_cmd(video_url, quality, out_template, browser_label)
        else:
            cmd = build_audio_cmd(video_url, out_template, browser_label)

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
        (2, "🎵 Música individual de YouTube"),
        (3, "📂 Playlist de Video de YouTube"),
        (4, "🎶 Playlist de Música de YouTube"),
    ]

    def __init__(self, root):
        self.root = root
        self.log_queue = queue.Queue()
        self.busy = False
        self._pending_opt = None
        self._pending_quality = None
        self._pending_title = None

        self._build_ui()
        self._poll_queue()

    # ── UI ──
    def _build_ui(self):
        self.root.title("yt-dlp GUI 🎧 — Edición Windows")
        self.root.geometry("620x700")
        self.root.minsize(560, 620)

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

        self.number_playlist_var = tk.BooleanVar(value=True)
        self.number_playlist_check = ttk.Checkbutton(
            main, text="Conservar numeración de la playlist",
            variable=self.number_playlist_var,
        )

        # ── Cookies opcionales: nada de búsquedas automáticas, el usuario elige ──
        ttk.Label(main, text="Cookies del navegador (opcional, para videos privados/con edad):").pack(anchor="w")
        self.browser_var = tk.StringVar(value="Ninguna (sin cookies)")
        ttk.Combobox(
            main, textvariable=self.browser_var, state="readonly",
            values=list(BROWSER_LABELS.keys()),
        ).pack(fill="x", pady=(0, 10))

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
        if opt in (3, 4):
            self.number_playlist_check.pack(anchor="w", pady=(0, 10), before=self.action_btn)
        else:
            self.number_playlist_check.pack_forget()
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

        opt = self.option_var.get()
        quality = self.quality_var.get()
        browser_label = self.browser_var.get()

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
                args=(url, browser_label, self.log_queue),
                daemon=True,
            ).start()
        else:
            self.status_var.set("Descargando...")
            self.progress.config(mode="determinate")
            self.progress["value"] = 0
            threading.Thread(
                target=download_single_thread,
                args=(opt, url, quality, browser_label, self.log_queue),
                daemon=True,
            ).start()

    def _on_playlist_confirm(self, selected_entries):
        self._set_busy(True)
        self.status_var.set(f"Descargando {len(selected_entries)} elementos...")
        self.progress.config(mode="determinate", value=0)
        threading.Thread(
            target=download_playlist_thread,
            args=(self._pending_opt, self._pending_quality, self._pending_title,
                  selected_entries, self.number_playlist_var.get(), self.browser_var.get(),
                  self.log_queue),
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

    root.deiconify()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
