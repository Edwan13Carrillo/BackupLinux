"""
modulo_musica.py — Módulo Música del organizador multimedia.

Formato final : 000 - Título.flac / 000 - Título.m4a
Extensiones   : .flac y .m4a
"""

import os
import re

try:
    from mutagen.mp4  import MP4
    from mutagen.flac import FLAC
    MUTAGEN_DISPONIBLE = True
except ImportError:
    MUTAGEN_DISPONIBLE = False
    print("  [AVISO] mutagen no está instalado. Se omitirán los metadatos.")
    print("  Instalá con: pip install mutagen\n")

from utils import (
    CARPETA_TRABAJO,
    verificar_carpeta,
    detectar_numero,
    formatear_numero,
    clasificar_archivo,
    mostrar_vista_previa,
    pedir_confirmacion,
    limpiar_pantalla
)

EXTENSIONES_MUSICA = ('.flac', '.m4a')


# ---------------------------------------------------------------------------
# Lectura de metadatos
# ---------------------------------------------------------------------------

def leer_titulo(ruta: str) -> str | None:
    """Lee el título desde los metadatos del archivo (flac o m4a)."""
    if not MUTAGEN_DISPONIBLE:
        return None

    ext = os.path.splitext(ruta)[1].lower()

    try:
        if ext == '.flac':
            audio  = FLAC(ruta)
            titulo = audio.get('title')
            if titulo:
                return titulo[0].strip()

        elif ext == '.m4a':
            audio = MP4(ruta)
            tags  = audio.tags or {}
            titulo = tags.get('\xa9nam')
            if titulo:
                return titulo[0].strip()

    except Exception:
        pass

    return None


def pedir_titulo(nombre_archivo: str) -> str:
    """Solicita el título al usuario cuando los metadatos no lo tienen."""
    print(f"\n  El archivo '{nombre_archivo}' no tiene título en sus metadatos.")
    while True:
        valor = input("  Ingresá el título: ").strip()
        if valor:
            return valor
        print("  El campo no puede estar vacío.")


# ---------------------------------------------------------------------------
# Sanitización de nombres
# ---------------------------------------------------------------------------

# Caracteres inválidos en sistemas de archivos Linux/Windows
_CHARS_INVALIDOS = re.compile(r'[\\/:*?"<>|]')
# Espacios múltiples y espacios al inicio/fin
_ESPACIOS_MULTIPLES = re.compile(r' {2,}')

def sanitizar_titulo(titulo: str) -> str:
    """
    Limpia el título para que sea un nombre de archivo válido.
    - Reemplaza caracteres inválidos por guion o los elimina.
    - Colapsa espacios múltiples.
    - Quita espacios al inicio y fin.
    """
    # Caracteres con reemplazo semántico
    titulo = titulo.replace('"', "'").replace('/', '-').replace('\\', '-')
    # Resto de inválidos: eliminar directamente
    titulo = _CHARS_INVALIDOS.sub('', titulo)
    # Limpiar espacios
    titulo = _ESPACIOS_MULTIPLES.sub(' ', titulo).strip()
    # Evitar nombre vacío tras sanitizar
    return titulo or 'Sin título'


# ---------------------------------------------------------------------------
# Construcción de nombre final
# ---------------------------------------------------------------------------

def construir_nombre_final(numero: int, titulo: str, ext: str) -> str:
    """Construye el nombre final: '000 - Título.ext'"""
    return f"{formatear_numero(numero)} - {titulo}{ext}"


# ---------------------------------------------------------------------------
# Escaneo y clasificación
# ---------------------------------------------------------------------------

def escanear_carpeta() -> dict:
    """
    Escanea ./organizar y devuelve un resumen con:
      - 'musica'       : lista de archivos .flac y .m4a
      - 'otros'        : archivos de otras extensiones
      - 'organizados'  : archivos de música ya con formato correcto
      - 'sin_numero'   : archivos de música sin número detectado
      - 'total'        : total de archivos en la carpeta
    """
    try:
        todos = sorted(
            f for f in os.listdir(CARPETA_TRABAJO)
            if os.path.isfile(os.path.join(CARPETA_TRABAJO, f))
        )
    except PermissionError:
        print(f"\n  [ERROR] Sin permisos para leer '{CARPETA_TRABAJO}'.\n")
        return {}

    musica      = []
    otros       = []
    organizados = []
    sin_numero  = []

    for nombre in todos:
        ext = os.path.splitext(nombre)[1].lower()
        if ext in EXTENSIONES_MUSICA:
            musica.append(nombre)
            nombre_sin_ext = os.path.splitext(nombre)[0]
            estado = clasificar_archivo(nombre_sin_ext)
            if estado == 'correcto':
                organizados.append(nombre)
            elif estado == 'sin_numero':
                sin_numero.append(nombre)
        else:
            otros.append(nombre)

    return {
        'musica':      musica,
        'otros':       otros,
        'organizados': organizados,
        'sin_numero':  sin_numero,
        'total':       len(todos),
    }


def mostrar_resumen_modulo(info: dict):
    """Muestra el resumen al entrar al módulo Música."""
    print()
    print("=" * 60)
    print("  MODULO MUSICA — resumen de la carpeta")
    print("=" * 60)
    print(f"  Total de archivos encontrados  : {info['total']}")
    print(f"  Archivos de música (.flac/.m4a): {len(info['musica'])}")
    print(f"  Ya organizados (formato 000)   : {len(info['organizados'])}")
    print(f"  Sin número detectado           : {len(info['sin_numero'])}")
    print(f"  Otros formatos (no música)     : {len(info['otros'])}")

    if info['otros']:
        print()
        print("  Archivos fuera de formato:")
        for nombre in info['otros']:
            print(f"    - {nombre}")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Opción 1: Ordenar nombres
# ---------------------------------------------------------------------------

def opcion_ordenar():
    limpiar_pantalla()
    print("\n  --- Ordenar nombres de música ---\n")

    if not verificar_carpeta():
        return

    info = escanear_carpeta()
    if not info:
        return

    archivos = info['musica']

    if not archivos:
        print("  No se encontraron archivos .flac ni .m4a en ./ordenar\n")
        return

    cambios      = []
    advertencias = []

    for nombre in archivos:
        ext            = os.path.splitext(nombre)[1].lower()
        nombre_sin_ext = os.path.splitext(nombre)[0]
        ruta           = os.path.join(CARPETA_TRABAJO, nombre)
        estado         = clasificar_archivo(nombre_sin_ext)
        numero         = detectar_numero(nombre_sin_ext)

        if estado == 'sin_numero':
            cambios.append({
                'original': nombre,
                'nuevo':    nombre,
                'estado':   'sin_numero',
            })
            advertencias.append(f"Sin número detectado: {nombre}")
            continue

        # Leer título desde metadatos
        titulo = leer_titulo(ruta)
        if not titulo:
            titulo = pedir_titulo(nombre)
        titulo = sanitizar_titulo(titulo)

        nombre_nuevo = construir_nombre_final(numero, titulo, ext)

        cambios.append({
            'original': nombre,
            'nuevo':    nombre_nuevo,
            'estado':   estado,
        })

    mostrar_vista_previa(cambios, advertencias)

    hay_cambios = any(c['original'] != c['nuevo'] for c in cambios)
    if not hay_cambios:
        print("  No hay cambios que aplicar.\n")
        return

    if not pedir_confirmacion():
        print("\n  Operación cancelada. No se modificó ningún archivo.\n")
        return

    _aplicar_renombrado(cambios)


def _aplicar_renombrado(cambios: list[dict]):
    """Aplica renombrados simples (sin riesgo de colisión entre ellos)."""
    aplicados = 0
    errores   = 0

    for c in cambios:
        if c['original'] == c['nuevo']:
            continue
        if c['estado'] in ('sin_numero', 'dudoso'):
            continue

        ruta_orig  = os.path.join(CARPETA_TRABAJO, c['original'])
        ruta_nueva = os.path.join(CARPETA_TRABAJO, c['nuevo'])

        if os.path.exists(ruta_nueva):
            print(f"  [!] Conflicto — ya existe: {c['nuevo']} (se omite)")
            errores += 1
            continue

        try:
            os.rename(ruta_orig, ruta_nueva)
            aplicados += 1
        except OSError as e:
            print(f"  [ERROR] No se pudo renombrar '{c['original']}': {e}")
            errores += 1

    print(f"\n  Renombrados: {aplicados}  |  Omitidos/errores: {errores}\n")


# ---------------------------------------------------------------------------
# Opción 2: Insertar canciones
# ---------------------------------------------------------------------------

def opcion_insertar():
    limpiar_pantalla()
    print("\n  --- Insertar canciones a la lista ---\n")

    if not verificar_carpeta():
        return

    info = escanear_carpeta()
    if not info:
        return

    # Separar organizados de sin número
    organizados = []
    sin_numero  = info['sin_numero']

    # Vamos directo al grano con los que ya están en formato
    for nombre in info['organizados']:
        nombre_sin_ext = os.path.splitext(nombre)[0]
        numero = detectar_numero(nombre_sin_ext)
        organizados.append({'nombre': nombre, 'numero': numero})

    organizados.sort(key=lambda x: x['numero'])

    print(f"  Canciones ya organizadas : {len(organizados)}")
    print(f"  Canciones sin número     : {len(sin_numero)}")

    if not sin_numero:
        print("\n  No hay canciones nuevas para insertar.\n")
        return

    total_final = len(organizados) + len(sin_numero)
    print()
    print("  Canciones sin número (a insertar):")
    for i, nombre in enumerate(sin_numero, 1):
        print(f"    [{i}] {nombre}")

    print(f"\n  La lista final tendrá {total_final} elemento(s).")
    print(f"  Posiciones válidas para inserción: 1 a {total_final}")

    # Recopilar posiciones
    inserciones = []
    for nombre in sin_numero:
        while True:
            try:
                pos = int(input(f"\n  ¿En qué posición insertás '{nombre}'? (1-{total_final}): "))
                if 1 <= pos <= total_final:
                    inserciones.append({'nombre': nombre, 'posicion': pos})
                    break
                else:
                    print(f"  Posición fuera de rango. Ingresá un número entre 1 y {total_final}.")
            except ValueError:
                print("  Ingresá un número entero válido.")

    # Resolver lista virtual
    lista_final = _resolver_inserciones(organizados, inserciones)

    # Leer/pedir títulos de archivos nuevos
    titulos_nuevos = {}
    for ins in inserciones:
        ruta   = os.path.join(CARPETA_TRABAJO, ins['nombre'])
        titulo = leer_titulo(ruta)
        if not titulo:
            titulo = pedir_titulo(ins['nombre'])
        titulos_nuevos[ins['nombre']] = sanitizar_titulo(titulo)

    # Construir cambios
    cambios = []
    for entrada in lista_final:
        numero_nuevo = entrada['numero']
        nombre_orig  = entrada['nombre']
        ext          = os.path.splitext(nombre_orig)[1].lower()

        if nombre_orig in titulos_nuevos:
            # Archivo nuevo sin número
            titulo       = titulos_nuevos[nombre_orig]
            nombre_nuevo = construir_nombre_final(numero_nuevo, titulo, ext)
        else:
            # Archivo ya organizado — conservar el título exactamente como
            # aparece en el nombre actual, sin releer metadatos.
            titulo = _extraer_titulo_del_nombre(nombre_orig)

            if not titulo:
                # Caso raro: nombre no tiene formato esperado, pedir al usuario
                titulo = pedir_titulo(nombre_orig)

            nombre_nuevo = construir_nombre_final(numero_nuevo, titulo, ext)

        cambios.append({
            'original': nombre_orig,
            'nuevo':    nombre_nuevo,
            'estado':   'formato_incorrecto',
        })

    mostrar_vista_previa(cambios)

    hay_cambios = any(c['original'] != c['nuevo'] for c in cambios)
    if not hay_cambios:
        print("  No hay cambios que aplicar.\n")
        return

    if not pedir_confirmacion():
        print("\n  Operación cancelada. No se modificó ningún archivo.\n")
        return

    _aplicar_renombrado_seguro(cambios)


def _resolver_inserciones(organizados: list[dict], inserciones: list[dict]) -> list[dict]:
    """
    Construye la lista virtual final y asigna numeración correlativa.

    - organizados : [{'nombre': str, 'numero': int}, ...]  ordenados por número
    - inserciones : [{'nombre': str, 'posicion': int}, ...]

    Devuelve: [{'nombre': str, 'numero': int, 'es_nuevo': bool}, ...]
    """
    lista = [{'nombre': e['nombre'], 'es_nuevo': False} for e in organizados]

    # Insertar de menor a mayor posición para mantener coherencia
    inserciones_ord = sorted(inserciones, key=lambda x: x['posicion'])

    offset = 0
    for ins in inserciones_ord:
        pos_real = ins['posicion'] - 1 + offset
        pos_real = max(0, min(pos_real, len(lista)))
        lista.insert(pos_real, {'nombre': ins['nombre'], 'es_nuevo': True})
        offset += 1

    for i, entrada in enumerate(lista, 1):
        entrada['numero'] = i

    return lista


def _extraer_titulo_del_nombre(nombre: str) -> str | None:
    """
    Extrae el título de un nombre con formato '000 - Título.ext'.
    Devuelve el título o None.
    """
    nombre_sin_ext = os.path.splitext(nombre)[0]
    partes = nombre_sin_ext.split(' - ', 1)
    if len(partes) == 2:
        return partes[1].strip()
    return None


def _aplicar_renombrado_seguro(cambios: list[dict]):
    """
    Renombrado en dos pasos (via temporal) para evitar colisiones
    cuando múltiples archivos intercambian números.
    """
    SUFIJO_TEMP = '.__tmp__'
    aplicados   = 0
    errores     = 0

    # Paso 1: todo a temporal
    temporales = []
    for c in cambios:
        if c['original'] == c['nuevo']:
            continue
        if c['estado'] in ('sin_numero', 'dudoso'):
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
# Menú del módulo Música
# ---------------------------------------------------------------------------

def menu_musica():
    if not verificar_carpeta():
        return

    info = escanear_carpeta()
    if info:
        mostrar_resumen_modulo(info)

    while True:
        print()
        print("=" * 30)
        print("  MODULO MUSICA")
        print("=" * 30)
        print("  1. Ordenar nombres")
        print("  2. Insertar canciones a la lista")
        print("  3. Volver al menú principal")
        print("=" * 30)

        opcion = input("  Seleccioná una opción: ").strip()

        if opcion == '1':
            opcion_ordenar()
        elif opcion == '2':
            opcion_insertar()
        elif opcion == '3':
            limpiar_pantalla()
            break
        else:
            print("\n  Opción no válida. Ingresá 1, 2 o 3.\n")
