from ursina import (
    Ursina, camera, window, color, DirectionalLight,invoke, AmbientLight, Text, Vec3, scene, destroy)
from mapa import construir_nivel, MiniMapaNivel2
from entidades import Jugador, Meta, generar_martillos
from enemigos import DiddyKong, BarrilAceite
import pausa

app = Ursina(title='Diddy Kong - Nivel 2', borderless=False, fullscreen=False, development_mode=False)

def maximizar_ventana():
    import ctypes
    hwnd = ctypes.windll.user32.FindWindowW(None, "Diddy Kong - Nivel 2")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 3)
        window.clear_size()
        window.clear_origin()

invoke(maximizar_ventana, delay=1.5)

window.color = color.Color(0.05, 0.05, 0.15, 1)
window.exit_button.visible = False

# Iluminación
luz = DirectionalLight()
luz.look_at(Vec3(1, -2, 1))
AmbientLight(color=color.Color(0, 0, 0.3, 0.2))

# ── CÁMARA PRIMERA PERSONA ──────────────────
camera.orthographic = False
camera.fov = 90

# Variables de Progresión Arcade
puntos_actuales = 0
high_score = 0

# HUD Arcade
ui_high = Text(text=f'TOP: {high_score}', position=(0.60, 0.46), scale=2.2, color=color.cyan, background=True)


def _limpiar_nivel():
    tipos = {'viga', 'escalera', 'muerte', 'barril', 'enemigo', 'meta', 'martillo', 'aceite', 'llama', 'minimapa'}
    for e in scene.entities[:]:
        if getattr(e, 'type', None) in tipos:
            destroy(e)
        elif hasattr(e, 'vidas'):
            destroy(e)


def iniciar_nivel(puntos=0, nivel=2):
    global puntos_actuales
    puntos_actuales = puntos

    _limpiar_nivel()
    construir_nivel()
    generar_martillos()

    jugador = Jugador(posicion=(0, -10.7, 0))
    jugador.puntos = puntos_actuales
    jugador.high_score = high_score
    jugador.texto_puntos.text = f'PUNTOS: {puntos_actuales}'
    jugador.ui_high_ref = ui_high

    MiniMapaNivel2(jugador)

    Meta(posicion=(0, 34.8, 0))
    # Barril de aceite sobre la plataforma inferior central, a la izquierda
    BarrilAceite(posicion=(-28.0, -11.0, 0))

    # ── UN ÚNICO DIDDY KONG ──
    # Él mismo calculará sus saltos aleatorios en enemigos.py
    DiddyKong()


def reinicio_nivel(): iniciar_nivel(puntos_actuales)

def reinicio_total(): iniciar_nivel(puntos=0)

def siguiente_nivel(puntos_ganados): iniciar_nivel(puntos=puntos_ganados)

pausa._reinicio_nivel_ref = reinicio_nivel
pausa._reinicio_total_ref = reinicio_total
pausa._siguiente_nivel_ref = siguiente_nivel

iniciar_nivel()

def input(key):
    if key == 'escape':
        if pausa.esta_pausado():
            pausa.cerrar_menu()
        else:
            pausa.abrir_pausa()

app.run()