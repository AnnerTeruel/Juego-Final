from ursina import *

class Suelo(Entity):
    def __init__(self):
        super().__init__(
            model='plane',
            scale=(200, 1, 200),
            color=color.dark_gray,
            collider='box',
            position=(0, -2, 0)
        )

class Plataforma(Entity):
    def __init__(self, position, rotation_z=0, scale=(30, 1, 5), color_plat=color.azure):
        super().__init__(
            model='cube',
            color=color_plat,
            texture='white_cube',
            collider='box',
            position=position,
            rotation_z=rotation_z,
            scale=scale
        )
        self.rotacion_original = rotation_z
        self.estado_inclinacion = 0 # 0: original, 1: recta, 2: invertida
        
    def alternar_inclinacion(self):
        self.estado_inclinacion = (self.estado_inclinacion + 1) % 3
        
        if self.estado_inclinacion == 0:
            self.rotation_z = self.rotacion_original
        elif self.estado_inclinacion == 1:
            self.rotation_z = 0
        elif self.estado_inclinacion == 2:
            self.rotation_z = -self.rotacion_original

class PlataformaTrampa(Plataforma):
    def __init__(self, position, rotation_z=0, scale=(30, 1, 5), color_plat=color.azure, jugador_ref=None):
        super().__init__(position, rotation_z, scale, color_plat)
        self.jugador_ref = jugador_ref
        self.trampa_activada = False
        self.desaparecida = False
        self.tiempo_restante = 5.0      # Ahora el parpadeo dura 5 segundos
        self.tiempo_reaparicion = 8.0   # Tarda 8 segundos en volver a aparecer
        self.parpadeo_timer = 0
        self.color_base = color_plat
        
    def update(self):
        # 1. Estado: Desaparecida (contando para reaparecer)
        if self.desaparecida:
            self.tiempo_reaparicion -= time.dt
            if self.tiempo_reaparicion <= 0:
                # Restaurar plataforma
                self.visible = True
                self.collider = 'box'
                self.color = self.color_base
                self.desaparecida = False
                self.trampa_activada = False
                self.tiempo_restante = 5.0
                self.tiempo_reaparicion = 8.0
            return

        # 2. Estado: Normal (esperando a que el jugador la pise)
        if not self.trampa_activada:
            if self.jugador_ref and self.jugador_ref.controller:
                dx = abs(self.x - self.jugador_ref.controller.x)
                dz = abs(self.z - self.jugador_ref.controller.z)
                # Si el jugador está sobre los límites de la plataforma
                if dx < self.scale_x / 2 and dz < self.scale_z / 2:
                    # Y si está a la altura correcta (parado sobre ella)
                    if self.y <= self.jugador_ref.controller.y <= self.y + 3.0:
                        self.trampa_activada = True
                        
        # 3. Estado: Activada (Parpadeando en rojo)
        else:
            if self.tiempo_restante > 0:
                self.tiempo_restante -= time.dt
                self.parpadeo_timer += time.dt
                # Efecto de parpadeo rojo
                if self.parpadeo_timer > 0.15:
                    self.color = color.red if self.color == self.color_base else self.color_base
                    self.parpadeo_timer = 0
            else:
                # Desaparecer físicamente sin usar disable() para que update() siga corriendo
                self.visible = False
                self.collider = None
                self.desaparecida = True

class PlataformaMovil(Plataforma):
    def __init__(self, position, rotation_z=0, scale=(30, 1, 5), mov_x=0, mov_z=0, velocidad=1):
        super().__init__(position, rotation_z, scale, color_plat=color.orange)
        self.start_x = position[0]
        self.start_z = position[2]
        self.mov_x = mov_x
        self.mov_z = mov_z
        self.velocidad = velocidad
        self.en_movimiento = False
        
    def update(self):
        import math
        if not self.en_movimiento:
            return
            
        tiempo = time.time() * self.velocidad
        self.x = self.start_x + math.sin(tiempo) * self.mov_x
        self.z = self.start_z + math.cos(tiempo) * self.mov_z

class Escalera(Entity):
    def __init__(self, position, scale=(2, 10, 0.5)):
        super().__init__(
            model='cube',
            color=color.yellow,
            texture='white_cube',
            collider='box',
            position=position,
            scale=scale
        )

class Teletransportador(Entity):
    def __init__(self, position, destino, scale=(3, 3, 3)):
        super().__init__(
            model='sphere',
            color=color.cyan,
            collider='box',
            position=position,
            scale=scale
        )
        self.destino = destino
        
    def update(self):
        self.rotation_y += 100 * time.dt
