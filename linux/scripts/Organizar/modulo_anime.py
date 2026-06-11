"""
modulo_anime.py — Módulo Anime del organizador multimedia.

Formato final : 00 - Nombre del anime.mkv
Extensión     : .mkv

Filosofía: no adivinar de forma agresiva. Si hay ambigüedad, marcar
como dudoso y preguntar al usuario.
"""

import os
import re

from utils import (
    CARPETA_TRABAJO,
    verificar_carpeta,
    listar_archivos,
    mostrar_vista_previa,
    pedir_confirmacion,
    limpiar_pantalla
)


def _formatear_numero_anime(numero: int) -> str:
    """Formatea el episodio con al menos 2 dígitos (01, 02, 03...)."""
    return f"{numero:02d}"


# ---------------------------------------------------------------------------
# Patrones de detección de episodio
# Orden: de más específico a más general.
# Cada patrón devuelve el número de episodio en el grupo 1.
# ---------------------------------------------------------------------------

_PATRONES_EPISODIO = [
    # S01E26, S04E02, S05E01v2  →  captura el número de episodio (E parte)
    re.compile(r'\bS\d{1,2}E(\d{1,4})(?:v\d+)?\b', re.IGNORECASE),

    # Episode 07 / Episodio 07 / Ep 07 / Cap 07
    re.compile(
        r'\b(?:EP(?:ISODE)?|Episodio|Episódio|Cap(?:itulo|ítulo)?)\s*0*(\d{1,4})\b',
        re.IGNORECASE,
    ),

    # "- 07" antes de un bloque de metadatos, extensión o fin de cadena.
    # Cubre: "[Erai-raws] Serie - 07 [1080p ...].mkv"
    # y también "Serie - 07.mkv"
    re.compile(r'(?<!\d)-\s*0*(\d{1,4})(?=\s*(?:\[|\(|\.|$))'),

    # Número aislado al inicio: "09 The Promised Neverland.mkv"
    re.compile(r'^\s*0*(\d{1,4})(?=\s+)'),

    # Número aislado al final antes de corchetes o extensión
    re.compile(r'\s0*(\d{1,4})(?=\s*(?:\[|\(|\.|$))'),
]


# ---------------------------------------------------------------------------
# Detección principal
# ---------------------------------------------------------------------------

def detectar_episodio(nombre_sin_ext: str) -> tuple[int | None, str]:
    """
    Intenta detectar el número de episodio en el nombre del archivo.

    Devuelve:
      (numero, estado)
      - estado puede ser: 'ok', 'dudoso'

    'dudoso' se produce cuando:
      - ningún patrón detecta el episodio.
    """
    
    for patron in _PATRONES_EPISODIO:
        m = patron.search(nombre_sin_ext)
        if m:
            return int(m.group(1)), 'ok'

    return None, 'dudoso'

# ---------------------------------------------------------------------------
# Resolución de dudosos: intervención del usuario
# ---------------------------------------------------------------------------

def resolver_dudosos(dudosos: list[str]) -> dict[str, int | None]:
    """
    Para cada archivo dudoso, le muestra el nombre al usuario y le pide
    que escriba el número de episodio correcto o 's' para saltarlo.

    Devuelve dict: nombre_archivo → número (int) o None (saltado).
    """
    resultado = {}

    print()
    print("=" * 30)
    print("  ARCHIVOS DUDOSOS — se requiere intervención")
    print("=" * 30)
    print("  Para cada archivo, escribí el número de episodio correcto")
    print("  o presioná Enter para saltarlo (no se renombrará).")
    print()

    for nombre in dudosos:
        print(f"  Archivo: {nombre}")
        while True:
            resp = input("  Número de episodio (o Enter para saltar): ").strip()
            if resp == '':
                resultado[nombre] = None
                print("  → Saltado.\n")
                break
            try:
                numero = int(resp)
                if numero < 1:
                    print("  El número debe ser mayor a 0.")
                    continue
                resultado[nombre] = numero
                print(f"  → Asignado episodio {numero:02d}.\n")
                break
            except ValueError:
                print("  Ingresá un número entero válido o Enter para saltar.")

    return resultado


# ---------------------------------------------------------------------------
# Construcción de nombre final
# ---------------------------------------------------------------------------

def construir_nombre_final(numero: int, nombre_anime: str) -> str:
    """Construye '00 - Nombre del anime.mkv'"""
    return f"{_formatear_numero_anime(numero)} - {nombre_anime}.mkv"


# ---------------------------------------------------------------------------
# Opción 1: Ordenar nombres
# ---------------------------------------------------------------------------

def opcion_ordenar():
    limpiar_pantalla()
    print("\n  --- Ordenar nombres de Anime ---\n")

    if not verificar_carpeta():
        return

    archivos = listar_archivos('.mkv')

    if not archivos:
        print("  No se encontraron archivos .mkv en ./organizar\n")
        return

    print(f"  Archivos .mkv encontrados: {len(archivos)}")

    # Clasificar archivos
    procesables = []   # {'nombre': str, 'numero': int}
    dudosos     = []   # nombres de archivos dudosos

    for nombre in archivos:
        nombre_sin_ext = os.path.splitext(nombre)[0]
        numero, estado = detectar_episodio(nombre_sin_ext)

        if estado == 'dudoso' or numero is None:
            dudosos.append(nombre)
        else:
            procesables.append({'nombre': nombre, 'numero': numero})

    # Resolver dudosos antes de continuar
    resolucion_dudosos = {}
    if dudosos:
        print()
        print(f"  Se encontraron {len(dudosos)} archivo(s) dudoso(s).")
        resolucion_dudosos = resolver_dudosos(dudosos)

        # Agregar los dudosos resueltos a procesables
        for nombre, numero in resolucion_dudosos.items():
            if numero is not None:
                procesables.append({'nombre': nombre, 'numero': numero})

    if not procesables:
        print("\n  No hay archivos procesables. Revisá los archivos dudosos.\n")
        return

    # Pedir nombre del anime
    print()
    nombre_anime = input("  Nombre del anime (ej: Kimetsu no Yaiba): ").strip()
    while not nombre_anime:
        print("  El nombre no puede estar vacío.")
        nombre_anime = input("  Nombre del anime: ").strip()

    # Construir lista de cambios
    cambios      = []
    advertencias = []

    # Verificar duplicados de episodio
    numeros_vistos = {}
    for p in procesables:
        n = p['numero']
        if n in numeros_vistos:
            advertencias.append(
                f"Episodio {n:02d} duplicado: '{p['nombre']}' y '{numeros_vistos[n]}'"
            )
        else:
            numeros_vistos[n] = p['nombre']

    for p in sorted(procesables, key=lambda x: x['numero']):
        nombre_orig  = p['nombre']
        nombre_nuevo = construir_nombre_final(p['numero'], nombre_anime)

        # Determinar estado para la vista previa
        if nombre_orig == nombre_nuevo:
            estado_cambio = 'correcto'
        else:
            estado_cambio = 'formato_incorrecto'

        cambios.append({
            'original': nombre_orig,
            'nuevo':    nombre_nuevo,
            'estado':   estado_cambio,
        })

    # Agregar dudosos no resueltos a la vista previa
    for nombre in dudosos:
        if resolucion_dudosos.get(nombre) is None:
            cambios.append({
                'original': nombre,
                'nuevo':    nombre,
                'estado':   'dudoso',
            })

    mostrar_vista_previa(cambios, advertencias if advertencias else None)

    hay_cambios = any(
        c['original'] != c['nuevo']
        for c in cambios
        if c['estado'] not in ('dudoso', 'sin_numero')
    )

    if not hay_cambios:
        print("  No hay cambios que aplicar.\n")
        return

    if not pedir_confirmacion():
        print("\n  Operación cancelada. No se modificó ningún archivo.\n")
        return

    _aplicar_renombrado(cambios)


def _aplicar_renombrado(cambios: list[dict]):
    """Aplica el renombrado, omitiendo dudosos."""
    SUFIJO_TEMP = '.__tmp__'
    aplicados   = 0
    errores     = 0

    # Paso 1: todo a temporal (por si hay intercambio de nombres)
    temporales = []
    for c in cambios:
        if c['original'] == c['nuevo']:
            continue
        if c['estado'] in ('dudoso', 'sin_numero'):
            continue

        ruta_orig = os.path.join(CARPETA_TRABAJO, c['original'])
        ruta_temp = ruta_orig + SUFIJO_TEMP

        try:
            os.rename(ruta_orig, ruta_temp)
            temporales.append({'temp': c['original'] + SUFIJO_TEMP, 'nuevo': c['nuevo']})
        except OSError as e:
            print(f"  [ERROR] No se pudo mover a temporal '{c['original']}': {e}")
            errores += 1

    # Paso 2: temporal → nombre final
    for t in temporales:
        ruta_temp  = os.path.join(CARPETA_TRABAJO, t['temp'])
        ruta_nueva = os.path.join(CARPETA_TRABAJO, t['nuevo'])

        if os.path.exists(ruta_nueva):
            print(f"  [!] Conflicto — ya existe: {t['nuevo']} (se omite)")
            errores += 1
            continue

        try:
            os.rename(ruta_temp, ruta_nueva)
            aplicados += 1
        except OSError as e:
            print(f"  [ERROR] No se pudo finalizar '{t['nuevo']}': {e}")
            errores += 1

    print(f"\n  Renombrados: {aplicados}  |  Omitidos/errores: {errores}\n")


# ---------------------------------------------------------------------------
# Menú del módulo Anime
# ---------------------------------------------------------------------------

def menu_anime():
    while True:
        print()
        print("=" * 30)
        print("  MODULO ANIME")
        print("=" * 30)
        print("  1. Ordenar nombres")
        print("  2. Volver al menú principal")
        print("=" * 30)

        opcion = input("  Seleccioná una opción: ").strip()

        if opcion == '1':
            opcion_ordenar()
        elif opcion == '2':
            limpiar_pantalla()
            break
        else:
            print("\n  Opción no válida. Ingresá 1 o 2.\n")
