from ursina import *    
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

# Música de fondo del nivel (loop, volumen bajo para no tapar efectos)
musica_nivel = Audio('MusicaNivel.wav', loop=True, autoplay=True, volume=0.35)

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

# HUD Arcade (TOP score eliminado)


def _limpiar_nivel():
    tipos = {'viga', 'escalera', 'muerte', 'barril', 'enemigo', 'meta', 'martillo', 'aceite', 'llama', 'minimapa'}
    for e in list(scene.entities):
        if hasattr(e, 'destroy_ui'):
            try: e.destroy_ui()
            except Exception: pass
        if getattr(e, 'type', None) in tipos or hasattr(e, 'vidas'):
            destroy(e)


def iniciar_nivel(puntos=0, nivel=2):
    global puntos_actuales, musica_nivel
    puntos_actuales = puntos

    try:
        if 'musica_nivel' in globals() and musica_nivel:
            musica_nivel.volume = 0.35
            if not getattr(musica_nivel, 'playing', False):
                musica_nivel.play()
        else:
            musica_nivel = Audio('MusicaNivel.wav', loop=True, autoplay=True, volume=0.35)
    except Exception:
        pass

    _limpiar_nivel()
    construir_nivel()
    generar_martillos()

    jugador = Jugador(posicion=(0, -10.7, 0))
    jugador.puntos = puntos_actuales
    jugador.high_score = high_score
    jugador.texto_puntos.text = f'PUNTOS: {puntos_actuales}'
    jugador.ui_high_ref = None

    MiniMapaNivel2(jugador)

    Meta(posicion=(0, 34.8, 0))
    # Barril de aceite sobre la plataforma inferior central, a la izquierda
    BarrilAceite(posicion=(-28.0, -11.0, 0))

    # ── UN ÚNICO DIDDY KONG ──
    # Él mismo calculará sus saltos aleatorios en enemigos.py
    DiddyKong()


def reinicio_nivel(): iniciar_nivel(puntos_actuales)

def reinicio_total(): iniciar_nivel(puntos=0)

def siguiente_nivel(puntos_ganados):
    try:
        import json, os
        from pathlib import Path
        ruta_res = Path(__file__).resolve().parent.parent.parent / 'run_result.json'
        with open(ruta_res, 'w', encoding='utf-8') as f:
            json.dump({'puntos': puntos_ganados, 'nivel_desbloqueado': 3, 'nivel': 2}, f)
    except Exception as err:
        print("Error al guardar resultado:", err)
    application.quit()

pausa._reinicio_nivel_ref = reinicio_nivel
pausa._reinicio_total_ref = reinicio_total
pausa._siguiente_nivel_ref = siguiente_nivel

import sys
pts_ini = 0
if len(sys.argv) > 1:
    try: pts_ini = int(sys.argv[1])
    except: pts_ini = 0

iniciar_nivel(puntos=pts_ini)

def input(key):
    if key == 'escape':
        if pausa.esta_pausado():
            pausa.cerrar_menu()
        else:
            pausa.abrir_pausa()

app.run()