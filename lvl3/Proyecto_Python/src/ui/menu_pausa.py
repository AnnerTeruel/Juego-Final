from ursina import *

class MenuPausa:
    """Maneja toda la UI y lógica del menú de pausa"""
    
    def __init__(self, manager):
        self.manager = manager
        self.pausa_activa = False
        self.sensibilidad_actual = 20
        self.elementos_pausa = []
        
        self._crear_ui()
        
    def _crear_ui(self):
        # Panel de fondo: z=0 (detras de los elementos UI)
        self.panel_pausa = Entity(
            parent=camera.ui,
            model='quad',
            color=Color(0.02, 0.04, 0.14, 0.92),
            scale=(0.52, 0.62),
            z=0,
            enabled=False
        )

        # Todos los elementos van con z=-0.01 para aparecer ENCIMA del panel
        self.titulo_pausa = Text(
            parent=self.panel_pausa,
            text='PAUSA',
            scale=5.5,
            position=(0, 0.38),
            origin=(0, 0),
            color=color.rgb(255, 200, 50),
            z=-0.01,
            enabled=True
        )

        self.linea = Entity(
            parent=self.panel_pausa,
            model='quad',
            color=Color(1, 0.78, 0.2, 0.5),
            scale=(0.92, 0.005),
            position=(0, 0.24),
            z=-0.01,
            enabled=True
        )

        self.lbl_sens = Text(
            parent=self.panel_pausa,
            text='Sensibilidad de camara',
            scale=2.2,
            position=(0, 0.17),
            origin=(0, 0),
            color=color.rgb(180, 210, 255),
            z=-0.01,
            enabled=True
        )

        self.slider_sens = Slider(
            min=5,
            max=60,
            default=self.sensibilidad_actual,
            step=1,
            position=(0, 0.04),
            scale=0.55,
            enabled=False
        )

        self.lbl_valor_sens = Text(
            parent=self.panel_pausa,
            text=str(self.sensibilidad_actual),
            scale=2.5,
            position=(0, -0.06),
            origin=(0, 0),
            color=color.yellow,
            z=-0.01,
            enabled=True
        )

        self.btn_reanudar = Button(
            text='Reanudar',
            color=Color(0.12, 0.55, 0.24, 0.95),
            highlight_color=Color(0.18, 0.72, 0.32, 1),
            pressed_color=Color(0.08, 0.38, 0.16, 1),
            scale=(0.3, 0.07),
            position=(0, -0.17),
            enabled=False
        )

        self.btn_salir = Button(
            text='Salir al escritorio',
            color=Color(0.62, 0.12, 0.12, 0.95),
            highlight_color=Color(0.82, 0.22, 0.22, 1),
            pressed_color=Color(0.46, 0.08, 0.08, 1),
            scale=(0.3, 0.07),
            position=(0, -0.27),
            enabled=False
        )
        
        self.btn_reanudar.on_click = self.reanudar
        self.btn_salir.on_click = application.quit
        
        self.elementos_pausa = [
            self.panel_pausa, 
            self.slider_sens, 
            self.btn_reanudar, 
            self.btn_salir
        ]
    
    def mostrar(self, estado):
        """Muestra u oculta el menú de pausa"""
        self.pausa_activa = estado
        for e in self.elementos_pausa:
            e.enabled = estado
        application.paused = estado
        mouse.locked = not estado
        mouse.visible = estado
        
        if estado and self.manager.jugador:
            # Sincronizamos el slider con la sensibilidad actual
            self.slider_sens.value = self.manager.jugador.controller.mouse_sensitivity.x
    
    def reanudar(self):
        """Cierra el menú de pausa"""
        self.mostrar(False)
    
    def update(self):
        """Actualiza la sensibilidad en tiempo real cuando está en pausa"""
        if self.pausa_activa and self.manager.jugador:
            val = int(self.slider_sens.value)
            self.manager.jugador.controller.mouse_sensitivity = Vec2(val, val)
            self.lbl_valor_sens.text = str(val)
    
    def input(self, key):
        """Maneja el input de escape para toggle de pausa"""
        if key == 'escape':
            self.mostrar(not self.pausa_activa)
