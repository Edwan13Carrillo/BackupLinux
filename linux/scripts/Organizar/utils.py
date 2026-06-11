"""
utils.py — Funciones compartidas del organizador multimedia.
"""

import re
import os

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
# ---------------------------------------------------------------------------
# Detección de número en nombre de archivo
# ---------------------------------------------------------------------------

# Patrones en orden de prioridad (de más específico a más general)
_PATRONES_NUMERO = [
    re.compile(r'^\s*(\d+)\s*[-.,]\s*'),   # "01 - ", "01. ", "01, "
    re.compile(r'^\s*(\d+)\s+'),            # "01 titulo"
    re.compile(r'^\s*(\d+)$'),              # solo número
]


def detectar_numero(nombre_sin_ext: str) -> int | None:
    """
    Intenta extraer el número de episodio/pista del nombre del archivo.
    Devuelve el entero puro o None si no encuentra nada.
    """
    for patron in _PATRONES_NUMERO:
        m = patron.match(nombre_sin_ext)
        if m:
            return int(m.group(1))
    return None


def formatear_numero(n: int) -> str:
    """Formatea un entero a tres dígitos: 1 → '001', 26 → '026'."""
    return str(n).zfill(3)


# ---------------------------------------------------------------------------
# Clasificación de archivos
# ---------------------------------------------------------------------------

def clasificar_archivo(nombre_sin_ext: str) -> str:
    """
    Devuelve el estado del archivo:
      'correcto'           — número detectado, formato ya es 000
      'formato_incorrecto' — número detectado, formato no es 000
      'sin_numero'         — no se detectó número
    """
    numero = detectar_numero(nombre_sin_ext)
    if numero is None:
        return 'sin_numero'

    # Verificar si ya está en formato "000 - ..."
    if re.match(r'^\d{3} - ', nombre_sin_ext):
        return 'correcto'

    return 'formato_incorrecto'


# ---------------------------------------------------------------------------
# Vista previa en consola
# ---------------------------------------------------------------------------

def mostrar_vista_previa(cambios: list[dict], advertencias: list[str] = None):
    """
    Muestra la vista previa de renombrado.

    Cada elemento de `cambios` es un dict con:
      - 'original': nombre actual del archivo (con extensión)
      - 'nuevo':    nombre resultante (con extensión)
      - 'estado':   'correcto' | 'formato_incorrecto' | 'sin_numero' | 'dudoso'
    """
    print()
    print("=" * 30)
    print("  VISTA PREVIA DE CAMBIOS")
    print("=" * 30)

    if advertencias:
        print()
        print("  ADVERTENCIAS:")
        for adv in advertencias:
            print(f"  [!] {adv}")

    # Separar los que cambian de los que no
    con_cambio    = [c for c in cambios if c['original'] != c['nuevo'] and c['estado'] != 'sin_numero' and c['estado'] != 'dudoso']
    sin_numero    = [c for c in cambios if c['estado'] == 'sin_numero']
    dudosos       = [c for c in cambios if c['estado'] == 'dudoso']
    sin_cambio    = [c for c in cambios if c['original'] == c['nuevo'] and c['estado'] not in ('sin_numero', 'dudoso')]

    if con_cambio:
        print()
        print(f"  Archivos a renombrar ({len(con_cambio)}):")
        print("  " + "-" * 56)
        for c in con_cambio:
            print(f"  {c['original']}")
            print(f"  → {c['nuevo']}")
            print()

    if sin_cambio:
        print(f"  Archivos ya con formato correcto ({len(sin_cambio)}) — sin cambios:")
        for c in sin_cambio:
            print(f"    {c['original']}")
        print()

    if sin_numero:
        print(f"  Archivos SIN número detectado ({len(sin_numero)}) — se omiten:")
        for c in sin_numero:
            print(f"    [?] {c['original']}")
        print()

    if dudosos:
        print(f"  Archivos DUDOSOS ({len(dudosos)}) — requieren intervención manual:")
        for c in dudosos:
            print(f"    [!] {c['original']}")
        print()

    print("=" * 30)
    total_cambios = len(con_cambio)
    print(f"  Total de renombrados: {total_cambios}")
    print("=" * 30)
    print()


def pedir_confirmacion(mensaje: str = "¿Aplicar los cambios? (s/n): ") -> bool:
    """Pide confirmación al usuario. Devuelve True si responde 's'."""
    while True:
        resp = input(mensaje).strip().lower()
        if resp in ('s', 'si', 'sí', 'y', 'yes'):
            return True
        if resp in ('n', 'no'):
            return False
        print("  Respuesta no válida. Escribí 's' para confirmar o 'n' para cancelar.")


# ---------------------------------------------------------------------------
# Helpers de carpeta
# ---------------------------------------------------------------------------

CARPETA_TRABAJO = os.path.join('.', 'ordenar')


def verificar_carpeta() -> bool:
    """Verifica que la carpeta ./ordenar existe. Si no, avisa y devuelve False."""
    if not os.path.isdir(CARPETA_TRABAJO):
        print(f"\n  [ERROR] No se encontró la carpeta '{CARPETA_TRABAJO}'.")
        print("  Creá la carpeta y colocá los archivos dentro antes de continuar.\n")
        return False
    return True


def listar_archivos(extension: str | tuple) -> list[str]:
    """
    Lista los archivos en ./organizar con la extensión dada.
    `extension` puede ser un string ('.m4a') o una tupla ('.flac', '.m4a').
    Devuelve lista de nombres de archivo (sin ruta).
    """
    if isinstance(extension, str):
        extension = (extension,)

    extension = tuple(e.lower() for e in extension)

    try:
        return sorted(
            f for f in os.listdir(CARPETA_TRABAJO)
            if os.path.isfile(os.path.join(CARPETA_TRABAJO, f))
            and os.path.splitext(f)[1].lower() in extension
        )
    except PermissionError:
        print(f"\n  [ERROR] Sin permisos para leer '{CARPETA_TRABAJO}'.\n")
        return []
