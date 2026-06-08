# 🐧 Linux Backup & Restore Kit

Mi colección personal de configuraciones, scripts, recursos y notas para reinstalar Linux sin tener que volver a configurar todo desde cero.

La idea es simple: después de una instalación limpia, ejecutar el setup y recuperar gran parte de mi entorno habitual de forma automática.

## ✨ ¿Qué incluye?

* Configuraciones de Linux y KDE.
* Wallpapers e iconos.
* Fuentes personalizadas.
* Scripts útiles.
* Herramientas de organización de archivos.
* Configuración y notas para gaming.
* Recursos de Minecraft.
* Guía personal de reinstalación.

---

# 🚀 Uso rápido

```bash
chmod +x setup.sh
./setup.sh
```

El script principal muestra un menú donde puedes:

* Instalar todo de una vez.
* Elegir componentes específicos.
* Restaurar configuraciones individuales.

---

# 📂 Estructura del proyecto

## setup.sh

El corazón del proyecto.

Se encarga de mostrar el menú principal y automatizar la instalación o restauración de los distintos componentes.

---

## docs/

Documentación y guías.

### Contenido

* Guía de reinstalación de Linux en PDF.

---

## assets/

Recursos visuales para el escritorio.

### wallpapers/

Fondos de pantalla.

### icons/

Paquetes de iconos y recursos gráficos.

---

## gaming/

Todo lo relacionado con juegos.

### notes/

Notas, configuraciones y parámetros útiles para Steam y otros juegos.

### mc_skins/

Colección de skins de Minecraft.

---

## linux/

Configuraciones y herramientas específicas de Linux.

### configs/

Archivos que el setup organiza automáticamente en sus ubicaciones correspondientes.

Incluye configuraciones como:

* `.local`
* `kdedefaults`
* `alacritty`
* `fastfetch`
* y otras configuraciones personales.

El objetivo es recuperar el entorno habitual sin copiar archivos manualmente.

---

### scripts/

Scripts utilitarios.

#### YtDlp/

Herramientas relacionadas con yt-dlp.

**ytdlp.sh**

Script para facilitar descargas mediante yt-dlp.

---

#### organizar/

Sistema de organización automática de archivos.

Incluye varios scripts Python para organizar:

* Música
* ASMR
* Anime
* PDF BL

El archivo principal es:

```text
main.py
```

que coordina el resto de módulos.

##### orden/

Archivos auxiliares utilizados por el sistema de organización.

---

### fonts/

Fuentes personalizadas utilizadas en el sistema.

---

# ⚠️ Nota

Este proyecto está pensado principalmente para mi flujo de trabajo personal.

Puede servir como referencia para crear tu propio sistema de backup y restauración, pero probablemente necesites adaptar algunas rutas, configuraciones o scripts a tu entorno.

Si algo explota, al menos los wallpapers seguirán estando bonitos.
