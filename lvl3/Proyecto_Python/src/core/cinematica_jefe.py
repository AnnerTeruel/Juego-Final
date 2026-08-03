"""
Módulo para manejar la cinemática y fase del jefe final

Responsable de:
- Iniciar la secuencia cinemática cuando el jugador llega a la cima
- Manejar las animaciones de cámara
- Configurar la arena final del jefe
- Iniciar el minijuego de barriles en 3D
"""

from ursina import *


class CinematicaJefe:
    """Maneja toda la secuencia cinemática del jefe final"""
    
    def __init__(self, manager):
        self.manager = manager
        self.fase_iniciada = False
    
    def iniciar(self):
        """Inicia la secuencia cinemática del jefe"""
        if self.fase_iniciada:
            return
            
        self.fase_iniciada = True
        
        if self.manager.jugador:
            self.manager.jugador.activar(False)
            camera.parent = scene
            
            # Detener el spawner de la intro
            if hasattr(self.manager, 'spawner') and self.manager.spawner:
                self.manager.spawner.activo = False
            
            # Limpiar base_y_original para que el spawner 3D calcule la altura correcta
            if hasattr(self.manager, 'jefe') and hasattr(self.manager.jefe, 'base_y_original'):
                del self.manager.jefe.base_y_original
            
            # Ocultar HUD y arma
            if self.manager.jugador.tiene_martillo:
                self.manager.jugador.martillo_pivot.visible = False
            self.manager.jugador.texto_martillo.visible = False
            self.manager.jugador.texto_puntuacion.visible = False
            if hasattr(self.manager.jugador, 'barra_estamina'):
                self.manager.jugador.barra_estamina.visible = False
                self.manager.jugador.barra_fondo.visible = False
            
            # 1. Saltar a animación 2D (rápido)
            camera.animate_position((0, 45, -150), duration=2, curve=curve.in_out_sine)
            camera.animate_rotation((0, 0, 0), duration=2, curve=curve.in_out_sine)
            
            # 2. Saltar al jefe
            def ir_al_jefe():
                camera.animate_position((-11, 102.5, -40), duration=2, curve=curve.in_out_sine)
            invoke(ir_al_jefe, delay=2.5)
            
            def jefe_salta_cielo():
                if hasattr(self.manager, 'jefe'):
                    manager.jefe.animate_position((manager.jefe.x, 800, manager.jefe.z), duration=0.5, curve=curve.in_expo)
            invoke(jefe_salta_cielo, delay=4.5)
            
            # 3. Volver a vista 2D enfocado ABAJO para empezar a subir con las plataformas
            def enfocar_abajo():
                camera.animate_position((0, 0, -50), duration=2, curve=curve.in_out_sine)
            invoke(enfocar_abajo, delay=5)
            
            # 4. Desaparecer barriles y enderezar plataformas
            invoke(self._enderezar_y_limpiar, delay=7.5)
    
    def _enderezar_y_limpiar(self):
        """Endereza las plataformas y limpia los barriles"""
        # Desaparecer barriles e items
        from src.entidades.barril import Barril
        for b in list(Barril.todos_los_barriles):
            destroy(b)
            
        from src.entidades.bono import Bono, BonoMartillo
        for e in scene.entities:
            if isinstance(e, (Bono, BonoMartillo)):
                idx = int(round(e.y / 9.0))
                target_z = idx * 11
                e.animate_position((e.x, e.y, target_z), duration=0.2, curve=curve.linear)
        
        # Obtener plataformas y ordenarlas de ABAJO hacia ARRIBA
        from src.entidades.entorno import Plataforma, PlataformaTrampa, PlataformaMovil, Teletransportador
        plataformas = [e for e in self.manager.entidades if isinstance(e, (Plataforma, PlataformaTrampa, PlataformaMovil))]
        plataformas.sort(key=lambda p: p.y)
        
        teleporters = [e for e in self.manager.entidades if isinstance(e, Teletransportador)]
        teleporters.sort(key=lambda t: t.y)
        
        def soltar_plataforma(plat, index):
            plat.rotation_z = 0
            
            # Profundidad Z: Empieza en 0 y se aleja 11 unidades por nivel hacia el fondo
            target_z = index * 11
            # Ancho X: Empieza en 80 y se acorta 5.5 unidades por nivel
            target_scale_x = 80 - (index * 5.5)
            
            plat.animate_position((0, plat.y, target_z), duration=0.2, curve=curve.linear)
            plat.animate_scale((target_scale_x, 1, 5), duration=0.2, curve=curve.linear)
            
            if index < len(teleporters):
                tel = teleporters[index]
                signo_actual = 1 if index % 2 == 0 else -1
                tel_x = (target_scale_x / 2 - 2) * signo_actual
                tel.animate_position((tel_x, plat.y + 0.5, target_z), duration=0.2, curve=curve.linear)
                
                target_scale_x_next = 80 - ((index + 1) * 5.5)
                # El destino debe ser en el MISMO lado de donde se teletransportó
                dest_x = (target_scale_x_next / 2 - 2) * signo_actual
                tel.destino = (dest_x, plat.y + 9 + 2, target_z + 11)
            
            camera.shake(duration=0.3, magnitude=1.5)
            # La cámara sube enfocando el centro
            camera.animate_position((0, plat.y, -50), duration=0.4, curve=curve.linear)
        
        retraso = 0.0
        for i, plat in enumerate(plataformas):
            invoke(soltar_plataforma, plat, i, delay=retraso)
            retraso += 0.5
            
        def preparar_camara_jefe():
            # Mover cámara frente al jefe para ver su caída
            camera.animate_position((0, 105, 100), duration=0.5, curve=curve.in_out_sine)
            camera.animate_rotation((0, 0, 0), duration=0.5, curve=curve.in_out_sine)
        
        invoke(preparar_camara_jefe, delay=retraso)
        
        def caer_jefe():
            if hasattr(self.manager, 'jefe'):
                self.manager.jefe.position = (0, 800, 121)
                # Caer con curva linear (sin bounce) para evitar que atraviese la plataforma
                self.manager.jefe.animate_position((0, 101, 121), duration=0.5, curve=curve.out_quad)
                camera.shake(duration=0.5, magnitude=3.0)
        
        invoke(caer_jefe, delay=retraso + 0.8)
        
        # 6. Lanzamiento del JUGADOR
        invoke(self._lanzar_jugador, delay=retraso + 2.5)
    
    def _lanzar_jugador(self):
        """Lanza al jugador hacia atrás después del golpe del jefe"""
        if not self.manager.jugador:
            return
        
        # 1. Colocar al jugador mirando AL JEFE (0° de rotación)
        self.manager.jugador.controller.position = (0, 102, 108)
        self.manager.jugador.controller.rotation_y = 0  # Mirando de frente al jefe
        
        for seq in camera.animations:
            seq.kill()
        camera.parent = self.manager.jugador.controller.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = 90
        
        # Restaurar HUD y arma
        if self.manager.jugador.tiene_martillo:
            self.manager.jugador.martillo_pivot.visible = True
        self.manager.jugador.texto_martillo.visible = True
        self.manager.jugador.texto_puntuacion.visible = True
        if hasattr(self.manager.jugador, 'barra_estamina'):
            self.manager.jugador.barra_estamina.visible = True
            self.manager.jugador.barra_fondo.visible = True

        # 2. EL GOLPE DEL JEFE: Sacudida e impacto
        camera.shake(duration=0.4, magnitude=3.0)

        # 3. TRAYECTORIA DEL GOLPE: El jugador vuela hacia atrás MIRANDO FIJO AL JEFE
        # Subida inicial por el impacto (0.8s)
        self.manager.jugador.controller.animate_position((0, 135, 60), duration=0.8, curve=curve.out_sine)
        
        # Caída directa de espaldas a la primera plataforma (0, 3.5, 0) manteniendo la mirada en el jefe (2.2s)
        def caer_a_base():
            self.manager.jugador.controller.animate_position((0, 3.5, 0), duration=2.2, curve=curve.in_sine)
        invoke(caer_a_base, delay=0.8)
        
        # 4. ATERRIZAJE: Reactivar control manteniendo la mirada fija al jefe en 3D
        invoke(self._fin_lanzamiento, delay=3.0)
    
    def _fin_lanzamiento(self):
        """Finaliza el lanzamiento y prepara la arena del jefe"""
        self.manager.jugador.controller.position = (0, 3.5, 0)
        self.manager.jugador.controller.rotation_y = 0  # Mantener mirada al frente hacia el jefe en modo 3D
        camera.rotation = (0, 0, 0)
        self.manager.jugador.activar(True)
        
        # Iniciar movimiento del jefe
        if hasattr(self.manager, 'jefe'):
            self.manager.jefe.base_y_original = self.manager.jefe.y
            self.manager.jefe.direccion_x = 1
            # Entity helper que mueve al jefe cada frame solo en X
            jefe_mover = Entity()
            jefe_ref_local = self.manager.jefe
            def _mover_jefe():
                jefe_ref_local.x += jefe_ref_local.direccion_x * 12 * time.dt
                if jefe_ref_local.x > 7:
                    jefe_ref_local.direccion_x = -1
                elif jefe_ref_local.x < -7:
                    jefe_ref_local.direccion_x = 1
            jefe_mover.update = _mover_jefe
            self.manager.jefe_mover = jefe_mover  # Guardar referencia para no perderla
        
        # Iniciar minijuego de barriles
        if hasattr(self.manager, 'spawner') and self.manager.spawner:
            destroy(self.manager.spawner)
        from src.entidades.barril import BarrilSpawner
        self.manager.spawner = BarrilSpawner(
            position=(0, 101, 121), 
            jugador_ref=self.manager.jugador, 
            activo=True, 
            modo_rebote3d=True, 
            jefe_ref=getattr(self.manager, 'jefe', None)
        )
