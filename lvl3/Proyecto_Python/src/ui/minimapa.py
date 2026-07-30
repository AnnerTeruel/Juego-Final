from ursina import *
from src.entidades.barril import Barril
from src.entidades.entorno import Plataforma

class MiniMapa(Entity):
    def __init__(self, jugador_ref, jefe_ref=None):
        super().__init__(
            parent=camera.ui,
            model='quad',
            color=color.black,
            scale=(0.3, 0.35),
            position=(0.7, 0.3)  # Esquina superior derecha
        )
        self.alpha = 0.3 # Establecemos la transparencia directamente en la entidad (30% opaco)
        self.jugador_ref = jugador_ref
        self.plat_uis = []
        
        # Crear la representación de las plataformas en 2D
        self.dibujar_plataformas()
        
        # Punto verde para el jugador
        self.dot_jugador = Entity(
            parent=self,
            model='circle',
            color=color.green,
            scale=(0.04, 0.04),
            z=-1
        )
        
        # Punto rojo para el jefe
        self.jefe_ref = jefe_ref
        self.dot_jefe = Entity(
            parent=self,
            model='cube',
            color=color.red,
            scale=(0.06, 0.06),
            z=-1
        )
        
        self.dots_barriles = []
        
    def dibujar_plataformas(self):
        # Escaneamos la escena buscando las plataformas para calcarlas en el minimapa
        for p in scene.entities:
            if isinstance(p, Plataforma):
                # Mapeo de coordenadas: 
                # El mundo de Donkey Kong va aprox de X(-50 a 50) y Y(0 a 100)
                # El UI Quad local va de -0.5 a 0.5
                px = p.x / 100
                py = (p.y / 110) - 0.45 
                pw = p.scale_x / 100
                
                ui_ent = Entity(
                    parent=self,
                    model='quad',
                    color=color.azure,
                    scale=(pw, 0.01),
                    position=(px, py, -0.5),
                    rotation_z=p.rotation_z
                )
                self.plat_uis.append((p, ui_ent))

    def update(self):
        # Actualizar plataformas dinámicamente
        for p, ui_ent in self.plat_uis:
            ui_ent.x = p.x / 100
            ui_ent.y = (p.y / 110) - 0.45
            ui_ent.scale_x = p.scale_x / 100
            ui_ent.rotation_z = p.rotation_z
        # Actualizar la posición del jugador
        if self.jugador_ref and self.jugador_ref.controller:
            jx = self.jugador_ref.controller.x / 100
            jy = (self.jugador_ref.controller.y / 110) - 0.45
            self.dot_jugador.position = (jx, jy, -1)
            
        # Actualizar la posición del jefe
        if self.jefe_ref:
            jx = self.jefe_ref.x / 100
            jy = (self.jefe_ref.y / 110) - 0.45
            self.dot_jefe.position = (jx, jy, -1)
            
        # Actualizar los barriles
        # Asegurar tener la misma cantidad de "puntitos" que barriles físicos
        while len(self.dots_barriles) < len(Barril.todos_los_barriles):
            self.dots_barriles.append(Entity(parent=self, model='circle', color=color.orange, scale=(0.025, 0.025), z=-1))
            
        while len(self.dots_barriles) > len(Barril.todos_los_barriles):
            b = self.dots_barriles.pop()
            destroy(b)
            
        # Mover cada puntito a la posición de su respectivo barril
        for i, barril in enumerate(Barril.todos_los_barriles):
            bx = barril.x / 100
            by = (barril.y / 110) - 0.45
            self.dots_barriles[i].position = (bx, by, -1)
