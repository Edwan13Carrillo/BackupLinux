"""
gui_bl_pdf.py - Interfaz grafica inicial para el modulo BL PDF.
"""

import os
import re
import shutil
import tkinter as tk
import unicodedata
from tkinter import filedialog, messagebox, simpledialog, ttk

from utils import CARPETA_TRABAJO


SEP = "·"
EXTENSIONES_BL_PDF = (".pdf",)
_RE_ESPECIAL = re.compile(r"\b(especial(?:es)?)(?![a-zA-Z])", re.IGNORECASE)
_RE_EXTRA = re.compile(r"\b(extra(?:s)?)(?![a-zA-Z])", re.IGNORECASE)
_RE_FIN = re.compile(r"\b(fin)(?![a-zA-Z])", re.IGNORECASE)
_PALABRAS_SOSPECHOSAS = re.compile(r"\b(bonus|side\s*story|historia\s+alternativa|omake|gaiden|spin[- ]?off)\b", re.IGNORECASE)
_RE_RANGO = re.compile(r"(\d+)\s*[-–]\s*(\d+)")
_RE_NUMERO = re.compile(r"(\d+)")


def normalizar_unicode(texto: str) -> str:
    small_caps = str.maketrans("ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡʏᴢ", "abcdefghijklmnopqrstuvwyz")
    return "".join(
        caracter for caracter in unicodedata.normalize("NFKD", texto.translate(small_caps))
        if unicodedata.category(caracter) != "Mn"
    )


def es_caracter_sospechoso(caracter: str) -> bool:
    if ord(caracter) < 128:
        return False
    categoria = unicodedata.category(caracter)
    return categoria[0] not in ("L", "N", "M", "P", "Z") and not unicodedata.name(caracter, "").startswith(("BOX DRAWINGS", "BLOCK ELEMENT"))


def _razon_unicode_sospechoso(texto: str) -> str | None:
    sospechosos = [caracter for caracter in texto if es_caracter_sospechoso(caracter)]
    if sospechosos:
        return f"Unicode estilizado detectado: '{''.join(dict.fromkeys(sospechosos))[:6]}' — revisar manualmente"
    return None


def analizar_nombre(nombre_sin_ext: str) -> dict:
    nombre_normalizado = normalizar_unicode(nombre_sin_ext)
    if razon := _razon_unicode_sospechoso(nombre_sin_ext):
        return {"tipo": "dudoso", "inicio": None, "fin_num": None, "etiqueta": None, "razon": razon}
    if coincidencia := _PALABRAS_SOSPECHOSAS.search(nombre_normalizado):
        return {"tipo": "dudoso", "inicio": None, "fin_num": None, "etiqueta": None, "razon": f"Contiene palabra de tipo desconocido: '{coincidencia.group()}'"}
    especial, extra, fin = _RE_ESPECIAL.search(nombre_normalizado), _RE_EXTRA.search(nombre_normalizado), _RE_FIN.search(nombre_normalizado)
    if sum(bool(tipo) for tipo in (especial, extra, fin)) > 1:
        return {"tipo": "dudoso", "inicio": None, "fin_num": None, "etiqueta": None, "razon": "Conflicto entre tipos detectados (Especial/Extra/Fin combinados)"}
    etiqueta = especial.group(0).capitalize() if especial else extra.group(0).capitalize() if extra else None
    rango, numero = _RE_RANGO.search(nombre_normalizado), _RE_NUMERO.search(nombre_normalizado)
    if rango:
        inicio, final = int(rango.group(1)), int(rango.group(2))
        if inicio > final:
            return {"tipo": "dudoso", "inicio": None, "fin_num": None, "etiqueta": None, "razon": f"Rango incoherente: {inicio} > {final}"}
        tipo = "especial" if especial else "extra" if extra else "fin" if fin else "normal"
        return {"tipo": tipo, "inicio": inicio, "fin_num": final, "etiqueta": etiqueta if tipo in ("especial", "extra") else None, "razon": ""}
    if numero:
        tipo = "especial" if especial else "extra" if extra else "fin" if fin else "normal"
        return {"tipo": tipo, "inicio": int(numero.group(1)), "fin_num": None, "etiqueta": etiqueta if tipo in ("especial", "extra") else None, "razon": ""}
    if extra or especial or fin:
        tipo = "extra" if extra else "especial" if especial else "fin"
        return {"tipo": tipo, "inicio": None, "fin_num": None, "etiqueta": etiqueta if tipo != "fin" else None, "razon": ""}
    return {"tipo": "dudoso", "inicio": None, "fin_num": None, "etiqueta": None, "razon": "Sin número ni rango detectado"}


def construir_nombre_final(analisis: dict, nombre_obra: str, es_lz: bool) -> str | None:
    inicio, final, tipo, etiqueta = analisis["inicio"], analisis["fin_num"], analisis["tipo"], analisis.get("etiqueta")
    rango = None if inicio is None else f"{inicio:03d}-{final:03d}" if final is not None else f"{inicio:03d}"
    obra = f"{nombre_obra}{' [LZ]' if es_lz else ''}.pdf"
    if tipo == "normal":
        return f"{rango} {SEP} {obra}"
    if tipo == "fin":
        return f"{rango + ' ' if rango else ''}Fin {SEP} {obra}"
    if tipo in ("especial", "extra"):
        return f"{etiqueta or tipo.capitalize()}{' ' + rango if rango else ''} {SEP} {obra}"
    return None


def listar_pdfs_bl() -> list[str]:
    try:
        return sorted(
            nombre for nombre in os.listdir(CARPETA_TRABAJO)
            if os.path.isfile(os.path.join(CARPETA_TRABAJO, nombre))
            and os.path.splitext(nombre)[1].lower() in EXTENSIONES_BL_PDF
        )
    except PermissionError:
        return []


def detectar_simbolos_lote(archivos: list[str] | None = None) -> set[str]:
    return {
        caracter for nombre in (archivos if archivos is not None else listar_pdfs_bl())
        for caracter in os.path.splitext(nombre)[0] if es_caracter_sospechoso(caracter)
    }


def preparar_nombres_limpios(archivos: list[str], limpiar_simbolos: bool = False) -> dict[str, str]:
    simbolos = detectar_simbolos_lote(archivos)
    nombres = {}
    for nombre in archivos:
        limpio = os.path.splitext(nombre)[0]
        if limpiar_simbolos:
            for simbolo in simbolos:
                limpio = limpio.replace(simbolo, "")
            limpio = re.sub(r" {2,}", " ", limpio).strip()
        nombres[nombre] = limpio
    return nombres


def obtener_pdfs_bl(limpiar_simbolos: bool = False) -> list[dict]:
    archivos = listar_pdfs_bl()
    nombres_limpios = preparar_nombres_limpios(archivos, limpiar_simbolos)
    items = []
    for nombre in archivos:
        analisis = analizar_nombre(nombres_limpios[nombre])
        items.append({
            "archivo": nombre, "nombre_limpio": nombres_limpios[nombre], "tipo": analisis["tipo"],
            "inicio": analisis["inicio"], "fin_num": analisis["fin_num"], "etiqueta": analisis.get("etiqueta"),
            "estado": "dudoso" if analisis["tipo"] == "dudoso" else "procesable", "razon": analisis.get("razon", ""),
            "ruta": os.path.join(CARPETA_TRABAJO, nombre),
        })
    return items


def crear_mapa_lz(archivos: list[str], modo: str) -> dict[str, bool]:
    if modo == "todos":
        return {nombre: True for nombre in archivos}
    if modo == "detectar":
        return {nombre: "[LZ]" in nombre.upper() for nombre in archivos}
    return {nombre: False for nombre in archivos}


def crear_cambios_organizar(nombre_obra: str, mapa_lz: dict[str, bool] | None = None, limpiar_simbolos: bool = False, resolucion_dudosos: dict[str, str | None] | None = None) -> tuple[list[dict], list[str]]:
    nombre_obra = nombre_obra.strip()
    if not nombre_obra:
        raise ValueError("El nombre de la obra no puede estar vacío.")
    archivos = listar_pdfs_bl()
    mapa_lz, resolucion_dudosos = mapa_lz or {nombre: False for nombre in archivos}, resolucion_dudosos or {}
    nombres_limpios = preparar_nombres_limpios(archivos, limpiar_simbolos)
    cambios, advertencias = [], []
    for nombre in archivos:
        analisis = analizar_nombre(nombres_limpios[nombre])
        if analisis["tipo"] == "dudoso":
            manual = resolucion_dudosos.get(nombre)
            if manual:
                cambios.append({"original": nombre, "nuevo": manual if manual.lower().endswith(".pdf") else manual + ".pdf", "estado": "formato_incorrecto", "razon": ""})
            else:
                cambios.append({"original": nombre, "nuevo": nombre, "estado": "dudoso", "razon": analisis["razon"]})
                advertencias.append(f"Dudoso: {nombre} ({analisis['razon']})")
            continue
        nuevo = construir_nombre_final(analisis, nombre_obra, mapa_lz.get(nombre, False))
        if nuevo is None:
            advertencias.append(f"No se pudo construir nombre para: {nombre}")
            continue
        cambios.append({"original": nombre, "nuevo": nuevo, "estado": "correcto" if nombre == nuevo else "formato_incorrecto", "razon": ""})
    return cambios, advertencias


def _ruta_disponible(ruta: str) -> str:
    if not os.path.exists(ruta):
        return ruta
    carpeta, nombre = os.path.split(ruta)
    base, extension = os.path.splitext(nombre)
    indice = 1
    while os.path.exists(candidata := os.path.join(carpeta, f"{base} ({indice}){extension}")):
        indice += 1
    return candidata


def _renombrar_seguro(cambios: list[dict]) -> dict:
    aplicables = [cambio for cambio in cambios if cambio.get("estado") == "formato_incorrecto"]
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
        if os.path.splitext(origen)[1].lower() not in EXTENSIONES_BL_PDF:
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
        if os.path.splitext(nombre)[1].lower() not in EXTENSIONES_BL_PDF:
            errores.append({"archivo": nombre, "error": "Extensión no soportada"})
            continue
        try:
            os.remove(os.path.join(CARPETA_TRABAJO, nombre))
            eliminados.append(nombre)
        except OSError as error:
            errores.append({"archivo": nombre, "error": str(error)})
    return {"eliminados": eliminados, "errores": errores}


class BlPdfFrame(ttk.Frame):
    def __init__(self, master, volver_callback=None):
        super().__init__(master)
        self.volver_callback = volver_callback
        self.items = {}
        self.resoluciones_dudosos = {}
        self.limpiar_simbolos_var = tk.BooleanVar(value=False)

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

        self.resumen_var = tk.StringVar(value="Cargando biblioteca BL PDF...")
        ttk.Label(encabezado, textvariable=self.resumen_var, font=("", 12, "bold")).grid(row=0, column=0, sticky="w")
        if self.volver_callback:
            ttk.Button(encabezado, text="Inicio", style="Toolbar.TButton", command=self.volver_callback).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(encabezado, text="Actualizar", style="Toolbar.TButton", command=self.refrescar).grid(row=0, column=2, padx=(8, 0))

        cuerpo = ttk.Frame(self, padding=(12, 0, 12, 0))
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        columnas = ("tipo", "rango", "estado", "razon", "archivo")
        self.tabla = ttk.Treeview(cuerpo, columns=columnas, show="headings", selectmode="extended")
        self.tabla.heading("tipo", text="Tipo")
        self.tabla.heading("rango", text="Rango")
        self.tabla.heading("estado", text="Estado")
        self.tabla.heading("razon", text="Razon")
        self.tabla.heading("archivo", text="Archivo actual")
        self.tabla.column("tipo", width=110, anchor="center", stretch=False)
        self.tabla.column("rango", width=110, anchor="center", stretch=False)
        self.tabla.column("estado", width=130, anchor="center", stretch=False)
        self.tabla.column("razon", width=260)
        self.tabla.column("archivo", width=390)
        self.tabla.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(cuerpo, orient="vertical", command=self.tabla.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=scroll.set)

        barra = ttk.Frame(self, padding=(12, 8, 12, 12))
        barra.grid(row=2, column=0, sticky="ew")
        for i in range(14):
            barra.columnconfigure(i, weight=0)
        barra.columnconfigure(13, weight=1)

        ttk.Checkbutton(
            barra,
            text="Limpiar símbolos",
            variable=self.limpiar_simbolos_var,
            command=self.refrescar,
        ).grid(row=0, column=0, padx=6)
        ttk.Button(barra, text="Resolver dudoso", style="Toolbar.TButton", command=self.resolver_dudoso).grid(row=0, column=1, padx=6)
        ttk.Button(barra, text="Organizar", style="Toolbar.TButton", command=self.organizar).grid(row=0, column=2, padx=6)

        self.estado_var = tk.StringVar(value="")
        ttk.Label(barra, textvariable=self.estado_var, anchor="e").grid(row=0, column=13, sticky="ew")

    def refrescar(self):
        if not os.path.isdir(CARPETA_TRABAJO):
            self.resumen_var.set(f"No existe la carpeta: {CARPETA_TRABAJO}")
            self.estado_var.set("Crea la carpeta de trabajo antes de continuar.")
            return

        for item in self.tabla.get_children():
            self.tabla.delete(item)

        items = obtener_pdfs_bl(self.limpiar_simbolos_var.get())
        self.items = {item["archivo"]: item for item in items}
        for item in items:
            rango = self._formatear_rango(item)
            estado = "resuelto" if item["archivo"] in self.resoluciones_dudosos else item["estado"]
            self.tabla.insert("", "end", iid=item["archivo"], values=(
                item["tipo"],
                rango,
                estado,
                item["razon"],
                item["archivo"],
            ))

        simbolos = detectar_simbolos_lote(list(self.items))
        procesables = sum(1 for item in items if item["estado"] == "procesable")
        dudosos = sum(1 for item in items if item["estado"] == "dudoso")
        self.resumen_var.set(
            f"{len(items)} PDFs en {CARPETA_TRABAJO} | "
            f"{procesables} procesables | {dudosos} dudosos"
        )
        if simbolos and not self.limpiar_simbolos_var.get():
            self.estado_var.set(f"Símbolos detectados: {' '.join(sorted(simbolos))}")
        else:
            self.estado_var.set("Biblioteca actualizada.")

    def seleccion(self) -> list[str]:
        return list(self.tabla.selection())

    def agregar(self):
        tipos = [("PDF", " ".join(f"*{ext}" for ext in EXTENSIONES_BL_PDF)), ("Todos", "*.*")]
        rutas = filedialog.askopenfilenames(title="Agregar BL PDF", filetypes=tipos)
        if not rutas:
            return
        resultado = agregar_archivos(list(rutas))
        self.refrescar()
        mensaje = f"Archivos copiados: {len(resultado['copiados'])}"
        if resultado["omitidos"]:
            mensaje += f"\nOmitidos: {len(resultado['omitidos'])}"
        messagebox.showinfo("Agregar BL PDF", mensaje)

    def eliminar_seleccion(self):
        seleccion = self.seleccion()
        if not seleccion:
            messagebox.showwarning("Eliminar", "Selecciona uno o mas PDFs.")
            return

        if not messagebox.askyesno("Eliminar BL PDF", f"Eliminar {len(seleccion)} archivo(s) de la carpeta?"):
            return

        resultado = eliminar_archivos(seleccion)
        for nombre in seleccion:
            self.resoluciones_dudosos.pop(nombre, None)
        self.refrescar()
        mensaje = f"Eliminados: {len(resultado['eliminados'])}"
        if resultado["errores"]:
            mensaje += f"\nErrores: {len(resultado['errores'])}"
        messagebox.showinfo("Eliminar BL PDF", mensaje)

    def resolver_dudoso(self):
        seleccion = self.seleccion()
        if len(seleccion) != 1:
            messagebox.showwarning("Resolver dudoso", "Selecciona un solo PDF.")
            return

        nombre = seleccion[0]
        item = self.items.get(nombre)
        if not item:
            return

        inicial = self.resoluciones_dudosos.get(nombre, os.path.splitext(nombre)[0])
        nuevo = simpledialog.askstring(
            "Resolver dudoso",
            "Nombre final completo o sin .pdf:",
            initialvalue=inicial,
            parent=self,
        )
        if nuevo is None:
            return
        nuevo = nuevo.strip()
        if not nuevo:
            self.resoluciones_dudosos.pop(nombre, None)
        else:
            self.resoluciones_dudosos[nombre] = nuevo if nuevo.lower().endswith(".pdf") else nuevo + ".pdf"
        self.refrescar()

    def organizar(self):
        archivos = listar_pdfs_bl()
        if not archivos:
            messagebox.showinfo("Organizar", "No hay PDFs que organizar.")
            return

        datos = OrganizarDialog(self).mostrar()
        if not datos:
            return

        mapa_lz = crear_mapa_lz(archivos, datos["modo_lz"])
        try:
            cambios, advertencias = crear_cambios_organizar(
                datos["nombre_obra"],
                mapa_lz=mapa_lz,
                limpiar_simbolos=self.limpiar_simbolos_var.get(),
                resolucion_dudosos=self.resoluciones_dudosos,
            )
        except ValueError as e:
            messagebox.showerror("Organizar", str(e))
            return

        cambios_reales = [c for c in cambios if c["estado"] == "formato_incorrecto"]
        if not cambios_reales:
            messagebox.showinfo("Organizar", "No hay cambios que aplicar.")
            return

        mensaje = f"Renombrar {len(cambios_reales)} archivo(s)?"
        if advertencias:
            mensaje += f"\nAdvertencias: {len(advertencias)}"
        if not messagebox.askyesno("Organizar BL PDF", mensaje):
            return

        resultado = aplicar_cambios(cambios)
        for item in resultado.get("aplicados", []):
            self.resoluciones_dudosos.pop(item["original"], None)
        self._mostrar_resultado("Organizar BL PDF", resultado)
        self.refrescar()

    def _formatear_rango(self, item: dict) -> str:
        inicio = item.get("inicio")
        fin_num = item.get("fin_num")
        if inicio is None:
            return ""
        if fin_num is None:
            return f"{inicio:03d}"
        return f"{inicio:03d}-{fin_num:03d}"

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


class OrganizarDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Organizar BL PDF")
        self.resizable(False, False)
        self.resultado = None
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self.nombre_var = tk.StringVar()
        self.lz_var = tk.StringVar(value="ninguno")

        frame = ttk.Frame(self, padding=14)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Nombre de la obra").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(frame, textvariable=self.nombre_var, width=44).grid(row=0, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="Marca [LZ]").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Combobox(
            frame,
            textvariable=self.lz_var,
            state="readonly",
            values=("ninguno", "todos", "detectar"),
            width=18,
        ).grid(row=1, column=1, sticky="w", pady=(0, 8))

        botones = ttk.Frame(frame)
        botones.grid(row=2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(botones, text="Cancelar", command=self._cancelar).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(botones, text="Organizar", command=self._aceptar).grid(row=0, column=1)

        self.bind("<Return>", lambda _event: self._aceptar())
        self.bind("<Escape>", lambda _event: self._cancelar())

    def mostrar(self):
        self.wait_window()
        return self.resultado

    def _aceptar(self):
        nombre = self.nombre_var.get().strip()
        if not nombre:
            messagebox.showwarning("Organizar BL PDF", "El nombre de la obra no puede estar vacío.", parent=self)
            return
        self.resultado = {"nombre_obra": nombre, "modo_lz": self.lz_var.get()}
        self.destroy()

    def _cancelar(self):
        self.resultado = None
        self.destroy()


class BlPdfApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador multimedia - BL PDF")
        self.geometry("1040x640")
        self.minsize(820, 480)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        BlPdfFrame(self)


def main():
    app = BlPdfApp()
    app.mainloop()


if __name__ == "__main__":
    main()
