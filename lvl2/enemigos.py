from ursina import scene
from ursina import Entity, color, time, destroy, Vec3, raycast, Text, invoke, curve
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

    def update(self):
        if pausa.esta_pausado(): return
        dt = time.dt

        # La gravedad se maneja en el raycast inferior
        self.x += self.vel_x * dt

        # Destruir barril muy por debajo del nivel para que se vean caer al vacío
        if self.y < -40.0:
            destroy(self)
            return

        if self.x > 30.5 or self.x < -30.5:
            if hasattr(self, '_altura_fija'):
                delattr(self, '_altura_fija')

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

    def _actualizar_direccion(self, nueva_direccion):
        self.direccion = nueva_direccion
        # Compensamos 90 grados porque el modelo está orientado hacia el eje Z por defecto
        if self.direccion == -1:
            self.rotation_y = 180 - 90
        else:
            self.rotation_y = 0 - 90

    def update(self):
        if pausa.esta_pausado(): return
        
        jugador = next((e for e in scene.entities if getattr(e, 'type', None) == 'jugador'), None)
        if jugador:
            # Cada 2 plataformas (aprox 10 unidades de Y) aumenta la velocidad de lanzamiento
            nivel = max(0, int((jugador.y + 11.0) / 10.0))
            nuevo_playrate = 2.0 + (nivel * 1.5)
            self.actor.setPlayRate(nuevo_playrate, 'Armature|Step_Forward_and_Push|baselayer')
            self.duracion_anim = self.actor.getDuration('Armature|Step_Forward_and_Push|baselayer') / nuevo_playrate

        self._timer += time.dt
        if self._timer >= self._intervalo and not self.animando:
            self._timer = 0.0
            # El próximo intervalo es la duración exacta de la animación
            self._intervalo = self.duracion_anim
            self.iniciar_animacion_lanzamiento()
            
    def iniciar_animacion_lanzamiento(self):
        self.animando = True
        
        # Reproducimos la animación una sola vez por ciclo
        self.actor.play('Armature|Step_Forward_and_Push|baselayer')
        
        # Lanza el barril justo en el momento del "empuje" de la animación (ej. a la mitad del tiempo)
        invoke(self.lanzar_barril, delay=self.duracion_anim * 0.5)
        
        # Se teletransporta justo al terminar la animación
        invoke(self.teletransportar, delay=self.duracion_anim)

    def lanzar_barril(self):
        try:
            if not self.enabled: return
            # Ajustamos un poco la posición de salida del barril para que parezca salir de sus manos
            offset_x = 0.9 * self.direccion
            Barril(pos=self.position + Vec3(offset_x, 1.5, 0), direccion=self.direccion)
        except AssertionError:
            pass

    def teletransportar(self):
        try:
            if not self.enabled: return
            
            jugador = next((e for e in scene.entities if getattr(e, 'type', None) == 'jugador'), None)
            alturas_spawn = [-8.3, -3.3, 1.7, 6.7, 11.7, 16.7, 21.7, 26.7, 31.7]
            
            if jugador:
                mejor_y = min(alturas_spawn, key=lambda y: abs(y - jugador.y))
            else:
                mejor_y = random.choice(alturas_spawn)
                
            if random.choice([True, False]):
                nueva_pos = Vec3(-35.0, mejor_y, 0)
                nueva_dir = 1
            else:
                nueva_pos = Vec3(35.0, mejor_y, 0)
                nueva_dir = -1

            self.position = Vec3(nueva_pos.x, nueva_pos.y - 0.55, nueva_pos.z)
            self._actualizar_direccion(nueva_dir)
            self.animando = False
        except AssertionError:
            pass