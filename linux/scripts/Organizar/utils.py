import os
import re

CARPETA_TRABAJO = os.path.join('.', 'ordenar')

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

