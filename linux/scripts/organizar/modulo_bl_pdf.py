"""
modulo_bl_pdf.py — Módulo BL PDF del organizador multimedia.

Formatos de salida:
  Normal       : 101-120 · Nombre de la Obra.pdf
  Con fin      : 121-129 Fin · Nombre de la Obra.pdf
  Especial     : Especial 001-002 · Nombre de la Obra.pdf
  Sin número   : Extra · Nombre de la Obra.pdf
  Oficial [LZ] : 101-120 · Nombre de la Obra [LZ].pdf

Filosofía: CORRECTO solo si todo lo relevante se interpreta con confianza.
           DUDOSO ante cualquier ambigüedad o texto sobrante importante.
"""

import os
import re
import unicodedata

from utils import (
    CARPETA_TRABAJO,
    verificar_carpeta,
    listar_archivos,
    mostrar_vista_previa,
    pedir_confirmacion,
)

# Separador visual del formato final
SEP = '·'


# ---------------------------------------------------------------------------
# Normalización Unicode
# ---------------------------------------------------------------------------

# Tabla de dígitos Unicode estilizados → ASCII
# Cubre: matemáticos en negrita, itálica, sans-serif, doble barra, etc.
_DIGITOS_UNICODE: dict[int, str] = {}

# Rangos de dígitos estilizados en Unicode (Mathematical Alphanumeric Symbols)
_RANGOS_DIGITOS = [
    0x1D7CE,  # Mathematical Bold Digit Zero
    0x1D7D8,  # Mathematical Double-Struck Digit Zero
    0x1D7E2,  # Mathematical Sans-Serif Digit Zero
    0x1D7EC,  # Mathematical Sans-Serif Bold Digit Zero
    0x1D7F6,  # Mathematical Monospace Digit Zero
]
for _base in _RANGOS_DIGITOS:
    for _i in range(10):
        _DIGITOS_UNICODE[_base + _i] = str(_i)

# Superíndices numéricos
_SUPERINDICES = {
    ord('⁰'): '0', ord('¹'): '1', ord('²'): '2', ord('³'): '3',
    ord('⁴'): '4', ord('⁵'): '5', ord('⁶'): '6', ord('⁷'): '7',
    ord('⁸'): '8', ord('⁹'): '9',
}
_DIGITOS_UNICODE.update(_SUPERINDICES)

# Tabla de letras estilizadas → ASCII (para palabras clave)
# Se construye mapeando cada variante estilizada conocida carácter a carácter.
# Palabras clave objetivo: Especial, Extra, Fin
_LETRAS_UNICODE: dict[int, str] = {}

# Rangos de letras mayúsculas estilizadas (Mathematical Alphanumeric Symbols)
# Negrita, Itálica, Negrita Itálica, Script, Fraktur, Doble barra, Sans-serif, etc.
_RANGOS_MAYUS = [
    (0x1D400, 'A'),  # Bold
    (0x1D434, 'A'),  # Italic
    (0x1D468, 'A'),  # Bold Italic
    (0x1D49C, 'A'),  # Script (con huecos)
    (0x1D4D0, 'A'),  # Bold Script
    (0x1D504, 'A'),  # Fraktur (con huecos)
    (0x1D538, 'A'),  # Double-struck (con huecos)
    (0x1D56C, 'A'),  # Bold Fraktur
    (0x1D5A0, 'A'),  # Sans-serif
    (0x1D5D4, 'A'),  # Sans-serif Bold
    (0x1D608, 'A'),  # Sans-serif Italic
    (0x1D63C, 'A'),  # Sans-serif Bold Italic
    (0x1D670, 'A'),  # Monospace
]
_RANGOS_MINUS = [
    (0x1D41A, 'a'),  # Bold
    (0x1D44E, 'a'),  # Italic
    (0x1D482, 'a'),  # Bold Italic
    (0x1D4B6, 'a'),  # Script (con huecos)
    (0x1D4EA, 'a'),  # Bold Script
    (0x1D518, 'a'),  # Fraktur (con huecos)
    (0x1D552, 'a'),  # Double-struck
    (0x1D586, 'a'),  # Bold Fraktur
    (0x1D5BA, 'a'),  # Sans-serif
    (0x1D5EE, 'a'),  # Sans-serif Bold
    (0x1D622, 'a'),  # Sans-serif Italic
    (0x1D656, 'a'),  # Sans-serif Bold Italic
    (0x1D68A, 'a'),  # Monospace
]

for _base, _letra_base in _RANGOS_MAYUS:
    for _i in range(26):
        _LETRAS_UNICODE[_base + _i] = chr(ord(_letra_base) + _i)

for _base, _letra_base in _RANGOS_MINUS:
    for _i in range(26):
        _LETRAS_UNICODE[_base + _i] = chr(ord(_letra_base) + _i)

# Tabla combinada
_TABLA_UNICODE: dict[int, str] = {**_DIGITOS_UNICODE, **_LETRAS_UNICODE}


def normalizar_unicode(texto: str) -> str:
    """
    Normaliza caracteres Unicode estilizados a ASCII.
    Aplica:
      1. Descomposición NFC para unificar formas equivalentes.
      2. Mapeo carácter a carácter usando la tabla de estilizados.
      3. Transliteración de caracteres con diacríticos via NFKD si siguen sin mapearse.
    """
    # Paso 1: NFC
    texto = unicodedata.normalize('NFC', texto)

    # Paso 2: mapeo de estilizados
    resultado = []
    for ch in texto:
        cp = ord(ch)
        if cp in _TABLA_UNICODE:
            resultado.append(_TABLA_UNICODE[cp])
        else:
            resultado.append(ch)
    texto = ''.join(resultado)

    # Paso 3: NFKD para caracteres con diacríticos restantes
    # Ej: é → e + combining accent → solo 'e' al filtrar non-ASCII combining marks
    normalizado = unicodedata.normalize('NFKD', texto)
    texto = ''.join(
        ch for ch in normalizado
        if unicodedata.category(ch) != 'Mn' or ord(ch) < 128
    )

    return texto


# ---------------------------------------------------------------------------
# Palabras clave y sus variantes
# ---------------------------------------------------------------------------

# Después de normalizar, estas regex detectan las palabras clave.
# Se aplican sobre el texto ya normalizado (ASCII-friendly).
_RE_ESPECIAL = re.compile(r'\bEspecial\b', re.IGNORECASE)
_RE_EXTRA    = re.compile(r'\bExtra\b',    re.IGNORECASE)
_RE_FIN      = re.compile(r'\bFin\b',      re.IGNORECASE)

# Palabras que el programa NO conoce y que podrían significar algo
# Si aparecen, el archivo va a DUDOSO.
_PALABRAS_SOSPECHOSAS = re.compile(
    r'\b(bonus|side\s*story|historia\s+alternativa|omake|gaiden|spin[- ]?off)\b',
    re.IGNORECASE,
)

# Rango numérico: "101-120" o "001-002"
_RE_RANGO  = re.compile(r'(\d+)\s*[-–]\s*(\d+)')
# Número suelto: "001" o "15"
_RE_NUMERO = re.compile(r'(\d+)')


# ---------------------------------------------------------------------------
# Análisis de nombre
# ---------------------------------------------------------------------------

def analizar_nombre(nombre_sin_ext: str) -> dict:
    """
    Analiza el nombre de un archivo PDF (sin extensión) y devuelve un dict con:
      {
        'tipo'    : 'normal' | 'fin' | 'especial' | 'extra' | 'dudoso',
        'inicio'  : int | None,   — primer número del rango
        'fin_num' : int | None,   — segundo número del rango
        'razon'   : str,          — explicación si es dudoso
      }

    Regla central: DUDOSO ante cualquier ambigüedad o texto sobrante importante.
    """
    # Normalizar primero
    nombre_norm = normalizar_unicode(nombre_sin_ext)

    # Detectar palabras sospechosas desconocidas → dudoso inmediato
    if _PALABRAS_SOSPECHOSAS.search(nombre_norm):
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'razon': f"Contiene palabra no reconocida: '{_PALABRAS_SOSPECHOSAS.search(nombre_norm).group()}'",
        }

    tiene_especial = bool(_RE_ESPECIAL.search(nombre_norm))
    tiene_extra    = bool(_RE_EXTRA.search(nombre_norm))
    tiene_fin      = bool(_RE_FIN.search(nombre_norm))

    # Ambigüedad entre tipos
    tipos_detectados = sum([tiene_especial, tiene_extra, tiene_fin])
    if tipos_detectados > 1:
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'razon': "Conflicto entre palabras clave (Especial/Extra/Fin combinadas)",
        }

    # Detectar rango numérico
    m_rango = _RE_RANGO.search(nombre_norm)

    if tiene_extra and not m_rango:
        # Extra sin número → "Extra · Obra.pdf"
        # Verificar que no haya ningún número suelto que podría ser relevante
        if _RE_NUMERO.search(nombre_norm):
            return {
                'tipo': 'dudoso',
                'inicio': None, 'fin_num': None,
                'razon': "Extra con número suelto sin rango claro",
            }
        return {'tipo': 'extra', 'inicio': None, 'fin_num': None, 'razon': ''}

    if not m_rango:
        # Sin rango: buscar número suelto
        m_num = _RE_NUMERO.search(nombre_norm)
        if not m_num:
            return {
                'tipo': 'dudoso',
                'inicio': None, 'fin_num': None,
                'razon': "Sin número ni rango detectado",
            }
        # Número suelto sin rango → dudoso (no hay forma segura de saber si
        # es un capítulo único o algo más; preferimos que el usuario lo revise)
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'razon': f"Número suelto '{m_num.group()}' sin rango — revisar manualmente",
        }

    inicio  = int(m_rango.group(1))
    fin_num = int(m_rango.group(2))

    # Validar coherencia del rango
    if inicio > fin_num:
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'razon': f"Rango incoherente: {inicio} > {fin_num}",
        }

    # Verificar texto sobrante relevante DESPUÉS de quitar lo ya interpretado
    texto_restante = nombre_norm
    texto_restante = _RE_RANGO.sub('', texto_restante)
    if tiene_especial:
        texto_restante = _RE_ESPECIAL.sub('', texto_restante)
    if tiene_extra:
        texto_restante = _RE_EXTRA.sub('', texto_restante)
    if tiene_fin:
        texto_restante = _RE_FIN.sub('', texto_restante)

    # Limpiar separadores y espacios residuales del texto restante
    texto_restante = re.sub(r'[\s\-_.·\[\](),]+', '', texto_restante)

    # Si queda texto significativo (más de 1 carácter no trivial), es dudoso
    if len(texto_restante) > 1:
        return {
            'tipo': 'dudoso',
            'inicio': inicio, 'fin_num': fin_num,
            'razon': f"Texto sobrante no interpretado: '{texto_restante}'",
        }

    # Clasificar tipo final
    if tiene_especial:
        return {'tipo': 'especial', 'inicio': inicio, 'fin_num': fin_num, 'razon': ''}
    if tiene_fin:
        return {'tipo': 'fin',      'inicio': inicio, 'fin_num': fin_num, 'razon': ''}

    # Normal
    return {'tipo': 'normal', 'inicio': inicio, 'fin_num': fin_num, 'razon': ''}


# ---------------------------------------------------------------------------
# Construcción de nombre final
# ---------------------------------------------------------------------------

def construir_nombre_final(analisis: dict, nombre_obra: str, es_lz: bool) -> str:
    """
    Construye el nombre final según el tipo detectado.

    Normal    : 101-120 · Nombre de la Obra.pdf
    Fin       : 121-129 Fin · Nombre de la Obra.pdf
    Especial  : Especial 001-002 · Nombre de la Obra.pdf
    Extra     : Extra · Nombre de la Obra.pdf
    [LZ]      : agrega '[LZ]' antes de .pdf
    """
    sufijo_lz = ' [LZ]' if es_lz else ''
    tipo      = analisis['tipo']
    inicio    = analisis['inicio']
    fin_num   = analisis['fin_num']

    if tipo == 'normal':
        rango = f"{inicio}-{fin_num}"
        nombre = f"{rango} {SEP} {nombre_obra}{sufijo_lz}.pdf"

    elif tipo == 'fin':
        rango = f"{inicio}-{fin_num}"
        nombre = f"{rango} Fin {SEP} {nombre_obra}{sufijo_lz}.pdf"

    elif tipo == 'especial':
        rango = f"{inicio:03d}-{fin_num:03d}"
        nombre = f"Especial {rango} {SEP} {nombre_obra}{sufijo_lz}.pdf"

    elif tipo == 'extra':
        nombre = f"Extra {SEP} {nombre_obra}{sufijo_lz}.pdf"

    else:
        # Dudoso: no debería llegar aquí, pero por seguridad
        nombre = None

    return nombre


def nombre_ya_correcto(nombre_sin_ext: str, nombre_obra: str, es_lz: bool) -> bool:
    """
    Verifica si el nombre actual ya coincide exactamente con el formato esperado,
    para evitar marcarlo como 'formato_incorrecto' cuando ya está bien.
    """
    analisis = analizar_nombre(nombre_sin_ext)
    if analisis['tipo'] == 'dudoso':
        return False
    nombre_esperado = construir_nombre_final(analisis, nombre_obra, es_lz)
    if nombre_esperado is None:
        return False
    return (nombre_sin_ext + '.pdf') == nombre_esperado


# ---------------------------------------------------------------------------
# Gestión de [LZ]
# ---------------------------------------------------------------------------

def preguntar_lz(archivos: list[str]) -> dict[str, bool]:
    """
    Pregunta al usuario cómo manejar la marca [LZ].
    Devuelve dict: nombre_archivo → True/False
    """
    print()
    print("  ¿Cómo manejamos la marca [LZ] (traducción oficial)?")
    print("  1. Todos los archivos son [LZ]")
    print("  2. Ninguno es [LZ]")
    print("  3. Decidir uno por uno")

    while True:
        resp = input("  Opción (1/2/3): ").strip()
        if resp == '1':
            return {nombre: True for nombre in archivos}
        if resp == '2':
            return {nombre: False for nombre in archivos}
        if resp == '3':
            return _preguntar_lz_individual(archivos)
        print("  Ingresá 1, 2 o 3.")


def _preguntar_lz_individual(archivos: list[str]) -> dict[str, bool]:
    """Pregunta [LZ] archivo por archivo."""
    resultado = {}
    print()
    for nombre in archivos:
        while True:
            resp = input(f"  ¿'{nombre}' es [LZ]? (s/n): ").strip().lower()
            if resp in ('s', 'si', 'sí', 'y', 'yes'):
                resultado[nombre] = True
                break
            if resp in ('n', 'no'):
                resultado[nombre] = False
                break
            print("  Respondé s o n.")
    return resultado


# ---------------------------------------------------------------------------
# Resolución de dudosos
# ---------------------------------------------------------------------------

def resolver_dudosos_pdf(dudosos: list[dict]) -> dict[str, str | None]:
    """
    Para cada archivo dudoso, muestra el nombre y la razón, y le pide al
    usuario que escriba el nombre final manualmente o lo salte.

    Devuelve dict: nombre_original → nombre_nuevo (str con .pdf) o None (saltado).
    """
    resultado = {}

    print()
    print("=" * 60)
    print("  ARCHIVOS DUDOSOS — se requiere intervención")
    print("=" * 60)
    print("  Para cada archivo podés escribir el nombre final completo")
    print(f"  (sin extensión, el programa agrega .pdf)")
    print("  o presioná Enter para saltarlo.")
    print()

    for item in dudosos:
        nombre   = item['nombre']
        razon    = item['razon']
        print(f"  Archivo : {nombre}")
        print(f"  Razón   : {razon}")

        while True:
            resp = input("  Nombre final (sin .pdf) o Enter para saltar: ").strip()
            if resp == '':
                resultado[nombre] = None
                print("  → Saltado.\n")
                break
            if resp:
                resultado[nombre] = resp + '.pdf'
                print(f"  → Nombre asignado: {resp}.pdf\n")
                break

    return resultado


# ---------------------------------------------------------------------------
# Vista previa específica para PDF
# ---------------------------------------------------------------------------

def mostrar_vista_previa_pdf(cambios: list[dict], advertencias: list[str] = None):
    """
    Vista previa adaptada al módulo PDF.
    Igual estructura que mostrar_vista_previa de utils pero con etiquetas propias.
    """
    print()
    print("=" * 60)
    print("  VISTA PREVIA DE CAMBIOS — BL PDF")
    print("=" * 60)

    if advertencias:
        print()
        print("  ADVERTENCIAS:")
        for adv in advertencias:
            print(f"  [!] {adv}")

    con_cambio = [c for c in cambios if c['estado'] == 'formato_incorrecto']
    sin_cambio = [c for c in cambios if c['estado'] == 'correcto']
    dudosos    = [c for c in cambios if c['estado'] == 'dudoso']

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

    if dudosos:
        print(f"  Archivos DUDOSOS ({len(dudosos)}) — se omiten:")
        for c in dudosos:
            razon = c.get('razon', '')
            print(f"    [!] {c['original']}")
            if razon:
                print(f"        Razón: {razon}")
        print()

    print("=" * 60)
    print(f"  Total a renombrar : {len(con_cambio)}")
    print(f"  Sin cambios       : {len(sin_cambio)}")
    print(f"  Dudosos omitidos  : {len(dudosos)}")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Aplicar renombrado
# ---------------------------------------------------------------------------

def _aplicar_renombrado(cambios: list[dict]):
    """Aplica renombrado via temporal para evitar colisiones."""
    SUFIJO_TEMP = '.__tmp__'
    aplicados   = 0
    errores     = 0

    temporales = []
    for c in cambios:
        if c['estado'] != 'formato_incorrecto':
            continue
        ruta_orig = os.path.join(CARPETA_TRABAJO, c['original'])
        ruta_temp = ruta_orig + SUFIJO_TEMP
        try:
            os.rename(ruta_orig, ruta_temp)
            temporales.append({'temp': c['original'] + SUFIJO_TEMP, 'nuevo': c['nuevo']})
        except OSError as e:
            print(f"  [ERROR] No se pudo mover a temporal '{c['original']}': {e}")
            errores += 1

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
# Flujo principal del módulo
# ---------------------------------------------------------------------------

def opcion_organizar():
    print("\n  --- Organizar BL PDF ---\n")

    if not verificar_carpeta():
        return

    archivos = listar_archivos('.pdf')

    if not archivos:
        print("  No se encontraron archivos .pdf en ./organizar\n")
        return

    print(f"  Archivos .pdf encontrados: {len(archivos)}")

    # Paso 1: nombre de la obra
    print()
    nombre_obra = input("  Nombre de la obra: ").strip()
    while not nombre_obra:
        print("  El nombre no puede estar vacío.")
        nombre_obra = input("  Nombre de la obra: ").strip()

    # Paso 2: gestión [LZ]
    mapa_lz = preguntar_lz(archivos)

    # Paso 3: analizar cada archivo
    procesables = []   # {'nombre', 'analisis', 'es_lz'}
    dudosos_raw = []   # {'nombre', 'razon'}

    for nombre in archivos:
        nombre_sin_ext = os.path.splitext(nombre)[0]
        analisis       = analizar_nombre(nombre_sin_ext)
        es_lz          = mapa_lz.get(nombre, False)

        if analisis['tipo'] == 'dudoso':
            dudosos_raw.append({'nombre': nombre, 'razon': analisis['razon']})
        else:
            procesables.append({'nombre': nombre, 'analisis': analisis, 'es_lz': es_lz})

    # Paso 4: resolver dudosos
    resolucion_dudosos = {}
    if dudosos_raw:
        print(f"\n  Se encontraron {len(dudosos_raw)} archivo(s) dudoso(s).")
        resolucion_dudosos = resolver_dudosos_pdf(dudosos_raw)

    # Paso 5: construir cambios
    cambios      = []
    advertencias = []

    for p in procesables:
        nombre_orig  = p['nombre']
        nombre_sin_ext = os.path.splitext(nombre_orig)[0]
        nombre_nuevo = construir_nombre_final(p['analisis'], nombre_obra, p['es_lz'])

        if nombre_nuevo is None:
            advertencias.append(f"No se pudo construir nombre para: {nombre_orig}")
            continue

        if nombre_orig == nombre_nuevo:
            estado = 'correcto'
        else:
            estado = 'formato_incorrecto'

        cambios.append({
            'original': nombre_orig,
            'nuevo':    nombre_nuevo,
            'estado':   estado,
            'razon':    '',
        })

    # Agregar dudosos resueltos
    for item in dudosos_raw:
        nombre    = item['nombre']
        nuevo     = resolucion_dudosos.get(nombre)
        if nuevo:
            cambios.append({
                'original': nombre,
                'nuevo':    nuevo,
                'estado':   'formato_incorrecto',
                'razon':    '',
            })
        else:
            cambios.append({
                'original': nombre,
                'nuevo':    nombre,
                'estado':   'dudoso',
                'razon':    item['razon'],
            })

    # Paso 6: vista previa
    mostrar_vista_previa_pdf(cambios, advertencias if advertencias else None)

    hay_cambios = any(c['estado'] == 'formato_incorrecto' for c in cambios)
    if not hay_cambios:
        print("  No hay cambios que aplicar.\n")
        return

    if not pedir_confirmacion():
        print("\n  Operación cancelada. No se modificó ningún archivo.\n")
        return

    _aplicar_renombrado(cambios)


# ---------------------------------------------------------------------------
# Menú del módulo BL PDF
# ---------------------------------------------------------------------------

def menu_bl_pdf():
    while True:
        print()
        print("=" * 60)
        print("  MODULO BL PDF")
        print("=" * 60)
        print("  1. Organizar PDFs")
        print("  2. Volver al menú principal")
        print("=" * 60)

        opcion = input("  Seleccioná una opción: ").strip()

        if opcion == '1':
            opcion_organizar()
        elif opcion == '2':
            break
        else:
            print("\n  Opción no válida. Ingresá 1 o 2.\n")
