from ursina import (
    Entity, color, held_keys, time, Text, destroy,
    Vec3, raycast, clamp, invoke, scene, mouse, camera, EditorCamera,
    Sequence, Func, curve
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
        super().__init__(model='cube', color=color.violet, scale=(1.0, 1.4, 1.0), position=posicion, collider='box')
        self.type = 'meta'


class Jugador(Entity):
    def __init__(self, posicion):
        super().__init__(position=posicion, collider='box', model='cube', scale=(0.7, 0.8, 0.7), color=color.blue)
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
        camera.parent = self
        camera.position = (0, 0.2, 0)
        camera.rotation = (0, 0, 0)
        # Ocultamos el cubo del jugador con transparencia en lugar de visible=False para no ocultar la mano
        self.color = color.rgba(0, 0, 0, 0)

        self.texto_vidas = Text(text='VIDA: 3', position=(-0.83, 0.46), scale=2.2, color=color.red, background=True)
        self.texto_puntos = Text(text='PUNTOS: 0', position=(-0.02, 0.46), origin=(0, 0), scale=2.0, color=color.yellow,
                                 background=True)

        # Pivot emparentado a la CÁMARA, esquina inferior derecha estilo FPS
        self.pivot_martillo = Entity(parent=camera, position=(0.5, 0.01, 1.0), enabled=False)
        self.martillo_rotador = Entity(parent=self.pivot_martillo, rotation=(-189, 103, 188))
        self.martillo_actual = None

        mouse.locked = True
        mouse.visible = False

    def input(self, key):
        if key == 'left mouse down' and self.tiene_martillo and not getattr(self, '_atacando_martillo', False):
            self._atacar_con_martillo()

        if camera.parent == self:
            if key == 'space' and self.en_suelo:
                self.vel_y = FUERZA_SALTO
                self.en_suelo = False
                self.escalando = False
            elif key == 'space up' and self.vel_y > 0:
                self.vel_y *= 0.5

        if key == 'c':
            if camera.parent == self:
                camera.parent = scene
                camera.position = (0, 14, -140)
                camera.rotation = (8, 0, 0)
            else:
                camera.parent = self
                camera.position = (0, 0.2, 0)
                camera.rotation = (0, 0, 0)
                camera.rotation_x = 0

    def update(self):
        if self._ganando or pausa.esta_pausado(): return
        dt = time.dt

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

        # Movimiento horizontal SIEMPRE ACTIVO
        move_dir = Vec3(0, 0, 0)
        if camera.parent == self:
            if held_keys['w'] or held_keys['up arrow']: move_dir += self.forward
            if held_keys['s'] or held_keys['down arrow']: move_dir += self.back
            if held_keys['a'] or held_keys['left arrow']: move_dir += self.left
            if held_keys['d'] or held_keys['right arrow']: move_dir += self.right
        
        if move_dir.length() > 0:
            mov_normalizado = move_dir.normalized()
            self.position += mov_normalizado * self.velocidad * dt
            
        self.x = clamp(self.x, -32.0, 32.0)
        self.z = 0.0  # Fijo en 0 para evitar esquivar por profundidad

        escalera_cercana = _obtener_escalera_cercana(self)
        
        # Lógica de escalera
        # Solo nos agarramos si no estamos saltando hacia arriba
        if escalera_cercana and self.vel_y <= 0:
            self.escalando = True
            self.vel_y = 0
            
            # Subir o bajar
            if camera.parent == self:
                if held_keys['space']: 
                    self.y += 3.5 * dt
                if held_keys['left shift'] or held_keys['q']:
                    ray_abajo = raycast(self.world_position, Vec3(0, -1, 0), distance=DISTANCIA_PISO + 0.1, ignore=(self,))
                    if ray_abajo.hit:
                        self.y = ray_abajo.world_point.y + DISTANCIA_PISO
                        self.en_suelo = True
                        self.escalando = False
                    else:
                        self.y -= 3.5 * dt
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
        hit_info = self.intersects()
        if not hit_info.hit: return
        e = hit_info.entity
        if not getattr(e, 'type', None): return

        if e.type == 'martillo' and not getattr(e, 'recogido', False):
            self.tiene_martillo = True
            self.pivot_martillo.enabled = True
            e.recogido = True
            e.collider = None
            e.parent = self.martillo_rotador
            e.position = (0, 1.34, 0)
            e.rotation = (0, 0, 0)
            e.origin = (0, 0, 0)
            self.pivot_martillo.rotation_x = 0
            self.pivot_martillo.rotation_z = 0  # Posición inicial
            e.scale = 0.0015
            self.martillo_actual = e
            
            invoke(self._perder_martillo, delay=10)

        elif e.type == 'barril' or e.type == 'llama':
            if self._invulnerable: return
            if self.tiene_martillo:
                self._sumar_puntos(500)
                destroy(e)
            else:
                self._recibir_danio()

        elif e.type == 'meta':
            self._ganar()
        elif e.type == 'muerte':
            self._recibir_danio()

    def _atacar_con_martillo(self):
        self._atacando_martillo = True
        
        def paso_1_caida():
            # Baja el brazo (posición) y rota hacia adelante sin exagerar el ángulo
            self.pivot_martillo.animate_rotation_x(-75, duration=0.45, curve=curve.in_sine)
            self.pivot_martillo.animate_position((0.5, -0.65, 1.2), duration=0.45, curve=curve.in_sine)
            
        def paso_2_recuperacion():
            # Regresa a la posición y rotación original
            self.pivot_martillo.animate_rotation_x(0, duration=0.55, curve=curve.out_elastic)
            self.pivot_martillo.animate_position((0.5, 0.01, 1.0), duration=0.55, curve=curve.out_elastic)
            
        def liberar_ataque():
            self._atacando_martillo = False

        Sequence(
            Func(paso_1_caida),
            0.45,
            Func(paso_2_recuperacion),
            0.55,
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
        pausa.mostrar_victoria(self.puntos)

    def _recibir_danio(self):
        if self._invulnerable: return
        self.vidas -= 1
        self._invulnerable = True
        self.texto_vidas.text = f'VIDA: {self.vidas}'

        # Los barriles ya no se destruyen al recibir daño
        # (Solo se destruyen cuando salen de la plataforma y caen al vacío)

        self.x, self.y, self.z = self._spawn.x, self._spawn.y, self._spawn.z
        self.vel_y = 0
        self.escalando = False
        self.tiene_martillo = False
        if getattr(self, 'martillo_actual', None):
            destroy(self.martillo_actual)
            self.martillo_actual = None

        invoke(self._fin_invulnerabilidad, delay=2)
        if self.vidas <= 0: self._game_over()

    def _fin_invulnerabilidad(self):
        self._invulnerable = False

    def _perder_martillo(self):
        self.tiene_martillo = False
        self._atacando_martillo = False
        self.pivot_martillo.enabled = False
            
        if getattr(self, 'martillo_actual', None):
            destroy(self.martillo_actual)
            self.martillo_actual = None

    def _game_over(self):
        pausa.mostrar_game_over()

    def on_destroy(self):
        if hasattr(self, 'texto_vidas') and self.texto_vidas: destroy(self.texto_vidas)
        if hasattr(self, 'texto_puntos') and self.texto_puntos: destroy(self.texto_puntos)


def generar_martillos():
    alturas = [-4.0, 1.0, 6.0, 11.0, 16.0, 21.0, 26.0, 31.0]
    seleccionadas = random.sample(alturas, 2)
    for y in seleccionadas:
        x = random.uniform(-28.0, 28.0)
        Martillo(posicion=(x, y, 0))