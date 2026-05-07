#!/usr/bin/env python3
"""
Organizador de M4A — Unificado
Carpeta de trabajo: ordenar/ (en el mismo directorio que este script)

Modos:
  A) ASMR  — Renombrado con metadatos (requiere mutagen)
  B) Música — Renombrado numérico clásico (sin dependencias externas)
"""

import os
import re
import sys
from pathlib import Path


# ─── Ruta compartida ──────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.resolve()
CARPETA_PATH = SCRIPT_DIR / "ordenar"
CARPETA_STR  = str(CARPETA_PATH) + os.sep   # para funciones que usan os.path
EXT          = ".m4a"


def limpiar():
    os.system('cls' if os.name == 'nt' else 'clear')


def asegurar_carpeta():
    CARPETA_PATH.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MODO A — ASMR
# ══════════════════════════════════════════════════════════════════════════════

def _cargar_mutagen():
    """Importa mutagen o termina con mensaje claro."""
    try:
        from mutagen.mp4 import MP4
        return MP4
    except ImportError:
        print("\n❌ Falta la librería 'mutagen'. Instálala con:")
        print("   pip install mutagen")
        sys.exit(1)


# "001 Artista - Título.m4a" → ya organizado
PATRON_ORGANIZADO = re.compile(r"^(\d{3})\s+.+\s+-\s+.+\.m4a$", re.IGNORECASE)

# "001 - Título.m4a" → formato original sin artista
PATRON_ORIGINAL   = re.compile(r"^(\d{3})\s*-\s*(.+)\.m4a$", re.IGNORECASE)


def _limpiar_nombre(texto: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", texto).strip()


def _leer_metadatos(ruta: Path, MP4) -> dict:
    datos = {"artista": "Desconocido", "titulo": ruta.stem}
    try:
        audio = MP4(ruta)
        if '\xa9ART' in audio:
            datos["artista"] = _limpiar_nombre(str(audio['\xa9ART'][0]))
        if '\xa9nam' in audio:
            datos["titulo"]  = _limpiar_nombre(str(audio['\xa9nam'][0]))
    except Exception:
        pass
    return datos


def _construir_nombre_asmr(numero: int, artista: str, titulo: str) -> str:
    return f"{numero:03d} {artista} - {titulo}.m4a"


def _listar_organizados() -> list:
    archivos = []
    for f in CARPETA_PATH.iterdir():
        if f.suffix.lower() == ".m4a" and PATRON_ORGANIZADO.match(f.name):
            num = int(f.name[:3])
            archivos.append((num, f))
    archivos.sort(key=lambda x: x[0])
    return archivos


def _listar_pendientes() -> list:
    pendientes = []
    for f in CARPETA_PATH.iterdir():
        if f.suffix.lower() == ".m4a" and not PATRON_ORGANIZADO.match(f.name):
            pendientes.append(f)
    pendientes.sort(key=lambda x: x.name.lower())
    return pendientes


def _renombrar(ruta_actual: Path, nuevo_nombre: str) -> Path:
    nueva_ruta = ruta_actual.parent / nuevo_nombre
    if ruta_actual != nueva_ruta:
        ruta_actual.rename(nueva_ruta)
    return nueva_ruta


def _ejecutar_renombrado_masivo(lista_final):
    """Renombra en dos pasos (temp → final) para evitar colisiones."""
    temporales = []
    for num, f, meta in lista_final:
        temp = f.parent / f"__TEMP_{num:03d}_{f.stem}__.m4a"
        f.rename(temp)
        temporales.append((num, temp, meta))

    for num, temp, meta in temporales:
        nuevo = _construir_nombre_asmr(num, meta["artista"], meta["titulo"])
        temp.rename(temp.parent / nuevo)
        print(f"  ✅ {nuevo}")

    print("\n🎉 ¡Archivos reformateados con éxito!")


# ── Subopción A1 ──────────────────────────────────────────────────────────────

def asmr_reorganizar_todo(MP4):
    print("\n📂 Leyendo archivos en 'ordenar/'...\n")

    todos = [f for f in CARPETA_PATH.iterdir() if f.suffix.lower() == ".m4a"]
    if not todos:
        print("❌ No hay archivos .m4a en la carpeta.")
        return

    con_numero, sin_numero = [], []
    for f in todos:
        m = PATRON_ORIGINAL.match(f.name)
        if m:
            con_numero.append((int(m.group(1)), f))
        elif not PATRON_ORGANIZADO.match(f.name):
            sin_numero.append(f)

    if not con_numero:
        print("⚠️  No se encontraron archivos con el formato '001 - Título.m4a'.")
        print("   💡 Si tus nombres están desordenados, usa la Opción 3 (Rescate Total).")
        return

    con_numero.sort(key=lambda x: x[0])
    lista_final = [(num, f, _leer_metadatos(f, MP4)) for num, f in con_numero]

    print(f"{'N°':<6} {'Artista':<30} {'Título':<40}")
    print("─" * 78)
    for num, f, meta in lista_final:
        print(f"{num:<6} {meta['artista'][:28]:<30} {meta['titulo'][:38]:<40}")

    if input("\n¿Proceder con el renombrado? (s/n): ").strip().lower() == "s":
        _ejecutar_renombrado_masivo(lista_final)


# ── Subopción A2 ──────────────────────────────────────────────────────────────

def asmr_insertar_nuevos(MP4):
    pendientes  = _listar_pendientes()
    if not pendientes:
        print("\n✅ No hay archivos nuevos pendientes de insertar.")
        return

    organizados  = _listar_organizados()
    total_actual = len(organizados)

    print(f"\n📥 Archivos nuevos detectados: {len(pendientes)}")
    print(f"📁 Archivos ya organizados   : {total_actual}")

    inserciones = []
    for archivo in pendientes:
        meta = _leer_metadatos(archivo, MP4)
        print(f"\n─── Archivo: {archivo.name}")
        print(f"    Artista : {meta['artista']}")
        print(f"    Título  : {meta['titulo']}")

        while True:
            entrada = input(f"    ¿En qué posición insertarlo? (1-{total_actual + 1}): ").strip()
            if entrada.isdigit() and 1 <= int(entrada) <= total_actual + 1:
                inserciones.append((archivo, meta, int(entrada)))
                break
            print("    ⚠️  Ingresa un número válido.")

    inserciones.sort(key=lambda x: x[2], reverse=True)

    print("\n📋 Resumen de inserciones:")
    for archivo, meta, pos in sorted(inserciones, key=lambda x: x[2]):
        print(f"  Pos {pos:03d} → {meta['artista']} - {meta['titulo']}")

    if input("\n¿Proceder? (s/n): ").strip().lower() == "s":
        for archivo, meta, pos in inserciones:
            organizados = _listar_organizados()
            afectados   = sorted([(n, f) for n, f in organizados if n >= pos],
                                 key=lambda x: x[0], reverse=True)
            for num, f in afectados:
                meta_f = _leer_metadatos(f, MP4)
                _renombrar(f, _construir_nombre_asmr(num + 1, meta_f["artista"], meta_f["titulo"]))

            _renombrar(archivo, _construir_nombre_asmr(pos, meta["artista"], meta["titulo"]))
            print(f"  ✅ Insertado: {_construir_nombre_asmr(pos, meta['artista'], meta['titulo'])}")


# ── Subopción A3 ──────────────────────────────────────────────────────────────

def asmr_rescate_total(MP4):
    print("\n🌪️  Modo Rescate: Reconstruyendo nombres desde los metadatos...\n")

    todos = [f for f in CARPETA_PATH.iterdir() if f.suffix.lower() == ".m4a"]
    if not todos:
        print("❌ No hay archivos .m4a en la carpeta.")
        return

    def extraer_num(nombre):
        m = re.search(r'^(\d+)', nombre)
        return int(m.group(1)) if m else 9999

    todos.sort(key=lambda f: (extraer_num(f.name), f.name))

    lista_final = []
    print(f"{'N°':<6} {'Artista':<30} {'Título':<40}")
    print("─" * 78)

    for i, f in enumerate(todos):
        num  = extraer_num(f.name)
        if num == 9999:
            num = i + 1
        meta = _leer_metadatos(f, MP4)
        lista_final.append((num, f, meta))
        print(f"{num:<6} {meta['artista'][:28]:<30} {meta['titulo'][:38]:<40}")

    print(f"\nTotal: {len(lista_final)} archivos a formatear desde cero.")
    if input("\n¿Aplicar formato limpio a todos? (s/n): ").strip().lower() == "s":
        _ejecutar_renombrado_masivo(lista_final)


# ── Menú ASMR ─────────────────────────────────────────────────────────────────

def menu_asmr():
    MP4 = _cargar_mutagen()

    while True:
        limpiar()
        todos = [f for f in CARPETA_PATH.iterdir() if f.suffix.lower() == ".m4a"]

        print("\n" + "═" * 45)
        print("       🎙️   Organizador ASMR   🎙️")
        print("═" * 45)
        print(f"\n📁 Carpeta : {CARPETA_PATH}")
        print(f"   Total .m4a : {len(todos)}")
        print("\n¿Qué quieres hacer?")
        print("  1. Reformatear  ('001 - Titulo' → '001 Artista - Titulo')")
        print("  2. Insertar archivo(s) nuevo(s) en posiciones específicas")
        print("  3. Rescate Total (reconstruir desde 0 leyendo metadatos)")
        print("  4. Volver al menú principal")

        op = input("\nElige una opción (1/2/3/4): ").strip()

        if op == "1":
            asmr_reorganizar_todo(MP4)
        elif op == "2":
            asmr_insertar_nuevos(MP4)
        elif op == "3":
            asmr_rescate_total(MP4)
        elif op == "4":
            break
        else:
            print("\n⚠️  Opción inválida.")

        input("\nPresiona Enter para continuar...")


# ══════════════════════════════════════════════════════════════════════════════
#  MODO B — MÚSICA
# ══════════════════════════════════════════════════════════════════════════════

def _obtener_m4a() -> list:
    return sorted(f for f in os.listdir(CARPETA_STR) if f.lower().endswith(EXT))

def _es_correcto(nombre) -> bool:
    return bool(re.match(r"^\d{3} - .+\.m4a$", nombre, re.IGNORECASE))

def _tiene_numero(nombre) -> bool:
    return bool(re.match(r"^\d+ - .+\.m4a$", nombre, re.IGNORECASE))

def _extraer_partes(nombre):
    m = re.match(r"^(\d+) - (.+)\.m4a$", nombre, re.IGNORECASE)
    return (int(m.group(1)), m.group(2)) if m else (None, None)

def _puro(nombre) -> str:
    m = re.match(r"^(?:\d+ - )?(.+)\.m4a$", nombre, re.IGNORECASE)
    return m.group(1) if m else re.sub(r"\.m4a$", "", nombre, flags=re.IGNORECASE)

def _fmt(num, nombre_puro) -> str:
    return f"{num:03d} - {nombre_puro}.m4a"

def _analizar():
    correctos, fmt_malo, sin_num = [], [], []
    for a in _obtener_m4a():
        if _es_correcto(a):
            correctos.append(a)
        elif _tiene_numero(a):
            fmt_malo.append(a)
        else:
            sin_num.append(a)
    return correctos, fmt_malo, sin_num


# ── Subopción B1 ──────────────────────────────────────────────────────────────

def musica_ordenar_nombres():
    limpiar()
    print("╔══════════════════════════════════════╗")
    print("║          ORDENAR NOMBRES             ║")
    print("╚══════════════════════════════════════╝\n")

    correctos, fmt_malo, sin_num = _analizar()

    print(f"  ✓ Formato correcto (000) : {len(correctos)}")
    print(f"  ⚠ Número pero mal formato: {len(fmt_malo)}")
    print(f"  ✗ Sin número             : {len(sin_num)}")

    if sin_num:
        print("\n  Las siguientes no tienen número (usa 'Meter música'):")
        for s in sin_num:
            print(f"    - {s}")

    if not fmt_malo:
        print("\n  ✓ No hay nada que estandarizar. Todo bien.")
        input("\n  Enter para continuar...")
        return

    cambios = []
    for a in fmt_malo:
        num, nombre = _extraer_partes(a)
        nuevo = _fmt(num, nombre)
        if a != nuevo:
            cambios.append((a, nuevo))

    if not cambios:
        print("\n  ✓ Todo ya está bien.")
        input("\n  Enter para continuar...")
        return

    print(f"\n  ─── CAMBIOS A REALIZAR ({len(cambios)}) ───")
    for viejo, nuevo in cambios:
        print(f"    {viejo}  →  {nuevo}")

    print()
    if input("  ¿Aplicar cambios? (s/n): ").strip().lower() == 's':
        errores = 0
        for viejo, nuevo in cambios:
            try:
                src = os.path.join(CARPETA_STR, viejo)
                dst = os.path.join(CARPETA_STR, nuevo)
                if src != dst:
                    os.rename(src, dst)
            except Exception as e:
                print(f"    ✗ Error renombrando '{viejo}': {e}")
                errores += 1
        exitosos = len(cambios) - errores
        print(f"\n  ✓ {exitosos} archivo(s) renombrado(s).")
        if errores:
            print(f"  ✗ {errores} error(es).")
    else:
        print("\n  Cancelado.")

    input("\n  Enter para continuar...")


# ── Subopción B2 ──────────────────────────────────────────────────────────────

def _construir_lista(nombres_base, inserciones):
    total  = len(nombres_base) + len(inserciones)
    lista  = [None] * total

    for pos, npuro in inserciones.items():
        lista[pos - 1] = npuro

    idx = 0
    for i in range(total):
        if lista[i] is None:
            lista[i] = nombres_base[idx]
            idx += 1

    return lista


def musica_meter_musica():
    limpiar()
    print("╔══════════════════════════════════════╗")
    print("║           METER MÚSICA               ║")
    print("╚══════════════════════════════════════╝\n")

    correctos, fmt_malo, sin_num = _analizar()

    if not sin_num:
        print("  No hay canciones sin número para insertar.")
        input("\n  Enter para continuar...")
        return

    con_num      = sorted(correctos + fmt_malo, key=lambda f: _extraer_partes(f)[0])
    nombres_base = [_extraer_partes(f)[1] for f in con_num]
    total_base   = len(nombres_base)
    total_final  = total_base + len(sin_num)

    print(f"  Canciones sin número ({len(sin_num)}):")
    for i, s in enumerate(sin_num, 1):
        print(f"    {i}. {s}")

    print(f"\n  Numeradas actualmente : {total_base}")
    print(f"  Total final           : {total_final}")
    print(f"  Posiciones válidas    : 1 – {total_final}\n")

    puro_a_archivo = {_puro(a): a for a in sin_num}
    inserciones    = {}
    pendientes     = list(sin_num)

    while pendientes:
        archivo = pendientes[0]
        npuro   = _puro(archivo)

        try:
            entrada = input(f"  Posición para '{archivo}' (1-{total_final}): ").strip()
            pos     = int(entrada)
        except ValueError:
            print("    ✗ Ingresa un número válido.\n")
            continue

        if not (1 <= pos <= total_final):
            print(f"    ✗ Debe ser entre 1 y {total_final}.\n")
            continue

        if pos not in inserciones:
            inserciones[pos] = npuro
            pendientes.pop(0)
            print(f"    ✓ '{archivo}' → posición {pos:03d}\n")
            continue

        conflicto = inserciones[pos]
        print(f"\n    ⚠ La posición {pos:03d} ya está asignada a '{conflicto}'.")
        print(f"       ¿Cuál va primero?")
        print(f"       1. {conflicto}  (ya asignado)")
        print(f"       2. {npuro}  (nuevo)")

        cual = ""
        while cual not in ("1", "2"):
            cual = input("       Opción (1/2): ").strip()

        if cual == "1":
            print(f"    → '{conflicto}' se queda en {pos:03d}. Elige otra posición para '{npuro}'.\n")
        else:
            inserciones[pos]    = npuro
            pendientes.pop(0)
            archivo_conflicto   = puro_a_archivo.get(conflicto, conflicto + ".m4a")
            pendientes.insert(0, archivo_conflicto)
            print(f"    → '{npuro}' toma {pos:03d}. Elige nueva posición para '{conflicto}'.\n")

    lista_final = _construir_lista(nombres_base, inserciones)
    nuevos_set  = set(inserciones.values())

    ancho = 54
    print(f"\n  {'─' * ancho}")
    print(f"  {'LISTA FINAL':^{ancho}}")
    print(f"  {'─' * ancho}")
    for i, npuro in enumerate(lista_final, 1):
        marca = "  ← NUEVO" if npuro in nuevos_set else ""
        print(f"  {i:03d} - {npuro}{marca}")
    print(f"  {'─' * ancho}")
    print(f"  Total: {len(lista_final)} canciones")

    print()
    if input("  ¿Aplicar cambios? (s/n): ").strip().lower() != 's':
        print("\n  Cancelado.")
        input("\n  Enter para continuar...")
        return

    todos        = _obtener_m4a()
    puro_a_actual = {}
    for a in todos:
        p = _puro(a)
        if p in puro_a_actual:
            print(f"  ⚠ Advertencia: '{a}' y '{puro_a_actual[p]}' tienen el mismo nombre base.")
        else:
            puro_a_actual[p] = a

    TMP = "__M4AORG_TMP__"

    try:
        for p, archivo in puro_a_actual.items():
            os.rename(os.path.join(CARPETA_STR, archivo),
                      os.path.join(CARPETA_STR, TMP + p + ".m4a"))

        for i, npuro in enumerate(lista_final, 1):
            os.rename(os.path.join(CARPETA_STR, TMP + npuro + ".m4a"),
                      os.path.join(CARPETA_STR, _fmt(i, npuro)))

        print(f"\n  ✓ ¡Listo! {len(lista_final)} canciones organizadas.")

    except Exception as e:
        print(f"\n  ✗ Error durante el renombrado: {e}")
        print("  Algunos archivos pueden tener prefijo temporal. Revisa la carpeta.")

    input("\n  Enter para continuar...")


# ── Menú Música ───────────────────────────────────────────────────────────────

def menu_musica():
    while True:
        limpiar()
        correctos, fmt_malo, sin_num = _analizar()
        total = len(correctos) + len(fmt_malo) + len(sin_num)

        print("╔══════════════════════════════════════╗")
        print("║      ORGANIZADOR DE MÚSICA M4A       ║")
        print("╚══════════════════════════════════════╝")
        print(f"\n  📁 Carpeta : {CARPETA_PATH}")
        print(f"  🎵 Total   : {total} archivos m4a")
        print(f"  ✓ Listos   : {len(correctos)}")
        print(f"  ⚠ Formato  : {len(fmt_malo)}")
        print(f"  ✗ Sin #    : {len(sin_num)}")
        print()
        print("  ────────────────────────────────────")
        print("  1. Ordenar nombres  (estandarizar formato 000)")
        print("  2. Meter música     (asignar posiciones)")
        print("  3. Volver al menú principal")
        print("  ────────────────────────────────────")

        op = input("\n  Opción: ").strip()
        if op == "1":
            musica_ordenar_nombres()
        elif op == "2":
            musica_meter_musica()
        elif op == "3":
            break
        else:
            print("\n  Opción no válida.")
            input("  Enter para continuar...")


# ══════════════════════════════════════════════════════════════════════════════
#  MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    asegurar_carpeta()

    while True:
        limpiar()
        print("╔══════════════════════════════════════╗")
        print("║       ORGANIZADOR DE M4A 🎵          ║")
        print("╚══════════════════════════════════════╝")
        print(f"\n  📁 Carpeta de trabajo: {CARPETA_PATH}")
        print()
        print("  ¿Qué quieres organizar?")
        print()
        print("  1. 🎙️  ASMR   (renombrado con metadatos del archivo)")
        print("  2. 🎵  Música (renombrado numérico clásico)")
        print("  3. 🚪  Salir")
        print()

        op = input("  Opción (1/2/3): ").strip()

        if op == "1":
            menu_asmr()
        elif op == "2":
            menu_musica()
        elif op == "3":
            print("\n  ¡Hasta luego! 👋\n")
            break
        else:
            print("\n  Opción no válida.")
            input("  Enter para continuar...")


if __name__ == "__main__":
    main()
