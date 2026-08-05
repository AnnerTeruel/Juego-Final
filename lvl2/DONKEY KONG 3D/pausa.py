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

    _menu_actual = Entity(parent=camera.ui, model='quad', color=color.Color(0.06, 0.06, 0.14, 0.94), scale=(0.65, 0.76), z=-1)
    borde = Entity(parent=_menu_actual, model='quad', color=color.hex('#00F0FF'), scale=(1.02, 1.02), z=0.01)
    
    Text(parent=_menu_actual, text=titulo, font='assets/PressStart2P-Regular.ttf', origin=(0, 0), position=(0, 0.35), scale=1.6, color=color_titulo, z=-0.01)
    Entity(parent=_menu_actual, model='quad', color=color.hex('#00F0FF'), scale=(0.90, 0.005), position=(0, 0.23), z=-0.01)

    return _menu_actual

def _boton(parent, texto, pos, accion):
    b = Button(
        parent=parent, text=texto, position=pos, scale=(0.48, 0.08),
        color=color.Color(0.10, 0.10, 0.25, 1), highlight_color=color.hex('#00F0FF'),
        pressed_color=color.hex('#FFD700'), text_color=color.white, on_click=accion, z=-0.02
    )
    if hasattr(b, 'text_entity') and b.text_entity:
        b.text_entity.font = 'assets/PressStart2P-Regular.ttf'
    return b

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
    menu = _crear_menu('OPCIONES', color.hex('#00F0FF'))
    
    texto_sens = Text(parent=menu, text=f'SENSIBILIDAD: {int(config.sensibilidad)}', font='assets/PressStart2P-Regular.ttf', origin=(0, 0), position=(0, 0.08), scale=0.8, color=color.white, z=-0.01)
    
    def subir_sens():
        config.sensibilidad += 10
        texto_sens.text = f'SENSIBILIDAD: {int(config.sensibilidad)}'
        config.guardar()
        
    def bajar_sens():
        config.sensibilidad = max(10, config.sensibilidad - 10)
        texto_sens.text = f'SENSIBILIDAD: {int(config.sensibilidad)}'
        config.guardar()
        
    _boton(menu, '+10', (0.20, 0.08), subir_sens)
    _boton(menu, '-10', (-0.20, 0.08), bajar_sens)
    
    _boton(menu, 'VOLVER', (0, -0.20), lambda: abrir_pausa(fuerza=True))

def abrir_pausa(fuerza=False):
    global _menu_actual
    if _menu_actual is not None and not fuerza: return
    menu = _crear_menu('PAUSA', color.hex('#FFD700'))
    _boton(menu, 'CONTINUAR', (0, 0.16), cerrar_menu)
    _boton(menu, 'REINICIAR', (0, 0.03), lambda: _ejecutar(_reinicio_nivel_ref))
    _boton(menu, 'OPCIONES', (0, -0.10), abrir_opciones)
    _boton(menu, 'SALIR', (0, -0.23), application.quit)

def mostrar_game_over():
    menu = _crear_menu('GAME OVER', color.hex('#FF0055'))
    Text(parent=menu, text='TE HAS QUEDADO SIN VIDAS', font='assets/PressStart2P-Regular.ttf', origin=(0, 0), position=(0, 0.15), scale=0.8, color=color.white, z=-0.01)
    _boton(menu, 'REINICIAR', (0, -0.05), lambda: _ejecutar(_reinicio_total_ref))
    _boton(menu, 'SALIR', (0, -0.20), application.quit)

def mostrar_victoria(puntos):
    menu = _crear_menu('VICTORIA', color.hex('#00FF66'))
    Text(parent=menu, text=f'PUNTOS: {puntos}', font='assets/PressStart2P-Regular.ttf', origin=(0, 0), position=(0, 0.15), scale=1.0, color=color.hex('#FFD700'), z=-0.01)
    _boton(menu, 'SIGUIENTE', (0, -0.05), lambda: _ejecutar(_siguiente_nivel_ref, puntos))
    _boton(menu, 'SALIR', (0, -0.20), application.quit)