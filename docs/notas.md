# Notas y extras

Cosas que no son parte del setup del sistema en sí, pero que quiero tener a la mano.

---

## 🎌 Anime — fuentes y calidad

- **Nyaa** — anime con buena calidad de video.
- **Nensaysubs** — subtítulos oficiales.
- **Nekomitai** — doblajes latinos.

### Listas de extensión para Hayase

| Fuente | Link |
|---|---|
| Wotaku | https://exten.pages.dev/index.json |
| Grok | https://raw.githubusercontent.com/anh9000/anitorrent/main/hayase/index.json |

---

## 🛠️ Solución de problemas

### KDE Connect — el envío Teléfono → Laptop no funciona

**Causa:** restricciones de almacenamiento (*Scoped Storage*) en Android.

**Solución:**
1. Abrir la app KDE Connect en el teléfono → *Ajustes de plugins* → *Compartir y recibir*.
2. Asignar manualmente un **Directorio de destino** (ej. la carpeta `Descargas`).
3. *(Si sigue fallando)* Abrir los puertos del firewall en Linux: `1714:1764` (TCP/UDP).

### Millennium + NEVKO-UI (Steam) — no lo hace `setup.sh`

`setup.sh` solo instala el paquete `millennium`. Activar el tema y copiar el CSS se maneja aparte, en otro script.

**Pasos:**
1. Abrir Steam y activar el tema **NEVKO-UI** desde la interfaz de Millennium.
2. Copiar el CSS guardado en el backup a su ruta real:
   ```bash
   cp "linux/niri/Millennium/Library Code.css" \
     ~/.steam/steam/millennium/themes/NEVKO-UI/"Main Refresh UI"/"Refresh Library"/"Library Code.css"
   ```
   *(Confirmar la ruta real de Steam — puede variar según cómo quede montado el subvolumen `games/`).*

### Teclado y ratón por Bluetooth desde el celular

**Causa:** Linux deshabilita por defecto el perfil Bluetooth HID de software (necesario para simular periféricos).

**Solución:**
1. Editar `/etc/bluetooth/main.conf` con `sudo`.
2. En la sección `[General]`, agregar o cambiar:
   ```
   Experimental = true
   ```
   *(Opcional, si lo anterior no funciona, probar también)*
   ```
   KernelExperimental = true
   ```
3. Reiniciar el servicio:
   ```bash
   sudo systemctl restart bluetooth
   ```
4. Desemparejar y volver a conectar desde la app.

---

## 🌙 Noctalia — actualizar el backup de configuración

Cuando cambies algo en Noctalia (colores, barra, plugins) y quieras reflejarlo en `BackupLinux`:

1. Si algo quedó de una prueba que no vas a usar (ej. un plugin que activaste y ya no quieres), bórralo directo en `~/.local/state/noctalia/settings.toml` — el comando de export solo *lee* lo que ya está guardado ahí, no sirve para "limpiar" desde su propia salida.
2. Exporta la configuración fusionada:
   ```bash
   noctalia config export > ~/BackupLinux/linux/niri/noctalia/config.toml
   ```
3. Revisa el archivo resultante antes de subirlo — confirma que no quedaron plugins de prueba ni rutas de carpetas que no existan (ej. `directory` de wallpapers).