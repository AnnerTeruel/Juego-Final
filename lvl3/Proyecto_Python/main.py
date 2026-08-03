from ursina import *
from src.core.level_manager import LevelManager
from src.ui.menu_pausa import MenuPausa
from src.core.cinematica_jefe import CinematicaJefe

app = Ursina()

window.exit_button.visible = False
window.exit_button.enabled = False

manager = LevelManager()
manager.cargar_nivel(3)

# Inicializar sistemas UI y cinemáticas
menu_pausa = MenuPausa(manager)
cinematica_jefe = CinematicaJefe(manager)

# ==========================================================
# INPUT - Delegado a menu_pausa
# ==========================================================
def input(key):
    # Input del menú de pausa
    menu_pausa.input(key)
    
    # ATAQUE CON MARTILLO: clic izquierdo
    if key == 'left mouse down' and not menu_pausa.pausa_activa:
        jugador = manager.jugador
        if jugador and jugador.tiene_martillo and not jugador.atacando:
            jugador.atacando = True
            # Animacion de golpe: baja rapido y regresa a idle
            jugador.martillo_pivot.animate('rotation_x', 80, duration=0.1, curve=curve.linear)
            def fin_golpe():
                if jugador:
                    jugador.martillo_pivot.animate('rotation_x', 20, duration=0.12, curve=curve.linear)
                    invoke(lambda: setattr(jugador, 'atacando', False), delay=0.12)
            invoke(fin_golpe, delay=0.1)

            from src.entidades.barril import Barril
            hit = raycast(camera.world_position, camera.forward, distance=5, ignore=[jugador.controller])
            if hit.hit and isinstance(hit.entity, Barril):
                # Si el jugador rompe el barril dorado recibe un bonus enorme
                if getattr(hit.entity, 'es_dorado', False):
                    puntos = 1000
                    jugador.multiplicador = 2
                    texto_str = f'¡BARRIL DORADO! +{puntos} (x2)'
                    texto_color = color.gold
                else:
                    puntos = 300
                    texto_str = f'SMAAASH! +{puntos}'
                    texto_color = color.orange
                    
                jugador.sumar_puntos(puntos)
                texto = Text(text=texto_str, position=(0, 0.1), scale=3, color=texto_color, origin=(0,0))
                destroy(texto, delay=1.5)
                destroy(hit.entity)

    if key == 'v' and not menu_pausa.pausa_activa:
        # Alternar Modo Creativo (Camara Libre)
        if hasattr(camera, 'editor_camera') and camera.editor_camera.enabled:
            camera.editor_camera.enabled = False
            camera.parent = manager.jugador.controller.camera_pivot
            camera.position = (0, 0, 0)
            camera.rotation = (0, 0, 0)
            manager.jugador.controller.enabled = True
            mouse.locked = True

    if key == 'g' and not menu_pausa.pausa_activa:
        if manager.jugador:
            manager.jugador.god_mode = not getattr(manager.jugador, 'god_mode', False)
            if manager.jugador.god_mode:
                manager.jugador.texto_martillo.text = 'MODO DIOS: ACTIVO'
                manager.jugador.texto_martillo.color = color.cyan
            else:
                manager.jugador.texto_martillo.text = 'MARTILLO: INACTIVO' if not manager.jugador.tiene_martillo else f'MARTILLO: {int(manager.jugador.tiempo_martillo)}s'
                manager.jugador.texto_martillo.color = color.orange if not manager.jugador.tiene_martillo else color.red

    if key == 'p' and not menu_pausa.pausa_activa:
        # Delegar el cambio de nivel/estado al LevelManager
        if manager.jugador:
            manager.siguiente_nivel()

# ==========================================================
# UPDATE
# ==========================================================
def update():
    # Verificar si se debe iniciar la cinemática del jefe
    if manager.jugador and not cinematica_jefe.fase_iniciada:
        if manager.jugador.controller.y >= 89.0 and abs(manager.jugador.controller.x) < 5.0:
            cinematica_jefe.iniciar()
            
    # Actualizar menú de pausa (sensibilidad en tiempo real)
    menu_pausa.update()

    # Modo Creativo: mover camara con teclas
    if hasattr(camera, 'editor_camera') and camera.editor_camera.enabled:
        velocidad_vuelo = 30 * time.dt
        if held_keys['up arrow']:
            camera.editor_camera.position += camera.up * velocidad_vuelo
        if held_keys['down arrow']:
            camera.editor_camera.position -= camera.up * velocidad_vuelo
        if held_keys['right arrow']:
            camera.editor_camera.position += camera.right * velocidad_vuelo
        if held_keys['left arrow']:
            camera.editor_camera.position -= camera.right * velocidad_vuelo
        if held_keys['w']:
            camera.editor_camera.position += camera.forward * velocidad_vuelo
        if held_keys['s']:
            camera.editor_camera.position -= camera.forward * velocidad_vuelo

app.run()
