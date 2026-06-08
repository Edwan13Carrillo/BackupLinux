"""
modulo_asmr.py — Módulo ASMR del organizador multimedia.

Formato final: 000 - Artista - Título.m4a
"""

import os
import re

try:
    from mutagen.mp4 import MP4
    MUTAGEN_DISPONIBLE = True
except ImportError:
    MUTAGEN_DISPONIBLE = False
    print("  [AVISO] mutagen no está instalado. Se omitirán los metadatos.")
    print("  Instalá con: pip install mutagen\n")

from utils import (
    CARPETA_TRABAJO,
    verificar_carpeta,
    listar_archivos,
    detectar_numero,
    formatear_numero,
    clasificar_archivo,
    mostrar_vista_previa,
    pedir_confirmacion,
)


# ---------------------------------------------------------------------------
# Lectura de metadatos
# ---------------------------------------------------------------------------

def leer_metadatos_m4a(ruta: str) -> dict:
    """
    Lee artista y título desde los metadatos del archivo m4a.
    Devuelve dict con claves 'artista' y 'titulo' (pueden ser None).
    """
    resultado = {'artista': None, 'titulo': None}

    if not MUTAGEN_DISPONIBLE:
        return resultado

    try:
        audio = MP4(ruta)
        tags  = audio.tags or {}

        # Artista: tag '\xa9ART'
        artista = tags.get('\xa9ART')
        if artista:
            resultado['artista'] = artista[0].strip()

        # Título: tag '\xa9nam'
        titulo = tags.get('\xa9nam')
        if titulo:
            resultado['titulo'] = titulo[0].strip()

    except Exception:
        pass  # Si falla la lectura, se pedirán los datos al usuario

    return resultado


def pedir_dato(nombre_campo: str, nombre_archivo: str) -> str:
    """Solicita al usuario un metadato faltante."""
    print(f"\n  El archivo '{nombre_archivo}' no tiene '{nombre_campo}' en sus metadatos.")
    while True:
        valor = input(f"  Ingresá el {nombre_campo}: ").strip()
        if valor:
            return valor
        print("  El campo no puede estar vacío.")


# ---------------------------------------------------------------------------
# Construcción de nombre final
# ---------------------------------------------------------------------------

def construir_nombre_final(numero: int, artista: str, titulo: str) -> str:
    """Construye el nombre final con formato '000 - Artista - Título'."""
    return f"{formatear_numero(numero)} - {artista} - {titulo}"


# ---------------------------------------------------------------------------
# Opción 1: Reformatear nombres
# ---------------------------------------------------------------------------

def opcion_reformatear():
    print("\n  --- Reformatear nombres ASMR ---\n")

    if not verificar_carpeta():
        return

    archivos = listar_archivos('.m4a')

    if not archivos:
        print("  No se encontraron archivos .m4a en ./organizar\n")
        return

    print(f"  Archivos .m4a encontrados: {len(archivos)}")

    cambios      = []
    advertencias = []
    datos_extra  = {}   # nombre_original → {'artista': str, 'titulo': str}

    for nombre in archivos:
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

        # Leer metadatos
        meta    = leer_metadatos_m4a(ruta)
        artista = meta['artista']
        titulo  = meta['titulo']

        # Pedir datos faltantes al usuario
        if not artista:
            artista = pedir_dato('artista', nombre)
        if not titulo:
            titulo = pedir_dato('título', nombre)

        datos_extra[nombre] = {'artista': artista, 'titulo': titulo}

        nombre_nuevo = construir_nombre_final(numero, artista, titulo) + '.m4a'

        cambios.append({
            'original': nombre,
            'nuevo':    nombre_nuevo,
            'estado':   estado,
        })

    # Vista previa
    mostrar_vista_previa(cambios, advertencias)

    hay_cambios = any(c['original'] != c['nuevo'] for c in cambios)
    if not hay_cambios:
        print("  No hay cambios que aplicar.\n")
        return

    if not pedir_confirmacion():
        print("\n  Operación cancelada. No se modificó ningún archivo.\n")
        return

    # Aplicar renombrado
    _aplicar_renombrado(cambios)


def _aplicar_renombrado(cambios: list[dict]):
    """Aplica el renombrado de archivos en ./organizar."""
    errores  = 0
    aplicados = 0

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
# Opción 2: Insertar nuevo ASMR
# ---------------------------------------------------------------------------

def opcion_insertar():
    print("\n  --- Insertar nuevo ASMR en la lista ---\n")

    if not verificar_carpeta():
        return

    todos    = listar_archivos('.m4a')
    archivos = []

    # Separar organizados (con número) de nuevos (sin número)
    organizados = []
    sin_numero  = []

    for nombre in todos:
        nombre_sin_ext = os.path.splitext(nombre)[0]
        numero = detectar_numero(nombre_sin_ext)
        if numero is not None:
            organizados.append({'nombre': nombre, 'numero': numero})
        else:
            sin_numero.append(nombre)

    # Ordenar los organizados por número actual
    organizados.sort(key=lambda x: x['numero'])

    print(f"  Archivos ya organizados : {len(organizados)}")
    print(f"  Archivos sin número     : {len(sin_numero)}")

    if not sin_numero:
        print("\n  No hay archivos nuevos para insertar.\n")
        return

    print()
    print("  Archivos sin número (a insertar):")
    for i, nombre in enumerate(sin_numero, 1):
        print(f"    [{i}] {nombre}")

    total_final   = len(organizados) + len(sin_numero)
    print(f"\n  La lista final tendrá {total_final} elemento(s).")
    print(f"  Posiciones válidas para inserción: 1 a {total_final}")

    # Recopilar posiciones deseadas para cada archivo nuevo
    inserciones = []   # lista de {'nombre': str, 'posicion': int}

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

    # -----------------------------------------------------------------------
    # Resolver inserciones mediante lista virtual
    # -----------------------------------------------------------------------
    lista_final = _resolver_inserciones(organizados, inserciones)

    # Leer/pedir metadatos de los archivos nuevos
    meta_nuevos = {}
    for ins in inserciones:
        ruta    = os.path.join(CARPETA_TRABAJO, ins['nombre'])
        meta    = leer_metadatos_m4a(ruta)
        artista = meta['artista'] or pedir_dato('artista', ins['nombre'])
        titulo  = meta['titulo']  or pedir_dato('título',  ins['nombre'])
        meta_nuevos[ins['nombre']] = {'artista': artista, 'titulo': titulo}

    # Construir lista de cambios para vista previa
    cambios = []
    for entrada in lista_final:
        numero_nuevo = entrada['numero']
        nombre_orig  = entrada['nombre']

        if nombre_orig in meta_nuevos:
            # Archivo nuevo
            m = meta_nuevos[nombre_orig]
            nombre_nuevo = construir_nombre_final(numero_nuevo, m['artista'], m['titulo']) + '.m4a'
        else:
            # Archivo ya organizado — obtener metadatos para reconstruir nombre
            ruta  = os.path.join(CARPETA_TRABAJO, nombre_orig)
            meta  = leer_metadatos_m4a(ruta)

            artista = meta['artista']
            titulo  = meta['titulo']

            # Si los metadatos fallan, intentar extraer del nombre actual
            if not artista or not titulo:
                artista, titulo = _extraer_meta_del_nombre(nombre_orig)

            if artista and titulo:
                nombre_nuevo = construir_nombre_final(numero_nuevo, artista, titulo) + '.m4a'
            else:
                # Caso raro: no se puede reconstruir, conservar nombre pero actualizar número
                nombre_nuevo = nombre_orig  # Se dejará igual, se avisa
                cambios.append({
                    'original': nombre_orig,
                    'nuevo':    nombre_orig,
                    'estado':   'dudoso',
                })
                continue

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
    Construye la lista virtual final.

    - `organizados` : [{'nombre': str, 'numero': int}, ...]  (ya ordenados)
    - `inserciones` : [{'nombre': str, 'posicion': int}, ...]

    Devuelve lista ordenada con {'nombre': str, 'numero': int} para cada elemento.
    """
    # Construir lista de slots: primero los organizados como slots sin número fijo
    lista = [{'nombre': e['nombre'], 'es_nuevo': False} for e in organizados]

    # Ordenar inserciones de menor a mayor posición para insertarlas en orden
    inserciones_ord = sorted(inserciones, key=lambda x: x['posicion'])

    # Insertar en la lista virtual (ajustando por cada inserción previa)
    offset = 0
    for ins in inserciones_ord:
        pos_real = ins['posicion'] - 1 + offset   # índice base-0 ajustado
        pos_real = max(0, min(pos_real, len(lista)))
        lista.insert(pos_real, {'nombre': ins['nombre'], 'es_nuevo': True})
        offset += 1

    # Asignar numeración correlativa desde 1
    for i, entrada in enumerate(lista, 1):
        entrada['numero'] = i

    return lista


def _extraer_meta_del_nombre(nombre: str) -> tuple[str | None, str | None]:
    """
    Intenta extraer artista y título de un nombre con formato '000 - Artista - Título.m4a'.
    Devuelve (artista, titulo) o (None, None).
    """
    nombre_sin_ext = os.path.splitext(nombre)[0]
    partes = nombre_sin_ext.split(' - ', 2)
    if len(partes) == 3:
        return partes[1].strip(), partes[2].strip()
    return None, None


def _aplicar_renombrado_seguro(cambios: list[dict]):
    """
    Aplica renombrados usando un nombre temporal para evitar colisiones
    cuando varios archivos intercambian nombres.
    """
    SUFIJO_TEMP = '.__tmp__'
    errores  = 0
    aplicados = 0

    # Paso 1: renombrar todo a temporal
    temporales = []
    for c in cambios:
        if c['original'] == c['nuevo'] or c['estado'] in ('sin_numero', 'dudoso'):
            continue
        ruta_orig = os.path.join(CARPETA_TRABAJO, c['original'])
        ruta_temp = ruta_orig + SUFIJO_TEMP
        try:
            os.rename(ruta_orig, ruta_temp)
            temporales.append({'temp': c['original'] + SUFIJO_TEMP, 'nuevo': c['nuevo']})
        except OSError as e:
            print(f"  [ERROR] No se pudo mover a temporal '{c['original']}': {e}")
            errores += 1

    # Paso 2: renombrar de temporal al nombre final
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
# Menú del módulo ASMR
# ---------------------------------------------------------------------------

def menu_asmr():
    while True:
        print()
        print("=" * 60)
        print("  MODULO ASMR")
        print("=" * 60)
        print("  1. Reformatear nombres")
        print("  2. Insertar nuevo ASMR en la lista")
        print("  3. Volver al menú principal")
        print("=" * 60)

        opcion = input("  Seleccioná una opción: ").strip()

        if opcion == '1':
            opcion_reformatear()
        elif opcion == '2':
            opcion_insertar()
        elif opcion == '3':
            break
        else:
            print("\n  Opción no válida. Ingresá 1, 2 o 3.\n")
