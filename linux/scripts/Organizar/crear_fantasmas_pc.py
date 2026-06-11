import os
from tkinter import Tk, filedialog

# Esto evita que se abra una ventana en blanco molesta de tkinter
Tk().withdraw()

# La dirección de destino se queda fija como querías
carpeta_destino = './Documentos/Organizar/ordenar'
os.makedirs(carpeta_destino, exist_ok=True)

# Abre el explorador de archivos para que elijas la carpeta con un clic
print("Selecciona la carpeta de origen en la ventana emergente...")
carpeta_origen = filedialog.askdirectory(title="Selecciona la carpeta de origen")

# Verificamos que el usuario sí haya seleccionado una carpeta y no haya cerrado la ventana
if carpeta_origen:
    for archivo in os.listdir(carpeta_origen):
        if archivo.endswith('.pdf'):
            ruta_fantasma = os.path.join(carpeta_destino, archivo)
            open(ruta_fantasma, 'w').close()

    print(f"\n¡Listo! Se crearon los archivos fantasma en {carpeta_destino}.")
else:
    print("\nOperación cancelada. No seleccionaste ninguna carpeta.")