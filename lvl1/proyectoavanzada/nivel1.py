from ursina import texture_importer
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader, camera_contrast_shader, unlit_shader
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone
import random
import math
from direct.actor.Actor import Actor
# ==========================================
# CONSTANTES
# ==========================================
PUNTUACION_INICIAL = 4000
SALUD_INICIAL = 2.0 # Corazones
TIEMPO_MARTILLO_MAX = 15.0
PENALIZACION_TIEMPO = 10.0
PENALIZACION_PUNTOS = 50
PUNTOS_POR_BARRIL = 100
BONUS_POR_SECUAZ = 10000

DAÑO_BARRIL = 1.0
VELOCIDAD_BARRIL_CAIDA = 10.0
VELOCIDAD_BARRIL_RODAR = 5.0

SALUD_JEFE = 3
VELOCIDAD_JEFE = 3.0
TIEMPO_SPAWN_BARRIL = 2.5

# Posición exacta de inicio (Primera Persona)
POSICION_INICIAL_JUGADOR = (-23.4, 1.8, -0.2)
COLOR_JUGADOR_NORMAL = color.white 
COLOR_JUGADOR_MARTILLO = color.yellow

POSICIONES_MARTILLOS = [
    (15.0, 24.3, 0.0),   # Plataforma 3 (derecha)
    (-15.0, 36.3, 0.0),  # Plataforma 4 (izquierda)
    (15.0, 48.3, 0.0),   # Plataforma 5 (derecha)
    (-15.0, 60.3, 0.0),  # Plataforma 6 (izquierda)
    (15.0, 72.3, 0.0)    # Plataforma 7 (derecha) - ÚLTIMO MARTILLO INFINITO
]

en_intro = False
texto_intro = None
victoria_cinematica = False

# ==========================================
# GAME MANAGER (Estado y UI)
# ==========================================
class GameManager(Entity):
    def __init__(self):
        super().__init__()
        self.puntuacion = PUNTUACION_INICIAL
        self.salud_jugador = SALUD_INICIAL
        self.martillo_activo = False
        self.tiempo_martillo = 0.0
        self.temporizador_puntos = PENALIZACION_TIEMPO
        self.muerto = False
        
        self.texto_ui = Text(text='', position=(-0.85, 0.45), scale=2, color=color.white)
        self.texto_salud = Text(text='', position=(-0.85, 0.40), scale=2, color=color.red)
        self.texto_coords = Text(text='', position=(-0.85, 0.35), scale=1.5, color=color.rgba(100, 220, 255, 200))
        
        self.actualizar_ui()

    def actualizar_ui(self):
        if self.martillo_activo:
            if getattr(self, 'martillo_infinito', False):
                self.texto_ui.text = f'BONUS: {self.puntuacion} | MARTILLO: ∞ INFINITO'
            else:
                self.texto_ui.text = f'BONUS: {self.puntuacion} | MARTILLO: {int(self.tiempo_martillo)}s'
        else:
            self.texto_ui.text = f'BONUS: {self.puntuacion}'
            
        self.texto_salud.text = f'SALUD: {self.salud_jugador/2} Corazones'

    def agregar_puntos(self, puntos):
        self.puntuacion += puntos
        self.actualizar_ui()

    def recibir_dano(self, cantidad):
        if self.muerto: return
        self.salud_jugador -= cantidad
        self.actualizar_ui()
        if self.salud_jugador <= 0:
            self.morir()
            
    def morir(self):
        if getattr(self, 'muerto', False): return
        self.muerto = True
        
        if 'jugador' in globals():
            jugador.speed = 0
            jugador.jump_height = 0
            
        mouse.locked = False
        
        # Animación de desmayo (cae la cámara hacia un lado)
        camera.animate_rotation((0, 0, 90), duration=1.0, curve=curve.out_bounce)
        
        # Llamar al Game Over con retraso
        invoke(menu_game_over.mostrar, delay=1.5)

    def activar_martillo(self, infinito=False):
        self.martillo_activo = True
        self.martillo_infinito = infinito
        self.tiempo_martillo = TIEMPO_MARTILLO_MAX
        self.actualizar_ui()

    def update(self):
        if application.paused or getattr(self, 'muerto', False): return

        # Coordenadas en tiempo real
        if 'jugador' in globals():
            p = jugador.position
            self.texto_coords.text = f'X:{p.x:.1f}  Y:{p.y:.1f}  Z:{p.z:.1f}'

        # Penalización por tiempo
        self.temporizador_puntos -= time.dt
        if self.temporizador_puntos <= 0:
            self.puntuacion -= PENALIZACION_PUNTOS
            self.temporizador_puntos = PENALIZACION_TIEMPO
            self.actualizar_ui()
            if self.puntuacion <= 0:
                self.morir()

        # Temporizador del martillo
        if self.martillo_activo:
            if not getattr(self, 'martillo_infinito', False):
                self.tiempo_martillo -= time.dt
            self.actualizar_ui()
            if self.tiempo_martillo <= 0 and not getattr(self, 'martillo_infinito', False):
                self.martillo_activo = False
                if hasattr(jugador, 'malla'):
                    jugador.malla.color = COLOR_JUGADOR_NORMAL
                if hasattr(jugador, 'martillo_visual'):
                    jugador.martillo_visual.enabled = False
                self.actualizar_ui()

    def reiniciar(self):
        self.puntuacion = PUNTUACION_INICIAL
        self.salud_jugador = SALUD_INICIAL
        self.martillo_activo = False
        self.martillo_infinito = False
        self.tiempo_martillo = 0.0
        self.temporizador_puntos = PENALIZACION_TIEMPO
        self.muerto = False
        camera.rotation = (0, 0, 0)
        
        # Limpiar efectos visuales del jugador al reiniciar
        if 'jugador' in globals():
            if hasattr(jugador, 'malla'):
                jugador.malla.color = COLOR_JUGADOR_NORMAL
            if hasattr(jugador, 'martillo_visual'):
                jugador.martillo_visual.enabled = False
                
        self.actualizar_ui()

# ==========================================
# 1. JUGADOR Y CÁMARA
# ==========================================
class Jugador(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.position = POSICION_INICIAL_JUGADOR
        self.position = POSICION_INICIAL_JUGADOR
        
        # FOV Natural FPS (75) para evitar distorsión visual
        camera.fov = 75
        
        self.cursor.color = color.red
        self.cursor.visible = False # Cursor deshabilitado para evitar el punto rojo marcador en el centro
        self.mouse_sensitivity = Vec2(40, 40)
        self.en_escalera = False
        self.ultimo_dano_tiempo = 0

    def restaurar_color(self):
        pass

    def input(self, key):
        super().input(key)
        
        # Swing manual opcional (aunque se anima solo)
        if key == 'left mouse down' and getattr(game_manager, 'martillo_activo', False):
            if hasattr(self, 'martillo_visual') and self.martillo_visual and getattr(self.martillo_visual, 'enabled', False):
                try:
                    self.martillo_visual.animate_rotation((100, 0, -20), duration=0.15)
                    def revertir():
                        if hasattr(self, 'martillo_visual') and self.martillo_visual:
                            try:
                                self.martillo_visual.animate_rotation((30, 0, -20), duration=0.2)
                            except: pass
                    invoke(revertir, delay=0.15)
                except: pass
            
            # Destruir barriles frente a nosotros manualmente
            for b in list(Barril.instancias):
                if distance(self, b) < 4.0:
                    game_manager.agregar_puntos(PUNTOS_POR_BARRIL)
                    TextoFlotante(f'+{PUNTOS_POR_BARRIL}', b.position + Vec3(0, 1, 0))
                    crear_explosion(b.position, textura='barril_texture')
                    destroy(b)

    def reiniciar(self):
        self.position = POSICION_INICIAL_JUGADOR
        self.rotation = Vec3(0, 90, 0)
        self.camera_pivot.rotation_x = 0
        self.color = COLOR_JUGADOR_NORMAL
        self.gravity = 1
        self.velocity_y = 0 # Prevenir que siga cayendo si murió en el aire
        self.jump_height = 2 # Restaurar altura de salto por si murió

    def update(self):
        global en_intro
        if application.paused or game_manager.muerto or (globals().get('en_intro', False)): return
        
        # Mapear flechas direccionales a WASD para habilitar el movimiento con flechas en FirstPersonController
        held_keys['w'] = held_keys['w'] or held_keys['up arrow']
        held_keys['s'] = held_keys['s'] or held_keys['down arrow']
        held_keys['a'] = held_keys['a'] or held_keys['left arrow']
        held_keys['d'] = held_keys['d'] or held_keys['right arrow']
        
        super().update()
        
        # (El modelo visual y animaciones fueron removidas para mantener el modo primera persona puro)
        # Animación automática del martillo clásico
        if getattr(game_manager, 'martillo_activo', False) and hasattr(self, 'martillo_visual') and self.martillo_visual.enabled:
            swing = math.sin(time.time() * 12) * 45
            if globals().get('vista_cinematica', False):
                self.martillo_visual.rotation_x = swing
                self.martillo_visual.rotation_z = -45
            else:
                self.martillo_visual.rotation_x = 30 + swing
                self.martillo_visual.rotation_z = -20

        # Detección de escaleras
        self.en_escalera = False
        escalera_actual = None
        for esc in escaleras:
            if abs(self.x - esc.x) < 0.8 and abs(self.z - esc.z) < 4.0:
                altura_esc = getattr(esc, 'altura', esc.scale_y)
                if (esc.y - altura_esc/2 - 0.5) <= self.y <= (esc.y + altura_esc/2 + 1.5):
                    self.en_escalera = True
                    escalera_actual = esc
                    break

        # Colisión con el techo y Sprint
        if not self.en_escalera:
            hit_techo = raycast(self.position + Vec3(0, 1, 0), direction=Vec3(0, 1, 0), distance=1.2, ignore=(self,))
            if hit_techo.hit:
                self.y = hit_techo.world_point.y - 2.2
                
        # Movimiento en escalera
        if self.en_escalera:
            self.gravity = 0 
            self.speed = 0 # Inhabilita el movimiento horizontal de WASD nativo del FirstPersonController
            
            if held_keys['w']: 
                self.y += 5 * time.dt
                
                # Auto-desmontaje suave en la cima
                if escalera_actual:
                    tope_esc = escalera_actual.y + getattr(escalera_actual, 'altura', escalera_actual.scale_y)/2
                    if self.y > tope_esc + 0.2:
                        dir_auto = -1 if self.x > 0 else 1 # Empujar hacia el centro del nivel
                        self.x += dir_auto * 5 * time.dt
                    else:
                        # AUTO-CENTRADO EN LA ESCALERA (solo si estamos en la parte vertical)
                        self.x = escalera_actual.x
                            
            if held_keys['s']: 
                self.y -= 5 * time.dt
        else:
            self.gravity = 1
            # Mecánica de sprint corregida y aumentada
            if held_keys['shift']:
                self.speed = 12 # Sprint ajustado
            else:
                self.speed = 7.0 # Caminar rápido
            
        # Detección de caída al vacío
        if self.y < -15:
            game_manager.morir()

    def recibir_dano(self):
        if time.time() - self.ultimo_dano_tiempo < 0.5:
            return
        self.ultimo_dano_tiempo = time.time()
        
        game_manager.recibir_dano(DAÑO_BARRIL)
        self.color = color.white
        invoke(setattr, self, 'color', COLOR_JUGADOR_NORMAL, delay=0.2)

# ==========================================
# SISTEMA DE PARTÍCULAS (VOXELS ESTILO PIXELS)
# ==========================================
class Particula(Entity):
    def __init__(self, posicion, textura=None):
        if textura:
            super().__init__(model='cube', texture=textura, color=color.white, scale=random.uniform(0.3, 0.7), position=posicion, shader=lit_with_shadows_shader)
        else:
            color_voxel = random.choice([color.orange, color.yellow, color.red, color.white])
            super().__init__(model='cube', color=color_voxel, scale=random.uniform(0.1, 0.4), position=posicion, shader=lit_with_shadows_shader)
            
        self.dx = random.uniform(-6, 6)
        self.dy = random.uniform(5, 15)
        self.dz = random.uniform(-6, 6)
        self.rot_x = random.uniform(-200, 200)
        self.rot_y = random.uniform(-200, 200)
        self.lifetime = 1.5

    def update(self):
        if application.paused: return
        self.position += Vec3(self.dx, self.dy, self.dz) * time.dt
        self.rotation_x += self.rot_x * time.dt
        self.rotation_y += self.rot_y * time.dt
        self.dy -= 25 * time.dt 
        self.scale -= Vec3(0.3, 0.3, 0.3) * time.dt
        self.lifetime -= time.dt
        if self.lifetime <= 0 or self.scale.x <= 0.02:
            destroy(self)
            return

def crear_explosion(posicion, textura=None):
    for _ in range(40): Particula(posicion, textura)

class TextoFlotante(Entity):
    def __init__(self, texto, posicion, color_texto=color.yellow):
        super().__init__(position=posicion)
        self.t = Text(parent=self, text=texto, scale=5, color=color_texto, origin=(0,0), billboard=True)
        self.animate_y(self.y + 3, duration=1.0, curve=curve.out_expo)
        self.t.fade_out(value=0, duration=1.0, delay=0.2)
        invoke(destroy, self, delay=1.5)

# ==========================================
# ITEMS Y COLECCIONABLES
# ==========================================
class MartilloItem(Entity):
    instancias = []
    def __init__(self, position):
        panda_hammer = application.base.loader.loadModel('assets/toy_hammer.glb')
        
        # Se eleva 2.5 unidades sobre la plataforma para que flote bien arriba y no se hunda
        self.pos_inicial = Vec3(*position) + Vec3(0, 2.5, 0)
        
        super().__init__(
            model=panda_hammer,
            color=color.white,
            scale=0.0027, 
            position=self.pos_inicial, 
            collider='box',
            shader=lit_with_shadows_shader
        )
        
        self.rotation_z = 0 # Totalmente vertical/horizontal dependiendo del modelo base
        self.rotation_x = 0
        self.activo = True
        import math
        MartilloItem.instancias.append(self)

    def on_destroy(self):
        if self in MartilloItem.instancias:
            MartilloItem.instancias.remove(self)

    def update(self):
        if application.paused: return
        import math
        self.rotation_y += 100 * time.dt
        self.y = self.pos_inicial.y + math.sin(time.time() * 3) * 0.3
        
        if distance(self, jugador) < 3.0:
            es_infinito = (self.pos_inicial.y > 74.0) # El último martillo está en Y=72.3 (pos_inicial.y=74.8)
            game_manager.activar_martillo(infinito=es_infinito)
            jugador.color = COLOR_JUGADOR_MARTILLO
            
            # Crear modelo visual en la mano (cámara en primera persona)
            if not hasattr(jugador, 'martillo_visual'):
                jugador.martillo_visual = Entity(
                    parent=camera,
                    position=(0.5, -0.5, 0.8),
                    rotation=(30, 0, -20)
                )
                panda_hammer_visual = application.base.loader.loadModel('assets/toy_hammer.glb')
                
                Entity(
                    parent=jugador.martillo_visual,
                    model=panda_hammer_visual, 
                    color=color.white,
                    scale=0.00068,
                    position=(0, 0.68, 0),
                    rotation_y=90,
                    shader=lit_with_shadows_shader
                )
            jugador.martillo_visual.enabled = True
            
            destroy(self)

def spawn_martillo():
    for pos in POSICIONES_MARTILLOS:
        MartilloItem(position=pos)

# ==========================================
# 2. SISTEMA DE BARRILES
# ==========================================
class Barril(Entity):
    instancias = [] 

    def __init__(self, position):
        super().__init__(
            position=position, 
            collider='box'
        )
        self.collider = BoxCollider(self, size=(1.2,1.2,1.2))
        self.dir = -1
        self.activo = True
        
        panda_barrel = application.base.loader.loadModel('assets/spiked_barrel.obj')
        # Separamos el modelo visual en un hijo para que rotation_x no interfiera con el rodamiento en Z
        self.visual = Entity(
            parent=self,
            model=panda_barrel,
            texture='assets/barrel_albedo.png',
            color=color.white,
            scale=1.0,
            shader=lit_with_shadows_shader,
            rotation_x=90
        )
        
        Barril.instancias.append(self)

    def on_destroy(self):
        if self in Barril.instancias:
            Barril.instancias.remove(self)

    def update(self):
        if application.paused or not self.activo: return

        esta_en_suelo = False
        suelo_y = -100
        suelo_dir = -1

        for p in plataformas:
            if p.x_izq <= self.x <= p.x_der:
                distancia = self.y - p.y_base
                if 0 <= distancia <= 1.8:
                    esta_en_suelo = True
                    suelo_y = p.y_base + 0.9
                    suelo_dir = p.dir_b
                    break

        if esta_en_suelo:
            self.y = suelo_y
            self.dir = suelo_dir
            self.x += self.dir * VELOCIDAD_BARRIL_RODAR * time.dt
            
            # Para que "rueden" (rodamiento), el eje correcto del modelo es el Z local.
            # Aplicamos la velocidad lineal proporcional para que no patine.
            self.rotation_z -= self.dir * VELOCIDAD_BARRIL_RODAR * 115 * time.dt
        else:
            self.y -= VELOCIDAD_BARRIL_CAIDA * time.dt
        
        # Medimos la distancia al centro del jugador (su origen está en los pies)
        # Esto permite que saltar (elevar los pies) aumente la distancia real y evite el daño
        centro_jugador = jugador.position + Vec3(0, 1.0, 0)
        dist = distance(self.position, centro_jugador)
        
        if dist < 1.3 or (getattr(game_manager, 'martillo_activo', False) and dist < 2.5): 
            if game_manager.martillo_activo:
                game_manager.agregar_puntos(PUNTOS_POR_BARRIL)
                TextoFlotante(f'+{PUNTOS_POR_BARRIL}', self.position + Vec3(0, 1, 0))
                crear_explosion(self.position, textura='barril_texture')
                destroy(self)
                return
            else:
                jugador.recibir_dano()
                self.x += (self.dir * -1) * 2.0 

        if self.y < -15:
            destroy(self)

class Secuaz(Entity):
    def __init__(self, position):
        super().__init__(
            position=position, 
            collider='box'
        )
        
        # 1. Instanciar la entidad cargando el GLB con Actor de Panda3D
        try:
            self.actor = Actor('assets/secuaz_lanza_barril.glb')
            self.actor.reparentTo(self)
            self.actor.setScale(0.8) # Ajustar la escala a un tamaño visible y adecuado (0.8)
            
            # Obtener el nombre de la animación 
            anim_names = self.actor.getAnimNames()
            if anim_names:
                self.anim_name = anim_names[0]
            else:
                self.anim_name = None
        except Exception as e:
            print(f"Error al cargar el modelo animado: {e}")
            self.actor = None
            self.anim_name = None

        self.derrotado = False
        self.barril_lanzado = False # Para no lanzar múltiples veces en el mismo ciclo
        self.animacion_iniciada = False
        self.fase2 = False
        
    def update(self):
        if application.paused or self.derrotado or ('en_intro' in globals() and en_intro): return
        
        if not self.actor or not self.anim_name: return

        # Lógica de fase 2 para aumentar dificultad (acelerar animación)
        if not self.fase2 and 'jugador' in globals() and jugador.y > 30:
            self.fase2 = True
            self.actor.setPlayRate(1.5, self.anim_name)
        
        # 3. Detectar proximidad del jugador y mirar hacia él
        if 'jugador' in globals():
            distancia = distance(self.position, jugador.position)
            
            # Hacer que el secuaz apunte siempre al jugador en el eje horizontal
            self.look_at_2d(jugador.position, 'y')
            # Ajuste de rotación por si el modelo de Blender está exportado de espaldas o de lado. 
            # Si el gorila te da la espalda, cambia este 180 a 0 o 90.
            self.rotation_y += 180
        else:
            distancia = 100

        if distancia < 100.0:
            # Configurar la reproducción en bucle (loop)
            if not self.animacion_iniciada:
                self.actor.loop(self.anim_name)
                self.animacion_iniciada = True
                self.anim_timer = 0.0 # Temporizador manual de respaldo
                
            # Obtener el fotograma actual de la animación
            frame_actual = self.actor.getCurrentFrame(self.anim_name)
            
            # Fallback manual por si el motor no devuelve el frame (glTF sin soporte completo de frames en Panda3D)
            if frame_actual is None:
                self.anim_timer += time.dt * (1.5 if self.fase2 else 1.0)
                duracion_asumida = 1.0 # 60 frames a 60 fps = 1 segundo
                frame_actual = ((self.anim_timer % duracion_asumida) / duracion_asumida) * 60.0

            # 1. Mostrar barril falso en las manos al iniciar el ciclo (antes del frame 5)
            if frame_actual < 5 and not getattr(self, 'barril_falso_visible', False):
                panda_barrel_falso = application.base.loader.loadModel('assets/spiked_barrel.obj')
                self.barril_falso = Entity(parent=self, model=panda_barrel_falso, texture='assets/barrel_albedo.png', color=color.white, y=1.5, z=-0.8, scale=0.8, rotation_x=90, shader=lit_with_shadows_shader)
                self.barril_falso_visible = True
                self.barril_lanzado = False
            
            # 2. Soltar barril real y ocultar el falso en el fotograma 40 exacto
            if frame_actual >= 40 and not self.barril_lanzado:
                # Ocultar el barril de las manos
                if hasattr(self, 'barril_falso') and self.barril_falso:
                    destroy(self.barril_falso)
                    self.barril_falso = None
                self.barril_falso_visible = False
                
                # Instanciar el barril real que rueda hacia el jugador
                self.instanciar_barril()
                self.barril_lanzado = True

        else:
            # Detener la animación si el jugador está lejos para ahorrar recursos
            if self.animacion_iniciada:
                self.actor.stop()
                self.actor.pose(self.anim_name, 0)
                self.animacion_iniciada = False
                self.barril_lanzado = False
                if hasattr(self, 'barril_falso') and self.barril_falso:
                    destroy(self.barril_falso)
                    self.barril_falso_visible = False

    def instanciar_barril(self):
        # Crear la instancia del barril real un poco delante del secuaz
        offset_z = random.uniform(-1.5, 1.5)
        Barril(position=self.position + Vec3(0, -1, offset_z))

    def recibir_dano(self):
        if self.derrotado: return
        self.derrotado = True
        
        # SUPER GOLPE FINAL CINEMÁTICO (Epic Finisher)
        time.time_scale = 0.2 # Slow motion brutal
        
        # Explosión gigante y Texto
        for _ in range(120): Particula(self.position)
        TextoFlotante("¡GOLPE FINAL!", self.position + Vec3(0,4,0), color_texto=color.red)
        
        # El jefe sale volando
        self.animate_rotation((360, 360, 360), duration=1.0)
        self.animate_position(self.position + Vec3(0, 15, 20), duration=0.5, curve=curve.out_expo)
        self.animate_y(-20, duration=0.5, delay=0.5, curve=curve.in_expo)
        
        global victoria_cinematica
        victoria_cinematica = True
        
        # Cámara épica desprendida
        camera.parent = scene
        cam_pos = self.position + Vec3(-12, 5, -12)
        camera.position = cam_pos
        camera.look_at(self.position)
        
        # Zoom in y paneo dramático
        camera.animate_position(cam_pos + Vec3(6, 2, 6), duration=1.0)
        
        game_manager.agregar_puntos(BONUS_POR_SECUAZ)
        
        # Detener barriles existentes para que no molesten en la cinemática
        for b in Barril.instancias:
            b.activo = False
            
        # Desactivar controles
        jugador.speed = 0
        mouse.locked = False
        mouse.visible = True
        
        def fin_epic():
            time.time_scale = 1.0
            if 'menu_victoria' in globals():
                menu_victoria.activar(game_manager.puntuacion)
            
        invoke(fin_epic, delay=0.8)

# ==========================================
# MENÚ DE VICTORIA ÉPICO
# ==========================================
class MenuVictoria(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True)
        self.fondo = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 0), scale=(2,2), z=1)
        
        # Textos con colores invisibles iniciales (alpha 0)
        self.titulo = Text(parent=self, text='¡ENHORABUENA!', origin=(0,0), y=0.25, scale=4, color=color.rgba(255, 215, 0, 0))
        self.mensaje1 = Text(parent=self, text='Has destruido al secuaz.', origin=(0,0), y=0.12, scale=2, color=color.rgba(255, 255, 255, 0))
        self.mensaje2 = Text(parent=self, text='Esto es solo el comienzo de una gran aventura.', origin=(0,0), y=0.05, scale=1.5, color=color.rgba(200, 200, 200, 0))
        
        self.pregunta = Text(parent=self, text='¿Deseas avanzar al segundo nivel?', origin=(0,0), y=-0.08, scale=1.8, color=color.rgba(100, 200, 255, 0))
        self.puntos_text = Text(parent=self, text='', origin=(0,0), y=0.35, scale=1.2, color=color.rgba(255, 255, 255, 0))
        
        # Botones (escondidos inicialmente)
        self.btn_siguiente = Button(parent=self, text='Avanzar a Nivel 2', color=color.rgba(0,100,255,0), highlight_color=color.rgba(0,150,255,255), scale=(0.35, 0.08), y=-0.22, origin=(0,0))
        self.btn_siguiente.text_entity.scale = 1.2
        self.btn_siguiente.text_entity.color = color.rgba(255, 255, 255, 0)
        self.btn_siguiente.on_click = self.accion_siguiente
        
        self.btn_reiniciar = Button(parent=self, text='Reiniciar Nivel 1', color=color.rgba(100,100,100,0), highlight_color=color.rgba(150,150,150,255), scale=(0.25, 0.06), x=-0.15, y=-0.35, origin=(0,0))
        self.btn_reiniciar.text_entity.color = color.rgba(255, 255, 255, 0)
        self.btn_reiniciar.on_click = self.accion_reiniciar
        
        self.btn_salir = Button(parent=self, text='Salir del Juego', color=color.rgba(200,0,0,0), highlight_color=color.rgba(255,50,50,255), scale=(0.25, 0.06), x=0.15, y=-0.35, origin=(0,0))
        self.btn_salir.text_entity.color = color.rgba(255, 255, 255, 0)
        self.btn_salir.on_click = application.quit

    def activar(self, puntuacion):
        self.enabled = True
        mouse.locked = False
        mouse.visible = True
        
        # Resetear textos si se vuelve a jugar
        self.pregunta.text = '¿Deseas avanzar al segundo nivel?'
        self.pregunta.color = color.rgba(100, 200, 255, 0)
        
        self.puntos_text.text = f'PUNTUACIÓN FINAL: {puntuacion}'
        
        # Secuencia épica de Fade-Ins
        self.fondo.animate_color(color.rgba(0, 0, 0, 230), duration=2.0)
        
        self.titulo.animate_color(color.rgba(255, 215, 0, 255), duration=1.5, delay=0.5)
        self.puntos_text.animate_color(color.rgba(255, 255, 255, 200), duration=1.5, delay=0.5)
        
        self.mensaje1.animate_color(color.rgba(255, 255, 255, 255), duration=1.5, delay=1.5)
        self.mensaje2.animate_color(color.rgba(200, 200, 200, 255), duration=1.5, delay=2.5)
        
        self.pregunta.animate_color(color.rgba(100, 200, 255, 255), duration=1.5, delay=4.0)
        
        # Función para revelar botones
        def mostrar_botones():
            self.btn_siguiente.animate_color(color.rgba(0, 100, 200, 255), duration=1.0)
            self.btn_siguiente.text_entity.animate_color(color.rgba(255, 255, 255, 255), duration=1.0)
            
            self.btn_reiniciar.animate_color(color.rgba(100, 100, 100, 255), duration=1.0)
            self.btn_reiniciar.text_entity.animate_color(color.rgba(255, 255, 255, 255), duration=1.0)
            
            self.btn_salir.animate_color(color.rgba(200, 0, 0, 255), duration=1.0)
            self.btn_salir.text_entity.animate_color(color.rgba(255, 255, 255, 255), duration=1.0)
            
        invoke(mostrar_botones, delay=5.0)

    def accion_reiniciar(self):
        self.enabled = False
        reiniciar_juego()

    def accion_siguiente(self):
        # Como aún no hay nivel 2, damos un mensaje divertido/épico
        self.pregunta.text = "¡El Nivel 2 se encuentra en desarrollo! Muy pronto..."
        self.pregunta.color = color.rgba(255, 255, 0, 255)
        self.pregunta.animate_scale(1.9, duration=0.2, curve=curve.out_expo)
        invoke(lambda: self.pregunta.animate_scale(1.8, duration=0.2), delay=0.2)

# ==========================================
# MINIMAPA
# ==========================================
class Minimapa(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, scale=(0.3, 0.4), position=(0.7, 0.25))
        
        self.fondo = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 150), z=1)
        self.borde = Entity(parent=self.fondo, model='quad', color=color.clear, scale=1.05, z=0.1)
        
        # Escala para que el nivel (x: -26 a 26, y: 0 a 84) entre en el cuadro (que va de -0.5 a 0.5 internamente)
        self.mapa_escala_x = 1 / 55.0
        self.mapa_escala_y = 1 / 105.0
        self.offset_y = -0.4 # Centrar verticalmente, ya que y empieza en 0
        
        self.blips = []
        self.jugador_blip = None
        self.secuaz_blip = None
        self.barrel_blips = []  # Pool de blips para barriles
        
        # Pequeño retraso para asegurar que el nivel esté generado
        invoke(self.dibujar_mapa, delay=0.1)

    def dibujar_mapa(self):
        if 'generador' not in globals(): return
        
        # Dibujar Plataformas
        for p in generador.plataformas:
            ancho = (p.x_der - p.x_izq) * self.mapa_escala_x
            centro_x = p.x * self.mapa_escala_x
            centro_y = p.y * self.mapa_escala_y + self.offset_y
            Entity(parent=self, model='quad', color=color.white, scale=(ancho, 0.015), position=(centro_x, centro_y, -0.1), rotation_z=p.rotation_z)
            
        # Dibujar Escaleras
        for esc in generador.escaleras:
            alto = 8.0 * self.mapa_escala_y # Altura estándar visual
            centro_x = esc.x * self.mapa_escala_x
            centro_y = esc.y * self.mapa_escala_y + self.offset_y
            Entity(parent=self, model='quad', color=color.gray, scale=(0.01, alto), position=(centro_x, centro_y, -0.1))
            
        # Blips
        self.jugador_blip = Entity(parent=self, model='circle', color=color.cyan, scale=0.035, z=-0.2)
        self.secuaz_blip = Entity(parent=self, model='circle', color=color.red, scale=0.045, z=-0.2)

    def update(self):
        if not self.jugador_blip or not self.secuaz_blip: return
        
        if 'jugador' in globals() and jugador:
            self.jugador_blip.x = jugador.x * self.mapa_escala_x
            # Usar la Y real para que el punto se dibuje encima de la línea de la plataforma
            self.jugador_blip.y = jugador.y * self.mapa_escala_y + self.offset_y
            
        if 'secuaz_nivel' in globals() and secuaz_nivel:
            self.secuaz_blip.x = secuaz_nivel.x * self.mapa_escala_x
            self.secuaz_blip.y = secuaz_nivel.y * self.mapa_escala_y + self.offset_y

        # ---- Blips de barriles (pool dinámico) ----
        barriles_activos = Barril.instancias
        n_barriles = len(barriles_activos)
        n_blips   = len(self.barrel_blips)

        # Crear blips que faltan
        for _ in range(n_barriles - n_blips):
            b = Entity(parent=self, model='circle', color=color.orange, scale=0.025, z=-0.2)
            self.barrel_blips.append(b)

        # Destruir blips sobrantes
        for b in self.barrel_blips[n_barriles:]:
            destroy(b)
        self.barrel_blips = self.barrel_blips[:n_barriles]

        # Posicionar los blips existentes
        for i, barril in enumerate(barriles_activos):
            self.barrel_blips[i].x = barril.x * self.mapa_escala_x
            self.barrel_blips[i].y = barril.y * self.mapa_escala_y + self.offset_y
            
        # Ocultar en cinemáticas
        _victoria = 'victoria_cinematica' in globals() and victoria_cinematica
        _intro = 'en_intro' in globals() and en_intro
        self.visible = not (_victoria or _intro)

# ==========================================
# MENÚ DE GAME OVER SECUENCIAL
# ==========================================
class MenuGameOver(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True)
        self.fondo = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 0), scale=(2,2))
        self.mensaje = Text(parent=self, text='¡EL SECUAZ TE HA ALCANZADO!\nHas perdido el Nivel 1', origin=(0,0), y=0.1, scale=2.5, color=color.red)
        
        self.btn_reiniciar = Button(parent=self, text='Reiniciar Nivel', y=-0.05, scale=(0.35, 0.08), on_click=self.accion_reiniciar, enabled=False)
        self.btn_salir = Button(parent=self, text='Salir', y=-0.17, scale=(0.35, 0.08), on_click=application.quit, enabled=False)
        self.btn_reiniciar.visible = False
        self.btn_salir.visible = False

    def mostrar(self):
        self.enabled = True
        application.paused = True
        mouse.locked = False
        mouse.visible = True
        self.fondo.color = color.rgba(0, 0, 0, 230)
        self.btn_reiniciar.enabled = True
        self.btn_reiniciar.visible = True
        self.btn_salir.enabled = True
        self.btn_salir.visible = True

    def revelar_opciones(self):
        self.fondo.color = color.rgba(0, 0, 0, 230)
        self.btn_reiniciar.enabled = True
        self.btn_reiniciar.visible = True
        self.btn_salir.enabled = True
        self.btn_salir.visible = True

    def accion_reiniciar(self):
        self.enabled = False
        reiniciar_juego()

# ==========================================
# INTERFAZ Y MENÚ DE PAUSA
# ==========================================
class MenuPausa(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True)
        self.fondo = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 200), scale=(2,2))
        Text(parent=self, text='JUEGO PAUSADO', origin=(0,0), y=0.3, scale=2)
        Button(parent=self, text='Continuar', y=0.1, scale=(0.3, 0.08), on_click=self.reanudar)
        Button(parent=self, text='Reiniciar Nivel', y=0, scale=(0.3, 0.08), on_click=self.accion_reiniciar)
        Button(parent=self, text='Salir', y=-0.1, scale=(0.3, 0.08), on_click=application.quit)

    def alternar(self):
        if menu_game_over.enabled: return 
        self.enabled = not self.enabled
        application.paused = self.enabled
        if self.enabled:
            mouse.locked = False
            mouse.visible = True
        else:
            mouse.locked = True
            mouse.visible = False
    def reanudar(self): 
        self.alternar()
        
    def accion_reiniciar(self):
        self.alternar()
        reiniciar_juego()

# ==========================================
# CONTROL GLOBAL Y REINICIO
# ==========================================
def iniciar_intro():
    global en_intro, texto_intro, intro_pivot
    en_intro = True
    
    jugador.speed = 0
    jugador.jump_height = 0
    jugador.gravity = 0
    jugador.velocity_y = 0 # Prevenir caídas fantasma
    mouse.locked = False
    
    jugador.position = POSICION_INICIAL_JUGADOR
    jugador.visible = True # Reaparecer al jugador si estaba oculto
    
    camera.parent = scene
    camera.rotation = (0, 0, 0)
    camera.position = Vec3(0, secuaz_nivel.y + 2, -35)
    
    target_pos = Vec3(*POSICION_INICIAL_JUGADOR) + Vec3(0, 1.5, -35)
    camera.animate_position(target_pos, duration=2.5, curve=curve.in_out_sine)
    
    if texto_intro: destroy(texto_intro)
    texto_intro = Text(text='NIVEL 1', scale=4, color=color.white, origin=(0,0), y=0.3)
    texto_intro.fade_out(value=0, duration=1.0, delay=1.5)
    
    invoke(mostrar_go, delay=2.6)

def mostrar_go():
    global texto_intro, en_intro
    if not texto_intro: return
    
    texto_intro.alpha = 1
    texto_intro.text = '¡GO!'
    texto_intro.color = color.green
    texto_intro.scale = 5
    texto_intro.animate_scale(8, duration=0.6, curve=curve.out_expo)
    texto_intro.fade_out(value=0, duration=0.5, delay=0.5)
    
    # PASO 1: Posicionar al jugador (gravedad aún apagada)
    jugador.gravity = 0
    jugador.velocity_y = 0
    jugador.speed = 0
    jugador.jump_height = 0
    jugador.position = POSICION_INICIAL_JUGADOR
    jugador.rotation = Vec3(0, 0, 0)
    jugador.camera_pivot.rotation = Vec3(0, 0, 0)
    
    invoke(destroy, texto_intro, delay=1.1)
    
    # PASO 2: Zoom cinematográfico hacia los ojos de Mario
    fpc_height = jugador.camera_pivot.y
    ojo_pos = Vec3(jugador.x, jugador.y + fpc_height, jugador.z)
    dur_zoom = 1.2
    camera.animate_position(ojo_pos, duration=dur_zoom, curve=curve.in_out_sine)
    camera.animate_rotation(Vec3(0, 90, 0), duration=dur_zoom, curve=curve.in_out_sine)
    
    # PASO 3: Al terminar el zoom, snap a primera persona
    def activar_primera_persona():
        
        # FIJACIÓN ESTRICTA: Aseguramos la posición milimétrica antes de que el motor de físicas reaccione
        jugador.position = POSICION_INICIAL_JUGADOR
        jugador.rotation = Vec3(0, 90, 0) # Mirar hacia la derecha (hacia la plataforma)
        jugador.camera_pivot.rotation_x = 0 # Vista totalmente de frente, sin mirar al piso
        
        camera.parent = jugador.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        
        jugador.speed = 5
        jugador.jump_height = 1.5
        jugador.cursor.visible = False # Punto rojo marcador oculto
        jugador.mouse_sensitivity = Vec2(40, 40)
        mouse.locked = True
        
        def reactivar_fisica():
            jugador.gravity = 1
            jugador.velocity_y = 0
        invoke(reactivar_fisica, delay=0.1)
        
        def reactivar_update():
            global en_intro
            en_intro = False
        invoke(reactivar_update, delay=0.2)
    
    invoke(activar_primera_persona, delay=dur_zoom + 0.05)

def reiniciar_juego():
    global secuaz_nivel, texto_victoria
    time.time_scale = 1.0
    game_manager.reiniciar()
    jugador.reiniciar()
    
    # Destruir todos los barriles activos
    for barril in list(Barril.instancias):
        destroy(barril)
        
    # Reiniciar Secuaz (sin destruirlo para evitar crasheos por animaciones pendientes)
    global secuaz_nivel
    try:
        if secuaz_nivel in scene.entities:
            secuaz_nivel.fase2 = False
            secuaz_nivel.derrotado = False
            secuaz_nivel.timer = 0
            secuaz_nivel.barriles_lanzados = 0
            secuaz_nivel.en_pausa_oleada = False
            secuaz_nivel.color = color.white
            secuaz_nivel.rotation = (0, 0, 0)
            secuaz_nivel.position = (0, 84.3, 0)
            secuaz_nivel.scale = 0.08
        else:
            secuaz_nivel = Secuaz(position=(0, 84.3, 0))
    except NameError:
        secuaz_nivel = Secuaz(position=(0, 84.3, 0))
    
    # Reiniciar Martillo
    for martillo in list(MartilloItem.instancias):
        destroy(martillo)
    MartilloItem.instancias.clear()
    spawn_martillo()
    
    # Limpiar estado victoria
    global victoria_cinematica
    victoria_cinematica = False
    if secuaz_nivel:
        secuaz_nivel.derrotado = False
        secuaz_nivel.timer = 0
        secuaz_nivel.barriles_lanzados = 0
        secuaz_nivel.en_pausa_oleada = False
    
    # Limpiar texto de victoria si existe
    try:
        if texto_victoria:
            destroy(texto_victoria)
            texto_victoria = None
    except NameError:
        pass
        
    application.paused = False
    mouse.locked = True
    mouse.visible = False
    
    camera.parent = jugador.camera_pivot
    camera.position = (0, 0, 0)
    camera.rotation = (0, 0, 0)

def input(key):
    _victoria = 'victoria_cinematica' in globals() and victoria_cinematica
    _intro = 'en_intro' in globals() and en_intro
    if _victoria or _intro:
        return

    if key == 'escape':
        menu_pausa.alternar()

    if application.paused: return

    if key == 'left mouse down' and not _victoria and not _intro:
        if game_manager.martillo_activo:
            hit_info = raycast(camera.world_position, camera.forward, distance=4)
            if hit_info.hit and hit_info.entity == secuaz_nivel:
                secuaz_nivel.recibir_dano()

def update():
    if not application.paused and not en_intro:
        try:
            game_manager.update()
        except NameError:
            pass
            
        # Animación de respiración para los neones (efecto Bloom pulsante)
        pulso = (math.sin(time.time() * 3) * 0.5 + 0.5) * 0.4 + 0.6
        if 'generador' in globals() and hasattr(generador, 'neones'):
            for neon, col_orig in generador.neones:
                neon.color = color.rgba(col_orig.r * pulso, col_orig.g * pulso, col_orig.b * pulso, 1.0)
            
        # Animación Cinemática de Victoria
        if 'victoria_cinematica' in globals() and victoria_cinematica:
            camera.parent = scene
            pos_objetivo = secuaz_nivel.position + Vec3(-10, 5, -15)
            camera.position = lerp(camera.position, pos_objetivo, time.dt * 1.5)
            camera.look_at(secuaz_nivel)

# ==========================================
# GENERADOR DE NIVEL
# ==========================================
class GeneradorNivel:
    def __init__(self):
        self.plataformas = []
        self.escaleras = []
        self.neones = []
        self.datos_plat = [
            (0.0,  0, -24.0, 26.0, -1),
            (12.0, 0, -26.0, 24.0,  1),
            (24.0, 0, -24.0, 26.0, -1),
            (36.0, 0, -26.0, 24.0,  1),
            (48.0, 0, -24.0, 26.0, -1),
            (60.0, 0, -26.0, 24.0,  1),
            (72.0, 0, -24.0, 26.0, -1),
            (84.0, 0, -24.0, 24.0,  1)
        ]
        
        # Cálculo de la posición X de las escaleras en los bordes de la plataforma
        self.datos_escaleras = []
        for i in range(len(self.datos_plat) - 1):
            p_inf = self.datos_plat[i]
            p_sup = self.datos_plat[i+1]
            
            y_inf = p_inf[0]
            y_sup = p_sup[0]
            
            # LÓGICA DE POSICIONAMIENTO SOLICITADA
            # Para que la escalera llegue correctamente, usamos la plataforma superior como referencia
            plataforma_x = (p_sup[2] + p_sup[3]) / 2.0
            plataforma_scale_x = p_sup[3] - p_sup[2]
            offset_escalera_x = 1.4 / 2.0 # El ancho del hueco es 1.4, el offset al centro es 0.7
            
            if i % 2 == 0:
                # Escalera Principal Derecha (opcional, para alternar)
                ex = plataforma_x + (plataforma_scale_x / 2.0) - offset_escalera_x
            else:
                # Escalera Principal Izquierda
                ex = plataforma_x - (plataforma_scale_x / 2.0) + offset_escalera_x
                
            self.datos_escaleras.append((ex, y_inf, y_sup))

    def construir_plataforma_3d(self, padre, escala, posicion):
        # Contenedor/Collider principal invisible
        col = Entity(
            parent=padre, 
            model='cube', 
            color=color.clear, 
            scale=escala, 
            position=posicion, 
            collider='box'
        )
        
        ancho, alto, prof = escala
        
        # 1. Base principal (Suelo de madera espectacular)
        base = Entity(
            parent=col,
            model='cube',
            texture='assets/dark_wood_floor.png',
            color=color.white, # Blanco puro para que la textura de madera luzca sus colores naturales y haya buen contraste
            scale=(1.0, 1.0, 1.0), 
            position=(0, 0, 0),
            shader=lit_with_shadows_shader
        )
        # DESACTIVAR FRUSTUM CULLING: Evita que la plataforma desaparezca visualmente cuando el jugador está en los bordes
        from panda3d.core import OmniBoundingVolume
        base.node().setBounds(OmniBoundingVolume())
        base.node().setFinal(True)
        
        # Ajustamos el patrón de la textura (Tiling) para tablones de tamaño realista (repite cada 3 unidades)
        base.texture_scale = (ancho / 3.0, prof / 3.0)
        
        # 2. Tiras de Neón (Bordes decorativos estilo Arcade Moderno)
        color_neon = color.rgb(200, 40, 40) # Rojo industrial vibrante
        n1 = Entity(parent=col, model='cube', color=color_neon, 
               scale=(1.0, 0.05, 0.02), position=(0, 0.45, -0.46))
        n2 = Entity(parent=col, model='cube', color=color_neon, 
               scale=(1.0, 0.05, 0.02), position=(0, 0.45, 0.46))
        self.neones.extend([(n1, color_neon), (n2, color_neon)])
        
        # 3. Paredes invisibles (barreras laterales) para no caer al vacío
        # Las posicionamos exactamente en los bordes (+0.5 y -0.5) del contenedor
        Entity(parent=col, model='cube', color=color.clear, scale=(1.0, 10.0, 0.05), position=(0, 5.0, -0.5), collider='box')
        Entity(parent=col, model='cube', color=color.clear, scale=(1.0, 10.0, 0.05), position=(0, 5.0, 0.5), collider='box')
               
        return col

    def construir_escalera_3d(self, x, y_centro, z, altura):
        # 1. Contenedor invisible sin colisión (evita bugs al subir)
        vis = Entity(
            position=(x, y_centro, z),
            model='cube',
            color=color.clear
        )
        vis.altura = altura 
        vis.scale = (1.5, altura, 0.5) 
        
        # 2. Contenedor visual que anula la deformación del collider padre
        visual = Entity(parent=vis, scale=(1/1.5, 1/altura, 1/0.5))
        
        # 3. Malla de la Escalera (modelo GLB)
        panda_ladder = application.base.loader.loadModel('assets/medieval_wooden-ladder.glb')
        
        # Pivote para rotar la escalera sobre su centro real
        escalera_pivot = Entity(parent=visual)
        escalera_pivot.rotation_y = 90
        # Escalera totalmente recta
        escalera_pivot.rotation_x = 0
        
        escalera_mesh = Entity(
            parent=escalera_pivot,
            model=panda_ladder,
            color=color.white,
            shader=lit_with_shadows_shader
        )
        
        # El modelo mide 2 de alto y su centro está en Y=0.
        scale_y = altura / 2.0
        # Su ancho original
        scale_xz = 1.4 / 0.42
        escalera_mesh.scale = (scale_xz, scale_y, scale_xz)
        
        # Como está centrado, no requiere offset
        escalera_mesh.position = (0, 0, 0)


        return vis

    def generar(self):
        # Paredes invisibles eliminadas para permitir caer de la plataforma (6 de ancho)

        for y_base, rot, x_izq, x_der, dir_b in self.datos_plat:
            centro_x = (x_izq + x_der) / 2
            ancho_total = x_der - x_izq
            
            hueco_x = None
            for ex, ey1, ey2 in self.datos_escaleras:
                if ey2 == y_base:
                    hueco_x = ex
                    break
                    
            p_base = Entity(position=(centro_x, y_base, 0), rotation_z=rot)
            p_base.y_base = y_base; p_base.x_izq = x_izq; p_base.x_der = x_der; p_base.dir_b = dir_b
            
            # DESACTIVAR FRUSTUM CULLING ABSOLUTO: Evita que la plataforma entera desaparezca cuando la cámara va a los extremos
            from panda3d.core import OmniBoundingVolume
            p_base.node().setBounds(OmniBoundingVolume())
            p_base.node().setFinal(True)
            
            self.plataformas.append(p_base)
            
            if hueco_x is not None:
                rel_izq = x_izq - centro_x
                rel_der = x_der - centro_x
                rel_hueco = hueco_x - centro_x
                w_hueco = 1.4 # Ajustado para que encaje a la orilla
                
                ancho1 = (rel_hueco - w_hueco/2) - rel_izq
                if ancho1 > 0:
                    centro1 = rel_izq + ancho1 / 2
                    p1 = self.construir_plataforma_3d(p_base, (ancho1, 0.6, 6.0), (centro1, 0, 0))
                    p1.dir_b = dir_b
                
                ancho2 = rel_der - (rel_hueco + w_hueco/2)
                if ancho2 > 0:
                    centro2 = (rel_hueco + w_hueco/2) + ancho2 / 2
                    p2 = self.construir_plataforma_3d(p_base, (ancho2, 0.6, 6.0), (centro2, 0, 0))
                    p2.dir_b = dir_b
            else:
                p_full = self.construir_plataforma_3d(p_base, (ancho_total, 0.6, 6.0), (0, 0, 0))
                p_full.dir_b = dir_b

            Entity(model='cube', collider='box', position=(x_izq - 0.5, y_base + 6, 0), scale=(1, 12, 12.0), visible=False)
            Entity(model='cube', collider='box', position=(x_der + 0.5, y_base + 6, 0), scale=(1, 12, 12.0), visible=False)

        for ex, ey1, ey2 in self.datos_escaleras:
            p_inf = next((p for p in self.plataformas if getattr(p, 'y_base', None) == ey1), None)
            p_sup = next((p for p in self.plataformas if getattr(p, 'y_base', None) == ey2), None)
            
            real_y1 = ey1
            if p_inf:
                centro_inf = (p_inf.x_izq + p_inf.x_der) / 2
                real_y1 = ey1 + (ex - centro_inf) * math.tan(math.radians(p_inf.rotation_z))
                
            real_y2 = ey2
            if p_sup:
                centro_sup = (p_sup.x_izq + p_sup.x_der) / 2
                real_y2 = ey2 + (ex - centro_sup) * math.tan(math.radians(p_sup.rotation_z))
                
            altura = real_y2 - real_y1
            # El centro Y de la escalera debe tomar en cuenta el grosor de la plataforma (0.3 hacia arriba para grosor 0.6)
            centro_y = (real_y1 + real_y2) / 2 + 0.3
            # Las escaleras se ubican en Z
            
            # Ajuste de posición de la escalera para que esté en el borde izquierdo de la cámara
            # Si ex > 0 (plataforma va hacia la derecha), la izquierda es Z positivo (2.6)
            # Si ex < 0 (plataforma va hacia la izquierda), la izquierda es Z negativo (-2.6)
            pos_z_escalera = 2.6 if ex > 0 else -2.6
            esc = self.construir_escalera_3d(ex, centro_y, pos_z_escalera, altura)
            esc.x = ex; esc.z = pos_z_escalera
            self.escaleras.append(esc)

        return self.plataformas, self.escaleras

# ==========================================
# INICIALIZACIÓN PRINCIPAL
# ==========================================
if __name__ == '__main__':
    app = Ursina(title='Donkey Kong 3D - Nivel 1', development_mode=False)
    
    # IMPORTANTE: Fondo negro absoluto y limpieza de atmósfera para evitar lavado de colores
    window.color = color.black
    camera.background_color = color.black
    scene.fog_color = color.black
    scene.fog_density = (0.015, 60) 
    window.exit_button.visible = False

    # (Skybox eliminado para mantener el negro absoluto sin quemar pantalla)

    # Iluminación Global (Suavizada para evitar quemar texturas)
    AmbientLight(color=color.hex('#334155')) # Luz ambiental ligeramente más clara para contrarrestar
    dir_light = DirectionalLight(color=color.hex('#E2E8F0'), shadows=True) # Direccional más suave
    dir_light.look_at(Vec3(1, -2, 0.5))

    # Objetos globales
    texto_victoria = None
    victoria_cinematica = False
    
    # Generar el nivel
    generador = GeneradorNivel()
    plataformas, escaleras = generador.generar()

    # Inicializar instancias de juego
    menu_victoria = MenuVictoria()
    minimapa_ui = Minimapa()
    menu_game_over = MenuGameOver()
    menu_pausa = MenuPausa()
    game_manager = GameManager()
    jugador = Jugador()
    secuaz_nivel = Secuaz(position=(0, 84.3, 0))
    spawn_martillo()
    
    iniciar_intro()
    app.run()
