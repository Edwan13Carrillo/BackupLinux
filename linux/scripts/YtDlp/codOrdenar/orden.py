#!/usr/bin/env python3
"""
Organizador de MP3
Carpeta de trabajo: organizar/ (en el mismo directorio que este script)
"""

import re
import sys
from pathlib import Path

try:
    from mutagen.id3 import ID3, ID3NoHeaderError
except ImportError:
    print("❌ Falta la librería 'mutagen'. Instálala con:")
    print("   pip install mutagen")
    sys.exit(1)


# ─── Rutas ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
ORGANIZAR_DIR = SCRIPT_DIR / "organizar"

# "001 Artista - Título.mp3" → ya organizado
PATRON_ORGANIZADO = re.compile(r"^(\d{3})\s+.+\s+-\s+.+\.mp3$", re.IGNORECASE)

# "001 - Título.mp3" → formato original sin artista
PATRON_ORIGINAL = re.compile(r"^(\d{3})\s*-\s*(.+)\.mp3$", re.IGNORECASE)


# ─── Utilidades ───────────────────────────────────────────────────────────────

def limpiar_nombre(texto: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", texto).strip()


def leer_metadatos(ruta: Path) -> dict:
    datos = {"artista": "Desconocido", "titulo": ruta.stem}
    try:
        tags = ID3(ruta)
        if "TPE1" in tags:
            datos["artista"] = limpiar_nombre(str(tags["TPE1"].text[0]))
        if "TIT2" in tags:
            datos["titulo"] = limpiar_nombre(str(tags["TIT2"].text[0]))
    except (ID3NoHeaderError, Exception):
        pass
    return datos


def construir_nombre(numero: int, artista: str, titulo: str) -> str:
    return f"{numero:03d} {artista} - {titulo}.mp3"


def listar_organizados() -> list[tuple[int, Path]]:
    """Archivos con formato final '001 Artista - Título.mp3', ordenados por número."""
    archivos = []
    for f in ORGANIZAR_DIR.iterdir():
        if f.suffix.lower() == ".mp3" and PATRON_ORGANIZADO.match(f.name):
            num = int(f.name[:3])
            archivos.append((num, f))
    archivos.sort(key=lambda x: x[0])
    return archivos


def listar_pendientes() -> list[Path]:
    """Archivos .mp3 que NO tienen el formato final organizado."""
    pendientes = []
    for f in ORGANIZAR_DIR.iterdir():
        if f.suffix.lower() == ".mp3" and not PATRON_ORGANIZADO.match(f.name):
            pendientes.append(f)
    pendientes.sort(key=lambda x: x.name.lower())
    return pendientes


def renombrar_archivo(ruta_actual: Path, nuevo_nombre: str) -> Path:
    nueva_ruta = ruta_actual.parent / nuevo_nombre
    if ruta_actual != nueva_ruta:
        ruta_actual.rename(nueva_ruta)
    return nueva_ruta


# ─── Modo 1: Reformatear conservando el orden numérico actual ─────────────────

def reorganizar_todo():
    print("\n📂 Leyendo archivos en 'organizar/'...\n")

    todos = [f for f in ORGANIZAR_DIR.iterdir() if f.suffix.lower() == ".mp3"]
    if not todos:
        print("❌ No hay archivos .mp3 en la carpeta.")
        return

    con_numero = []
    sin_numero = []

    for f in todos:
        m = PATRON_ORIGINAL.match(f.name)
        if m:
            num = int(m.group(1))
            con_numero.append((num, f))
        elif not PATRON_ORGANIZADO.match(f.name):
            sin_numero.append(f)

    if not con_numero:
        print("⚠️  No se encontraron archivos con formato '001 - Título.mp3'.")
        print("   Si ya están organizados, usa la opción 2 para insertar nuevos.")
        return

    if sin_numero:
        print(f"⚠️  {len(sin_numero)} archivo(s) sin número serán ignorados:")
        for f in sin_numero:
            print(f"   - {f.name}")
        print()

    # Ordenar por número existente → respeta tu orden personalizado
    con_numero.sort(key=lambda x: x[0])

    # Leer metadatos
    lista_final = []
    for num, f in con_numero:
        meta = leer_metadatos(f)
        lista_final.append((num, f, meta))

    # Preview
    print(f"{'N°':<6} {'Artista':<30} {'Título':<40}")
    print("─" * 78)
    for num, f, meta in lista_final:
        print(f"{num:<6} {meta['artista']:<30} {meta['titulo']:<40}")

    print(f"\nTotal: {len(lista_final)} archivos")
    confirmar = input("\n¿Proceder con el renombrado? (s/n): ").strip().lower()
    if confirmar != "s":
        print("Operación cancelada.")
        return

    # Paso 1: renombrar a temporales para evitar conflictos
    temporales = []
    for num, f, meta in lista_final:
        temp = f.parent / f"__TEMP_{num:03d}__.mp3"
        f.rename(temp)
        temporales.append((num, temp, meta))

    # Paso 2: renombrar a formato final conservando el número original
    for num, temp, meta in temporales:
        nuevo = construir_nombre(num, meta["artista"], meta["titulo"])
        temp.rename(temp.parent / nuevo)
        print(f"  ✅ {nuevo}")

    print(f"\n🎉 ¡Listo! {len(lista_final)} archivos reformateados.")


# ─── Modo 2: Insertar archivos nuevos ─────────────────────────────────────────

def insertar_nuevos():
    pendientes = listar_pendientes()
    if not pendientes:
        print("\n✅ No hay archivos nuevos pendientes de insertar.")
        return

    organizados = listar_organizados()
    total_actual = len(organizados)

    print(f"\n📥 Archivos nuevos detectados: {len(pendientes)}")
    print(f"📁 Archivos ya organizados: {total_actual}")
    if organizados:
        print(f"   (van del 001 al {organizados[-1][0]:03d})\n")

    inserciones = []

    for archivo in pendientes:
        meta = leer_metadatos(archivo)
        print(f"─── Archivo: {archivo.name}")
        print(f"    Artista : {meta['artista']}")
        print(f"    Título  : {meta['titulo']}")

        while True:
            entrada = input(f"    ¿En qué posición insertarlo? (1-{total_actual + 1}): ").strip()
            if entrada.isdigit():
                pos = int(entrada)
                if 1 <= pos <= total_actual + 1:
                    break
            print(f"    ⚠️  Ingresa un número entre 1 y {total_actual + 1}.")

        inserciones.append((archivo, meta, pos))
        print()

    # Ordenar de mayor a menor posición para no interferir entre sí
    inserciones.sort(key=lambda x: x[2], reverse=True)

    # Resumen
    print("\n📋 Resumen de inserciones:")
    for archivo, meta, pos in sorted(inserciones, key=lambda x: x[2]):
        print(f"  Pos {pos:03d} → {meta['artista']} - {meta['titulo']}")

    confirmar = input("\n¿Proceder? (s/n): ").strip().lower()
    if confirmar != "s":
        print("Operación cancelada.")
        return

    for archivo, meta, pos in inserciones:
        _ejecutar_insercion(archivo, meta, pos)

    print("\n🎉 ¡Inserción completada!")


def _ejecutar_insercion(archivo: Path, meta: dict, posicion: int):
    organizados = listar_organizados()

    # Desplazar hacia arriba los archivos desde la posición en adelante
    afectados = [(num, f) for num, f in organizados if num >= posicion]
    afectados.sort(key=lambda x: x[0], reverse=True)

    for num, f in afectados:
        meta_f = leer_metadatos(f)
        renombrar_archivo(f, construir_nombre(num + 1, meta_f["artista"], meta_f["titulo"]))

    # Insertar el nuevo en la posición indicada
    nuevo_nombre = construir_nombre(posicion, meta["artista"], meta["titulo"])
    renombrar_archivo(archivo, nuevo_nombre)
    print(f"  ✅ Insertado: {nuevo_nombre}")


# ─── Menú principal ───────────────────────────────────────────────────────────

def menu():
    print("\n" + "═" * 45)
    print("        🎵  Organizador de MP3  🎵")
    print("═" * 45)

    if not ORGANIZAR_DIR.exists():
        print(f"\n❌ No existe la carpeta 'organizar/' en:\n   {SCRIPT_DIR}")
        print("Créala y agrega tus MP3 antes de continuar.")
        sys.exit(1)

    pendientes = listar_pendientes()
    organizados = listar_organizados()

    print(f"\n📁 Carpeta: {ORGANIZAR_DIR}")
    print(f"   Organizados : {len(organizados)}")
    print(f"   Pendientes  : {len(pendientes)}")

    print("\n¿Qué quieres hacer?")
    print("  1. Reformatear toda la carpeta (agrega artista al nombre)")
    print("  2. Insertar archivo(s) nuevo(s)")
    print("  3. Salir")

    opcion = input("\nElige una opción (1/2/3): ").strip()

    if opcion == "1":
        reorganizar_todo()
    elif opcion == "2":
        insertar_nuevos()
    elif opcion == "3":
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)
    else:
        print("\n⚠️  Opción inválida.")

    input("\nPresiona Enter para volver al menú...")
    menu()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    menu()
