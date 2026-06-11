"""
main.py — Organizador de archivos multimedia.
Menú principal con módulos: ASMR, Música, Anime, BL PDF.
"""

from modulo_asmr    import menu_asmr
from modulo_musica  import menu_musica
from modulo_anime   import menu_anime
from modulo_bl_pdf  import menu_bl_pdf

def menu_principal():
    while True:
        print()
        print("=" * 30)
        print("  ORGANIZADOR MULTIMEDIA")
        print("=" * 30)
        print("  1. ASMR")
        print("  2. Musica")
        print("  3. Anime")
        print("  4. BL PDF")
        print("  5. Salir")
        print("=" * 30)

        opcion = input("  Seleccioná una opción: ").strip()

        if opcion == '1':
            menu_asmr()
        elif opcion == '2':
            menu_musica()
        elif opcion == '3':
            menu_anime()
        elif opcion == '4':
            menu_bl_pdf()
        elif opcion == '5':
            print("\n  ¡Hasta luego!\n")
            break
        else:
            print("\n  Opción no válida. Ingresá 1, 2, 3, 4 o 5.\n")


if __name__ == '__main__':
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n  ¡Hasta luego! (Ejecución cancelada por el usuario).\n")
