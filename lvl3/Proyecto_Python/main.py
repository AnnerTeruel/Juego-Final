from ursina import *
from src.core.level_manager import LevelManager

app = Ursina(title='Donkey Kong 3D - Nivel 3', development_mode=False, borderless=False, fullscreen=False)

def maximizar_ventana():
    import ctypes
    hwnd = ctypes.windll.user32.FindWindowW(None, "Donkey Kong 3D - Nivel 3")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 3)
        window.clear_size()
        window.clear_origin()

invoke(maximizar_ventana, delay=1.5)

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

    if key == 'g' and not pausa_activa:
        if manager.jugador:
            manager.jugador.god_mode = not getattr(manager.jugador, 'god_mode', False)
            if manager.jugador.god_mode:
                manager.jugador.texto_martillo.text = 'MODO DIOS: ACTIVO'
                manager.jugador.texto_martillo.color = color.cyan
            else:
                manager.jugador.texto_martillo.text = 'MARTILLO: INACTIVO' if not manager.jugador.tiene_martillo else f'MARTILLO: {int(manager.jugador.tiempo_martillo)}s'
                manager.jugador.texto_martillo.color = color.orange if not manager.jugador.tiene_martillo else color.red

    if key == 'p' and not pausa_activa:
        # PRUEBA ESPECIAL A PEDIDO
        if manager.jugador and not fase_jefe_iniciada:
            iniciar_cinematica_jefe()


fase_jefe_iniciada = False

def iniciar_cinematica_jefe():
    global fase_jefe_iniciada
    fase_jefe_iniciada = True
    
    if manager.jugador:
            manager.jugador.activar(False)
            camera.parent = scene
            
            # Detener el spawner de la intro para que no haya saltos del jefe durante la cinemática final
            if hasattr(manager, 'spawner') and manager.spawner:
                manager.spawner.activo = False
            
            # Limpiar base_y_original para que el spawner 3D calcule la altura correcta
            if hasattr(manager, 'jefe') and hasattr(manager.jefe, 'base_y_original'):
                del manager.jefe.base_y_original
            
            # Ocultar HUD y arma para que parezca una cámara cinematográfica
            if manager.jugador.tiene_martillo:
                manager.jugador.martillo_pivot.visible = False
            manager.jugador.texto_martillo.visible = False
            manager.jugador.texto_puntuacion.visible = False
            if hasattr(manager.jugador, 'barra_estamina'):
                manager.jugador.barra_estamina.visible = False
                manager.jugador.barra_fondo.visible = False
            
            # 1. Saltar a animación 2D (rápido)
            camera.animate_position((0, 45, -150), duration=2, curve=curve.in_out_sine)
            camera.animate_rotation((0, 0, 0), duration=2, curve=curve.in_out_sine)
            
            # 2. Saltar al jefe
            def ir_al_jefe():
                camera.animate_position((-11, 102.5, -40), duration=2, curve=curve.in_out_sine)
            invoke(ir_al_jefe, delay=2.5)
            
            def jefe_salta_cielo():
                if hasattr(manager, 'jefe'):
                    # Salta rápido hacia el cielo para desaparecer de la vista mientras lo miramos
                    manager.jefe.animate_position((manager.jefe.x, 800, manager.jefe.z), duration=0.5, curve=curve.in_expo)
            invoke(jefe_salta_cielo, delay=4.5)
            
            # 3. Volver a vista 2D enfocado ABAJO para empezar a subir con las plataformas
            def enfocar_abajo():
                camera.animate_position((0, 0, -50), duration=2, curve=curve.in_out_sine)
            invoke(enfocar_abajo, delay=5)
            
            # 4. Desaparecer barriles y enderezar plataformas de ABAJO hacia ARRIBA
            def enderezar_y_limpiar():
                # Desaparecer barriles e items
                from src.entidades.barril import Barril
                for b in list(Barril.todos_los_barriles):
                    destroy(b)
                    
                from src.entidades.bono import Bono, BonoMartillo
                for e in scene.entities:
                    if isinstance(e, (Bono, BonoMartillo)):
                        idx = int(round(e.y / 9.0))
                        target_z = idx * 11
                        e.animate_position((e.x, e.y, target_z), duration=0.2, curve=curve.linear)
                
                # Obtener plataformas y ordenarlas de ABAJO hacia ARRIBA
                from src.entidades.entorno import Plataforma, PlataformaTrampa, PlataformaMovil, Teletransportador
                plataformas = [e for e in manager.entidades if isinstance(e, (Plataforma, PlataformaTrampa, PlataformaMovil))]
                plataformas.sort(key=lambda p: p.y)
                
                teleporters = [e for e in manager.entidades if isinstance(e, Teletransportador)]
                teleporters.sort(key=lambda t: t.y)
                
                def soltar_plataforma(plat, index):
                    plat.rotation_z = 0
                    
                    # Profundidad Z: Empieza en 0 y se aleja 11 unidades por nivel hacia el fondo
                    target_z = index * 11
                    # Ancho X: Empieza en 80 y se acorta 5.5 unidades por nivel
                    target_scale_x = 80 - (index * 5.5)
                    
                    plat.animate_position((0, plat.y, target_z), duration=0.2, curve=curve.linear)
                    plat.animate_scale((target_scale_x, 1, 5), duration=0.2, curve=curve.linear)
                    
                    if index < len(teleporters):
                        tel = teleporters[index]
                        signo_actual = 1 if index % 2 == 0 else -1
                        tel_x = (target_scale_x / 2 - 2) * signo_actual
                        tel.animate_position((tel_x, plat.y + 0.5, target_z), duration=0.2, curve=curve.linear)
                        
                        target_scale_x_next = 80 - ((index + 1) * 5.5)
                        # El destino debe ser en el MISMO lado de donde se teletransportó, 
                        # para que tenga que caminar hacia el otro lado a buscar el siguiente
                        dest_x = (target_scale_x_next / 2 - 2) * signo_actual
                        tel.destino = (dest_x, plat.y + 9 + 2, target_z + 11)
                    
                    camera.shake(duration=0.3, magnitude=1.5)
                    # La cámara sube enfocando el centro
                    camera.animate_position((0, plat.y, -50), duration=0.4, curve=curve.linear)
                
                retraso = 0.0
                for i, plat in enumerate(plataformas):
                    invoke(soltar_plataforma, plat, i, delay=retraso)
                    retraso += 0.5
                    
                def preparar_camara_jefe():
                    # Mover cámara frente al jefe para ver su caída
                    camera.animate_position((0, 105, 100), duration=0.5, curve=curve.in_out_sine)
                    camera.animate_rotation((0, 0, 0), duration=0.5, curve=curve.in_out_sine)
                
                invoke(preparar_camara_jefe, delay=retraso)
                
                def caer_jefe():
                    if hasattr(manager, 'jefe'):
                        manager.jefe.position = (0, 800, 121)
                        # Caer con curva linear (sin bounce) para evitar que atraviese la plataforma
                        manager.jefe.animate_position((0, 101, 121), duration=0.5, curve=curve.out_quad)
                        camera.shake(duration=0.5, magnitude=3.0)
                        
                # retraso apunta al instante del último invoke de plataforma.
                # Las animaciones de plataforma duran 0.2s, así que esperamos eso + 0.6s extra.
                invoke(caer_jefe, delay=retraso + 0.8)
                    
                # 6. Lanzamiento del JUGADOR (cámara fija mirando al jefe durante todo el vuelo)
                def lanzar_jugador():
                    if not manager.jugador:
                        return
                    
                    # 1. Colocar al jugador mirando AL JEFE (0° de rotación)
                    manager.jugador.controller.position = (0, 102, 108)
                    manager.jugador.controller.rotation_y = 0  # Mirando de frente al jefe
                    
                    for seq in camera.animations:
                        seq.kill()
                    camera.parent = manager.jugador.controller.camera_pivot
                    camera.position = (0, 0, 0)
                    camera.rotation = (0, 0, 0)
                    camera.fov = 90
                    
                    # Restaurar HUD y arma
                    if manager.jugador.tiene_martillo:
                        manager.jugador.martillo_pivot.visible = True
                    manager.jugador.texto_martillo.visible = True
                    manager.jugador.texto_puntuacion.visible = True
                    if hasattr(manager.jugador, 'barra_estamina'):
                        manager.jugador.barra_estamina.visible = True
                        manager.jugador.barra_fondo.visible = True

                    # 2. EL GOLPE DEL JEFE: Sacudida e impacto
                    camera.shake(duration=0.4, magnitude=3.0)

                    # 3. TRAYECTORIA DEL GOLPE: El jugador vuela hacia atrás MIRANDO FIJO AL JEFE (sin rotar la cámara)
                    # Subida inicial por el impacto (0.8s)
                    manager.jugador.controller.animate_position((0, 135, 60), duration=0.8, curve=curve.out_sine)
                    
                    # Caída directa de espaldas a la primera plataforma (0, 3.5, 0) manteniendo la mirada en el jefe (2.2s)
                    def caer_a_base():
                        manager.jugador.controller.animate_position((0, 3.5, 0), duration=2.2, curve=curve.in_sine)
                    invoke(caer_a_base, delay=0.8)
                    
                    # 4. ATERRIZAJE: Reactivar control manteniendo la mirada fija al jefe en 3D (rotation_y = 0)
                    def fin_lanzamiento():
                        manager.jugador.controller.position = (0, 3.5, 0)
                        manager.jugador.controller.rotation_y = 0  # Mantener mirada al frente hacia el jefe en modo 3D
                        camera.rotation = (0, 0, 0)
                        manager.jugador.activar(True)
                        
                        # Iniciar movimiento del jefe: usar Entity helper (confiable en Ursina)
                        if hasattr(manager, 'jefe'):
                            manager.jefe.base_y_original = manager.jefe.y
                            manager.jefe.direccion_x = 1
                            # Entity helper que mueve al jefe cada frame solo en X
                            jefe_mover = Entity()
                            jefe_ref_local = manager.jefe
                            def _mover_jefe():
                                jefe_ref_local.x += jefe_ref_local.direccion_x * 12 * time.dt
                                if jefe_ref_local.x > 7:
                                    jefe_ref_local.direccion_x = -1
                                elif jefe_ref_local.x < -7:
                                    jefe_ref_local.direccion_x = 1
                            jefe_mover.update = _mover_jefe
                            manager.jefe_mover = jefe_mover  # Guardar referencia para no perderla
                        
                        # Iniciar minijuego de barriles
                        if hasattr(manager, 'spawner') and manager.spawner:
                            destroy(manager.spawner)
                        from src.entidades.barril import BarrilSpawner
                        manager.spawner = BarrilSpawner(position=(0, 101, 121), jugador_ref=manager.jugador, activo=True, modo_rebote3d=True, jefe_ref=getattr(manager, 'jefe', None))

                    invoke(fin_lanzamiento, delay=3.0)
                    
                # Le damos 2.5s después de soltar plataformas para que el jefe aterrice y se muestre claramente en pantalla
                invoke(lanzar_jugador, delay=retraso + 2.5)
                
            invoke(enderezar_y_limpiar, delay=7.5)

# ==========================================================
# UPDATE
# ==========================================================
def update():
    global fase_jefe_iniciada
    if manager.jugador and not fase_jefe_iniciada:
        if manager.jugador.controller.y >= 89.0 and abs(manager.jugador.controller.x) < 5.0:
            iniciar_cinematica_jefe()
            
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
