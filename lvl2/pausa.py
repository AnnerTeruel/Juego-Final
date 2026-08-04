from ursina import Entity, Text, Button, color, mouse, destroy, camera, application
import config

# ── Estado ───────────────────────────────────────────────────────
_menu_actual = None
pausado = False

# Referencias a funciones de main.py
_reinicio_nivel_ref = None
_reinicio_total_ref = None
_siguiente_nivel_ref = None

def esta_pausado():
    return pausado

def _crear_menu(titulo, color_titulo):
    global _menu_actual, pausado
    if _menu_actual is not None:
        destroy(_menu_actual)

    pausado = True
    mouse.locked = False
    mouse.visible = True

    _menu_actual = Entity(parent=camera.ui, model='quad', color=color.Color(0, 0, 0, 0.85), scale=(0.65, 0.75), z=-1)
    Text(parent=_menu_actual, text=titulo, origin=(0, 0), position=(0, 0.35), scale=4, color=color_titulo)
    Entity(parent=_menu_actual, model='quad', color=color.Color(1, 1, 1, 0.2), scale=(0.85, 0.003), position=(0, 0.23))

    return _menu_actual

def _boton(parent, texto, pos, accion):
    return Button(
        parent=parent, text=texto, position=pos, scale=(0.45, 0.1),
        color=color.Color(0.12, 0.12, 0.35, 1), highlight_color=color.Color(0.25, 0.25, 0.60, 1),
        text_color=color.white, on_click=accion
    )

def cerrar_menu():
    global _menu_actual, pausado
    if _menu_actual: destroy(_menu_actual)
    _menu_actual = None
    pausado = False
    mouse.locked = True
    mouse.visible = False

def _ejecutar(funcion, *args):
    cerrar_menu()
    if funcion: funcion(*args)

def abrir_opciones():
    global _menu_actual
    menu = _crear_menu('⚙ OPCIONES', color.light_gray)
    
    texto_sens = Text(parent=menu, text=f'Sensibilidad: {int(config.sensibilidad)}', origin=(0, 0), position=(0, 0.08), scale=2, color=color.white)
    
    def subir_sens():
        config.sensibilidad += 10
        texto_sens.text = f'Sensibilidad: {int(config.sensibilidad)}'
        config.guardar()
        
    def bajar_sens():
        config.sensibilidad = max(10, config.sensibilidad - 10)
        texto_sens.text = f'Sensibilidad: {int(config.sensibilidad)}'
        config.guardar()
        
    _boton(menu, '+', (0.25, 0.08), subir_sens)
    _boton(menu, '-', (-0.25, 0.08), bajar_sens)
    
    _boton(menu, 'Volver', (0, -0.20), lambda: abrir_pausa(fuerza=True))

def abrir_pausa(fuerza=False):
    global _menu_actual
    if _menu_actual is not None and not fuerza: return
    menu = _crear_menu('⏸ PAUSA', color.yellow)
    _boton(menu, '▶  Continuar', (0, 0.15), cerrar_menu)
    _boton(menu, '⚙  Opciones', (0, 0.00), abrir_opciones)
    _boton(menu, '↺  Reiniciar Nivel', (0, -0.15), lambda: _ejecutar(_reinicio_nivel_ref))
    _boton(menu, '✕  Salir', (0, -0.30), application.quit)

def mostrar_game_over():
    menu = _crear_menu('GAME OVER', color.red)
    Text(parent=menu, text='¡Te has quedado sin vidas!', origin=(0, 0), position=(0, 0.15), scale=1.5, color=color.white)
    _boton(menu, '↺  Reiniciar Juego', (0, -0.05), lambda: _ejecutar(_reinicio_total_ref))
    _boton(menu, '✕  Salir', (0, -0.20), application.quit)

def mostrar_victoria(puntos):
    menu = _crear_menu('¡NIVEL COMPLETADO!', color.green)
    Text(parent=menu, text=f'PUNTOS TOTALES: {puntos}', origin=(0, 0), position=(0, 0.15), scale=2, color=color.yellow)
    _boton(menu, '▶  Jugar de Nuevo', (0, -0.05), lambda: _ejecutar(_siguiente_nivel_ref, puntos))
    _boton(menu, '✕  Salir', (0, -0.20), application.quit)