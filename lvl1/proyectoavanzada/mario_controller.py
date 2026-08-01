from ursina import *
from direct.actor.Actor import Actor
import math

# Inicializar motor Ursina
app = Ursina(title="Controlador de Mario 3D")

# 5. Incluir un suelo plano básico con textura/color
suelo = Entity(
    model='plane', 
    scale=(100, 1, 100), 
    color=color.rgb(60, 60, 80), 
    collider='box',
    texture='white_cube'
)

# Cuadrícula para mejor referencia espacial
suelo.texture_scale = (50, 50) 

# 1. Instanciar a Mario usando Actor para animaciones GLTF
# Nota: Asumimos que 'mario.glb' está en la carpeta 'assets' como en tu proyecto base
try:
    mario_actor = Actor('assets/mario.glb')
except:
    # Fallback por si el modelo está en la misma carpeta del script
    mario_actor = Actor('mario.glb')

# Envolver el Actor de Panda3D dentro de un Entity de Ursina para aprovechar su ecosistema
mario = Entity()
mario_actor.reparentTo(mario)

# 2. Posicionar a Mario al iniciar
mario.position = Vec3(-23.4, 0.4, -0.2)

# Variable de control de estado de la animación
mario.is_running = False

# 4. Configurar una cámara en tercera persona (SmoothFollow dinámico)
# Ursina tiene un componente SmoothFollow, pero lo haremos dinámico manual
# para un control estilo tercera persona clásico.
camera_pivot = Entity(parent=mario, y=2)
camera.parent = camera_pivot
camera.position = (0, 3, -10)
camera.look_at(camera_pivot)

def update():
    velocidad = 8 * time.dt
    movimiento = Vec3(0, 0, 0)
    
    # 3. Crear un sistema de movimiento 3D con WASD / flechas
    if held_keys['w'] or held_keys['up arrow']:
        movimiento.z += 1
    if held_keys['s'] or held_keys['down arrow']:
        movimiento.z -= 1
    if held_keys['a'] or held_keys['left arrow']:
        movimiento.x -= 1
    if held_keys['d'] or held_keys['right arrow']:
        movimiento.x += 1
        
    # Normalizar para evitar movimiento más rápido en diagonal
    if movimiento.length() > 0:
        movimiento = movimiento.normalized()
        mario.position += movimiento * velocidad
        
        # Orientar la rotación del modelo hacia la dirección en la que avanza
        # atan2 toma (y, x) pero en plano 3D usamos (X, Z)
        angulo = math.degrees(math.atan2(movimiento.x, movimiento.z))
        
        # Rotación fluida usando lerp (opcional pero más pulido)
        mario.rotation_y = lerp(mario.rotation_y, angulo, time.dt * 15)
        # O rotación instantánea según la regla estricta:
        # mario.rotation_y = angulo
        
        # Si se está moviendo, ejecutar mario.loop('run')
        if not mario.is_running:
            mario_actor.loop('run')
            mario.is_running = True
    else:
        # Al soltar las teclas de movimiento, detener la animación y volver a pose
        if mario.is_running:
            mario_actor.stop()
            mario_actor.pose('run', 0) # Restablecer al primer frame de la animación
            mario.is_running = False
            
    # Ajuste dinámico de cámara (SmoothFollow casero)
    # Suaviza el seguimiento de la cámara cuando Mario se mueve rápido
    camera_pivot.position = lerp(camera_pivot.position, Vec3(0, 2, 0), time.dt * 5)

# Iluminación básica
AmbientLight(color=color.rgba(150, 150, 150, 1))
dir_light = DirectionalLight(y=2, z=3, shadows=True)
dir_light.look_at(Vec3(0, 0, 0))

# Iniciar la aplicación
if __name__ == '__main__':
    app.run()
