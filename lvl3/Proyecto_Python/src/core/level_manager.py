from ursina import *
from src.entidades.entorno import Suelo, Plataforma, PlataformaMovil, Teletransportador, PlataformaTrampa
from src.entidades.jugador import Jugador
from src.entidades.barril import BarrilSpawner, Barril
from src.entidades.bono import Bono, BonoMartillo
from src.ui.minimapa import MiniMapa

class LevelManager:
    def __init__(self):
        self.entidades = []
        self.jugador = None
        self.spawner = None
        self.suelo = None
        self.minimapa = None
        
    def limpiar_nivel(self):
        for e in self.entidades:
            destroy(e)
        self.entidades.clear()
        
        if self.jugador:
            self.jugador.destroy()
            self.jugador = None
            
        if self.spawner:
            destroy(self.spawner)
            self.spawner = None
            
        if self.suelo:
            destroy(self.suelo)
            self.suelo = None
            
        if self.minimapa:
            destroy(self.minimapa)
            self.minimapa = None

    def cargar_nivel(self, nivel):
        self.limpiar_nivel()
        self.suelo = Suelo()
        if nivel == 3:
            # NO creamos al jugador todavía para evitar que reclame la cámara en el primer frame.
            self.jugador = None
            
            # ANIMACIÓN DE INTRODUCCIÓN CINEMÁTICA
            
            # 1. Crear al Jefe (Placeholder)
            self.jefe = Entity(model='cube', color=color.red, scale=(4, 4, 4), position=(-11, 102.5, 0))
            self.entidades.append(self.jefe)
            
            # Desvincular cámara para hacer animación global desde el principio
            camera.parent = scene
            camera.fov = 90  # <--- FIX: Ursina usa FOV pequeño por defecto, FPC usa 90.
            
            # T=0: Vista 2D general (ahora será verdaderamente lo primero que se vea)
            camera.position = (0, 45, -150)
            camera.rotation = (0, 0, 0)
            
            # T=1s: Acercamiento suave al jefe
            invoke(lambda: camera.animate_position((-11, 102.5, -40), duration=3, curve=curve.in_out_sine), delay=1)
            
            # T=4.5s: El jefe lanza el primer barril
            def lanzar_barril_intro():
                from src.entidades.barril import Barril
                Barril(position=(-11, 99, 0), direction=1, jugador_ref=None, es_fuego=False)
            invoke(lanzar_barril_intro, delay=4.5)
            
            # T=6s: Alejarse suavemente de vuelta a la vista 2D
            invoke(lambda: camera.animate_position((0, 45, -150), duration=3, curve=curve.in_out_sine), delay=6)
            
            # T=10s: Acercarse al jugador y girar para ver hacia el camino de la plataforma (rotación Y = 90)
            def acercamiento_jugador():
                camera.animate_position((-30, 5, 0), duration=3, curve=curve.in_out_sine) # Y=5 es aprox la cabeza
                camera.animate_rotation((0, 90, 0), duration=3, curve=curve.in_out_sine)
            invoke(acercamiento_jugador, delay=10)
            
            # T=13.5s: Vincular cámara al jugador, orientarlo y empezar el juego
            def iniciar_juego():
                # AHORA creamos al jugador
                self.jugador = Jugador(position=(-30, 3, 0))
                self.jugador.controller.rotation_y = 90
                # Desatorar del piso: lo levantamos un poco para que caiga limpiamente
                self.jugador.controller.y += 2.0 
                
                camera.parent = self.jugador.controller.camera_pivot
                camera.position = (0, 0, 0)
                camera.rotation = (0, 0, 0)
                self.jugador.activar(True)
                
                # Actualizar referencias al jugador que faltaban por crearse
                if self.minimapa:
                    self.minimapa.jugador_ref = self.jugador
                for e in self.entidades:
                    if hasattr(e, 'jugador_ref'):
                        e.jugador_ref = self.jugador
                
                if self.spawner:
                    self.spawner.jugador_ref = self.jugador
                    self.spawner.activo = True
            invoke(iniciar_juego, delay=13.5)

            # ----------------------------------------------------------
            # PLATAFORMAS (DISENO ORIGINAL SIN HUECOS)
            # ----------------------------------------------------------
            # (y_base, cx, rot_z, es_trampa)
            datos_plataformas = [
                (0,   8, -2.0, False),
                (9,  -8,  2.0, False),
                (18,  8, -2.0, False),
                (27, -8,  2.0, False),
                (36,  8, -2.0, False),
                (45, -8,  2.0, False),
                (54,  8, -2.0, False),
                (63, -8,  2.0, False),
                (72,  8, -2.0, False),
                (81, -8,  2.0, False),
                (90,  8, -2.0, False),
            ]

            for y, cx, rot, es_trampa in datos_plataformas:
                ClasePlat = PlataformaTrampa if es_trampa else Plataforma
                kwargs = dict(position=(cx, y, 0), rotation_z=rot, scale=(80, 1, 5))
                if es_trampa:
                    kwargs['jugador_ref'] = self.jugador
                self.entidades.append(ClasePlat(**kwargs))

            # Plataforma superior (cima)
            self.entidades.append(Plataforma(position=(-12, 99, 0), rotation_z=4, scale=(40, 1, 5)))

            # ----------------------------------------------------------
            # TELETRANSPORTADORES
            # ----------------------------------------------------------
            for i in range(11):
                y_actual = i * 9
                y_siguiente = (i + 1) * 9
                
                # Para evitar problemas de colisión exacta, ponemos el teletransportador
                # ligeramente por encima de la plataforma
                y_pos = y_actual + 0.5
                
                # Extremos de la plataforma (como las escaleras originales)
                x_pos = 28 if i % 2 == 0 else -28
                
                # El destino será la misma X pero en la plataforma superior
                destino = (x_pos, y_siguiente + 2, 0) # Z=0 (centro a lo ancho)
                
                # Posición actual Z=0 para estar justo en el medio de lo ancho de la plataforma
                self.entidades.append(Teletransportador(position=(x_pos, y_pos, 0), destino=destino))

            # ----------------------------------------------------------
            # SPAWNER DE BARRILES
            # ----------------------------------------------------------
            # Inicia inactivo; la animación de intro lo activará al terminar
            self.spawner = BarrilSpawner(position=(-11, 99, 0), jugador_ref=self.jugador, activo=False, jefe_ref=self.jefe)

            # ----------------------------------------------------------
            # BONOS MARTILLO
            # ----------------------------------------------------------
            import random
            plataformas_y = [0, 9, 18, 27, 36, 45, 54, 63, 72, 81, 90]
            for _ in range(3):
                y_pos = random.choice(plataformas_y)
                x_pos = random.uniform(-25, 25)
                self.entidades.append(
                    BonoMartillo(position=(x_pos, y_pos + 1.5, 0), jugador_ref=self.jugador)
                )

            # ----------------------------------------------------------
            # MINIMAPA
            # ----------------------------------------------------------
            self.minimapa = MiniMapa(self.jugador, getattr(self, 'jefe', None))
