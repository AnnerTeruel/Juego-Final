# 🦍 DONKEY KONG 3D - ARCADE EDITION
> **Proyecto Final de Programación Avanzada en Python**  
> *Desarrollado con Python 3.14 + Ursina Engine 3D / Panda3D + Tkinter Arcade Interface*

---

## 📋 ÍNDICE
1. [Descripción General](#-descripción-general)
2. [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
3. [Lanzador Principal y Menú (`menu.py`)](#-lanzador-principal-y-menú-menupy)
4. [Nivel 1 — La Asunción del Secuaz (`lvl1`)](#-nivel-1--la-asunción-del-secuaz-lvl1)
5. [Nivel 2 — Plataformas 2.5D & Diddy Kong (`lvl2`)](#-nivel-2--plataformas-25d--diddy-kong-lvl2)
6. [Nivel 3 — El Desafío Final (`lvl3`)](#-nivel-3--el-desafío-final-lvl3)
7. [Diseño Técnico e Interfaz Unificada (HUD)](#-diseño-técnico-e-interfaz-unificada-hud)
8. [Decisiones de Arquitectura y Solución de Problemas](#-decisiones-de-arquitectura-y-solución-de-problemas)
9. [Instrucciones de Ejecución](#-instrucciones-de-ejecución)

---

## 🎮 DESCRIPCIÓN GENERAL
**Donkey Kong 3D - Arcade Edition** es un videojuego de plataformas tridimensional y 2.5D desarrollado en **Python** utilizando el motor **Ursina Engine (Panda3D)** para el entorno gráfico 3D y **Tkinter** para la interfaz del menú principal.

El proyecto está diseñado bajo una estética **Retro Arcade / Synthwave**, incorporando una paleta de colores neón, música ambiental en formato MCI, tablas de clasificación persistentes en JSON, tipografía de 8 bits (*Press Start 2P*) y un sistema de física e interactividad optimizado para 60 FPS.

---

## 🏗️ ARQUITECTURA DEL PROYECTO

```
Juego-Final/
├── menu.py                      # Lanzador principal y Menú Arcade (Tkinter)
├── estadisticas.json            # Base de datos local de ranking de jugadores
├── run_result.json              # Intercambio de resultados entre niveles y el menú
├── assets/
│   ├── PressStart2P-Regular.ttf # Tipografía oficial Arcade de 8-Bits
│   └── MusicaMenu.wav           # Banda sonora del menú principal
│
├── lvl1/proyectoavanzada/       # NIVEL 1: Plataformas 3D Verticales y Secuaz
│   ├── nivel1.py                # Script principal del Nivel 1
│   └── assets/                  # Modelos GLTF/GLB, texturas y efectos de audio
│
├── lvl2/DONKEY KONG 3D/         # NIVEL 2: Perspectiva 2.5D & Diddy Kong
│   ├── main.py                  # Lanzador del Nivel 2
│   ├── entidades.py             # Lógica de Jugador, Martillo, Física y Daño
│   ├── mapa.py                  # Generación de Plataformas, Escaleras y Minimapa
│   ├── enemigos.py              # IA de Diddy Kong y Barriles
│   └── pausa.py                 # Sistema de Menú de Pausa Neón
│
└── lvl3/Proyecto_Python/        # NIVEL 3: Desafío Final y Estamina
    ├── main.py                  # Lanzador del Nivel 3
    └── src/
        ├── entidades/           # Jugador, Enemigos, Estamina y Teletransportadores
        └── mundo/               # Escenario, Trampas y Partículas
```

---

## 🚀 LANZADOR PRINCIPAL Y MENÚ (`menu.py`)

El archivo [`menu.py`](file:///c:/Users/anner/Desktop/Nueva%20carpeta%20%285%29/Juego-Final/menu.py) actúa como el núcleo de arranque del juego:

- **Diseño Visual Arcade Neón:** Tarjetas oscuras metálicas (`#0D0D1A`), bordes dorados (`#FFD700`), títulos neón cian (`#00F0FF`) y botones magenta (`#FF0055`) con animación de estado al pasar el ratón (*hover*).
- **Reproducción de Música MCI de Windows:** Utiliza la API WinMM de Windows (`ctypes.windll.winmm.mciSendStringW`) forzando la decodificación `type mpegvideo`. Esto permite reproducir archivos comprimidos MP3 renombrados a `.wav` de forma fluida y sin bloqueos de hilo.
- **Sistema de Registro y Selección de Niveles:** Permite ingresar el nombre del jugador, desbloquear niveles progresivamente y consultar la tabla de **Ranking de Jugadores** ordenada por puntuación y tiempo.

---

## 🧱 NIVEL 1 — LA ASUNCIÓN DEL SECUAZ (`lvl1`)

**Ubicación:** [`lvl1/proyectoavanzada/nivel1.py`](file:///c:/Users/anner/Desktop/Nueva%20carpeta%20%285%29/Juego-Final/lvl1/proyectoavanzada/nivel1.py)

### Características Clave:
- **Cinemática de Inicio:** Vuelo de cámara en curva sinusoidal desde una vista aérea panorámica hasta situarse en la perspectiva de Primera Persona del jugador.
- **Mecánica de Juego:** Escalar vigas inclinadas mientras se esquivan barriles rodantes impulsados por física dinámicamente generada.
- **Combate de Jefe (El Secuaz):** Un mini-jefe que lanza barriles desde la cima. Al recoger el martillo, el jugador puede destruir barriles (sumando +500 pts) e infligir daño al secuaz hasta derrotarlo.
- **Guía de Controles Flotante:** Una superposición de controles (`WASD`, `ESPACIO`, `CLIC IZQ`) con desvanecimiento automático (*fade-out*) a los 5 segundos que se oculta al pausar.

---

## 🪜 NIVEL 2 — PLATAFORMAS 2.5D & DIDDY KONG (`lvl2`)

**Ubicación:** [`lvl2/DONKEY KONG 3D/main.py`](file:///c:/Users/anner/Desktop/Nueva%20carpeta%20%285%29/Juego-Final/lvl2/DONKEY%20KONG%203D/main.py)

### Características Clave:
- **Perspectiva 2.5D en Entorno 3D:** El jugador opera en Primera Persona pero con la coordenada de profundidad fija en `Z = 0.0`, ofreciendo la experiencia clásica de plataformas arcade de 1981 con gráficos 3D modernos.
- **Controles WASD + Sprint:**
  * `A` / `D` (o Flechas): Movimiento lateral fluido en el eje X.
  * `Shift`: **Sprint / Correr** (Aumenta la velocidad un 75% en suelo y escaleras).
  * `W` / `Espacio`: Subir escaleras o saltar.
  * `S` / `Down Arrow`: Bajar escaleras de forma natural.
  * `Clic Izquierdo / Derecho`: Ataque con martillo 3D (`toy_hammer.glb`).
- **Detección de Martillo por Distancia Vectorial:** Implementa cálculo tridimensional `(world_pos - e.world_pos).length() < 2.5`. Al tocar el martillo, destruye la entidad del suelo y activa de inmediato el arma 3D en las manos del jugador durante 10 segundos.
- **Minimapa en Tiempo Real (`MiniMapaNivel2`):** Muestra plataformas, escaleras, jugador y enemigos. Cuenta con protección contra excepciones `AssertionError` para evitar errores al reiniciar niveles.

---

## ⚡ NIVEL 3 — EL DESAFÍO FINAL (`lvl3`)

**Ubicación:** [`lvl3/Proyecto_Python/main.py`](file:///c:/Users/anner/Desktop/Nueva%20carpeta%20%285%29/Juego-Final/lvl3/Proyecto_Python/main.py)

### Características Clave:
- **Sistema de Estamina (Stamina Bar):** Gestión de energía para correr en sprint. Al agotarse la estamina, la barra inferior parpadea en rojo y exige esperar su recarga.
- **Teletransportadores y Trampas:** Portales de salto entre pisos y obstáculos móviles.
- **Multiplicadores de Puntos:** Bonificaciones progresivas por combos y eliminación continua de enemigos.

---

## 🎨 DISEÑO TÉCNICO E INTERFAZ UNIFICADA (HUD)

Para mantener una estética homogénea en todo el proyecto, los 3 niveles comparten exactamente la misma barra de estado superior:

```
+-------------------------------------------------------------------------------+
|  BONUS: 3950           VIDAS: 🔴 🔴 🔴         MARTILLO: 15s                 |
+-------------------------------------------------------------------------------+
```

### 1. Cero Cuadritos de Error (Solución de Fuentes 0% Unicode)
> **Problema Encontrado:** La fuente interna por defecto de Panda3D no soporta caracteres Unicode Emoji (`❤️` o `🔨`), mostrando cuadros de error (`🔲 🔲 🔲`) en pantalla.  
> **Solución Implementada:** Se eliminaron las fuentes de texto unicode para la salud y se crearon **insignias circulares geométricas 3D nativas (`model='circle'`)**. Brillan en **Rojo Neón (`#FF2E63`)** cuando hay vidas disponibles y cambian a gris oscuro (`#2A2A38`) al recibir daño.

### 2. Tipografía Pixel Arcade (`Press Start 2P`)
Se integró la fuente oficial retro de 8 bits [`PressStart2P-Regular.ttf`](file:///c:/Users/anner/Desktop/Nueva%20carpeta%20%285%29/Juego-Final/assets/PressStart2P-Regular.ttf), proporcionando el aspecto visual característico de las máquinas Arcade clásicas.

### 3. Distribución Anti-Colisión
- **Izquierda (`x = -0.82`):** Contador de Puntos/Bonus.
- **Centro (`x = -0.30`):** Etiqueta `VIDAS:` con 3 insignias circulares alineadas.
- **Derecha (`x = 0.28`):** Estado del Martillo (`MARTILLO: INACTIVO` / `MARTILLO: 15s`).
- **Esquina Superior Derecha:** Reservada exclusivamente para el **Minimapa táctico**, evitando cualquier cruce de texto.

### 4. Menú de Pausa Neón Unificado
Al presionar `ESC` en cualquier nivel, se despliega una tarjeta oscura estilizada (`#060614` al 94% de opacidad) con borde cian neón (`#00F0FF`), ofreciendo las siguientes opciones unificadas:
- **`CONTINUAR`**: Reanudar la partida.
- **`REINICIAR`**: Reiniciar el nivel actual sin duplicación de interfaz (ejecutando `destroy_ui()`).
- **`OPCIONES`**: Ajuste en tiempo real de la sensibilidad de cámara del ratón.
- **`SALIR`**: Salir al escritorio / volver al menú.

---

## 🛠️ DECISIONES DE ARQUITECTURA Y SOLUCIÓN DE PROBLEMAS

### A. Fijación de Maximizado de Ventana en Windows (`SW_MAXIMIZE`)
- **Desafío:** En Ursina, al alternar la propiedad `mouse.locked = True` (para capturar el ratón estilo FPS), Panda3D ejecutaba `requestProperties(window)`. Si la ventana conservaba su tamaño base (1280x720), Windows deshacía el maximizado enviando la ventana al centro de la pantalla.
- **Solución:** Implementamos una llamada explícita a la API de Windows Win32 en cada nivel:
  ```python
  def maximizar_ventana():
      hwnd = ctypes.windll.user32.GetActiveWindow()
      ctypes.windll.user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
      window.clear_size()   # Limpia la preferencia de 1280x720
      window.clear_origin() # Limpia la posición (192, 108)
  ```
  Al limpiar `clear_size()` y `clear_origin()`, Ursina respeta el estado maximizado de Windows sin reiniciar el tamaño del marco.

### B. Prevención de Duplicación de Interfaz al Reiniciar Nivel
- **Desafío:** Al reiniciar el Nivel 2 desde el menú de pausa, `_limpiar_nivel()` eliminaba la entidad del personaje 3D, pero las entidades de texto y círculos en `camera.ui` permanecían vivas. La nueva partida creaba un segundo set de interfaz que se encimaba sobre el primero (`VIDAS: VIDAS:`).
- **Solución:** Se creó un método `destroy_ui(self)` en la clase `Jugador` que elimina de raíz todos los elementos de `camera.ui` asociados antes de instanciar la nueva partida.

---

## 🏃 INSTRUCCIONES DE EJECUCIÓN

### Requisitos Previos:
- Python 3.10 o superior (Probado en Python 3.14.2 64-bit).
- Dependencias instaladas:
  ```bash
  pip install ursina
  ```

### Iniciar el Juego:
Ejecutar el script principal desde la raíz del proyecto:
```bash
python menu.py
```

---
*Documentación generada para el equipo de desarrollo de Donkey Kong 3D.*
