"""
gui_asmr.py - Interfaz grafica inicial para el modulo ASMR.
"""

import os
import re
import shutil
import tkinter as tk
import unicodedata
from tkinter import filedialog, messagebox, ttk

from utils import CARPETA_TRABAJO, clasificar_archivo, detectar_numero, formatear_numero

try:
    from mutagen.mp4 import MP4
    MUTAGEN_DISPONIBLE = True
except ImportError:
    MUTAGEN_DISPONIBLE = False


EXTENSIONES_ASMR = (".m4a",)


def leer_metadatos_m4a(ruta: str) -> dict:
    resultado = {"artista": None, "titulo": None}
    if not MUTAGEN_DISPONIBLE:
        return resultado
    try:
        tags = MP4(ruta).tags or {}
        artista = tags.get("\xa9ART")
        titulo = tags.get("\xa9nam")
        if artista:
            resultado["artista"] = artista[0].strip()
        if titulo:
            resultado["titulo"] = titulo[0].strip()
    except Exception:
        pass
    return resultado


def sanitizar_componente_nombre(valor: str) -> str:
    valor = unicodedata.normalize("NFKC", valor).strip()
    valor = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", valor)
    valor = re.sub(r"\s+", " ", valor).strip()
    return valor.rstrip(". ") or "Sin nombre"


def construir_nombre_final(numero: int, artista: str, titulo: str) -> str:
    return f"{formatear_numero(numero)} - {sanitizar_componente_nombre(artista)} - {sanitizar_componente_nombre(titulo)}"


def _extraer_artista_titulo_del_nombre(nombre: str) -> tuple[str | None, str | None]:
    partes = os.path.splitext(nombre)[0].split(" - ", 2)
    if len(partes) == 3 and partes[1].strip() and partes[2].strip():
        return partes[1].strip(), partes[2].strip()
    return None, None


def _listar_archivos_asmr() -> list[str]:
    try:
        return sorted(
            nombre for nombre in os.listdir(CARPETA_TRABAJO)
            if os.path.isfile(os.path.join(CARPETA_TRABAJO, nombre))
            and os.path.splitext(nombre)[1].lower() in EXTENSIONES_ASMR
        )
    except PermissionError:
        return []


def _quitar_prefijo_numero(nombre_sin_ext: str) -> str:
    titulo = re.sub(r"^\s*\d+\s*[-.,]?\s*", "", nombre_sin_ext).strip()
    return titulo or nombre_sin_ext.strip() or "Sin titulo"


def _ruta_disponible(ruta: str) -> str:
    if not os.path.exists(ruta):
        return ruta
    carpeta, nombre = os.path.split(ruta)
    base, extension = os.path.splitext(nombre)
    indice = 1
    while os.path.exists(candidata := os.path.join(carpeta, f"{base} ({indice}){extension}")):
        indice += 1
    return candidata


def obtener_asmr() -> list[dict]:
    items = []
    for nombre in _listar_archivos_asmr():
        nombre_sin_ext, extension = os.path.splitext(nombre)
        numero = detectar_numero(nombre_sin_ext)
        artista, titulo = _extraer_artista_titulo_del_nombre(nombre)
        if not artista or not titulo:
            metadatos = leer_metadatos_m4a(os.path.join(CARPETA_TRABAJO, nombre))
            artista = artista or metadatos["artista"]
            titulo = titulo or metadatos["titulo"]
        if not artista or not titulo:
            artista = artista or "Sin artista"
            titulo = titulo or _quitar_prefijo_numero(nombre_sin_ext)
        items.append({
            "archivo": nombre, "numero": numero, "artista": artista, "titulo": titulo,
            "extension": extension.lower(), "estado": clasificar_archivo(nombre_sin_ext),
            "ruta": os.path.join(CARPETA_TRABAJO, nombre),
        })
    return sorted(items, key=lambda item: (item["numero"] is None, item["numero"] or 0, item["archivo"].lower()))


def crear_cambios_reformatear(meta_manual: dict[str, dict] | None = None) -> tuple[list[dict], list[str]]:
    meta_manual = meta_manual or {}
    cambios, advertencias = [], []
    for nombre in _listar_archivos_asmr():
        nombre_sin_ext = os.path.splitext(nombre)[0]
        estado, numero = clasificar_archivo(nombre_sin_ext), detectar_numero(nombre_sin_ext)
        if estado == "sin_numero" or numero is None:
            cambios.append({"original": nombre, "nuevo": nombre, "estado": "sin_numero"})
            advertencias.append(f"Sin número detectado: {nombre}")
            continue
        metadatos = leer_metadatos_m4a(os.path.join(CARPETA_TRABAJO, nombre))
        artista = meta_manual.get(nombre, {}).get("artista") or metadatos["artista"]
        titulo = meta_manual.get(nombre, {}).get("titulo") or metadatos["titulo"]
        artista_nombre, titulo_nombre = _extraer_artista_titulo_del_nombre(nombre)
        artista, titulo = artista or artista_nombre, titulo or titulo_nombre
        if not artista or not titulo:
            cambios.append({"original": nombre, "nuevo": nombre, "estado": "dudoso"})
            advertencias.append(f"Faltan artista o título: {nombre}")
            continue
        cambios.append({"original": nombre, "nuevo": construir_nombre_final(numero, artista, titulo) + ".m4a", "estado": estado})
    return cambios, advertencias


def crear_cambios_reordenar(archivos_ordenados: list[str], meta: dict[str, dict] | None = None) -> list[dict]:
    meta = meta or {}
    cambios = []
    for numero, nombre in enumerate(archivos_ordenados, 1):
        datos = meta.get(nombre, {})
        artista, titulo = datos.get("artista"), datos.get("titulo")
        artista_nombre, titulo_nombre = _extraer_artista_titulo_del_nombre(nombre)
        artista, titulo = artista or artista_nombre, titulo or titulo_nombre
        if not artista or not titulo:
            metadatos = leer_metadatos_m4a(os.path.join(CARPETA_TRABAJO, nombre))
            artista = artista or metadatos["artista"] or "Sin artista"
            titulo = titulo or metadatos["titulo"] or _quitar_prefijo_numero(os.path.splitext(nombre)[0])
        cambios.append({"original": nombre, "nuevo": construir_nombre_final(numero, artista, titulo) + ".m4a", "estado": "formato_incorrecto"})
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
        temporal, nueva = os.path.join(CARPETA_TRABAJO, cambio["original"] + ".__tmp__"), os.path.join(CARPETA_TRABAJO, cambio["nuevo"])
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
        if os.path.splitext(origen)[1].lower() not in EXTENSIONES_ASMR:
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
        if os.path.splitext(nombre)[1].lower() not in EXTENSIONES_ASMR:
            errores.append({"archivo": nombre, "error": "Extensión no soportada"})
            continue
        try:
            os.remove(os.path.join(CARPETA_TRABAJO, nombre))
            eliminados.append(nombre)
        except OSError as error:
            errores.append({"archivo": nombre, "error": str(error)})
    return {"eliminados": eliminados, "errores": errores}


class AsmrFrame(ttk.Frame):
    def __init__(self, master, volver_callback=None):
        super().__init__(master)
        self.volver_callback = volver_callback
        self.items = {}

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

        self.resumen_var = tk.StringVar(value="Cargando biblioteca ASMR...")
        ttk.Label(encabezado, textvariable=self.resumen_var, font=("", 12, "bold")).grid(row=0, column=0, sticky="w")
        if self.volver_callback:
            ttk.Button(encabezado, text="Inicio", style="Toolbar.TButton", command=self.volver_callback).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(encabezado, text="Actualizar", style="Toolbar.TButton", command=self.refrescar).grid(row=0, column=2, padx=(8, 0))

        cuerpo = ttk.Frame(self, padding=(12, 0, 12, 0))
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        columnas = ("numero", "artista", "titulo", "estado", "archivo")
        self.tabla = ttk.Treeview(cuerpo, columns=columnas, show="headings", selectmode="extended")
        self.tabla.heading("numero", text="#")
        self.tabla.heading("artista", text="Artista")
        self.tabla.heading("titulo", text="Titulo")
        self.tabla.heading("estado", text="Estado")
        self.tabla.heading("archivo", text="Archivo actual")
        self.tabla.column("numero", width=70, anchor="center", stretch=False)
        self.tabla.column("artista", width=210)
        self.tabla.column("titulo", width=280)
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

        ttk.Button(barra, text="Ordenar ASMR", style="Toolbar.TButton", command=self.ordenar_asmr).grid(row=0, column=0, padx=(0, 6))
        ttk.Separator(barra, orient="vertical").grid(row=0, column=1, sticky="ns", padx=8)
        ttk.Button(barra, text="Subir", style="Toolbar.TButton", command=lambda: self.mover(-1)).grid(row=0, column=2, padx=6)
        ttk.Button(barra, text="Bajar", style="Toolbar.TButton", command=lambda: self.mover(1)).grid(row=0, column=3, padx=6)
        ttk.Button(barra, text="Aplicar orden", style="Toolbar.TButton", command=self.aplicar_orden).grid(row=0, column=4, padx=6)
        ttk.Separator(barra, orient="vertical").grid(row=0, column=5, sticky="ns", padx=8)
        ttk.Button(barra, text="Reformatear nombres", style="Toolbar.TButton", command=self.reformatear_nombres).grid(row=0, column=6, padx=6)

        self.estado_var = tk.StringVar(value="")
        ttk.Label(barra, textvariable=self.estado_var, anchor="e").grid(row=0, column=11, sticky="ew")

    def refrescar(self):
        if not os.path.isdir(CARPETA_TRABAJO):
            self.resumen_var.set(f"No existe la carpeta: {CARPETA_TRABAJO}")
            self.estado_var.set("Crea la carpeta de trabajo antes de continuar.")
            return

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        items = obtener_asmr()
        self.items = {item["archivo"]: item for item in items}
        for item in items:
            numero = "" if item["numero"] is None else str(item["numero"]).zfill(3)
            self.tabla.insert("", "end", iid=item["archivo"], values=(
                numero,
                item["artista"],
                item["titulo"],
                item["estado"],
                item["archivo"],
            ))

        organizados = sum(1 for item in items if item["estado"] == "correcto")
        sin_numero = sum(1 for item in items if item["estado"] == "sin_numero")
        self.resumen_var.set(
            f"{len(items)} archivos ASMR en {CARPETA_TRABAJO} | "
            f"{organizados} organizados | {sin_numero} sin numero"
        )
        self.estado_var.set("Biblioteca actualizada.")

    def seleccion(self) -> list[str]:
        return list(self.tabla.selection())

    def agregar(self):
        tipos = [("ASMR", " ".join(f"*{ext}" for ext in EXTENSIONES_ASMR)), ("Todos", "*.*")]
        rutas = filedialog.askopenfilenames(title="Agregar ASMR", filetypes=tipos)
        if not rutas:
            return
        resultado = agregar_archivos(list(rutas))
        self.refrescar()
        mensaje = f"Archivos copiados: {len(resultado['copiados'])}"
        if resultado["omitidos"]:
            mensaje += f"\nOmitidos: {len(resultado['omitidos'])}"
        messagebox.showinfo("Agregar ASMR", mensaje)

    def eliminar_seleccion(self):
        seleccion = self.seleccion()
        if not seleccion:
            messagebox.showwarning("Eliminar", "Selecciona uno o mas archivos.")
            return

        if not messagebox.askyesno("Eliminar ASMR", f"Eliminar {len(seleccion)} archivo(s) de la carpeta?"):
            return

        resultado = eliminar_archivos(seleccion)
        self.refrescar()
        mensaje = f"Eliminados: {len(resultado['eliminados'])}"
        if resultado["errores"]:
            mensaje += f"\nErrores: {len(resultado['errores'])}"
        messagebox.showinfo("Eliminar ASMR", mensaje)

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

    def ordenar_asmr(self):
        grupos = {}
        for archivo in self.tabla.get_children():
            artista = self.items.get(archivo, {}).get("artista", "")
            grupos.setdefault(artista, []).append(archivo)

        for _artista, archivos in sorted(grupos.items(), key=lambda grupo: (-len(grupo[1]), grupo[0].casefold())):
            for archivo in archivos:
                self.tabla.move(archivo, "", "end")

    def aplicar_orden(self):
        archivos = list(self.tabla.get_children())
        meta = {
            archivo: {
                "artista": self.items.get(archivo, {}).get("artista", ""),
                "titulo": self.items.get(archivo, {}).get("titulo", ""),
            }
            for archivo in archivos
        }
        cambios = crear_cambios_reordenar(archivos, meta)
        cambios_reales = [c for c in cambios if c["original"] != c["nuevo"]]
        if not cambios_reales:
            messagebox.showinfo("Aplicar orden", "No hay cambios que aplicar.")
            return

        if not messagebox.askyesno("Aplicar orden", f"Renumerar {len(cambios_reales)} archivo(s)?"):
            return

        resultado = aplicar_cambios(cambios)
        self._mostrar_resultado("Aplicar orden", resultado)
        self.refrescar()

    def reformatear_nombres(self):
        cambios, advertencias = crear_cambios_reformatear()
        cambios_reales = [c for c in cambios if c["original"] != c["nuevo"]]
        if not cambios_reales:
            messagebox.showinfo("Reformatear nombres", "No hay cambios que aplicar.")
            return

        mensaje = f"Renombrar {len(cambios_reales)} archivo(s)?"
        if advertencias:
            mensaje += f"\nAdvertencias: {len(advertencias)}"
        if not messagebox.askyesno("Reformatear nombres", mensaje):
            return

        resultado = aplicar_cambios(cambios)
        self._mostrar_resultado("Reformatear nombres", resultado)
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


class AsmrApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador multimedia - ASMR")
        self.geometry("980x620")
        self.minsize(780, 460)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        AsmrFrame(self)


def main():
    app = AsmrApp()
    app.mainloop()


if __name__ == "__main__":
    main()
