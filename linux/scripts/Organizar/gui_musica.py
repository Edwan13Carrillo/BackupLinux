"""
gui_musica.py - Interfaz grafica inicial para el modulo Musica.
"""

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from utils import CARPETA_TRABAJO, clasificar_archivo, detectar_numero, formatear_numero

try:
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_DISPONIBLE = True
except ImportError:
    MUTAGEN_DISPONIBLE = False


EXTENSIONES_MUSICA = (".flac", ".m4a")
_CHARS_INVALIDOS = re.compile(r'[\\/:*?"<>|]')
_ESPACIOS_MULTIPLES = re.compile(r" {2,}")


def leer_titulo(ruta: str) -> str | None:
    if not MUTAGEN_DISPONIBLE:
        return None
    try:
        if ruta.lower().endswith(".flac"):
            titulo = FLAC(ruta).get("title")
        else:
            titulo = (MP4(ruta).tags or {}).get("\xa9nam")
        return titulo[0].strip() if titulo else None
    except Exception:
        return None


def sanitizar_titulo(titulo: str) -> str:
    titulo = titulo.replace('"', "'").replace("/", "-").replace("\\", "-")
    titulo = _CHARS_INVALIDOS.sub("", titulo)
    return _ESPACIOS_MULTIPLES.sub(" ", titulo).strip() or "Sin título"


def construir_nombre_final(numero: int, titulo: str, extension: str) -> str:
    return f"{formatear_numero(numero)} - {titulo}{extension}"


def _extraer_titulo_del_nombre(nombre: str) -> str | None:
    partes = os.path.splitext(nombre)[0].split(" - ", 1)
    return partes[1].strip() if len(partes) == 2 else None


def _quitar_prefijo_numero(nombre_sin_ext: str) -> str:
    titulo = re.sub(r"^\s*\d+\s*[-.,]?\s*", "", nombre_sin_ext).strip()
    return titulo or nombre_sin_ext.strip() or "Sin título"


def _ruta_disponible(ruta: str) -> str:
    if not os.path.exists(ruta):
        return ruta
    carpeta, nombre = os.path.split(ruta)
    base, extension = os.path.splitext(nombre)
    indice = 1
    while os.path.exists(candidata := os.path.join(carpeta, f"{base} ({indice}){extension}")):
        indice += 1
    return candidata


def escanear_carpeta() -> dict:
    try:
        todos = sorted(
            nombre for nombre in os.listdir(CARPETA_TRABAJO)
            if os.path.isfile(os.path.join(CARPETA_TRABAJO, nombre))
        )
    except PermissionError:
        return {}
    musica = [nombre for nombre in todos if os.path.splitext(nombre)[1].lower() in EXTENSIONES_MUSICA]
    return {"musica": musica}


def obtener_canciones() -> list[dict]:
    canciones = []
    for nombre in escanear_carpeta().get("musica", []):
        nombre_sin_ext, extension = os.path.splitext(nombre)
        titulo = _extraer_titulo_del_nombre(nombre) or leer_titulo(os.path.join(CARPETA_TRABAJO, nombre))
        canciones.append({
            "archivo": nombre,
            "numero": detectar_numero(nombre_sin_ext),
            "titulo": titulo or _quitar_prefijo_numero(nombre_sin_ext),
            "extension": extension.lower(),
            "estado": clasificar_archivo(nombre_sin_ext),
            "ruta": os.path.join(CARPETA_TRABAJO, nombre),
        })
    return sorted(canciones, key=lambda cancion: (cancion["numero"] is None, cancion["numero"] or 0, cancion["archivo"].lower()))


def crear_cambios_ordenar(titulos_manual: dict[str, str] | None = None) -> tuple[list[dict], list[str]]:
    titulos_manual = titulos_manual or {}
    cambios, advertencias = [], []
    for nombre in escanear_carpeta().get("musica", []):
        nombre_sin_ext, extension = os.path.splitext(nombre)
        numero, estado = detectar_numero(nombre_sin_ext), clasificar_archivo(nombre_sin_ext)
        if estado == "sin_numero" or numero is None:
            cambios.append({"original": nombre, "nuevo": nombre, "estado": "sin_numero"})
            advertencias.append(f"Sin número detectado: {nombre}")
            continue
        titulo = leer_titulo(os.path.join(CARPETA_TRABAJO, nombre)) or titulos_manual.get(nombre) or _extraer_titulo_del_nombre(nombre)
        titulo = titulo or _quitar_prefijo_numero(nombre_sin_ext)
        cambios.append({"original": nombre, "nuevo": construir_nombre_final(numero, sanitizar_titulo(titulo), extension.lower()), "estado": estado})
    return cambios, advertencias


def crear_cambios_reordenar(archivos_ordenados: list[str], titulos: dict[str, str] | None = None) -> list[dict]:
    titulos = titulos or {}
    cambios = []
    for numero, nombre in enumerate(archivos_ordenados, 1):
        extension = os.path.splitext(nombre)[1].lower()
        titulo = titulos.get(nombre) or _extraer_titulo_del_nombre(nombre) or leer_titulo(os.path.join(CARPETA_TRABAJO, nombre))
        titulo = titulo or _quitar_prefijo_numero(os.path.splitext(nombre)[0])
        cambios.append({"original": nombre, "nuevo": construir_nombre_final(numero, sanitizar_titulo(titulo), extension), "estado": "formato_incorrecto"})
    return cambios


def _renombrar_seguro(cambios: list[dict]) -> dict:
    aplicables = [cambio for cambio in cambios if cambio.get("original") != cambio.get("nuevo") and cambio.get("estado") not in ("sin_numero", "dudoso")]
    errores, aplicados, temporales = [], [], []
    originales, destinos = {cambio["original"] for cambio in aplicables}, {}
    for cambio in aplicables:
        nuevo = cambio["nuevo"]
        if nuevo in destinos:
            errores.append({"archivo": cambio["original"], "error": f"Destino duplicado en la operación: {nuevo}"})
        destinos[nuevo] = cambio["original"]
        if os.path.exists(os.path.join(CARPETA_TRABAJO, nuevo)) and nuevo not in originales:
            errores.append({"archivo": cambio["original"], "error": f"Ya existe: {nuevo}"})
        if os.path.exists(os.path.join(CARPETA_TRABAJO, cambio["original"] + ".__tmp__")):
            errores.append({"archivo": cambio["original"], "error": f"Ya existe temporal pendiente: {cambio['original']}.__tmp__"})
    if errores:
        return {"aplicados": aplicados, "errores": errores}
    for cambio in aplicables:
        try:
            os.rename(os.path.join(CARPETA_TRABAJO, cambio["original"]), os.path.join(CARPETA_TRABAJO, cambio["original"] + ".__tmp__"))
            temporales.append(cambio)
        except OSError as error:
            errores.append({"archivo": cambio["original"], "error": str(error)})
    for cambio in temporales:
        temporal = os.path.join(CARPETA_TRABAJO, cambio["original"] + ".__tmp__")
        nueva = os.path.join(CARPETA_TRABAJO, cambio["nuevo"])
        if os.path.exists(nueva):
            errores.append({"archivo": cambio["original"], "error": f"Ya existe: {cambio['nuevo']}"})
            continue
        try:
            os.rename(temporal, nueva)
            aplicados.append({"original": cambio["original"], "nuevo": cambio["nuevo"]})
        except OSError as error:
            errores.append({"archivo": cambio["original"], "error": str(error)})
    return {"aplicados": aplicados, "errores": errores}


def aplicar_cambios(cambios: list[dict]) -> dict:
    return _renombrar_seguro(cambios)


def agregar_archivos(origenes: list[str]) -> dict:
    if not os.path.isdir(CARPETA_TRABAJO):
        raise FileNotFoundError(f"No se encontró la carpeta '{CARPETA_TRABAJO}'.")
    copiados, omitidos = [], []
    for origen in origenes:
        if os.path.splitext(origen)[1].lower() not in EXTENSIONES_MUSICA:
            omitidos.append({"archivo": origen, "error": "Extensión no soportada"})
            continue
        try:
            destino = _ruta_disponible(os.path.join(CARPETA_TRABAJO, os.path.basename(origen)))
            shutil.copy2(origen, destino)
            copiados.append(os.path.basename(destino))
        except OSError as error:
            omitidos.append({"archivo": origen, "error": str(error)})
    return {"copiados": copiados, "omitidos": omitidos}


def eliminar_archivos(nombres: list[str]) -> dict:
    eliminados, errores = [], []
    for nombre in nombres:
        if os.path.splitext(nombre)[1].lower() not in EXTENSIONES_MUSICA:
            errores.append({"archivo": nombre, "error": "Extensión no soportada"})
            continue
        try:
            os.remove(os.path.join(CARPETA_TRABAJO, nombre))
            eliminados.append(nombre)
        except OSError as error:
            errores.append({"archivo": nombre, "error": str(error)})
    return {"eliminados": eliminados, "errores": errores}


class MusicaFrame(ttk.Frame):
    def __init__(self, master, volver_callback=None):
        super().__init__(master)
        self.volver_callback = volver_callback
        self.canciones = {}

        self._configurar_estilo()
        self._construir_ui()
        self.refrescar()

    def _configurar_estilo(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("", 10, "bold"))
        style.configure("Toolbar.TButton", padding=(10, 6))

    def _construir_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.grid(row=0, column=0, sticky="nsew")

        encabezado = ttk.Frame(self, padding=(12, 10, 12, 6))
        encabezado.grid(row=0, column=0, sticky="ew")
        encabezado.columnconfigure(0, weight=1)

        self.resumen_var = tk.StringVar(value="Cargando biblioteca...")
        ttk.Label(encabezado, textvariable=self.resumen_var, font=("", 12, "bold")).grid(row=0, column=0, sticky="w")
        if self.volver_callback:
            ttk.Button(encabezado, text="Inicio", style="Toolbar.TButton", command=self.volver_callback).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(encabezado, text="Actualizar", style="Toolbar.TButton", command=self.refrescar).grid(row=0, column=2, padx=(8, 0))

        cuerpo = ttk.Frame(self, padding=(12, 0, 12, 0))
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        columnas = ("numero", "titulo", "extension", "estado", "archivo")
        self.tabla = ttk.Treeview(cuerpo, columns=columnas, show="headings", selectmode="extended")
        self.tabla.heading("numero", text="#")
        self.tabla.heading("titulo", text="Titulo")
        self.tabla.heading("extension", text="Ext.")
        self.tabla.heading("estado", text="Estado")
        self.tabla.heading("archivo", text="Archivo actual")
        self.tabla.column("numero", width=70, anchor="center", stretch=False)
        self.tabla.column("titulo", width=270)
        self.tabla.column("extension", width=70, anchor="center", stretch=False)
        self.tabla.column("estado", width=150, anchor="center", stretch=False)
        self.tabla.column("archivo", width=360)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(cuerpo, orient="vertical", command=self.tabla.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=scroll.set)

        barra = ttk.Frame(self, padding=(12, 8, 12, 12))
        barra.grid(row=2, column=0, sticky="ew")
        for i in range(12):
            barra.columnconfigure(i, weight=0)
        barra.columnconfigure(11, weight=1)

        ttk.Button(barra, text="Subir", style="Toolbar.TButton", command=lambda: self.mover(-1)).grid(row=0, column=0, padx=6)
        ttk.Button(barra, text="Bajar", style="Toolbar.TButton", command=lambda: self.mover(1)).grid(row=0, column=1, padx=6)
        ttk.Button(barra, text="Aplicar orden", style="Toolbar.TButton", command=self.aplicar_orden).grid(row=0, column=2, padx=6)
        ttk.Separator(barra, orient="vertical").grid(row=0, column=3, sticky="ns", padx=8)
        ttk.Button(barra, text="Ordenar nombres", style="Toolbar.TButton", command=self.ordenar_nombres).grid(row=0, column=4, padx=6)

        self.estado_var = tk.StringVar(value="")
        ttk.Label(barra, textvariable=self.estado_var, anchor="e").grid(row=0, column=11, sticky="ew")

    def refrescar(self):
        if not os.path.isdir(CARPETA_TRABAJO):
            self.resumen_var.set(f"No existe la carpeta: {CARPETA_TRABAJO}")
            self.estado_var.set("Crea la carpeta de trabajo antes de continuar.")
            return

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        canciones = obtener_canciones()
        self.canciones = {c["archivo"]: c for c in canciones}
        for c in canciones:
            numero = "" if c["numero"] is None else str(c["numero"]).zfill(3)
            self.tabla.insert("", "end", iid=c["archivo"], values=(
                numero,
                c["titulo"],
                c["extension"],
                c["estado"],
                c["archivo"],
            ))

        organizadas = sum(1 for c in canciones if c["estado"] == "correcto")
        sin_numero = sum(1 for c in canciones if c["estado"] == "sin_numero")
        self.resumen_var.set(
            f"{len(canciones)} canciones en {CARPETA_TRABAJO} | "
            f"{organizadas} organizadas | {sin_numero} sin numero"
        )
        self.estado_var.set("Biblioteca actualizada.")

    def seleccion(self) -> list[str]:
        return list(self.tabla.selection())

    def agregar(self):
        tipos = [("Musica", " ".join(f"*{ext}" for ext in EXTENSIONES_MUSICA)), ("Todos", "*.*")]
        rutas = filedialog.askopenfilenames(title="Agregar canciones", filetypes=tipos)
        if not rutas:
            return
        resultado = agregar_archivos(list(rutas))
        self.refrescar()
        mensaje = f"Archivos copiados: {len(resultado['copiados'])}"
        if resultado["omitidos"]:
            mensaje += f"\nOmitidos: {len(resultado['omitidos'])}"
        messagebox.showinfo("Agregar canciones", mensaje)

    def eliminar_seleccion(self):
        seleccion = self.seleccion()
        if not seleccion:
            messagebox.showwarning("Eliminar", "Selecciona una o mas canciones.")
            return

        if not messagebox.askyesno("Eliminar canciones", f"Eliminar {len(seleccion)} archivo(s) de la carpeta?"):
            return

        resultado = eliminar_archivos(seleccion)
        self.refrescar()
        mensaje = f"Eliminados: {len(resultado['eliminados'])}"
        if resultado["errores"]:
            mensaje += f"\nErrores: {len(resultado['errores'])}"
        messagebox.showinfo("Eliminar canciones", mensaje)

    def mover(self, direccion: int):
        seleccion = self.seleccion()
        if not seleccion:
            return

        items = list(self.tabla.get_children())
        seleccion_set = set(seleccion)
        orden = items if direccion < 0 else list(reversed(items))

        for item in orden:
            if item not in seleccion_set:
                continue
            indice = self.tabla.index(item)
            nuevo_indice = indice + direccion
            if 0 <= nuevo_indice < len(items):
                self.tabla.move(item, "", nuevo_indice)

    def aplicar_orden(self):
        archivos = list(self.tabla.get_children())
        titulos = {archivo: self.canciones.get(archivo, {}).get("titulo", "") for archivo in archivos}
        cambios = crear_cambios_reordenar(archivos, titulos)
        cambios_reales = [c for c in cambios if c["original"] != c["nuevo"]]
        if not cambios_reales:
            messagebox.showinfo("Aplicar orden", "No hay cambios que aplicar.")
            return

        if not messagebox.askyesno("Aplicar orden", f"Renumerar {len(cambios_reales)} archivo(s)?"):
            return

        resultado = aplicar_cambios(cambios)
        self._mostrar_resultado("Aplicar orden", resultado)
        self.refrescar()

    def ordenar_nombres(self):
        cambios, advertencias = crear_cambios_ordenar()
        cambios_reales = [c for c in cambios if c["original"] != c["nuevo"]]
        if not cambios_reales:
            messagebox.showinfo("Ordenar nombres", "No hay cambios que aplicar.")
            return

        mensaje = f"Renombrar {len(cambios_reales)} archivo(s)?"
        if advertencias:
            mensaje += f"\nAdvertencias: {len(advertencias)}"
        if not messagebox.askyesno("Ordenar nombres", mensaje):
            return

        resultado = aplicar_cambios(cambios)
        self._mostrar_resultado("Ordenar nombres", resultado)
        self.refrescar()

    def _mostrar_resultado(self, titulo: str, resultado: dict):
        aplicados = len(resultado.get("aplicados", []))
        errores = resultado.get("errores", [])
        mensaje = f"Renombrados: {aplicados}"
        if errores:
            detalle = "\n".join(f"- {e['archivo']}: {e['error']}" for e in errores[:5])
            mensaje += f"\nErrores: {len(errores)}\n{detalle}"
            messagebox.showwarning(titulo, mensaje)
        else:
            messagebox.showinfo(titulo, mensaje)


class MusicaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador multimedia - Musica")
        self.geometry("980x620")
        self.minsize(780, 460)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        MusicaFrame(self)


def main():
    app = MusicaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
