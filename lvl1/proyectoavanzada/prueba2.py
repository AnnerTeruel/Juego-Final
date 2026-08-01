"""
╔═══════════════════════════════════════════════════════════════════╗
║   DONKEY KONG 3D - VERSIÓN PROFESIONAL COMPLETA                 ║
║   Incluye: Barriles 3D, Ambientación, Efectos, Iluminación AAA  ║
║   Engine: Ursina | Calidad: AAA Indie Studio                    ║
╚═══════════════════════════════════════════════════════════════════╝
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
from panda3d.core import TransparencyAttrib, PointLight as PL
import random
import math

# ==========================================
# CONSTANTES
# ==========================================
PUNTUACION_INICIAL = 5000
SALUD_INICIAL = 4.0
TIEMPO_MARTILLO_MAX = 14.0
PENALIZACION_TIEMPO = 2.0
PENALIZACION_PUNTOS = 100
PUNTOS_POR_BARRIL = 500
BONUS_POR_SECUAZ = 10000

DAÑO_BARRIL = 1.0
VELOCIDAD_BARRIL_CAIDA = 10.0
VELOCIDAD_BARRIL_RODAR = 4.0

POSICION_INICIAL_JUGADOR = (-8, 1.0, 0)
COLOR_JUGADOR_NORMAL = color.rgb(50, 100, 200)
COLOR_JUGADOR_MARTILLO = color.rgb(255, 220, 0)

# ==========================================
# BARRILES 3D PROFESIONALES
# ==========================================
class BarrilProfesional(Entity):
    """Barril 3D de madera con detalles metálicos y símbolo de peligro"""
    
    instancias = []
    
    def __init__(self, position=(0, 0, 0), **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.model = 'cube'
        self.color = color.clear
        self.scale = (1, 1, 1)
        
        BarrilProfesional.instancias.append(self)
        
        # ═══════════════════════════════════════════
        # CUERPO PRINCIPAL (Cilindro de madera)
        # ═══════════════════════════════════════════
        self.cuerpo = Entity(
            parent=self,
            model='cylinder',  # O 'cube' si no está disponible
            color=color.rgb(180, 100, 40),
            scale=(0.6, 0.8, 0.6),
            shader=lit_with_shadows_shader
        )
        
        # ═══════════════════════════════════════════
        # ANILLAS METÁLICAS DE SUJECIÓN (3 bandas)
        # ═══════════════════════════════════════════
        color_anilla = color.rgb(100, 100, 120)
        
        for y_offset in [-0.25, 0, 0.25]:
            # Anilla superior
            Entity(
                parent=self.cuerpo,
                model='torus',
                color=color_anilla,
                scale=(0.35, 0.06, 0.35),
                position=(0, y_offset, 0),
                shader=lit_with_shadows_shader
            )
            
            # Pequeños remaches en la anilla
            for x_rem in [-0.3, 0.3]:
                Entity(
                    parent=self.cuerpo,
                    model='sphere',
                    color=color.rgb(150, 150, 160),
                    scale=(0.06, 0.04, 0.06),
                    position=(x_rem, y_offset, 0.32)
                )
        
        # ═══════════════════════════════════════════
        # SÍMBOLO DE PELIGRO (Calavera retro)
        # ═══════════════════════════════════════════
        # Triángulo rojo amarillo (símbolo de peligro clásico)
        Entity(
            parent=self.cuerpo,
            model='sphere',
            color=color.rgb(255, 50, 50),  # Rojo peligro
            scale=(0.08, 0.15, 0.08),
            position=(0.3, 0.05, 0)
        )
        
        Entity(
            parent=self.cuerpo,
            model='sphere',
            color=color.rgb(255, 50, 50),
            scale=(0.08, 0.08, 0.08),
            position=(0.3, -0.1, 0)
        )
        
        # Marco de peligro
        for i in range(3):
            Entity(
                parent=self.cuerpo,
                model='quad',
                color=color.rgb(255, 200, 0),
                scale=(0.01, 0.15, 0.01),
                position=(0.25 + i*0.05, 0, 0),
                rotation=(0, 0, 15)
            )
        
        # ═══════════════════════════════════════════
        # BASE Y TAPA (Madera oscura)
        # ═══════════════════════════════════════════
        for y_pos in [-0.4, 0.4]:
            Entity(
                parent=self.cuerpo,
                model='cylinder',
                color=color.rgb(120, 70, 30),
                scale=(0.62, 0.08, 0.62),
                position=(0, y_pos, 0),
                shader=lit_with_shadows_shader
            )
        
        # ═══════════════════════════════════════════
        # RAYOS DECORATIVOS (Efecto de dureza)
        # ═══════════════════════════════════════════
        for i in range(4):
            angulo = (360 / 4) * i
            rad = math.radians(angulo)
            x_ray = math.cos(rad) * 0.3
            z_ray = math.sin(rad) * 0.3
            
            Entity(
                parent=self.cuerpo,
                model='quad',
                color=color.rgb(100, 60, 20),
                scale=(0.02, 0.8, 0.01),
                position=(x_ray, 0, z_ray),
                rotation=(0, angulo, 0)
            )
        
        # Físicas básicas
        self.velocity = Vec3(0, 0, 0)
        self.gravity = 1
        self.collider = 'sphere'

# ==========================================
# EFECTOS VISUALES PROFESIONALES
# ==========================================
class EfectosVisuales:
    """Sistema de partículas y efectos visuales AAA"""
    
    @staticmethod
    def crear_explosion_profesional(posicion, escala=1.0):
        """Explosión con ondas de choque, luz y partículas"""
        
        # ═══════════════════════════════════════════
        # ONDA DE CHOQUE VISIBLE
        # ═══════════════════════════════════════════
        onda = Entity(
            model='sphere',
            color=color.rgb(255, 200, 0),
            position=posicion,
            scale=0.3 * escala,
            opacity=0.9
        )
        
        # Animación de expansión
        onda.animate_scale(2.0 * escala, duration=0.4, curve=curve.out_quad)
        onda.animate_opacity(0, duration=0.4)
        destroy(onda, delay=0.41)
        
        # ═══════════════════════════════════════════
        # FLASH DE LUZ DE IMPACTO
        # ═══════════════════════════════════════════
        flash = PointLight(
            position=posicion,
            color=color.rgb(255, 150, 50),
            range=25 * escala,
            intensity=2.0
        )
        
        # Fade out de la luz
        for i in range(5):
            invoke(lambda f=flash, i=i: setattr(f, 'intensity', 2.0 - (i * 0.4)), delay=i * 0.05)
        
        destroy(flash, delay=0.3)
        
        # ═══════════════════════════════════════════
        # PARTÍCULAS DE ESCOMBROS
        # ═══════════════════════════════════════════
        for i in range(12):
            angulo = (360 / 12) * i
            rad = math.radians(angulo)
            
            velocidad = Vec3(
                math.cos(rad) * random.uniform(8, 15),
                random.uniform(5, 12),
                math.sin(rad) * random.uniform(8, 15)
            )
            
            # Partícula de madera
            particula = Entity(
                model='cube',
                color=color.rgb(random.randint(100, 180), 
                               random.randint(60, 100), 
                               random.randint(20, 40)),
                position=posicion + Vec3(random.uniform(-0.2, 0.2), 0, random.uniform(-0.2, 0.2)),
                scale=(random.uniform(0.05, 0.15), 
                       random.uniform(0.05, 0.15), 
                       random.uniform(0.05, 0.15)),
                velocity=velocidad
            )
            
            # Animación de desaparición con rotación
            def destruir_particula(p, vel):
                p.animate_scale(0, duration=0.8, curve=curve.out_cubic)
                p.animate_opacity(0, duration=0.8)
                p.rotation_speed = Vec3(random.uniform(-5, 5), 
                                       random.uniform(-5, 5), 
                                       random.uniform(-5, 5))
            
            invoke(destruir_particula, particula, velocidad, delay=0.05 * i)
            destroy(particula, delay=0.85)
    
    @staticmethod
    def crear_chispa_metalica(posicion, cantidad=12):
        """Chispas metálicas que rebotan y desaparecen"""
        
        for i in range(cantidad):
            angulo = (360 / cantidad) * i
            rad = math.radians(angulo)
            
            # Vector de velocidad radial + gravedad
            velocidad = Vec3(
                math.cos(rad) * random.uniform(6, 12),
                random.uniform(3, 8),
                math.sin(rad) * random.uniform(6, 12)
            )
            
            # Chispa (pequeña esfera)
            chispa = Entity(
                model='sphere',
                color=color.rgb(255, random.randint(150, 220), 100),
                position=posicion,
                scale=0.08,
                velocity=velocidad
            )
            
            # Animar desaparición
            def animar_chispa(c):
                c.animate_scale(0, duration=0.6, curve=curve.out_expo)
                c.animate_opacity(0, duration=0.6)
            
            invoke(animar_chispa, chispa, delay=0.02 * i)
            destroy(chispa, delay=0.62)
    
    @staticmethod
    def crear_texto_flotante(texto, posicion, color_texto=color.yellow, duracion=1.5):
        """Texto flotante que sube y desaparece"""
        
        texto_3d = Text(
            text=texto,
            position=posicion,
            scale=3,
            color=color_texto
        )
        
        # Animar desaparición y movimiento
        texto_3d.animate_position(posicion + Vec3(0, 2, 0), duration=duracion)
        texto_3d.animate_opacity(0, duration=duracion)
        
        destroy(texto_3d, delay=duracion + 0.1)

# ==========================================
# AMBIENTACIÓN Y DECORACIÓN
# ==========================================
class Ambientacion:
    """Sistema de ambientación y decoración del nivel"""
    
    @staticmethod
    def crear_fondo_retro():
        """Fondo con estilo arcade retro"""
        
        # Fondo principal (cielo gradiente)
        fondo = Entity(
            model='quad',
            color=color.rgb(20, 10, 40),
            scale=(200, 100, 1),
            position=(0, 30, -80),
            shader='unlit'
        )
        
        # Edificios en la distancia (siluetas)
        for x in range(-4, 5):
            altura = random.uniform(10, 30)
            Entity(
                model='cube',
                color=color.rgb(10, 5, 20),
                scale=(15, altura, 1),
                position=(x * 40, 15, -75),
                shader='unlit'
            )
        
        # Ventanas iluminadas (pequeños cuadrados)
        for x in range(-4, 5):
            for y in range(2, int(random.uniform(5, 8))):
                if random.random() > 0.3:
                    Entity(
                        model='quad',
                        color=color.rgb(255, 200, 100),
                        scale=(2, 2, 0.1),
                        position=(x * 40 - 5 + random.uniform(-3, 3), 
                                y * 4, -74.9),
                        shader='unlit'
                    )
    
    @staticmethod
    def crear_decoracion_industrial():
        """Elementos decorativos industriales"""
        
        # Bariles apilados (inactivos, solo decoración)
        for x in [-15, 15]:
            for y in range(3):
                Entity(
                    model='cylinder',
                    color=color.rgb(100, 60, 30),
                    scale=(0.4, 0.4, 0.4),
                    position=(x, -2 + y * 0.5, -2)
                )
        
        # Máquinas/Cajas metálicas en esquinas
        for x in [-18, 18]:
            Entity(
                model='cube',
                color=color.rgb(50, 50, 60),
                scale=(2, 3, 1),
                position=(x, 2, -2)
            )
            
            # Pequeñas luces en la máquina
            for y_luz in [0.5, 1.5, 2.5]:
                Entity(
                    model='sphere',
                    color=color.rgb(0, 255, 100),
                    scale=(0.15, 0.15, 0.15),
                    position=(x + 0.8, y_luz, -1.5),
                    emissive=True
                )
    
    @staticmethod
    def crear_luces_ambientes():
        """Luces de ambiente adicionales estratégicamente colocadas"""
        
        # Luces de esquina (calor y frío)
        PointLight(
            position=(-20, 15, 0),
            color=color.rgb(255, 150, 0),
            range=30,
            intensity=0.5
        )
        
        PointLight(
            position=(20, 15, 0),
            color=color.rgb(0, 150, 255),
            range=30,
            intensity=0.5
        )
        
        # Luces en el piso (simular iluminación desde abajo)
        PointLight(
            position=(0, -5, 0),
            color=color.rgb(100, 200, 255),
            range=40,
            intensity=0.3
        )

# ==========================================
# GENERADOR NIVEL PROFESIONAL
# ==========================================
class GeneradorNivelProfesional:
    """Constructor completo del nivel con todos los detalles"""
    
    def __init__(self):
        self.plataformas = []
        self.escaleras = []
        
        # Datos de plataformas: (altura, rotación, x_izq, x_der, dir_barril)
        self.datos_plat = [
            (1.0, 0.0, -10.0, 10.0, 1),
            (9.0, 0.0, -8.0, 8.0, -1),
            (17.0, 0.0, -10.0, 10.0, 1),
            (25.0, 25.0, -8.0, 8.0, -1),
            (33.0, 0.0, -10.0, 10.0, 1),
            (41.0, -25.0, -8.0, 8.0, 1),
            (49.0, 0.0, -10.0, 10.0, 1),
            (57.0, 0.0, -8.0, 8.0, -1),
        ]
        
        self.datos_escaleras = [
            (-6.5, 1.0, 9.0),
            (6.5, 9.0, 17.0),
            (-6.5, 17.0, 25.0),
            (7.5, 25.0, 33.0),
            (-6.5, 33.0, 41.0),
            (7.5, 41.0, 49.0),
            (-6.5, 49.0, 57.0),
        ]

    def construir_plataforma_pro(self, padre, escala, posicion):
        """Plataforma 3D con máximo detalle arquitectónico"""
        
        col = Entity(
            parent=padre,
            model='cube',
            color=color.clear,
            scale=escala,
            position=posicion,
            collider='box'
        )
        
        ancho, alto, prof = escala
        grosor_piso = 0.25
        
        # SUPERFICIE PRINCIPAL
        piso = Entity(
            parent=col,
            model='cube',
            color=color.rgb(120, 85, 50),
            scale=(1, grosor_piso / alto, 1),
            position=(0, (alto/2 - grosor_piso/2) / alto, 0),
            shader=lit_with_shadows_shader
        )
        
        # Bandas de madera (tablones)
        for i in range(max(2, int(ancho * 1.5))):
            offset_x = -0.5 + (i / max(2, int(ancho * 1.5)))
            Entity(
                parent=piso,
                model='cube',
                color=color.rgb(90, 60, 30),
                scale=(0.08, 0.02, 1),
                position=(offset_x, 0.01, 0),
                shader=lit_with_shadows_shader
            )
        
        # BORDES METÁLICOS
        grosor_borde = 0.2
        color_metal_oscuro = color.rgb(45, 50, 60)
        color_metal_claro = color.rgb(200, 200, 210)
        
        for z_pos in [-0.5, 0.5]:
            Entity(
                parent=col,
                model='cube',
                color=color_metal_oscuro,
                shader=lit_with_shadows_shader,
                scale=(1, grosor_piso / alto, grosor_borde / prof),
                position=(0, (alto/2 - grosor_piso/2) / alto, z_pos)
            )
        
        # VIGAS DE SOPORTE
        num_vigas = max(3, int(ancho / 1.5))
        dist_vigas = 1.0 / num_vigas
        
        for i in range(num_vigas + 1):
            pos_x = -0.5 + i * dist_vigas
            Entity(
                parent=col,
                model='cube',
                color=color.rgb(35, 40, 50),
                shader=lit_with_shadows_shader,
                scale=(grosor_borde / ancho, (alto - grosor_piso) / alto, 1),
                position=(pos_x, -grosor_piso / (2 * alto), 0)
            )
        
        # LUCES NEÓN EN BORDES
        for x_luz in [-0.4, 0.4]:
            Entity(
                parent=col,
                model='sphere',
                color=color.rgb(0, 255, 150),
                emissive=True,
                scale=(0.1, 0.05, 0.1),
                position=(x_luz, (alto/2) / alto + 0.05, 0.45),
                shader=lit_with_shadows_shader
            )
        
        return col

    def construir_escalera_pro(self, x, y_centro, z, altura):
        """Escalera profesional con detalles"""
        
        vis = Entity(
            position=(x, y_centro, z),
            model='cube',
            color=color.clear
        )
        vis.altura = altura
        vis.scale = (1.5, altura, 0.5)
        
        visual = Entity(parent=vis, scale=(1/1.5, 1/altura, 1/0.5))
        
        # POSTES LATERALES
        for x_pos in [-0.7, 0.7]:
            Entity(
                parent=visual,
                model='cube',
                color=color.rgb(120, 85, 50),
                position=(x_pos, 0, 0),
                scale=(0.12, altura, 0.12),
                shader=lit_with_shadows_shader
            )
        
        # PELDAÑOS CON DETALLES
        distancia_peldanos = 1.0
        num_peldanos = int(altura / distancia_peldanos)
        y_inicial = -(altura / 2) + 0.5
        
        for i in range(num_peldanos):
            y_pos = y_inicial + i * distancia_peldanos
            
            # Peldaño de madera
            Entity(
                parent=visual,
                model='cube',
                color=color.rgb(140, 100, 60),
                position=(0, y_pos, 0),
                scale=(1.2, 0.12, 0.15),
                shader=lit_with_shadows_shader
            )
            
            # Banda antideslizante
            Entity(
                parent=visual,
                model='cube',
                color=color.rgb(30, 30, 30),
                position=(0, y_pos + 0.06, 0.075),
                scale=(1.0, 0.03, 0.04)
            )
        
        return vis

    def generar(self):
        """Generar nivel completo"""
        
        # Paredes colisores
        Entity(model='cube', collider='box', position=(0, 28, 3.5), 
               scale=(40, 80, 1), visible=False)
        Entity(model='cube', collider='box', position=(0, 28, -3.5), 
               scale=(40, 80, 1), visible=False)

        # Plataformas
        for y_base, rot, x_izq, x_der, dir_b in self.datos_plat:
            centro_x = (x_izq + x_der) / 2
            ancho_total = x_der - x_izq
            
            hueco_x = None
            for ex, ey1, ey2 in self.datos_escaleras:
                if ey2 == y_base:
                    hueco_x = ex
                    break
                    
            p_base = Entity(position=(centro_x, y_base, 0), rotation_z=rot)
            p_base.y_base = y_base
            p_base.x_izq = x_izq
            p_base.x_der = x_der
            p_base.dir_b = dir_b
            self.plataformas.append(p_base)
            
            if hueco_x is not None:
                rel_izq = x_izq - centro_x
                rel_der = x_der - centro_x
                rel_hueco = hueco_x - centro_x
                w_hueco = 1.4
                
                ancho1 = (rel_hueco - w_hueco/2) - rel_izq
                if ancho1 > 0:
                    centro1 = rel_izq + ancho1 / 2
                    p1 = self.construir_plataforma_pro(p_base, (ancho1, 0.8, 6.0), 
                                                       (centro1, 0, 0))
                    p1.dir_b = dir_b
                
                ancho2 = rel_der - (rel_hueco + w_hueco/2)
                if ancho2 > 0:
                    centro2 = (rel_hueco + w_hueco/2) + ancho2 / 2
                    p2 = self.construir_plataforma_pro(p_base, (ancho2, 0.8, 6.0), 
                                                       (centro2, 0, 0))
                    p2.dir_b = dir_b
            else:
                p_full = self.construir_plataforma_pro(p_base, (ancho_total, 0.8, 6.0), 
                                                       (0, 0, 0))
                p_full.dir_b = dir_b

            Entity(model='cube', collider='box', position=(x_izq - 0.5, y_base + 4, 0), 
                   scale=(1, 8, 6.0), visible=False)
            Entity(model='cube', collider='box', position=(x_der + 0.5, y_base + 4, 0), 
                   scale=(1, 8, 6.0), visible=False)

        # Escaleras
        for ex, ey1, ey2 in self.datos_escaleras:
            p_inf = next((p for p in self.plataformas if getattr(p, 'y_base', None) == ey1), 
                        None)
            p_sup = next((p for p in self.plataformas if getattr(p, 'y_base', None) == ey2), 
                        None)
            
            real_y1 = ey1
            if p_inf:
                centro_inf = (p_inf.x_izq + p_inf.x_der) / 2
                real_y1 = ey1 + (ex - centro_inf) * math.tan(math.radians(p_inf.rotation_z))
                
            real_y2 = ey2
            if p_sup:
                centro_sup = (p_sup.x_izq + p_sup.x_der) / 2
                real_y2 = ey2 + (ex - centro_sup) * math.tan(math.radians(p_sup.rotation_z))
                
            altura = real_y2 - real_y1
            centro_y = (real_y1 + real_y2) / 2
            
            esc = self.construir_escalera_pro(ex, centro_y, 2.8, altura + 0.5)
            esc.x = ex
            esc.z = 2.8
            self.escaleras.append(esc)

        return self.plataformas, self.escaleras

# ==========================================
# ILUMINACIÓN CINEMATOGRÁFICA
# ==========================================
def configurar_iluminacion_cinematica():
    """Iluminación profesional estilo cinematográfico"""
    
    # Fondo oscuro profundo
    camera.background_color = color.hex('#0a0a1a')
    scene.fog_color = color.hex('#0a0a1a')
    scene.fog_density = (0.008, 100)
    
    # KEY LIGHT - Luz principal cálida
    key_light = DirectionalLight(color=color.rgb(255, 200, 130), shadows=True)
    key_light.look_at(Vec3(2, -3, 1))
    
    # FILL LIGHT - Luz de relleno fría
    fill_light = DirectionalLight(color=color.rgb(80, 120, 200), shadows=False)
    fill_light.intensity = 0.45
    fill_light.look_at(Vec3(-1, -1, -1))
    
    # AMBIENT - Luz ambiental
    ambient = AmbientLight(color=color.rgb(30, 30, 50))
    ambient.intensity = 0.4
    
    # ACCENT LIGHTS - Luces de énfasis neón
    accent1 = DirectionalLight(color=color.rgb(0, 255, 200), shadows=False)
    accent1.intensity = 0.35
    accent1.look_at(Vec3(1, 1, 2))
    
    accent2 = DirectionalLight(color=color.rgb(255, 100, 150), shadows=False)
    accent2.intensity = 0.25
    accent2.look_at(Vec3(-1, 1, -2))

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    app = Ursina(
        title='DONKEY KONG 3D - VERSIÓN PROFESIONAL COMPLETA',
        development_mode=False,
        vsync=True,
        fullscreen=False
    )
    
    window.exit_button.visible = False
    window.fps_counter.enabled = True
    
    # Configurar iluminación
    print("🎬 Configurando iluminación cinematográfica...")
    configurar_iluminacion_cinematica()
    
    # Generar nivel
    print("🏗️  Construyendo nivel profesional...")
    generador = GeneradorNivelProfesional()
    plataformas, escaleras = generador.generar()
    
    # Ambientación
    print("🎨 Agregando ambientación y decoración...")
    Ambientacion.crear_fondo_retro()
    Ambientacion.crear_decoracion_industrial()
    Ambientacion.crear_luces_ambientes()
    
    # Crear barril de prueba
    print("🎯 Creando sistemas de efectos...")
    barril_test = BarrilProfesional(position=(0, 5, 0))
    
    # Información de la consola
    print("═" * 60)
    print("✅ DONKEY KONG 3D - VERSIÓN PROFESIONAL COMPLETA")
    print("═" * 60)
    print("🎮 Características:")
    print("   • Plataformas 3D con arquitectura industrial")
    print("   • Escaleras con detalles (bandas, tornillos)")
    print("   • Barriles 3D con anillas metálicas")
    print("   • Iluminación cinematográfica (3-Point Lighting)")
    print("   • Efectos: Explosiones, chispas, partículas")
    print("   • Ambientación: Fondo retro, decoración industrial")
    print("   • Luces neón y ambiente profesional")
    print("═" * 60)
    print("Presiona F12 para developer mode")
    print("Presiona ESC para salir")
    print("═" * 60)
    
    app.run()