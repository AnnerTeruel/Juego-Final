from ursina import *
from src.core.level_manager import LevelManager

app = Ursina()

window.exit_button.visible = False
window.exit_button.enabled = False

manager = LevelManager()
manager.cargar_nivel(3)

# ==========================================================
# MENU DE PAUSA
# ==========================================================
pausa_activa = False

# Panel de fondo: z=0 (detras de los elementos UI)
panel_pausa = Entity(
    parent=camera.ui,
    model='quad',
    color=Color(0.02, 0.04, 0.14, 0.92),
    scale=(0.52, 0.62),
    z=0,
    enabled=False
)

# Todos los elementos van con z=-0.01 para aparecer ENCIMA del panel
titulo_pausa = Text(
    parent=panel_pausa,
    text='PAUSA',
    scale=5.5,
    position=(0, 0.38),
    origin=(0, 0),
    color=color.rgb(255, 200, 50),
    z=-0.01,
    enabled=True
)

linea = Entity(
    parent=panel_pausa,
    model='quad',
    color=Color(1, 0.78, 0.2, 0.5),
    scale=(0.92, 0.005),
    position=(0, 0.24),
    z=-0.01,
    enabled=True
)

lbl_sens = Text(
    parent=panel_pausa,
    text='Sensibilidad de camara',
    scale=2.2,
    position=(0, 0.17),
    origin=(0, 0),
    color=color.rgb(180, 210, 255),
    z=-0.01,
    enabled=True
)

sensibilidad_actual = 20

slider_sens = Slider(
    min=5,
    max=60,
    default=sensibilidad_actual,
    step=1,
    position=(0, 0.04),
    scale=0.55,
    enabled=False
)

lbl_valor_sens = Text(
    parent=panel_pausa,
    text=str(sensibilidad_actual),
    scale=2.5,
    position=(0, -0.06),
    origin=(0, 0),
    color=color.yellow,
    z=-0.01,
    enabled=True
)

btn_reanudar = Button(
    text='Reanudar',
    color=Color(0.12, 0.55, 0.24, 0.95),
    highlight_color=Color(0.18, 0.72, 0.32, 1),
    pressed_color=Color(0.08, 0.38, 0.16, 1),
    scale=(0.3, 0.07),
    position=(0, -0.17),
    enabled=False
)

btn_salir = Button(
    text='Salir al escritorio',
    color=Color(0.62, 0.12, 0.12, 0.95),
    highlight_color=Color(0.82, 0.22, 0.22, 1),
    pressed_color=Color(0.46, 0.08, 0.08, 1),
    scale=(0.3, 0.07),
    position=(0, -0.27),
    enabled=False
)

elementos_pausa = [panel_pausa, slider_sens, btn_reanudar, btn_salir]

def mostrar_pausa(estado):
    global pausa_activa
    pausa_activa = estado
    for e in elementos_pausa:
        e.enabled = estado
    application.paused = estado
    mouse.locked = not estado
    mouse.visible = estado
    if estado:
        # Sincronizamos el slider con la sensibilidad actual
        jugador = manager.jugador
        if jugador:
            slider_sens.value = jugador.controller.mouse_sensitivity.x

def reanudar():
    mostrar_pausa(False)

btn_reanudar.on_click = reanudar
btn_salir.on_click = application.quit

# ==========================================================
# INPUT
# ==========================================================
def input(key):
    if key == 'escape':
        mostrar_pausa(not pausa_activa)

    # ATAQUE CON MARTILLO: clic izquierdo
    if key == 'left mouse down' and not pausa_activa:
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

    if key == 'v' and not pausa_activa:
        # Alternar Modo Creativo (Camara Libre)
        if hasattr(camera, 'editor_camera') and camera.editor_camera.enabled:
            camera.editor_camera.enabled = False
            camera.parent = manager.jugador.controller.camera_pivot
            camera.position = (0, 0, 0)
            camera.rotation = (0, 0, 0)
            manager.jugador.controller.enabled = True
            mouse.locked = True

    if key == 'p' and not pausa_activa:
        # PRUEBA ESPECIAL A PEDIDO
        if manager.jugador:
            manager.jugador.activar(False)
            camera.parent = scene
            
            # 1. Saltar a animación 2D (rápido)
            camera.animate_position((0, 45, -150), duration=2, curve=curve.in_out_sine)
            camera.animate_rotation((0, 0, 0), duration=2, curve=curve.in_out_sine)
            
            # 2. Saltar al jefe
            def ir_al_jefe():
                camera.animate_position((-11, 102.5, -40), duration=2, curve=curve.in_out_sine)
            invoke(ir_al_jefe, delay=2.5)
            
            # 3. Volver a vista 2D enfocado arriba para empezar a bajar con las plataformas (muy de cerca)
            def enfocar_arriba():
                camera.animate_position((0, 90, -50), duration=2, curve=curve.in_out_sine)
            invoke(enfocar_arriba, delay=5)
            
            # 4. Desaparecer barriles y enderezar plataformas una por una siguiendo la cámara
            def enderezar_y_limpiar():
                # Desaparecer barriles
                from src.entidades.barril import Barril
                for b in list(Barril.todos_los_barriles):
                    destroy(b)
                
                # Obtener plataformas y ordenarlas de arriba hacia abajo
                from src.entidades.entorno import Plataforma, PlataformaTrampa, PlataformaMovil
                plataformas = [e for e in manager.entidades if isinstance(e, (Plataforma, PlataformaTrampa, PlataformaMovil))]
                plataformas.sort(key=lambda p: p.y, reverse=True)
                
                def soltar_plataforma(plat):
                    plat.rotation_z = 0
                    camera.shake(duration=0.3, magnitude=1.5)
                    # La cámara baja para enfocarse de cerca en la plataforma que acaba de caer
                    camera.animate_position((0, plat.y, -50), duration=0.4, curve=curve.linear)
                
                retraso = 0.0
                for plat in plataformas:
                    invoke(soltar_plataforma, plat, delay=retraso)
                    retraso += 0.5
                    
                # 5. Volver a la camara normal al final del temblor
                def volver_camara():
                    # Desatorar del piso para que caiga limpiamente
                    manager.jugador.controller.y += 2.0
                    camera.parent = manager.jugador.controller.camera_pivot
                    camera.position = (0, 0, 0)
                    camera.rotation = (0, 0, 0)
                    manager.jugador.activar(True)
                    
                invoke(volver_camara, delay=retraso + 0.5)
            
            invoke(enderezar_y_limpiar, delay=7.5)

# ==========================================================
# UPDATE
# ==========================================================
def update():
    # Actualizar sensibilidad de camara en tiempo real segun el slider
    if pausa_activa:
        jugador = manager.jugador
        if jugador:
            val = int(slider_sens.value)
            jugador.controller.mouse_sensitivity = Vec2(val, val)
            lbl_valor_sens.text = str(val)

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
