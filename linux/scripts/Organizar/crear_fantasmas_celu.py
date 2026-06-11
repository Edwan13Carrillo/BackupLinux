import os

# Detecta automáticamente la ubicación del script (asumiendo que vive en Documents)
ruta_script = os.path.dirname(os.path.abspath(__file__))
base_dir = ruta_script if os.path.basename(ruta_script) == "Documents" else os.getcwd()

# Destino fijo
destino_base = os.path.join(base_dir, 'Organizar', 'ordenar')

def navegador_carpetas():
    dir_actual = base_dir
    while True:
        # Mostramos la ruta de forma amigable limpiando la raíz
        ruta_relativa = os.path.relpath(dir_actual, base_dir)
        print(f"\n📂 Ubicación actual: Documents/{'' if ruta_relativa == '.' else ruta_relativa}")
        print("-" * 60)
        print(" [0] 🚀 PROCESAR ESTA CARPETA (Incluye todos los archivos y subcarpetas)")
        
        try:
            # Listamos solo directorios, ignorando carpetas ocultas y la de destino
            subdirs = [d for d in os.listdir(dir_actual) 
                       if os.path.isdir(os.path.join(dir_actual, d)) 
                       and d != 'Organizar' 
                       and not d.startswith('.')]
            subdirs.sort()
        except Exception as e:
            print(f"❌ Error al leer el directorio: {e}")
            return None

        # Imprimir el menú de subcarpetas
        for i, d in enumerate(subdirs, start=1):
            print(f" [{i}] 📁 {d}/")
            
        print("-" * 60)
        print(" [B] ↩️ Volver atrás   |   [X] ❌ Salir")
        
        opcion = input("\nSelecciona una opción: ").strip().lower()
        
        if opcion == '0':
            return dir_actual
        elif opcion == 'b':
            if dir_actual == base_dir:
                print("⚠️ Ya estás en la raíz de Documents.")
            else:
                dir_actual = os.path.dirname(dir_actual)
        elif opcion == 'x':
            return None
        else:
            try:
                idx = int(opcion) - 1
                if 0 <= idx < len(subdirs):
                    dir_actual = os.path.join(dir_actual, subdirs[idx])
                else:
                    print("⚠️ Número fuera de rango.")
            except ValueError:
                print("⚠️ Opción no válida.")

def crear_archivos_fantasma(carpeta_origen):
    conteo = 0
    # os.walk recorre la carpeta que seleccionaste
    for root, dirs, files in os.walk(carpeta_origen):
        # Medida de seguridad: evitar entrar a la carpeta de organización
        if 'Organizar' in dirs:
            dirs.remove('Organizar')
            
        for archivo in files:
            ruta_completa_origen = os.path.join(root, archivo)
            
            # CAMBIO AQUÍ: Ahora calculamos la ruta relativa desde la carpeta SELECCIONADA (origen)
            # y no desde la raíz de Documents.
            ruta_relativa_archivo = os.path.relpath(ruta_completa_origen, carpeta_origen)
            
            # El destino final ahora será plano o solo con el contenido interno de 'obra'
            ruta_fantasma = os.path.join(destino_base, ruta_relativa_archivo)
            
            # Crea subcarpetas internas si 'obra' llegara a tener carpetas adentro
            os.makedirs(os.path.dirname(ruta_fantasma), exist_ok=True)
            
            # Crea el archivo vacío
            open(ruta_fantasma, 'w').close()
            conteo += 1
            
    return conteo

if __name__ == "__main__":
    print("=== ASISTENTE DE ARCHIVOS FANTASMA ===")
    origen = navegador_carpetas()
    
    if origen:
        print("\nGenerando estructura... Por favor espera.")
        total_archivos = crear_archivos_fantasma(origen)
        print(f"\n¡Listo! Se clonó la estructura y se crearon {total_archivos} archivos fantasma en:")
        print(f"📍 {destino_base}")
    else:
        print("\nProceso cancelado.")