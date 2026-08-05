from ursina import scene
from ursina import Entity, color, time, destroy, Vec3, raycast, Text, invoke, curve, Audio, distance
import random
import pausa

GRAVEDAD_BARRIL = 18.0
VEL_BARRIL = 4.5


class BarrilAceite(Entity):
    def __init__(self, posicion):
        super().__init__(model='cylinder', color=color.blue, scale=(1.2, 1.5, 1.2), position=posicion, collider='box')
        self.type = 'aceite'
        Text(parent=self, text='OIL', y=0.6, scale=4, color=color.cyan, origin=(0, 0))


class Barril(Entity):
    def __init__(self, pos, direccion=1):
        super().__init__(position=pos, collider='sphere', scale=1.0)
        self.modelo_visual = Entity(parent=self, model='barril.glb', rotation_x=90, scale=0.40)
        self.modelo_visual.model.setPos(0, -1.027, -12.46)
        self.type = 'barril'
        self.saltado = False
        self.vel_x = direccion * VEL_BARRIL
        self.vel_y = 0.0

        try:
            self.audio_rodar = Audio('RodarBarril.wav', loop=True, autoplay=True, volume=0.0, parent=self)
        except:
            self.audio_rodar = None

    def update(self):
        if pausa.esta_pausado() or getattr(self, 'destruido', False): return
        dt = time.dt

        # La gravedad se maneja en el raycast inferior
        self.x += self.vel_x * dt

        # Destruir barril muy por debajo del nivel para que se vean caer al vacío
        if self.y < -40.0:
            destroy(self)
            return

        # Destruir si sale de los límites del mapa jugable
        if self.x > 36.0 or self.x < -36.0:
            destroy(self)
            return

        ignorar_barriles = tuple(e for e in scene.entities if getattr(e, 'type', None) == 'barril')
        ray = raycast(self.world_position + Vec3(0, 0.05, 0), Vec3(0, -1, 0), distance=0.7, ignore=ignorar_barriles)
        if ray.hit and self.vel_y <= 0:
            self.y = ray.world_point.y + 0.5
            self.vel_y = 0.0
            self._altura_fija = self.y
        else:
            if hasattr(self, '_altura_fija'):
                self.y = self._altura_fija
                self.vel_y = 0.0
            else:
                self.vel_y -= GRAVEDAD_BARRIL * dt
                self.y += self.vel_y * dt

        self.rotation_z -= self.vel_x * 30 * dt

        if getattr(self, 'audio_rodar', None):
            jugador = next((e for e in scene.entities if getattr(e, 'type', None) == 'jugador'), None)
            if jugador:
                dist = distance(self.world_position, jugador.world_position)
                max_dist = 40.0
                # Reduce gradualmente desde 1.0 hasta 0.0 a medida que se aleja
                vol = max(0.0, 1.0 - (dist / max_dist))
                self.audio_rodar.volume = vol
            else:
                self.audio_rodar.volume = 0.0


class DiddyKong(Entity):
    def __init__(self):
        # Todas las posiciones posibles en las plataformas laterales (Ubicación, Dirección de tiro)
        alturas_spawn = [-8.3, -3.3, 1.7, 6.7, 11.7, 16.7, 21.7, 26.7, 31.7]
        self.posiciones_spawn = []
        for y in alturas_spawn:
            self.posiciones_spawn.append((Vec3(-35.0, y, 0), 1))
            self.posiciones_spawn.append((Vec3(35.0, y, 0), -1))

        # Inicia en un lugar aleatorio
        pos_inicial, dir_inicial = random.choice(self.posiciones_spawn)
        
        # Ajustamos la posición Y porque el modelo .glb tiene su origen en los pies 
        # y el cubo anterior lo tenía en el centro.
        pos_ajustada = Vec3(pos_inicial.x, pos_inicial.y - 0.55, pos_inicial.z)

        # Cargando el modelo animado .glb
        # Escala ajustada y aumentada a petición
        super().__init__(scale=2.2, position=pos_ajustada)
        from direct.actor.Actor import Actor
        self.actor = Actor('DIddyKongAnimado/Animation_Step_Forward_and_Push_withSkin.glb')
        self.actor.reparentTo(self)
        
        # Aumentamos la velocidad de la animación al doble para que el juego siga siendo dinámico
        self.actor.setPlayRate(2.0, 'Armature|Step_Forward_and_Push|baselayer')
        # Obtenemos la duración real después del cambio de velocidad
        self.duracion_anim = self.actor.getDuration('Armature|Step_Forward_and_Push|baselayer') / 2.0
        
        self.type = 'enemigo'
        self._actualizar_direccion(dir_inicial)

        self._timer = 0.0
        self._intervalo = 0.0 # Empieza a lanzar inmediatamente
        self.animando = False  # Bandera para saber si está animándose
        self.barriles_por_lanzar = 0
        self.nivel_actual_y = None  # Plataforma actual del enemigo
        
        # Variables para cinemática de caída
        self.cayendo = False
        self.vel_y = 0.0

    def _actualizar_direccion(self, nueva_direccion):
        self.direccion = nueva_direccion
        # Compensamos 90 grados porque el modelo está orientado hacia el eje Z por defecto
        if self.direccion == -1:
            self.rotation_y = 180 - 90
        else:
            self.rotation_y = 0 - 90

    def _spawn_para_jugador(self, jugador_y):
        """Dado el Y del jugador, devuelve la altura de spawn del enemigo correcta.
        
        El jugador camina sobre las plataformas PRINCIPALES (y_levels).
        El enemigo vive en las plataformas LATERALES (alturas_spawn), que están
        2.5 unidades ENCIMA de la plataforma principal correspondiente.
        Por eso debemos buscar el y_level más cercano al jugador primero,
        y luego ir al alturas_spawn[i] correspondiente.
        """
        y_levels   = [-11.5, -6.5, -1.5,  3.5,  8.5, 13.5, 18.5, 23.5, 28.5, 33.5]
        alturas_spawn = [-8.3, -3.3,  1.7,  6.7, 11.7, 16.7, 21.7, 26.7, 31.7]
        # Encontrar el índice de la plataforma principal más cercana al jugador
        idx = min(range(len(y_levels) - 1), key=lambda i: abs(y_levels[i] - jugador_y))
        return alturas_spawn[idx]

    def update(self):
        if pausa.esta_pausado(): return
        
        # Cinemática de victoria: el enemigo cae al vacío
        if self.cayendo:
            self.vel_y -= 15 * time.dt
            self.y += self.vel_y * time.dt
            # Para que también rote mientras cae
            self.rotation_z += 360 * time.dt
            return

        jugador = next((e for e in scene.entities if getattr(e, 'type', None) == 'jugador'), None)
        if jugador:
            # Cada 2 plataformas (aprox 10 unidades de Y) aumenta la velocidad de lanzamiento
            nivel = max(0, int((jugador.y + 11.0) / 10.0))
            nuevo_playrate = 2.0 + (nivel * 1.5)
            self.actor.setPlayRate(nuevo_playrate, 'Armature|Step_Forward_and_Push|baselayer')
            self.duracion_anim = self.actor.getDuration('Armature|Step_Forward_and_Push|baselayer') / nuevo_playrate
            
            # Detectar si el jugador cambió de plataforma (comparar con plataformas principales)
            mejor_y = self._spawn_para_jugador(jugador.y)
            # Si el jugador está en otra plataforma y el enemigo no está animando, seguirle
            if self.nivel_actual_y != mejor_y and not self.animando:
                self.nivel_actual_y = mejor_y
                self._ir_a_plataforma(mejor_y)

        self._timer += time.dt
        if self._timer >= self._intervalo and not self.animando:
            self._timer = 0.0
            if self.barriles_por_lanzar <= 0:
                self.barriles_por_lanzar = 2  # siempre 2 barriles por ráfaga
                self._cambiar_lado()           # lado aleatorio antes de cada ráfaga
            self.iniciar_animacion_lanzamiento()

    def _ir_a_plataforma(self, mejor_y):
        """Teletransporta al enemigo a la plataforma del jugador, eligiendo lado aleatorio."""
        try:
            if not self.enabled: return
            # Elegir lado ALEATORIO cada vez que sigue al jugador
            if random.choice([True, False]):
                nueva_x, nueva_dir = -35.0, 1
            else:
                nueva_x, nueva_dir = 35.0, -1
            self.position = Vec3(nueva_x, mejor_y - 0.55, 0)
            self._actualizar_direccion(nueva_dir)
        except AssertionError:
            pass

    def _cambiar_lado(self):
        """Cambia aleatoriamente el lado desde donde lanza, en la plataforma correcta del jugador."""
        try:
            if not self.enabled: return
            jugador = next((e for e in scene.entities if getattr(e, 'type', None) == 'jugador'), None)
            if jugador:
                mejor_y = self._spawn_para_jugador(jugador.y)
            else:
                alturas_spawn = [-8.3, -3.3, 1.7, 6.7, 11.7, 16.7, 21.7, 26.7, 31.7]
                mejor_y = self.nivel_actual_y or alturas_spawn[0]
            self.nivel_actual_y = mejor_y
            if random.choice([True, False]):
                nueva_x, nueva_dir = -35.0, 1
            else:
                nueva_x, nueva_dir = 35.0, -1
            self.position = Vec3(nueva_x, mejor_y - 0.55, 0)
            self._actualizar_direccion(nueva_dir)
        except AssertionError:
            pass
            
    def iniciar_animacion_lanzamiento(self):
        self.animando = True
        
        # Reproducimos la animación una sola vez por ciclo
        self.actor.play('Armature|Step_Forward_and_Push|baselayer')
        
        # Lanza el barril justo en el momento del "empuje" de la animación (ej. a la mitad del tiempo)
        invoke(self.lanzar_barril, delay=self.duracion_anim * 0.5)
        
        # Llama a finalizar lanzamiento cuando termina la animación
        invoke(self.finalizar_lanzamiento, delay=self.duracion_anim)

    def finalizar_lanzamiento(self):
        try:
            if not self.enabled: return
            self.barriles_por_lanzar -= 1
            if self.barriles_por_lanzar > 0:
                # Hay más barriles en la ráfaga: reproducir animación de nuevo inmediatamente
                self.animando = False
                self._intervalo = 0.0   # disparar en el próximo frame
                self._timer = 999.0     # forzar que el update lo detecte de inmediato
            else:
                # Ráfaga terminada: esperar 2 segundos
                self._intervalo = 2.0
                self._timer = 0.0
                self.animando = False
        except AssertionError:
            pass

    def lanzar_barril(self):
        try:
            if not self.enabled: return
            # El enemigo está en la plataforma lateral (x=±35).
            # Las plataformas laterales terminan en x=±33 y las principales empiezan en x=±28.
            # Hay un hueco de ~5 unidades donde el barril cae al vacío.
            # Solución: spawnear el barril en el BORDE INTERIOR de la plataforma principal
            # que está justo debajo del enemigo (2.5 unidades más abajo).
            #
            # Si el enemigo está a la izquierda (x=-35, dir=1)  → barril en x=-27.5, va a la derecha
            # Si el enemigo está a la derecha (x=35, dir=-1) → barril en x=27.5, va a la izquierda
            spawn_x = -27.5 * self.direccion
            # La plataforma principal está ~2.5 unidades abajo de la lateral
            # El barril debe aparecer justo encima de ella
            spawn_y = self.position.y - 2.5
            Barril(pos=Vec3(spawn_x, spawn_y, 0), direccion=self.direccion)
        except AssertionError:
            pass

    def teletransportar(self):
        """Alias: elige nuevo lado al azar en la plataforma del jugador."""
        self._cambiar_lado()