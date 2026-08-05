"""
main_gui.py - Pantalla principal grafica del organizador multimedia.
"""

import tkinter as tk
from tkinter import ttk

from gui_asmr import AsmrFrame
from gui_bl_pdf import BlPdfFrame
from gui_musica import MusicaFrame


class OrganizadorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador multimedia")
        self.geometry("980x620")
        self.minsize(780, 460)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._configurar_estilo()
        self.contenedor = ttk.Frame(self)
        self.contenedor.grid(row=0, column=0, sticky="nsew")
        self.contenedor.columnconfigure(0, weight=1)
        self.contenedor.rowconfigure(0, weight=1)
        self.mostrar_inicio()

    def _configurar_estilo(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("", 10))
        style.configure("Module.TButton", padding=(14, 12), font=("", 11, "bold"))

    def _limpiar(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def mostrar_inicio(self):
        self._limpiar()

        inicio = ttk.Frame(self.contenedor, padding=24)
        inicio.grid(row=0, column=0, sticky="nsew")
        inicio.columnconfigure(0, weight=1)
        inicio.columnconfigure(1, weight=1)
        inicio.rowconfigure(2, weight=1)

        ttk.Label(inicio, text="Organizador multimedia", style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            inicio,
            text="Selecciona un modulo para gestionar los archivos de la carpeta de trabajo.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 18))

        self._tarjeta_modulo(
            inicio,
            fila=2,
            columna=0,
            titulo="Musica",
            descripcion="Visualizar, agregar, eliminar y reordenar canciones.",
            accion=lambda: self._mostrar_modulo(lambda parent: MusicaFrame(parent, self.mostrar_inicio)),
        )
        self._tarjeta_modulo(
            inicio,
            fila=2,
            columna=1,
            titulo="ASMR",
            descripcion="Reformatear, agregar, eliminar y reordenar archivos.",
            accion=lambda: self._mostrar_modulo(lambda parent: AsmrFrame(parent, self.mostrar_inicio)),
        )
        self._tarjeta_modulo(
            inicio,
            fila=3,
            columna=1,
            titulo="PDF",
            descripcion="Analizar, agregar, eliminar y organizar BL PDF.",
            accion=lambda: self._mostrar_modulo(lambda parent: BlPdfFrame(parent, self.mostrar_inicio)),
        )

    def _tarjeta_modulo(self, parent, fila: int, columna: int, titulo: str, descripcion: str, accion):
        frame = ttk.Frame(parent, padding=12, relief="groove")
        frame.grid(row=fila, column=columna, sticky="nsew", padx=8, pady=8)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=titulo, font=("", 13, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text=descripcion, wraplength=360).grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Button(frame, text="Abrir", style="Module.TButton", command=accion).grid(row=2, column=0, sticky="ew")

    def _mostrar_modulo(self, construir_frame):
        self._limpiar()
        construir_frame(self.contenedor)


def main():
    app = OrganizadorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
