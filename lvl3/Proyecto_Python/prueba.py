from ursina import *

class ObjetoCayendo(Entity):
    def __init__(self, **kwargs):
        # Configuramos el objeto (puedes ajustar el modelo y color)
        super().__init__(model='cube', collider='box', color=color.orange, **kwargs)
        
        # Un vector de gravedad apuntando hacia abajo
        self.gravedad = Vec3(0, -9.8, 0)
    
    def update(self):
        # 1. Lanzamos un rayo hacia abajo puro (Vec3(0, -1, 0)) para detectar la plataforma
        hit_info = raycast(self.world_position, Vec3(0, -1, 0), ignore=(self,), distance=1.5)
        
        if hit_info.hit:
            # 2. Obtenemos la normal de la rampa
            normal = hit_info.world_normal
            
            # 3. Aplicamos la fórmula de proyección vectorial para el deslizamiento
            # Vec3.dot() multiplica los vectores
            fuerza_deslizamiento = self.gravedad - normal * self.gravedad.dot(normal)
            
            # 4. Movemos el objeto en la dirección de la rampa
            self.position += fuerza_deslizamiento * time.dt
            
            # 5. Mantenemos el objeto a ras del suelo para que la colisión no lo empuje hacia arriba
            # Usamos self.scale_y / 2 asumiendo que el centro (origen) del objeto está en el medio
            self.y = hit_info.world_point.y + (self.scale_y / 2)
        else:
            # Si no toca nada, cae en picada (caída libre)
            self.position += self.gravedad * time.dt

app = Ursina()

# Una rampa de prueba para que veas cómo resbala
rampa = Entity(model='cube', collider='box', scale=(10, 1, 10), rotation_z=20, position=(0, -2, 0), color=color.gray)

# Instanciamos tu objeto cayendo
mi_objeto = ObjetoCayendo(position=(0, 5, 0))

EditorCamera()
app.run()