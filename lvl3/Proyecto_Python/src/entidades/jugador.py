from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Velocidades del jugador
VELOCIDAD_NORMAL  = 5
VELOCIDAD_SPRINT  = 11

# Estamina
ESTAMINA_MAX      = 100.0
ESTAMINA_CONSUMO  = 28.0   # por segundo corriendo
ESTAMINA_RECARGA  = 16.0   # por segundo caminando/quieto
ESTAMINA_MIN_SPRINT = 10.0  # necesita al menos 10 para poder volver a correr

class Jugador:
    def __init__(self, position):
        self.start_position = position
        self.controller = FirstPersonController(position=self.start_position)
        self.controller.mouse_sensitivity = Vec2(20, 20)
        self.controller.speed = VELOCIDAD_NORMAL
        self.controller.jump_height = 4.5  # <--- Salto más grande
        
        self.puntuacion = 0
        self.multiplicador = 1
        
        self.texto_puntuacion = Text(
            text=f'Puntuacion: 0\nMultiplicador: x1', 
            position=(-0.85, 0.45), 
            scale=2, 
            color=color.yellow
        )
        
        # MARTILLO (Arma en primera persona)
        self.tiene_martillo = False
        self.tiempo_martillo = 0
        self.texto_martillo = Text(
            text='MARTILLO: INACTIVO', 
            position=(0.85, 0.45), 
            origin=(0.5, 0.5), 
            scale=2,
            color=color.orange
        )
        self.martillo_pivot = Entity(parent=camera, position=(0.83, -1.02, 0.81), visible=False)
        self.martillo_rotador = Entity(
            parent=self.martillo_pivot,
            rotation=(-189, 103, 188)
        )
        self.martillo_modelo = Entity(
            parent=self.martillo_rotador,
            model='assets/Models/toy_hammer.glb',
            scale=0.0015,
            y=1.34  # Desplaza el modelo para que el pivote quede en la base del mango
        )
        self.atacando = False

        # ESTAMINA
        self.estamina = ESTAMINA_MAX
        self.puede_correr = True  # se desactiva cuando la estamina llega a 0

        # HUD de estamina: fondo gris
        self.barra_fondo = Entity(
            parent=camera.ui,
            model='quad',
            color=Color(0.15, 0.15, 0.15, 0.75),
            scale=(0.28, 0.022),
            position=(0, -0.43),
            z=-1
        )
        # Barra verde de estamina actual
        self.barra_estamina = Entity(
            parent=camera.ui,
            model='quad',
            color=Color(0.1, 0.85, 0.25, 0.9),
            scale=(0.28, 0.022),
            position=(0, -0.43),
            z=-1.01
        )
        # Etiqueta
        self.lbl_estamina = Text(
            parent=camera.ui,
            text='STAMINA',
            scale=1.2,
            position=(0, -0.455),
            origin=(0, 0),
            color=Color(0.7, 1.0, 0.7, 0.85),
            z=-1.02
        )

        self.helper = Entity(update=self.update)

    # ----------------------------------------------------------
    def activar_martillo(self):
        self.tiene_martillo = True
        self.tiempo_martillo = 10.0
        self.martillo_pivot.visible = True
        self.actualizar_ui()

    # ----------------------------------------------------------
    def update(self):
        if not getattr(self, 'activo', True):
            return
            
        # --- MARTILLO: cuenta regresiva ---
        if self.tiene_martillo:
            self.tiempo_martillo -= time.dt
            if self.tiempo_martillo <= 0:
                self.tiene_martillo = False
                self.martillo_pivot.visible = False
            self.actualizar_ui()

        # Animacion idle del martillo
        if self.tiene_martillo and not self.atacando:
            self.martillo_pivot.rotation_x = 20

        # --- ESTAMINA Y SPRINT ---
        if getattr(self, 'god_mode', False):
            self.controller.speed = 40
            self.estamina = ESTAMINA_MAX
            corriendo = False
        else:
            corriendo = held_keys['shift'] and self.puede_correr
            if corriendo:
                self.controller.speed = VELOCIDAD_SPRINT
                self.estamina -= ESTAMINA_CONSUMO * time.dt
                if self.estamina <= 0:
                    self.estamina = 0
                    self.puede_correr = False  # se agoto, bloquear hasta recarga minima
            else:
                self.controller.speed = VELOCIDAD_NORMAL
                self.estamina += ESTAMINA_RECARGA * time.dt
            if self.estamina > ESTAMINA_MAX:
                self.estamina = ESTAMINA_MAX
            # Desbloquear sprint cuando recupere suficiente estamina
            if not self.puede_correr and self.estamina >= ESTAMINA_MIN_SPRINT:
                self.puede_correr = True

        self._actualizar_barra_estamina(corriendo)

        # --- MUERTE por caida ---
        if self.controller.y < -10:
            self.reaparecer()

        # --- TELETRANSPORTADORES ---
        if getattr(self, 'cooldown_teleport', 0) > 0:
            self.cooldown_teleport -= time.dt
            
        from src.entidades.entorno import Teletransportador
        for e in scene.entities:
            if isinstance(e, Teletransportador):
                dx = abs(self.controller.x - e.x)
                dz = abs(self.controller.z - e.z)
                # Si está cerca en X y Z, y también cerca en Y
                if dx < 2.0 and dz < 2.0 and getattr(self, 'cooldown_teleport', 0) <= 0:
                    if e.y - 1 <= self.controller.y <= e.y + 3:
                        self.controller.position = e.destino
                        self.cooldown_teleport = 1.0 # 1 segundo de enfriamiento para evitar teletransporte en cadena
                        break
                        
        self.controller.gravity = 1

    # ----------------------------------------------------------
    def _actualizar_barra_estamina(self, corriendo):
        porcentaje = self.estamina / ESTAMINA_MAX
        # La barra se escala desde el centro: ajustamos posicion X para que salga desde la izquierda
        self.barra_estamina.scale_x = 0.28 * porcentaje
        # Offset para que arranque desde el borde izquierdo del fondo
        self.barra_estamina.x = -0.14 * (1 - porcentaje)

        # Color dinamico: verde → amarillo → rojo segun el nivel
        if porcentaje > 0.5:
            t = (porcentaje - 0.5) * 2          # 0 a 1 entre 50%-100%
            barra_color = Color(1 - t, 0.85, 0.1 * t, 0.9)
        else:
            t = porcentaje * 2                   # 0 a 1 entre 0%-50%
            barra_color = Color(0.9, t * 0.85, 0, 0.9)

        if not self.puede_correr:
            # Parpadeo cuando esta agotado
            barra_color = Color(0.6, 0.1, 0.1, 0.7 + 0.3 * (int(time.time() * 6) % 2))

        self.barra_estamina.color = barra_color

    # ----------------------------------------------------------
    def sumar_puntos(self, puntos):
        self.puntuacion += puntos * self.multiplicador
        self.actualizar_ui()

    def actualizar_ui(self):
        self.texto_puntuacion.text = f'Puntuacion: {self.puntuacion}\nMultiplicador: x{self.multiplicador}'
        if self.tiene_martillo:
            self.texto_martillo.text = f'MARTILLO: {int(self.tiempo_martillo)}s'
            self.texto_martillo.color = color.red
        else:
            self.texto_martillo.text = 'MARTILLO: INACTIVO'
            self.texto_martillo.color = color.orange

    def reaparecer(self):
        self.controller.position = self.start_position
        self.multiplicador = 1
        self.estamina = ESTAMINA_MAX
        self.puede_correr = True
        self.actualizar_ui()

    def activar(self, estado):
        self.activo = estado
        self.controller.enabled = estado
        if estado:
            self.controller.speed = VELOCIDAD_NORMAL
            self.controller.jump_height = 4.5
            self.controller.mouse_sensitivity = Vec2(20, 20)
        else:
            self.controller.speed = 0
            self.controller.jump_height = 0
            self.controller.mouse_sensitivity = Vec2(0, 0)

    def destroy(self):
        destroy(self.controller)
        destroy(self.texto_puntuacion)
        destroy(self.texto_martillo)
        destroy(self.barra_fondo)
        destroy(self.barra_estamina)
        destroy(self.lbl_estamina)
        destroy(self.helper)
        if hasattr(self, 'martillo_modelo'):
            destroy(self.martillo_modelo)
        if hasattr(self, 'martillo_rotador'):
            destroy(self.martillo_rotador)
        destroy(self.martillo_pivot)
