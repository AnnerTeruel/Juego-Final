from ursina import *
from src.entidades.entorno import Plataforma, PlataformaMovil, Teletransportador

class Barril(Entity):
    todos_los_barriles = [] # Lista de todos los barriles activos para ignorar colisiones entre ellos

    def __init__(self, position, direction, jugador_ref, es_fuego=False, super_barril=False, es_dorado=False, modo_rebote3d=False):
        # Color del barril
        if es_dorado:
            barrel_color = color.gold
        elif es_fuego:
            barrel_color = color.orange
        else:
            barrel_color = color.white

        super().__init__(
            model='sphere',
            texture='brick',
            color=barrel_color,
            collider='sphere',
            position=position,
            scale=(4, 4, 4) if super_barril else ((2.5, 1.5, 1.5) if es_fuego or es_dorado else (1.5, 1.5, 1.5)),
            rotation_x=90
        )
        self.jugador_ref = jugador_ref
        self.es_fuego = es_fuego
        self.super_barril = super_barril
        self.es_dorado = es_dorado
        self.modo_rebote3d = modo_rebote3d
        
        # Barril dorado es más rápido, fuego medio, normal lento
        self.speed = 12.0 if super_barril else (10.0 if es_dorado else (10.0 if es_fuego else 8.0))
        
        # NUEVO SISTEMA VECTORIAL (como en prueba.py)
        if self.modo_rebote3d:
            # Cálculo matemático exacto para que salte de escalón a escalón:
            # t = 1.2s, delta_z = 11, delta_y = 9
            # v_z = 11 / 1.2 = 9.166
            # v_y = (9 + 0.5 * 25 * 1.44) / 1.2 = 7.5
            self.velocidad = Vec3(0, 0, -9.16) # Se mueve en Z hacia la cámara
        else:
            self.velocidad = Vec3(direction * self.speed, 0, 0) # Rueda normal en X
            
        self.gravedad = Vec3(0, -25.0, 0)
        
        self.puntaje_dado = False
        
        if self.es_fuego or self.super_barril or self.es_dorado:
            luz_color = color.yellow if self.es_dorado else (color.orange if es_fuego else color.red)
            self.luz = PointLight(parent=self, color=luz_color, position=(0,0,0))
            
        Barril.todos_los_barriles.append(self)

    def on_destroy(self):
        if self in Barril.todos_los_barriles:
            Barril.todos_los_barriles.remove(self)

    def update(self):
        # Levantamos el origen del rayo para que nunca empiece dentro de la plataforma
        origen_rayo = self.position + Vec3(0, self.scale_y, 0)
        
        # Raycast con distancia extendida
        distancia_rayo = self.scale_y + (self.scale_y / 2) + 0.5
        if self.velocidad.y < 0:
            distancia_rayo += abs(self.velocidad.y * time.dt) + 1.0

        # Ignoramos al jugador, barriles, ítems y teletransportadores
        from src.entidades.bono import Bono, BonoMartillo
        lista_ignorar = list(Barril.todos_los_barriles)
        lista_ignorar += list(Bono.todos)
        lista_ignorar += list(BonoMartillo.todos)
        lista_ignorar += list(Teletransportador.todos)
        if self.jugador_ref and hasattr(self.jugador_ref, 'controller'):
            lista_ignorar.append(self.jugador_ref.controller)
        
        hit = raycast(origen_rayo, (0, -1, 0), distance=distancia_rayo, ignore=lista_ignorar)
        
        # Sólo consideramos que toca el suelo si NO está saltando/rebotando hacia arriba
        en_plataforma = hit.hit and self.velocidad.y <= 0.1
        
        if en_plataforma:
            self.y = hit.world_point.y + (self.scale_y / 2)
            
            if self.modo_rebote3d:
                # Si está en modo rebote 3D, salta al tocar la plataforma
                self.velocidad.y = 7.5 # Salto calculado para caer exacto en el siguiente escalón
                # Movemos en Z y giramos en X (porque rueda hacia adelante)
                self.z += self.velocidad.z * time.dt
                self.rotation_x += self.velocidad.z * -100 * time.dt
            else:
                self.velocidad.y = 0
                # 1. Obtenemos la normal
                normal = hit.world_normal
                
                # 2. Proyección vectorial para fuerza de deslizamiento (cuesta abajo)
                fuerza_deslizamiento = self.gravedad - normal * self.gravedad.dot(normal)
                
                # 3. Amplificamos la fuerza X para que reaccione rápido (estilo arcade)
                self.velocidad.x += fuerza_deslizamiento.x * 15.0 * time.dt
                
                # 4. Limitamos la velocidad para que no ruede al infinito
                limite = self.speed * 1.5
                if self.velocidad.x > limite: self.velocidad.x = limite
                if self.velocidad.x < -limite: self.velocidad.x = -limite
                
                self.x += self.velocidad.x * time.dt
                self.rotation_z += self.velocidad.x * 100 * time.dt
            
        else:
            # Caída libre pura (o en el aire por el rebote)
            self.velocidad.y += self.gravedad.y * time.dt
            self.y += self.velocidad.y * time.dt
            
            if self.modo_rebote3d:
                # En el aire en modo rebote se sigue moviendo en Z
                self.z += self.velocidad.z * time.dt
                self.rotation_x += self.velocidad.z * -100 * time.dt
            else:
                # En el aire, reducimos severamente la inercia horizontal para que caiga casi recto
                self.x += self.velocidad.x * 0.25 * time.dt
                self.rotation_z += self.velocidad.x * 100 * time.dt

        # Si cae muy abajo o si se va demasiado profundo hacia nosotros (Z muy bajo)
        if self.y < -15 or self.z < -50:
            destroy(self)
            return

        self.verificar_colision_jugador()

    def verificar_colision_jugador(self):
        if not self.jugador_ref or not hasattr(self.jugador_ref, 'controller'):
            return
            
        jug_x = self.jugador_ref.controller.x
        jug_y = self.jugador_ref.controller.y
        jug_z = self.jugador_ref.controller.z
        
        dist_x = abs(self.x - jug_x)
        dist_z = abs(self.z - jug_z)
        dist_y = abs(self.y - jug_y)
        
        radio_x = self.scale_x / 2 + 0.5
        radio_y = self.scale_y / 2 + 1.0

        # Si es el barril dorado, no hace daño al chocar (simplemente lo atraviesas/ignora)
        # El jugador DEBE destruirlo con el martillo
        if self.es_dorado:
            pass
        elif dist_x < radio_x and dist_z < radio_x and dist_y < radio_y:
            if not getattr(self.jugador_ref, 'god_mode', False):
                self.jugador_ref.reaparecer()
            destroy(self)
            return
            
        if dist_x < radio_x + 1.5 and dist_z < radio_x + 1.5:
            if jug_y > self.y + radio_y and not self.puntaje_dado:
                self.puntaje_dado = True
                puntos = 200 if self.super_barril else (100 if self.es_fuego else 50)
                self.jugador_ref.sumar_puntos(puntos)
                texto = Text(text=f'+{puntos*self.jugador_ref.multiplicador}', position=self.jugador_ref.texto_puntuacion.position + (0.5, 0), scale=2, color=color.green, origin=(0,0))
                destroy(texto, delay=1)


class BarrilSpawner(Entity):
    def __init__(self, position, jugador_ref, activo=False, modo_rebote3d=False, jefe_ref=None):
        super().__init__(position=position)
        self.jugador_ref = jugador_ref
        self.activo = activo
        self.modo_rebote3d = modo_rebote3d
        self.jefe_ref = jefe_ref
        self.tiempo_restante = 3.0
        
    def update(self):
        if not self.activo:
            return
            
        self.tiempo_restante -= time.dt
        if self.tiempo_restante <= 0:
            import random
            r = random.random()
            es_fuego = False
            es_dorado = False
            
            if r < 0.15:
                es_dorado = True  # 15% probabilidad de barril dorado
            elif r < 0.45:
                es_fuego = True   # 30% probabilidad de barril de fuego

            # Animación de salto del jefe al lanzar el barril
            if self.jefe_ref:
                # Guardar base_y si no existe aún (así nunca se pierde la altura original)
                if not hasattr(self.jefe_ref, 'base_y_original'):
                    self.jefe_ref.base_y_original = self.jefe_ref.y
                base_y = self.jefe_ref.base_y_original
                
                # Matar animaciones previas para no acumular posiciones
                for seq in self.jefe_ref.animations:
                    seq.kill()
                
                self.jefe_ref.animate_y(base_y + 2.5, duration=0.18, curve=curve.out_sine)
                invoke(lambda: self.jefe_ref.animate_y(base_y, duration=0.18, curve=curve.in_sine), delay=0.18)
                spawn_pos = Vec3(self.jefe_ref.x, base_y + 1, self.jefe_ref.z)
            else:
                spawn_pos = self.position
                
            Barril(position=spawn_pos, direction=1, jugador_ref=self.jugador_ref, 
                   es_fuego=es_fuego, es_dorado=es_dorado, modo_rebote3d=self.modo_rebote3d)
                   
            if self.modo_rebote3d:
                self.tiempo_restante = random.uniform(1.2, 2.0)
            else:
                self.tiempo_restante = 1.8
