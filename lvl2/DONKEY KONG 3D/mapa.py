from ursina import Entity, color, Vec3, camera, scene, destroy


class Viga(Entity):
    def __init__(self, x, y, ancho):
        super().__init__(
            model='cube', color=color.white, scale=(ancho, 0.4, 3),
            position=(x, y, 0), collider='box',
            texture='suelo rojo/textures/red_brick_pavers_diff_4k.jpg'
        )
        self.type = 'viga'
        self.angulo = 0


class Escalera(Entity):
    def __init__(self, x, y, alto):
        # El modelo 'Escaleras.glb' tiene un alto original de 2.
        # Ajustamos la rotación en Y para que quede de frente.
        # Hacemos el eje Z (que ahora será el frente) de tamaño 1.5 para que quede más ancha.
        # El eje X (profundidad) lo mantenemos en 0.5.
        super().__init__(
            model='Escaleras.glb', color=color.white,
            scale=(0.5 / 0.138, alto / 2.0, 1.5 / 0.621), 
            position=(x, y, 1.2), collider=None,
            rotation_y=90
        )
        self.type = 'escalera'
        self.alto = alto
        self.ancho = 1.5


def crear_piso_con_huecos(y, x_min, x_max, huecos):
    huecos.sort()
    current_x = x_min
    for h in huecos:
        h_start = h - 1.2
        h_end = h + 1.2
        if h_start > current_x:
            w = h_start - current_x
            center_x = current_x + w / 2
            Viga(center_x, y, w)
        current_x = h_end
        
    if x_max > current_x:
        w = x_max - current_x
        center_x = current_x + w / 2
        Viga(center_x, y, w)


def construir_nivel():
    y_levels = [-11.5, -6.5, -1.5, 3.5, 8.5, 13.5, 18.5, 23.5, 28.5, 33.5]
    
    escaleras_por_piso = {
        0: [-20, 0, 20],   # De piso 0 a 1
        1: [-10, 10],      # De piso 1 a 2
        2: [-20, 0, 20],   # De piso 2 a 3
        3: [-10, 10],      # De piso 3 a 4
        4: [-20, 0, 20],   # De piso 4 a 5
        5: [-10, 10],      # De piso 5 a 6
        6: [-20, 0, 20],   # De piso 6 a 7
        7: [-10, 10],      # De piso 7 a 8
        8: [-20, 20]       # De piso 8 a 9
    }

    # Crear los pisos con huecos donde suben las escaleras del piso inferior
    # El piso 0 se extiende hasta -34 y 34 para que atrape los barriles que caen de las plataformas laterales y no caigan al vacío.
    crear_piso_con_huecos(y_levels[0], -34, 34, [])
    crear_piso_con_huecos(y_levels[1], -28, 28, escaleras_por_piso[0])
    crear_piso_con_huecos(y_levels[2], -28, 28, escaleras_por_piso[1])
    crear_piso_con_huecos(y_levels[3], -28, 28, escaleras_por_piso[2])
    crear_piso_con_huecos(y_levels[4], -28, 28, escaleras_por_piso[3])
    crear_piso_con_huecos(y_levels[5], -28, 28, escaleras_por_piso[4])
    crear_piso_con_huecos(y_levels[6], -28, 28, escaleras_por_piso[5])
    crear_piso_con_huecos(y_levels[7], -28, 28, escaleras_por_piso[6])
    crear_piso_con_huecos(y_levels[8], -28, 28, escaleras_por_piso[7])
    crear_piso_con_huecos(y_levels[9], -28, 28, escaleras_por_piso[8])

    # Crear las escaleras
    for piso, xs in escaleras_por_piso.items():
        y_inferior = y_levels[piso]
        for x in xs:
            Escalera(x, y_inferior + 2.5, 5.0)

    # ── PLATAFORMAS LATERALES (Fuera del rango) ──
    alturas_laterales = [-9.0, -4.0, 1.0, 6.0, 11.0, 16.0, 21.0, 26.0, 31.0]
    for y in alturas_laterales:
        Viga(-35.0, y, 4)  # Izquierda
        Viga(35.0, y, 4)  # Derecha

    # Las plataformas laterales ya están creadas

class MiniMapaNivel2(Entity):
    def __init__(self, jugador):
        super().__init__(parent=camera.ui, position=(0.75, 0.22), scale=(0.22, 0.22))
        self.type = 'minimapa'
        self.jugador = jugador
        self.fondo = Entity(parent=self, model='quad', color=color.black66, scale=(1, 1), z=0.1)
        self.contenedor = Entity(parent=self)
        self.marcador = Entity(parent=self.contenedor, model='circle', color=color.red, scale=(0.06, 0.06), z=-0.1)
        
        # Plataformas centrales
        y_levels = [-11.5, -6.5, -1.5, 3.5, 8.5, 13.5, 18.5, 23.5, 28.5, 33.5]
        for y in y_levels:
            Entity(parent=self.contenedor, model='quad', color=color.orange, scale=(60.0/80.0, 0.02), position=(0, y/35.0), z=0)
            
        # Plataformas laterales
        alturas_laterales = [-9.0, -4.0, 1.0, 6.0, 11.0, 16.0, 21.0, 26.0, 31.0]
        for y in alturas_laterales:
            Entity(parent=self.contenedor, model='quad', color=color.orange, scale=(4.0/80.0, 0.02), position=(-35.0/80.0, y/35.0), z=0)
            Entity(parent=self.contenedor, model='quad', color=color.orange, scale=(4.0/80.0, 0.02), position=(35.0/80.0, y/35.0), z=0)
            
        # Escaleras
        for e in list(scene.entities):
            try:
                if getattr(e, 'type', None) == 'escalera':
                    Entity(parent=self.contenedor, model='quad', color=color.cyan, scale=(1.5/80.0, 5.0/35.0), position=(e.x/80.0, e.y/35.0), z=0)
            except (AssertionError, Exception):
                continue
            
        self.marcadores_extra = {}

    def update(self):
        if getattr(self, 'destroyed', False): return
        
        try:
            if self.jugador and getattr(self.jugador, 'enabled', True):
                self.marcador.x = self.jugador.x / 80.0
                self.marcador.y = self.jugador.y / 35.0
                self.contenedor.y = -self.jugador.y / 35.0
        except (AssertionError, Exception):
            pass
            
        tipos_colores = {
            'barril': color.brown,
            'enemigo': color.magenta,
            'martillo': color.yellow
        }
        
        entidades_validas = []
        for e in list(scene.entities):
            try:
                if getattr(e, 'type', None) in tipos_colores:
                    entidades_validas.append(e)
            except (AssertionError, Exception):
                continue
        
        # Eliminar marcadores huérfanos
        for e in list(self.marcadores_extra.keys()):
            if e not in entidades_validas or getattr(e, 'destroyed', False):
                destroy(self.marcadores_extra[e])
                del self.marcadores_extra[e]
                
        # Actualizar posiciones
        for e in entidades_validas:
            if getattr(e, 'destroyed', False): continue
            
            try:
                ex = e.x
                ey = e.y
            except AssertionError:
                continue
                
            if e not in self.marcadores_extra:
                col = tipos_colores.get(e.type, color.white)
                self.marcadores_extra[e] = Entity(parent=self.contenedor, model='circle', color=col, scale=(0.04, 0.04), z=-0.1)
            self.marcadores_extra[e].x = ex / 80.0
            self.marcadores_extra[e].y = ey / 35.0
            
        try:
            for c in self.contenedor.children:
                pos_y_rel = c.y + self.contenedor.y
                if pos_y_rel > 0.48 or pos_y_rel < -0.48:
                    c.enabled = False
                else:
                    c.enabled = True
        except AssertionError:
            pass