from ursina import *

class Bono(Entity):
    def __init__(self, position, jugador_ref, multiplicador=2):
        super().__init__(
            model='cube',
            color=color.gold,
            texture='white_cube',
            collider='box',
            position=position,
            scale=(1.5, 1.5, 1.5)
        )
        self.multiplicador = multiplicador
        self.jugador_ref = jugador_ref
        self.activo = True

    def update(self):
        self.rotation_y += 50 * time.dt
        self.rotation_x += 30 * time.dt

        if not self.activo or not self.jugador_ref or not hasattr(self.jugador_ref, 'controller'):
            return

        jug_x = self.jugador_ref.controller.x
        jug_y = self.jugador_ref.controller.y
        jug_z = self.jugador_ref.controller.z
        
        dist_x = abs(self.x - jug_x)
        dist_z = abs(self.z - jug_z)
        dist_y = abs(self.y - jug_y)
        
        if dist_x < 2.0 and dist_z < 2.0 and dist_y < 2.5:
            self.activo = False
            self.jugador_ref.multiplicador = self.multiplicador
            self.jugador_ref.actualizar_ui()
            texto = Text(text=f'¡x{self.multiplicador} Activado!', position=(0, 0.2), scale=3, color=color.gold, origin=(0,0))
            destroy(texto, delay=2)
            destroy(self)

class BonoMartillo(Entity):
    def __init__(self, position, jugador_ref):
        super().__init__(
            model='cube',
            color=color.dark_gray,
            texture='white_cube',
            collider='box',
            position=position,
            scale=(1.5, 1.5, 1.5)
        )
        self.jugador_ref = jugador_ref
        self.activo = True

    def update(self):
        self.rotation_y += 50 * time.dt
        self.rotation_x += 30 * time.dt

        if not self.activo or not self.jugador_ref or not hasattr(self.jugador_ref, 'controller'):
            return

        jug_x = self.jugador_ref.controller.x
        jug_y = self.jugador_ref.controller.y
        jug_z = self.jugador_ref.controller.z
        
        dist_x = abs(self.x - jug_x)
        dist_z = abs(self.z - jug_z)
        dist_y = abs(self.y - jug_y)
        
        if dist_x < 2.0 and dist_z < 2.0 and dist_y < 2.5:
            self.activo = False
            self.jugador_ref.activar_martillo()
            texto = Text(text='¡MARTILLO ACTIVADO!', position=(0, 0.2), scale=3, color=color.red, origin=(0,0))
            destroy(texto, delay=2)
            destroy(self)
