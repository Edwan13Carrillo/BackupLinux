"""
modulo_bl_pdf.py — Módulo BL PDF del organizador multimedia.

Formatos de salida:
  Normal       : 101-120 · Nombre de la Obra.pdf
  Con fin      : 121-129 Fin · Nombre de la Obra.pdf
  Especial     : Especial / Especiales 001-002 · Nombre de la Obra.pdf
  Sin número   : Extra / Extras · Nombre de la Obra.pdf
  Con número   : Extra / Especial + 001 · Nombre de la Obra.pdf
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
    pedir_confirmacion,
    limpiar_pantalla
)

# Separador visual del formato final
SEP = '·'


# ---------------------------------------------------------------------------
# Normalización Unicode
# ---------------------------------------------------------------------------

def normalizar_unicode(texto: str) -> str:
    """
    Normaliza caracteres Unicode estilizados a ASCII.
    Aplica descomposición NFKD para unificar formas equivalentes (ej: ⓐ -> a)
    y separa los diacríticos para filtrarlos.
    """
    # Paso 0: Traductor manual para "Small Caps" (letras fonéticas/cirílicas)
    # que los fansubs usan para simular mayúsculas chiquitas.
    mapa_small_caps = str.maketrans(
        "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡʏᴢ", 
        "abcdefghijklmnopqrstuvwyz"
    )
    texto_traducido = texto.translate(mapa_small_caps)

    # Paso 1: NFKD convierte letras matemáticas/encerradas a normales y separa acentos
    texto_descompuesto = unicodedata.normalize('NFKD', texto_traducido)

    # Paso 2: Filtrar caracteres combinados (categoría 'Mn', que son los acentos)
    texto_limpio = ''.join(
        ch for ch in texto_descompuesto
        if unicodedata.category(ch) != 'Mn'
    )

    return texto_limpio

# ---------------------------------------------------------------------------
# Palabras clave y sus variantes
# ---------------------------------------------------------------------------

# Después de normalizar, estas regex detectan las palabras clave.
# Se aplican sobre el texto ya normalizado (ASCII-friendly).
_RE_ESPECIAL = re.compile(r'\b(especial(?:es)?)(?![a-zA-Z])', re.IGNORECASE)
_RE_EXTRA    = re.compile(r'\b(extra(?:s)?)(?![a-zA-Z])',     re.IGNORECASE)
_RE_FIN      = re.compile(r'\b(fin)(?![a-zA-Z])',             re.IGNORECASE)

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

def pre_limpiar_simbolos_lote(archivos: list[str]) -> dict[str, str]:
    """
    Escanea todos los archivos buscando símbolos raros. Si los hay, pregunta al 
    usuario si desea eliminarlos masivamente de los nombres en memoria.
    Devuelve un diccionario: { nombre_archivo_original : nombre_archivo_limpio }
    """
    simbolos_encontrados = set()
    nombres_limpios = {}

    # Recolectar todos los símbolos raros del lote
    for nombre in archivos:
        nombre_sin_ext = os.path.splitext(nombre)[0]
        for ch in nombre_sin_ext:
            if es_caracter_sospechoso(ch):
                simbolos_encontrados.add(ch)

    # Si no hay símbolos raros, devolvemos los nombres tal cual
    if not simbolos_encontrados:
        for nombre in archivos:
            nombres_limpios[nombre] = os.path.splitext(nombre)[0]
        return nombres_limpios

    # Si hay símbolos, preguntamos UNA sola vez
    print()
    print("  [!] ATENCIÓN: Se detectaron símbolos extraños en los nombres de este lote:")
    print(f"      Símbolos: {' '.join(simbolos_encontrados)}")
    
    while True:
        resp = input("  ¿Querés eliminarlos automáticamente de todos los archivos? (s/n): ").strip().lower()
        if resp in ('s', 'si', 'sí', 'y', 'yes'):
            ignorar = True
            break
        if resp in ('n', 'no'):
            ignorar = False
            break
        print("  Respondé s o n.")

    # Generamos el diccionario de nombres limpios (o intactos)
    for nombre in archivos:
        nombre_sin_ext = os.path.splitext(nombre)[0]
        if ignorar:
            # Borramos los símbolos raros
            for sim in simbolos_encontrados:
                nombre_sin_ext = nombre_sin_ext.replace(sim, '')
            # Limpiamos espacios dobles que hayan podido quedar al borrar el símbolo
            nombre_sin_ext = re.sub(r' {2,}', ' ', nombre_sin_ext).strip()
            
        nombres_limpios[nombre] = nombre_sin_ext

    return nombres_limpios

def _tiene_unicode_sospechoso(texto_original: str, texto_normalizado: str) -> str | None:
    sospechosos = [ch for ch in texto_original if es_caracter_sospechoso(ch)]
    if sospechosos:
        muestra = ''.join(dict.fromkeys(sospechosos))[:6]
        return f"Unicode estilizado detectado: '{muestra}' — revisar manualmente"
    return None

def es_caracter_sospechoso(ch: str) -> bool:
    """Devuelve True solo si el carácter es un Símbolo puro (decoraciones, emojis, etc)."""
    if ord(ch) < 128:
        return False
    
    cat = unicodedata.category(ch)
    
    # L=Letras, N=Números (incluye ¹²³), M=Marcas (ּ࣪), P=Puntuación (│), Z=Espacios
    if cat[0] in ('L', 'N', 'M', 'P', 'Z'):
        return False
        
    # Permitir líneas y cajas decorativas estándar
    if unicodedata.name(ch, '').startswith(('BOX DRAWINGS', 'BLOCK ELEMENT')):
        return False
        
    # Todo lo demás (Símbolos puros, emojis, etc) es sospechoso
    return True

def analizar_nombre(nombre_sin_ext: str) -> dict:
    """
    Analiza el nombre de un archivo PDF (sin extensión) y devuelve un dict con:
      {
        'tipo'    : 'normal' | 'fin' | 'especial' | 'extra' | 'dudoso',
        'inicio'  : int | None,
        'fin_num' : int | None,
        'etiqueta': str | None,
        'razon'   : str,
      }

    Filosofía:
      1. Normalizar Unicode.
      2. Si quedó Unicode sospechoso sin normalizar → DUDOSO inmediato.
      3. Buscar señales de tipo (Especial/Extra/Fin) y señales numéricas.
      4. Clasificar con lo encontrado, ignorar el resto del texto.
    """
    # Paso 1: normalizar
    nombre_norm = normalizar_unicode(nombre_sin_ext)

    # Paso 2: Unicode sospechoso — revisar ANTES de cualquier clasificación.
    # Si hay caracteres estilizados que no se convirtieron, podrían ser palabras
    # clave disfrazadas. No se ignoran silenciosamente.
    razon_unicode = _tiene_unicode_sospechoso(nombre_sin_ext, nombre_norm)
    if razon_unicode:
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'etiqueta': None,
            'razon': razon_unicode,
        }

    # Paso 3: palabras desconocidas que podrían indicar un tipo diferente
    if _PALABRAS_SOSPECHOSAS.search(nombre_norm):
        m = _PALABRAS_SOSPECHOSAS.search(nombre_norm)
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'etiqueta': None,
            'razon': f"Contiene palabra de tipo desconocido: '{m.group()}'",
        }

    # Paso 4: detectar palabras clave de tipo
    m_especial = _RE_ESPECIAL.search(nombre_norm)
    m_extra    = _RE_EXTRA.search(nombre_norm)
    m_fin      = _RE_FIN.search(nombre_norm)

    tiene_especial = bool(m_especial)
    tiene_extra    = bool(m_extra)
    tiene_fin      = bool(m_fin)

    # Conflicto real entre tipos → dudoso
    if (tiene_especial + tiene_extra + tiene_fin) > 1:
        return {
            'tipo': 'dudoso',
            'inicio': None, 'fin_num': None,
            'etiqueta': None,
            'razon': "Conflicto entre tipos detectados (Especial/Extra/Fin combinados)",
        }

    etiqueta = None
    if tiene_especial:
        etiqueta = m_especial.group(0).capitalize()
    elif tiene_extra:
        etiqueta = m_extra.group(0).capitalize()

    # Paso 5: buscar rango numérico primero, luego número suelto
    m_rango = _RE_RANGO.search(nombre_norm)
    m_num   = _RE_NUMERO.search(nombre_norm)

    # --- Extra / Especial sin número ---
    if (tiene_extra or tiene_especial) and not m_rango and not m_num:
        tipo = 'extra' if tiene_extra else 'especial'
        return {'tipo': tipo, 'inicio': None, 'fin_num': None, 'etiqueta': etiqueta, 'razon': ''}

    # --- Con rango ---
    if m_rango:
        inicio  = int(m_rango.group(1))
        fin_num = int(m_rango.group(2))
        if inicio > fin_num:
            return {
                'tipo': 'dudoso',
                'inicio': None, 'fin_num': None,
                'etiqueta': None,
                'razon': f"Rango incoherente: {inicio} > {fin_num}",
            }
        if tiene_especial:
            return {'tipo': 'especial', 'inicio': inicio, 'fin_num': fin_num, 'etiqueta': etiqueta, 'razon': ''}
        if tiene_extra:
            return {'tipo': 'extra',    'inicio': inicio, 'fin_num': fin_num, 'etiqueta': etiqueta, 'razon': ''}
        if tiene_fin:
            return {'tipo': 'fin',      'inicio': inicio, 'fin_num': fin_num, 'etiqueta': None, 'razon': ''}
        return     {'tipo': 'normal',   'inicio': inicio, 'fin_num': fin_num, 'etiqueta': None, 'razon': ''}

    # --- Con número suelto ---
    if m_num:
        numero = int(m_num.group(1))
        if tiene_especial:
            return {'tipo': 'especial', 'inicio': numero, 'fin_num': None, 'etiqueta': etiqueta, 'razon': ''}
        if tiene_extra:
            return {'tipo': 'extra',    'inicio': numero, 'fin_num': None, 'etiqueta': etiqueta, 'razon': ''}
        if tiene_fin:
            return {'tipo': 'fin',      'inicio': numero, 'fin_num': None, 'etiqueta': None, 'razon': ''}
        return     {'tipo': 'normal',   'inicio': numero, 'fin_num': None, 'etiqueta': None, 'razon': ''}

    # --- Sin ninguna señal numérica ---
    if tiene_extra:
        return {'tipo': 'extra', 'inicio': None, 'fin_num': None, 'etiqueta': etiqueta, 'razon': ''}
    if tiene_especial:
        return {'tipo': 'especial', 'inicio': None, 'fin_num': None, 'etiqueta': etiqueta, 'razon': ''}
    if tiene_fin:
        return {'tipo': 'fin', 'inicio': None, 'fin_num': None, 'etiqueta': None, 'razon': ''}

    return {'tipo': 'dudoso', 'inicio': None, 'fin_num': None, 'etiqueta': None, 'razon': "Sin número ni rango detectado"}


# ---------------------------------------------------------------------------
# Construcción de nombre final
# ---------------------------------------------------------------------------

def construir_nombre_final(analisis: dict, nombre_obra: str, es_lz: bool) -> str:
    """
    Construye el nombre final según el tipo detectado.
    Todos los números se formatean a 3 dígitos.

    Normal   : 001-010 · Nombre de la Obra.pdf  (o "005 · Obra.pdf" si es suelto)
    Fin      : 121-129 Fin · Nombre de la Obra.pdf
    Especial : Especial / Especiales 001-002 · Nombre de la Obra.pdf
    Extra    : Extra / Extras · Nombre de la Obra.pdf
    [LZ]     : agrega '[LZ]' antes de .pdf
    """
    sufijo_lz = ' [LZ]' if es_lz else ''
    tipo      = analisis['tipo']
    inicio    = analisis['inicio']
    fin_num   = analisis['fin_num']
    etiqueta  = analisis.get('etiqueta')

    def _rango(a, b):
        """Rango o número suelto, siempre con zero-padding a 3 dígitos."""
        if a is None:
            return None
        if b is not None:
            return f"{a:03d}-{b:03d}"
        return f"{a:03d}"

    rango = _rango(inicio, fin_num)

    if tipo == 'normal':
        nombre = f"{rango} {SEP} {nombre_obra}{sufijo_lz}.pdf"

    elif tipo == 'fin':
        if rango is None:
            nombre = f"Fin {SEP} {nombre_obra}{sufijo_lz}.pdf"
        else:
            nombre = f"{rango} Fin {SEP} {nombre_obra}{sufijo_lz}.pdf"

    elif tipo == 'especial':
        prefijo = etiqueta or 'Especial'
        if rango is None:
            nombre = f"{prefijo} {SEP} {nombre_obra}{sufijo_lz}.pdf"
        else:
            nombre = f"{prefijo} {rango} {SEP} {nombre_obra}{sufijo_lz}.pdf"

    elif tipo == 'extra':
        prefijo = etiqueta or 'Extra'
        if rango is None:
            nombre = f"{prefijo} {SEP} {nombre_obra}{sufijo_lz}.pdf"
        else:
            nombre = f"{prefijo} {rango} {SEP} {nombre_obra}{sufijo_lz}.pdf"

    else:
        nombre = None

    return nombre

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
    limpiar_pantalla()
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

    # NUEVO PASO: Limpieza global de símbolos
    nombres_pre_limpios = pre_limpiar_simbolos_lote(archivos)

    # Paso 3: analizar cada archivo
    procesables = []   # {'nombre', 'analisis', 'es_lz'}
    dudosos_raw = []   # {'nombre', 'razon'}

    for nombre in archivos:
        # AQUÍ ESTÁ LA MAGIA: usamos el nombre limpio (sin símbolos raros) para analizar
        nombre_para_analizar = nombres_pre_limpios[nombre]
        
        analisis = analizar_nombre(nombre_para_analizar)
        es_lz    = mapa_lz.get(nombre, False)

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
        print("=" * 30)
        print("  MODULO BL PDF")
        print("=" * 30)
        print("  1. Organizar PDFs")
        print("  2. Volver al menú principal")
        print("=" * 30)

        opcion = input("  Seleccioná una opción: ").strip()

        if opcion == '1':
            opcion_organizar()
        elif opcion == '2':
            limpiar_pantalla()
            break
        else:
            print("\n  Opción no válida. Ingresá 1 o 2.\n")
