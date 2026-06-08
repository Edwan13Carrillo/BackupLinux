# 🐧 My Linux Backup & Dotfiles System

¡Bienvenido! Este repositorio es mi santo grial para no mover un solo dedo (o casi ninguno) cada vez que reinstalo Linux o quiero sincronizar mi entorno. Aquí está concentrado todo mi flujo de trabajo, configuraciones visuales, scripts de automatización y hasta mis skins de Minecraft. 

Olvídate de configurar todo a mano durante tres horas. Un comando y a jugar.

---

## 🛠️ ¿Qué hay aquí dentro?

El repositorio está organizado de forma que todo sea modular y fácil de encontrar:

```text
├── 📄 setup.sh               # El cerebro del asunto (Script principal)
├── 📂 docs/                  # Guías de supervivencia
│   └── 📑 reinstalacion.pdf  # Mi guía paso a paso para revivir el sistema
├── 📂 assets/                # El toque visual
│   ├── 🖼️ wallpapers/       # Fondos de pantalla épicos
│   └── 🎨 icons/             # Packs de iconos personalizados
├── 📂 gaming/                # Zona de vicio
│   ├── 📝 notes              # Parámetros de lanzamiento de Steam y configs
│   └── 👕 mc_skins/          # Mis skins de Minecraft
└── 📂 linux/                 # El núcleo del entorno
    ├── ⚙️ configs/            # Alacritty, Fastfetch, KDE defaults, .local, etc.
    ├── 📜 scripts/            # Automatización pura
    │   ├── 📹 YtDlp/         # Descargas rápidas con yt-dlp
    │   └── 🗂️ organizar/     # Scripts en Python para ordenar mi caos
    └── 🔤 fonts/              # Tipografías esenciales para la terminal y el sistema

```

---

## 🚀 Cómo usar el `setup.sh`

El archivo `setup.sh` es el que hace toda la magia por ti. Cuenta con un menú interactivo en la terminal para que decidas qué quieres hacer:

* **Modo Full Send:** Instala y organiza absolutamente todo de un solo golpe. Ideal para instalaciones limpias.
* **Modo Quirúrgico:** ¿Solo quieres actualizar tus configs de Alacritty o mover los scripts? Elige la opción específica en el menú y listo.

Para ejecutarlo, abre tu terminal y lanza:

```bash
chmod +x setup.sh
./setup.sh

```

---

## 🔍 Detalle de los módulos

### ⚙️ Configuro-Sapiens (`linux/configs/`)

El script se encarga de mover automáticamente estas carpetas a su lugar correspondiente (`~/.config`, `~/.local`, etc.). Incluye la configuración optimizada para:

* **Alacritty:** Mi emulador de terminal hiperrápido.
* **Fastfetch:** Para presumir el sistema cada vez que abro la terminal.
* **KDE Defaults / Local:** Ajustes del entorno de escritorio para que luzca exactamente como me gusta desde el primer segundo.

### 🐍 Los Organizadores Automáticos (`linux/scripts/`)

Dentro de la carpeta `organizar/` hay un ecosistema de archivos `.py` dedicados a mantener mis carpetas limpias.

* **¿Cómo funciona?** Tú solo ejecutas el archivo `main.py` (que ya está conectado con todo) y el sistema ordenará automáticamente tus archivos de **Anime, Música, ASMR y PDFs BL**.
* La subcarpeta `orden/` contiene las reglas y la lógica interna que usa el sistema para clasificar todo en su lugar correcto.
* También incluye `ytdlp.sh` en su respectiva carpeta para bajar contenido multimedia sin pelear con comandos largos.

### 🎮 Gaming Section (`gaming/`)

Porque no todo es programar y automatizar:

* **`notes`:** Un recordatorio con los parámetros de lanzamiento (Launch Options) ideales para Steam y configuraciones optimizadas de juegos para exprimir cada FPS.
* **`mc_skins/`:** Mis skins de Minecraft guardadas y listas para usar.

---

> 💡 **Nota mental:** Si estás reinstalando el sistema desde cero, abre primero el PDF en `docs/reinstalacion.pdf`. Ahí está el paso a paso detallado para no romper nada en el proceso.
