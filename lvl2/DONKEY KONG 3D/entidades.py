from ursina import (
    Entity, color, held_keys, time, Text, destroy,
    Vec3, raycast, clamp, invoke, scene, mouse, camera, EditorCamera,
    Sequence, Func, curve, Audio
)
import pausa
import config
import random
import math

GRAVEDAD = 20.0
FUERZA_SALTO = 8.0
VELOCIDAD_MOV = 4.0
DISTANCIA_PISO = 0.45
RAY_DISTANCIA = 1.2
RADIO_ESCALERA_X = 0.70
RADIO_ESCALERA_Y = 0.55


def _obtener_escalera_cercana(jugador):
    jx, jy = jugador.x, jugador.y
    for e in scene.entities:
        if getattr(e, 'type', None) != 'escalera': continue
        sx = getattr(e, 'ancho', e.scale_x) * 0.5
        sy = getattr(e, 'alto', e.scale_y) * 0.5
        if (abs(jx - e.x) < RADIO_ESCALERA_X + sx and abs(jy - e.y) < RADIO_ESCALERA_Y + sy):
            return e
    return None


class Martillo(Entity):
    def __init__(self, posicion):
        super().__init__(model='toy_hammer.glb', color=color.yellow, scale=0.0015, position=posicion, collider='box')
        self.type = 'martillo'
        self.recogido = False
        self._t = 0

    def update(self):
        if pausa.esta_pausado() or self.recogido: return
        self._t += time.dt
        self.y += 0.005 * (1 if (self._t % 1) < 0.5 else -1)


class Meta(Entity):
    def __init__(self, posicion):
        # Colisionador invisible para la detección de victoria
        super().__init__(model='cube', color=color.rgba(0,0,0,0), scale=(1.2, 2.0, 1.2),
                         position=posicion, collider='box')
        self.type = 'meta'
        # Modelo visual de la palanca — estático, sobre la plataforma
        self.visual = Entity(
            parent=self,
            model='palanca level 2.glb',
            scale=0.45,
            position=(0, -0.5, 0),
            color=color.white
        )


class ParticulaBarril(Entity):
    def __init__(self, posicion):
        super().__init__(model='cube', color=color.brown, scale=random.uniform(0.15, 0.3), position=posicion)
        self.vel = Vec3(random.uniform(-5, 5), random.uniform(4, 10), random.uniform(-5, 5))
        self.rot_vel = Vec3(random.uniform(-400, 400), random.uniform(-400, 400), random.uniform(-400, 400))
        invoke(destroy, self, delay=0.6)
        
    def update(self):
        if pausa.esta_pausado(): return
        dt = time.dt
        self.vel.y -= 25 * dt  # Gravedad
        self.position += self.vel * dt
        self.rotation += self.rot_vel * dt


class Jugador(Entity):
    def __init__(self, posicion):
        super().__init__(position=posicion, collider='box', model='cube', scale=(0.7, 0.8, 0.7), color=color.blue)
        self.type = 'jugador'
        self.vel_y = 0.0
        self.en_suelo = False
        self.escalando = False
        self.velocidad = VELOCIDAD_MOV
        self.vidas = 3

        self.puntos = 0
        self.high_score = 0
        self.ui_high_ref = None

        self.tiene_martillo = False
        self._atacando_martillo = False
        self._invulnerable = False
        self._spawn = Vec3(posicion)
        self._ganando = False

        # Configuración de Primera Persona
        self.rotation_y = 90
        # Ocultamos el cubo del jugador con transparencia en lugar de visible=False para no ocultar la mano
        self.color = color.rgba(0, 0, 0, 0)
        
        self._en_cinematica = True
        self._cinematica_inicio()

        # --- HUD BARRA SUPERIOR PROFESIONAL ---
        self.hud_fondo = Entity(parent=camera.ui, model='quad', color=color.Color(0.05, 0.05, 0.12, 0.9), scale=(1.8, 0.07), position=(0, 0.465), z=10)
        self.hud_linea = Entity(parent=camera.ui, model='quad', color=color.Color(1.0, 0.84, 0.0, 0.9), scale=(1.8, 0.003), position=(0, 0.43), z=9.9)

        self.texto_puntos = Text(parent=camera.ui, text=f'PUNTOS: {self.puntos}', position=(-0.82, 0.478), scale=0.75, font='assets/PressStart2P-Regular.ttf', color=color.hex('#FFD700'), z=9)
        self.lbl_vidas = Text(parent=camera.ui, text='VIDAS:', position=(-0.30, 0.478), scale=0.75, font='assets/PressStart2P-Regular.ttf', color=color.hex('#FF2E63'), z=9)
        self.corazones_icons = []
        for i in range(3):
            c = Entity(parent=camera.ui, model='circle', color=color.hex('#FF2E63'), scale=(0.020, 0.020), position=(-0.16 + i * 0.035, 0.465), z=8)
            self.corazones_icons.append(c)

        self.texto_martillo = Text(parent=camera.ui, text='MARTILLO: INACTIVO', position=(0.28, 0.478), origin=(0, 0), scale=0.75, font='assets/PressStart2P-Regular.ttf', color=color.hex('#777799'), z=9)

        # Pivot emparentado a la CÁMARA, esquina inferior derecha estilo FPS
        # Empieza oculto; solo se activa cuando el jugador recoge un martillo
        self.pivot_martillo = Entity(parent=camera, position=(0.5, -1.25, 0.5), enabled=False)
        self.martillo_rotador = Entity(parent=self.pivot_martillo, rotation=(-189, 103, 188))
        self.martillo_actual = Entity(
            parent=self.martillo_rotador, 
            model='toy_hammer.glb', 
            color=color.yellow, 
            scale=0.0005, 
            y=1.34
        )

        mouse.locked = True
        mouse.visible = False
        
        try:
            self.audio_salto = Audio('saltar.wav', autoplay=False, loop=False)
        except:
            self.audio_salto = None

    def destroy_ui(self):
        try:
            if hasattr(self, 'hud_fondo') and self.hud_fondo: destroy(self.hud_fondo)
            if hasattr(self, 'hud_linea') and self.hud_linea: destroy(self.hud_linea)
            if hasattr(self, 'texto_puntos') and self.texto_puntos: destroy(self.texto_puntos)
            if hasattr(self, 'lbl_vidas') and self.lbl_vidas: destroy(self.lbl_vidas)
            if hasattr(self, 'corazones_icons') and self.corazones_icons:
                for c in self.corazones_icons:
                    destroy(c)
                self.corazones_icons = []
            if hasattr(self, 'texto_martillo') and self.texto_martillo: destroy(self.texto_martillo)
            if hasattr(self, 'pivot_martillo') and self.pivot_martillo: destroy(self.pivot_martillo)
        except Exception:
            pass

    def _cinematica_inicio(self):
        # Desactivamos el ratón para que el jugador no pueda mover la cámara todavía
        mouse.locked = False
        
        # Posición inicial de la cámara para ver todo el mapa (similar a la de victoria pero de frente)
        camera.parent = scene
        camera.position = (0, 11, -85)
        camera.rotation = (0, 0, 0)
        
        # Animamos la cámara hacia la posición del jugador
        delay_inicio = 1.0
        duracion_vuelo = 2.5
        
        pos_objetivo = self.position + Vec3(0, 0.8, 0)
        
        invoke(camera.animate_position, pos_objetivo, duration=duracion_vuelo, curve=curve.in_out_sine, delay=delay_inicio)
        invoke(camera.animate_rotation, (0, 90, 0), duration=duracion_vuelo, curve=curve.in_out_sine, delay=delay_inicio)
        
        # Al terminar, devolvemos el control
        invoke(self._fin_cinematica_inicio, delay=delay_inicio + duracion_vuelo + 0.1)

    def _fin_cinematica_inicio(self):
        self._en_cinematica = False
        mouse.locked = True
        camera.parent = self
        camera.position = (0, 0.8, 0)
        camera.rotation = (0, 0, 0)

    def input(self, key):
        if getattr(self, '_en_cinematica', False): return
        
        if (key == 'left mouse down' or key == 'right mouse down') and self.tiene_martillo and not getattr(self, '_atacando_martillo', False):
            self._atacar_con_martillo()

        if camera.parent == self:
            if key == 'space' and self.en_suelo:
                self.vel_y = FUERZA_SALTO
                self.en_suelo = False
                self.escalando = False
                if getattr(self, 'audio_salto', None):
                    try:
                        self.audio_salto.play()
                    except:
                        pass
            elif key == 'space up' and self.vel_y > 0:
                self.vel_y *= 0.5





    def update(self):
        if self._ganando or pausa.esta_pausado() or getattr(self, '_en_cinematica', False): return
        dt = time.dt

        if getattr(self, 'tiene_martillo', False):
            self.tiempo_restante_martillo -= dt
            if self.tiempo_restante_martillo <= 0:
                self._perder_martillo()
            else:
                if hasattr(self, 'texto_martillo') and self.texto_martillo:
                    self.texto_martillo.text = f'MARTILLO: {int(self.tiempo_restante_martillo)}s'

        # Vista de ratón
        if camera.parent == self:
            self.rotation_y += mouse.velocity[0] * config.sensibilidad
            camera.rotation_x -= mouse.velocity[1] * config.sensibilidad
            camera.rotation_x = clamp(camera.rotation_x, -90, 90)
        else:
            camera.rotation_y += mouse.velocity[0] * config.sensibilidad
            camera.rotation_x -= mouse.velocity[1] * config.sensibilidad
            camera.rotation_x = clamp(camera.rotation_x, -90, 90)
            
            vel_cam = 40 * dt
            if held_keys['w']: camera.position += camera.forward * vel_cam
            if held_keys['s']: camera.position += camera.back * vel_cam
            if held_keys['a']: camera.position += camera.left * vel_cam
            if held_keys['d']: camera.position += camera.right * vel_cam
            if held_keys['e'] or held_keys['space']: camera.y += vel_cam
            if held_keys['q'] or held_keys['left shift']: camera.y -= vel_cam

        # Sprint / Correr con Shift
        es_sprint = held_keys['left shift'] or held_keys['right shift'] or held_keys['shift']
        vel_actual = self.velocidad * 1.75 if es_sprint else self.velocidad

        # Movimiento horizontal (WASD + Flechas)
        move_x = 0.0
        if camera.parent == self:
            if held_keys['w'] or held_keys['up arrow']: move_x += (1.0 if self.forward.x >= 0 else -1.0)
            if held_keys['s'] or held_keys['down arrow']: move_x -= (1.0 if self.forward.x >= 0 else -1.0)
            if held_keys['d'] or held_keys['right arrow']: move_x += 1.0
            if held_keys['a'] or held_keys['left arrow']: move_x -= 1.0
        
        if move_x != 0:
            dir_norm = 1.0 if move_x > 0 else -1.0
            self.x += dir_norm * vel_actual * dt
            
        self.x = clamp(self.x, -32.0, 32.0)
        self.z = 0.0  # Fijo en 0 para mantener la perspectiva 2.5D

        escalera_cercana = _obtener_escalera_cercana(self)
        
        # Lógica de escalera
        # Solo nos agarramos si no estamos saltando hacia arriba
        if escalera_cercana and self.vel_y <= 0:
            self.escalando = True
            self.vel_y = 0
            
            # Subir (W, Espacio, Flecha Arriba) o Bajar (S, Flecha Abajo, Q)
            vel_escalera = 5.5 * dt if es_sprint else 3.5 * dt
            if camera.parent == self:
                if held_keys['w'] or held_keys['space'] or held_keys['up arrow']: 
                    self.y += vel_escalera
                if held_keys['s'] or held_keys['down arrow'] or held_keys['q']:
                    ray_abajo = raycast(self.world_position, Vec3(0, -1, 0), distance=DISTANCIA_PISO + 0.1, ignore=(self,))
                    if ray_abajo.hit:
                        self.y = ray_abajo.world_point.y + DISTANCIA_PISO
                        self.en_suelo = True
                        self.escalando = False
                    else:
                        self.y -= vel_escalera
        else:
            self.escalando = False

        if not self.escalando:
            # Calcular la distancia del rayo dinámicamente para no aterrizar de golpe
            distancia_rayo = DISTANCIA_PISO + (abs(self.vel_y) * dt) + 0.05
            ray = raycast(self.world_position, Vec3(0, -1, 0), distance=distancia_rayo, ignore=(self,))
            if ray.hit and self.vel_y <= 0:
                self.y = ray.world_point.y + DISTANCIA_PISO
                self.vel_y = 0
                self.en_suelo = True
            else:
                self.en_suelo = False

            if not self.en_suelo:
                # Menos gravedad en el punto más alto para un arco de salto más fluido ("hang time")
                mult_gravedad = 0.5 if abs(self.vel_y) < 3.0 else 1.0
                self.vel_y -= (GRAVEDAD * mult_gravedad) * dt
                self.y += self.vel_y * dt

        # (Animación de martillo controlada por Sequence al hacer clic)

        self._revisar_colisiones()
        self._revisar_salto_barriles()
        if self.y < -20: self._recibir_danio()

    def _revisar_salto_barriles(self):
        if not self.en_suelo and not self.escalando:
            for e in scene.entities:
                try:
                    if getattr(e, 'type', None) == 'barril' and not getattr(e, 'saltado', False):
                        if abs(self.x - e.x) < 1.0 and self.y > e.y and self.y < e.y + 3:
                            e.saltado = True
                            self._sumar_puntos(100)
                except AssertionError:
                    continue

    def _revisar_colisiones(self):
        # Revisar si el jugador recoge un martillo en el suelo
        for e in scene.entities:
            if getattr(e, 'type', None) == 'martillo' and not getattr(e, 'recogido', False):
                try:
                    if (self.world_position - e.world_position).length() < 2.5:
                        e.recogido = True
                        e.collider = None
                        destroy(e)
                        
                        self.tiene_martillo = True
                        self.pivot_martillo.enabled = True
                        self.tiempo_restante_martillo = 10.0
                        self.texto_martillo.text = f'MARTILLO: {int(self.tiempo_restante_martillo)}s'
                        self.texto_martillo.color = color.hex('#FFD700')
                        
                        if hasattr(self, '_timer_martillo') and self._timer_martillo:
                            try: destroy(self._timer_martillo)
                            except: pass
                        break
                except (AssertionError, Exception):
                    continue

        # Ignorar self y el modelo de martillo equipado en primera persona
        elementos_ignorados = (self, getattr(self, 'pivot_martillo', None), getattr(self, 'martillo_actual', None))
        hit_info = self.intersects(ignore=elementos_ignorados)
        if not hit_info.hit: return
        e = hit_info.entity
        if not getattr(e, 'type', None): return
        if getattr(e, 'recogido', False) or getattr(e, 'destruido', False): return

        if e.type == 'barril' or e.type == 'llama':
            if self._invulnerable: return
            if self.tiene_martillo:
                self._sumar_puntos(500)
                e.collider = None
                e.destruido = True
                
                # Sonido de destrucción del barril
                try:
                    Audio('destruirBarril.wav', autoplay=True, auto_destroy=True, volume=1.0)
                except:
                    pass
                
                for _ in range(8):
                    ParticulaBarril(e.world_position)
                    
                destroy(e)
            else:
                self._recibir_danio()

        elif e.type == 'meta':
            # Solo activa victoria si el jugador está en la plataforma superior de la palanca (Y >= 33)
            if self.y >= 33.0:
                self._ganar()
        elif e.type == 'muerte':
            self._recibir_danio()

    def _atacar_con_martillo(self):
        self._atacando_martillo = True
        try:
            Audio('MovimientoMartillo.wav', autoplay=True, auto_destroy=True, volume=1.0)
        except Exception:
            pass

        def paso_1_caida():
            # El martillo ahora da un martillazo girando hacia abajo con la parte roja
            self.pivot_martillo.animate_rotation_x(80, duration=0.25, curve=curve.in_sine)

        def paso_2_recuperacion():
            # Regresa a la posicion original
            self.pivot_martillo.animate_rotation_x(0, duration=0.35, curve=curve.out_expo)

        def liberar_ataque():
            self._atacando_martillo = False

        Sequence(
            Func(paso_1_caida),
            0.25,
            Func(paso_2_recuperacion),
            0.35,
            Func(liberar_ataque)
        ).start()

    def _sumar_puntos(self, cantidad):
        self.puntos += cantidad
        self.texto_puntos.text = f'PUNTOS: {self.puntos}'
        if self.puntos > self.high_score:
            self.high_score = self.puntos
            if self.ui_high_ref: self.ui_high_ref.text = f'TOP: {self.high_score}'

    def _ganar(self):
        if self._ganando: return
        self._ganando = True
        self._sumar_puntos(1000)
        # Detener música de fondo y reproducir fanfarria de victoria
        try:
            for e in scene.entities:
                if hasattr(e, 'clip') and getattr(e, 'loop', False):
                    e.stop()
            Audio('Ganar.wav', autoplay=True, auto_destroy=True, volume=1.0)
        except:
            pass
        # Bloquear ratón y liberar cámara para la cinemática
        mouse.locked = False
        mouse.visible = True
        camera.parent = scene
        invoke(self._cinematica_victoria, delay=0.1)

    def _cinematica_victoria(self):
        # Recopilar plataformas LATERALES (x > 30 ó x < -30) ordenadas de menor a mayor Y
        vigas_lat = sorted(
            [e for e in scene.entities
             if getattr(e, 'type', None) == 'viga' and abs(e.x) > 30],
            key=lambda e: e.y
        )

        # Agrupar por nivel Y (izquierda y derecha del mismo piso)
        niveles = {}
        for v in vigas_lat:
            nivel = round(v.y, 1)
            niveles.setdefault(nivel, []).append(v)

        niveles_ordenados = sorted(niveles.items())   # de abajo hacia arriba

        DURACION_POR_PISO = 0.5   # segundos por plataforma, más rápido
        delay = 0.0

        # Mover la cámara para ver todo el nivel (centro aprox y=11, lejos en z)
        cam_pos_global = Vec3(0, 11, -85)
        invoke(self._mover_camara_a, cam_pos_global, duration=1.5, delay=delay)
        delay += 1.5

        # Destruir plataformas de abajo hacia arriba
        for i, (y_nivel, vigas_grupo) in enumerate(niveles_ordenados):
            # Destruir las vigas del nivel con escala → 0
            invoke(self._destruir_grupo, vigas_grupo, delay=delay)
            delay += DURACION_POR_PISO

        # Activar gravedad en el enemigo para que caiga
        invoke(self._activar_gravedad_enemigo, delay=delay)
        delay += 2.0

        # Mostrar victoria tras la cinemática
        invoke(pausa.mostrar_victoria, self.puntos, delay=delay)

    def _mover_camara_a(self, pos, duration=0.5):
        camera.animate_position(pos, duration=duration, curve=curve.in_out_sine)
        camera.animate_rotation((0, 0, 0), duration=duration)

    def _destruir_grupo(self, vigas):
        for v in vigas:
            try:
                v.animate_scale_y(0, duration=0.35, curve=curve.out_expo)
                invoke(destroy, v, delay=0.4)
            except Exception:
                pass

    def _activar_gravedad_enemigo(self):
        for e in scene.entities:
            if getattr(e, 'type', None) == 'enemigo':
                e.cayendo = True
                
                # Creamos el seguidor on-the-fly con update
                class SeguidorCaida(Entity):
                    def update(self):
                        self.position = e.position
                
                s = SeguidorCaida(parent=scene)
                camera.parent = s
                camera.position = (0, 30, 0)    # 30 unidades por encima
                camera.rotation = (90, 0, 0)    # Mirando directamente hacia abajo
                
                # Efecto oscurecer pantalla (fade to black)
                pantalla_negra = Entity(parent=camera.ui, model='quad', color=color.clear, scale=(20, 20), z=-1)
                pantalla_negra.animate_color(color.black, duration=2.0)
                break

    def _actualizar_ui_vidas(self):
        for i, icon in enumerate(self.corazones_icons):
            if i < self.vidas:
                icon.color = color.hex('#FF2E63')
                icon.scale = (0.022, 0.022)
            else:
                icon.color = color.hex('#2A2A38')
                icon.scale = (0.016, 0.016)

    def _recibir_danio(self):
        if self._invulnerable: return
        self.vidas -= 1
        self._invulnerable = True
        self._actualizar_ui_vidas()

        # Animación de muerte en primera persona
        self._en_cinematica = True
        
        # La cámara "cae" hacia atrás y mira un poco hacia arriba
        camera.animate_position((0, -0.6, -1.0), duration=0.6, curve=curve.out_expo)
        camera.animate_rotation((-60, 0, 25), duration=0.6, curve=curve.out_expo)
        
        # Destello rojo
        pantalla_roja = Entity(parent=camera.ui, model='quad', color=color.rgba(1, 0, 0, 0.6), scale=(20, 20), z=-1)
        pantalla_roja.animate_color(color.clear, duration=1.0)
        destroy(pantalla_roja, delay=1.1)

        # Esperar 1 segundo en el suelo antes de reaparecer
        invoke(self._respawn, delay=1.0)
        invoke(self._fin_invulnerabilidad, delay=3.0)

    def _respawn(self):
        self.x, self.y, self.z = self._spawn.x, self._spawn.y, self._spawn.z
        self.vel_y = 0
        self.escalando = False
        self.tiene_martillo = False
        if getattr(self, 'martillo_actual', None):
            destroy(self.martillo_actual)
            self.martillo_actual = None

        # Restaurar cámara FPS
        camera.position = (0, 0.8, 0)
        camera.rotation = (0, 0, 0)
        self.rotation = (0, 90, 0)
        
        if self.vidas <= 0:
            self._game_over()
        else:
            self._en_cinematica = False

    def _fin_invulnerabilidad(self):
        self._invulnerable = False

    def _perder_martillo(self):
        self.tiene_martillo = False
        self._atacando_martillo = False
        if hasattr(self, 'pivot_martillo') and self.pivot_martillo:
            self.pivot_martillo.enabled = False
        if hasattr(self, 'texto_martillo') and self.texto_martillo:
            self.texto_martillo.text = 'MARTILLO: INACTIVO'
            self.texto_martillo.color = color.hex('#777799')

    def _game_over(self):
        # Detener música de fondo y reproducir sonido de derrota
        try:
            from ursina import scene
            for e in scene.entities:
                if hasattr(e, 'clip') and getattr(e, 'loop', False):
                    e.stop()
            Audio('Perder.wav', autoplay=True, auto_destroy=True, volume=1.0)
        except:
            pass
        pausa.mostrar_game_over()

    def on_destroy(self):
        if hasattr(self, 'texto_vidas') and self.texto_vidas: destroy(self.texto_vidas)
        if hasattr(self, 'texto_puntos') and self.texto_puntos: destroy(self.texto_puntos)


def generar_martillos():
    alturas = [-4.0, 1.0, 6.0, 11.0, 16.0, 21.0, 26.0]
    seleccionadas = random.sample(alturas, 2)
    for y in seleccionadas:
        x = random.uniform(-28.0, 28.0)
        Martillo(posicion=(x, y, 0))