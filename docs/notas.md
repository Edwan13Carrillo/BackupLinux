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
