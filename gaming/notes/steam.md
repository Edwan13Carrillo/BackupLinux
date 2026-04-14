# Configuraciones de Steam y Gaming 🎮

---

## Comando base

La mayoría de juegos solo necesitan este comando de lanzamiento:

```
game-performance %command%
```

**Juegos con comando base:**
- American Truck Simulator (DirectX 11)
- Gang Beasts
- Halo
- Hollow Knight
- Wallpaper Engine
- Lego (serie)
- SnowRunner
- Overwatch 2

---

## Juegos con configuración especial

### Left 4 Dead 2
```
PROTON_NO_ESYNC=1 PROTON_NO_FSYNC=1 taskset -c 0-3 %command%
```

### The Forest
```
game-performance PROTON_NO_FSYNC=1 taskset -c 0,1,2,3 %command%
```

### A Way Out
```
DXVK_ASYNC=1 PROTON_NO_ESYNC=1 PROTON_NO_FSYNC=1 taskset -c 0-3 %command%
```

### Far Cry 4
```
game-performance DXVK_ASYNC=1 %command% -skipintro
```

### Far Cry 5
```
game-performance %command% -skipintro
```

---

## Prism Launcher (Minecraft)

### Versión de Java
| Versión de Minecraft | Java |
|---|---|
| 1.20.1 y anteriores | Java 17 |
| 1.21 y posteriores | Java 21 |

### Memoria
| Parámetro | Valor |
|---|---|
| `-Xms` (mínimo) | 1024 MiB |
| `-Xmx` (máximo) | 4096 MiB |

### Variables de entorno
```
ALSOFT_DRIVERS = null
```

### Comando personalizado (Wrapper)
```
game-performance
```

### Argumentos de Java
```
-XX:+UseZGC -XX:+UnlockDiagnosticVMOptions -XX:+AlwaysPreTouch -XX:+DisableExplicitGC -XX:+PerfDisableSharedMem -XX:+ClassUnloading
```
