# Proyecto Python - Nivel 3

## Estructura del Proyecto

```
Proyecto_Python/
├── main.py                 # Punto de entrada principal
├── src/                    # Código fuente principal
│   ├── __init__.py
│   ├── core/               # Lógica central del juego
│   │   ├── __init__.py
│   │   ├── level_manager.py    # Gestor de niveles y entidades
│   │   └── cinematica_jefe.py  # Cinemática de la batalla final
│   ├── entidades/          # Entidades del juego
│   │   ├── jugador.py      # Clase Jugador
│   │   ├── barril.py       # Barriles y spawner
│   │   ├── bono.py         # Items coleccionables
│   │   └── entorno.py      # Plataformas, suelo, teletransportadores
│   └── ui/                 # Interfaz de usuario
│       ├── __init__.py
│       ├── minimapa.py     # Minimapa del nivel
│       └── menu_pausa.py   # Menú de pausa
├── tests/                  # Archivos de prueba (no producción)
│   ├── test_hammer2.py
│   ├── test_bounds.py
│   └── prueba.py
└── assets/                 # Recursos (modelos, texturas, audio)
    └── Models/
```

## Responsabilidades por Módulo

### `main.py`
- Inicialización de la aplicación Ursina
- Creación del LevelManager y sistemas principales
- Game loop (update, input)
- Delegación de lógica específica a módulos especializados

### `src/core/level_manager.py`
- Gestión del ciclo de vida del nivel
- Creación y destrucción de entidades
- Carga de configuración de plataformas
- Referencias globales (jugador, spawner, minimapa)

### `src/core/cinematica_jefe.py`
- Secuencia cinemática de la batalla final
- Animaciones de cámara
- Transición de 2D a 3D
- Configuración de la arena del jefe

### `src/ui/menu_pausa.py`
- UI del menú de pausa
- Control de sensibilidad del mouse
- Toggle pause/play

### `src/entidades/`
- **jugador.py**: Control del personaje, martillo, puntuación
- **barril.py**: Física de barriles, spawner, colisiones
- **bono.py**: Items coleccionables (puntos, martillo)
- **entorno.py**: Plataformas, trampas, teletransportadores

## Controles

| Tecla | Acción |
|-------|--------|
| WASD / Flechas | Mover jugador |
| Espacio | Saltar |
| Click izquierdo | Atacar con martillo |
| Escape | Pausa |
| V | Modo creativo (cámara libre) |
| G | Toggle god mode |
| P | Forzar cinemática del jefe (debug) |

## Flujo del Juego

1. **Intro cinemática**: Presentación del jefe y mecanismo de barriles
2. **Ascenso 2D**: Subir plataformas esquivando barriles
3. **Teletransportadores**: Alternancia izquierda/derecha
4. **Cima**: Activación de cinemática final
5. **Batalla 3D**: Esquivar barriles en arena 3D con jefe móvil

## Notas de Desarrollo

- Los archivos en `tests/` son para pruebas y no deben usarse en producción
- El backup `main_backup.py` fue eliminado durante la refactorización
- La sensibilidad del mouse se ajusta desde el menú de pausa (5-60)
