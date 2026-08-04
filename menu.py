"""
Menu principal interactivo basado en Tkinter.
Actua como un lanzador (launcher) aislando la UI del motor de juego Ursina.
"""
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
import subprocess
import sys
import json
import time
import threading


# ==========================================================
# RUTAS
# ==========================================================

CARPETA_PROYECTO = Path(__file__).resolve().parent

RUTA_FONDO_MENU = CARPETA_PROYECTO / "assets" / "fondo_juego_sin_sello.png"
RUTA_PROGRESS = CARPETA_PROYECTO / "progress.json"
RUTA_STATS = CARPETA_PROYECTO / "estadisticas.json"
RUTA_RUN_RESULT = CARPETA_PROYECTO / "run_result.json"

try:
    pass # estadisticas_db.crear_tablas()
except Exception as error:
    print(f"Error creando base de datos de estadisticas: {error}")


def normalizar_estado(estado):
    if estado.get('nivel3', False) and not estado.get('nivel2', False):
        estado['nivel2'] = True
    if not estado.get('nivel2', False):
        estado['nivel3'] = False
    return {
        'nivel2': bool(estado.get('nivel2', False)),
        'nivel3': bool(estado.get('nivel3', False))
    }


def cargar_estado_niveles():
    if not RUTA_PROGRESS.exists():
        estado = {'nivel2': False, 'nivel3': False}
        guardar_estado_niveles(estado)
        return estado

    try:
        with open(RUTA_PROGRESS, 'r', encoding='utf-8') as archivo:
            data = json.load(archivo)
    except Exception:
        estado = {'nivel2': False, 'nivel3': False}
        guardar_estado_niveles(estado)
        return estado

    estado = normalizar_estado({
        'nivel2': data.get('nivel2', False),
        'nivel3': data.get('nivel3', False)
    })
    guardar_estado_niveles(estado)
    return estado


def guardar_estado_niveles(estado):
    try:
        with open(RUTA_PROGRESS, 'w', encoding='utf-8') as archivo:
            json.dump({
                'nivel2': bool(estado.get('nivel2', False)),
                'nivel3': bool(estado.get('nivel3', False))
            }, archivo)
    except Exception as error:
        print(f"Error guardando progreso de niveles: {error}")


def nivel_desbloqueado(numero, estado):
    if numero == 1:
        return True
    return estado.get(f'nivel{numero}', False)


def dibujar_niveles():
    for hijo in contenedor_niveles.winfo_children():
        hijo.destroy()

    estado = cargar_estado_niveles()

    for numero_nivel in (1, 2, 3):
        crear_tarjeta_nivel(
            contenedor_niveles,
            numero_nivel,
            nivel_desbloqueado(numero_nivel, estado)
        ).grid(
            row=0,
            column=numero_nivel - 1,
            padx=12
        )


# ==========================================================
# CONFIGURACION
# ==========================================================

COLOR_MENU = "black"
DURACION_TRANSICION = 3000
PASOS_TRANSICION = 45


# ==========================================================
# VARIABLES GLOBALES
# ==========================================================

frame_actual = None
transicion_activa = False

nombre_jugador_actual = ""
nivel_seleccionado = None
# cargando_overlay removed — no loading overlay

# Conserva las imagenes para que Tkinter no las elimine
imagenes = {}
fondo_menu_original = None


# ==========================================================
# FUNCIONES PARA IMAGENES
# ==========================================================

def cargar_imagen_original(ruta):
    try:
        if not ruta.exists():
            print(f"No se encontro la imagen: {ruta}")
            return None

        return Image.open(ruta).convert("RGB")

    except Exception as error:
        print(f"Error al cargar la imagen de fondo: {error}")
        return None


def actualizar_fondo_menu(event=None):
    if event is not None and event.widget != frame_menu:
        return

    if fondo_menu_original is None:
        return

    ancho = max(frame_menu.winfo_width(), 1)
    alto = max(frame_menu.winfo_height(), 1)

    fondo_redimensionado = fondo_menu_original.resize(
        (ancho, alto),
        Image.Resampling.LANCZOS
    )

    imagenes["fondo_menu"] = ImageTk.PhotoImage(fondo_redimensionado)

    fondo_menu.configure(
        image=imagenes["fondo_menu"]
    )

    fondo_menu.place(
        x=0,
        y=0,
        relwidth=1,
        relheight=1
    )

    fondo_menu.lower()


# ==========================================================
# FUNCIONES GENERALES
# ==========================================================

def pantalla_completa():
    try:
        ventana.state("zoomed")

    except TclError:
        ancho = ventana.winfo_screenwidth()
        alto = ventana.winfo_screenheight()

        ventana.geometry(
            f"{ancho}x{alto}+0+0"
        )


def salir():
    respuesta = messagebox.askyesno(
        "Confirmación",
        "¿Está seguro que desea salir?"
    )

    if respuesta:
        ventana.destroy()


def mostrar_frame_inicial(frame):
    global frame_actual

    frame.place(
        x=0,
        y=0,
        relwidth=1,
        relheight=1
    )

    frame.tkraise()
    frame_actual = frame

    centrar_todo()


def centrar_todo():
    menu_centro.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    juego_centro.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    estadistica_centro.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )


def formatear_tiempo(segundos):
    minutos = int(segundos) // 60
    segundos_restantes = int(segundos) % 60
    return f"{minutos:02d}:{segundos_restantes:02d}"


def formatear_posicion(posicion):
    if isinstance(posicion, dict):
        x = posicion.get('x', 0)
        y = posicion.get('y', 0)
        z = posicion.get('z', 0)
    else:
        try:
            x, y, z = posicion[:3]
        except (TypeError, ValueError, IndexError):
            x, y, z = 0, 0, 0

    try:
        return f"X:{float(x):.1f} Y:{float(y):.1f} Z:{float(z):.1f}"
    except (TypeError, ValueError):
        return "X:0.0 Y:0.0 Z:0.0"


def cargar_estadisticas():
    try:
        # estadisticas_db.migrar_desde_json(RUTA_STATS)
        # return estadisticas_db.cargar_partidas()
        return []
    except Exception as error:
        print(f"Error cargando estadisticas: {error}")
        return []


def guardar_estadistica(nombre, puntos, tiempo, nivel, posicion=None):
    try:
        pass # estadisticas_db.guardar_partida(nombre, puntos, tiempo, nivel, posicion)
    except Exception as error:
        print(f"Error guardando estadisticas: {error}")
    return
    if False:
        print(f"Error guardando estadísticas: {error}")


def refrescar_tabla_estadisticas():
    for elemento in tabla_estadisticas.get_children():
        tabla_estadisticas.delete(elemento)

    registros = cargar_estadisticas()

    for indice, registro in enumerate(registros, start=1):
        etiqueta = "fila_par" if indice % 2 == 0 else "fila_impar"
        id_registro = registro.get('id')
        valores = (
            indice,
            registro.get('nombre', ''),
            registro.get('puntos', 0),
            formatear_tiempo(registro.get('tiempo', 0)),
            formatear_posicion(registro.get('posicion'))
        )

        if id_registro is None:
            tabla_estadisticas.insert(
                "",
                END,
                values=valores,
                tags=(etiqueta,)
            )
        else:
            tabla_estadisticas.insert(
                "",
                END,
                iid=str(id_registro),
                values=valores,
                tags=(etiqueta,)
            )

    actualizar_lineas_tabla()



def abrir_dialogo_nombre(numero=None):
    global nombre_jugador_actual

    dialogo = Toplevel(ventana)
    dialogo.title("Nombre Del Jugador")
    dialogo.configure(bg="black")
    dialogo.resizable(False, False)
    dialogo.grab_set()
    dialogo.transient(ventana)

    ancho_dialogo = 400
    alto_dialogo = 220
    dialogo.geometry(f"{ancho_dialogo}x{alto_dialogo}")
    dialogo.update_idletasks()
    x = ventana.winfo_x() + (ventana.winfo_width() - ancho_dialogo) // 2
    y = ventana.winfo_y() + (ventana.winfo_height() - alto_dialogo) // 2
    dialogo.geometry(f"{ancho_dialogo}x{alto_dialogo}+{x}+{y}")

    Label(
        dialogo,
        text="Nombre Del Jugador",
        font=("Arial", 16, "bold"),
        fg="white",
        bg="black"
    ).pack(pady=(20, 10))

    placeholder = "Nombre Del Jugador"
    entrada_nombre = Entry(dialogo, font=("Arial", 16), width=24, fg="#999999")
    if nombre_jugador_actual:
        entrada_nombre.insert(0, nombre_jugador_actual)
        entrada_nombre.config(fg="black")
    else:
        entrada_nombre.insert(0, placeholder)

    def limpiar_placeholder(event=None):
        if entrada_nombre.get() == placeholder:
            entrada_nombre.delete(0, END)
            entrada_nombre.config(fg="black")

    def restaurar_placeholder(event=None):
        if entrada_nombre.get().strip() == "":
            entrada_nombre.delete(0, END)
            entrada_nombre.insert(0, placeholder)
            entrada_nombre.config(fg="#999999")

    entrada_nombre.bind('<FocusIn>', limpiar_placeholder)
    entrada_nombre.bind('<FocusOut>', restaurar_placeholder)
    entrada_nombre.pack(pady=(0, 20))
    entrada_nombre.focus()

    def iniciar_desde_dialogo():
        global nombre_jugador_actual
        nombre = entrada_nombre.get().strip()
        if nombre == placeholder:
            nombre = ""
        nombre = nombre or "Jugador"
        nombre_jugador_actual = nombre
        dialogo.destroy()
        if numero is not None:
            iniciar_nivel(numero)

    Button(
        dialogo,
        text="Aceptar",
        font=("Arial", 14, "bold"),
        width=12,
        bg="#FFD700",
        fg="black",
        activebackground="#FFC300",
        activeforeground="black",
        borderwidth=0,
        cursor="hand2",
        command=iniciar_desde_dialogo
    ).pack(pady=(0, 20))

    dialogo.bind('<Return>', lambda event: iniciar_desde_dialogo())


# ==========================================================
# EFECTO DE BOTONES
# ==========================================================

def activar_efecto_presionado(boton):
    """
    Hace que un boton se vea hundido cuando el mouse pasa encima.
    """

    color_normal = boton.cget("background")
    color_texto_normal = boton.cget("foreground")
    color_hover = boton.cget("activebackground")
    color_texto_hover = boton.cget("activeforeground")

    boton.configure(
        relief="raised",
        overrelief="sunken",
        borderwidth=4
    )

    def mouse_encima(event):
        boton.configure(
            background=color_hover,
            foreground=color_texto_hover
        )

    def mouse_fuera(event):
        boton.configure(
            background=color_normal,
            foreground=color_texto_normal
        )

    boton.bind(
        "<Enter>",
        mouse_encima,
        add="+"
    )

    boton.bind(
        "<Leave>",
        mouse_fuera,
        add="+"
    )


def activar_efecto_en_botones(widget):
    for hijo in widget.winfo_children():
        if isinstance(hijo, Button) and str(hijo.cget("state")) != "disabled":
            activar_efecto_presionado(hijo)

        activar_efecto_en_botones(hijo)


def animar_cortina_vertical(
    posicion_inicial,
    posicion_final,
    callback=None,
    paso=0,
    pasos=PASOS_TRANSICION
):
    ancho = max(ventana.winfo_width(), 1)
    alto = max(ventana.winfo_height(), 1)

    progreso = paso / pasos
    progreso_suave = progreso * progreso * (3 - 2 * progreso)

    posicion_actual = int(
        posicion_inicial
        + (posicion_final - posicion_inicial) * progreso_suave
    )

    cortina_transicion.place(
        x=0,
        y=posicion_actual,
        width=ancho,
        height=alto
    )

    cortina_transicion.tkraise()

    if paso < pasos:
        intervalo = max(
            DURACION_TRANSICION // (2 * pasos),
            1
        )

        ventana.after(
            intervalo,
            lambda: animar_cortina_vertical(
                posicion_inicial,
                posicion_final,
                callback,
                paso + 1,
                pasos
            )
        )

    elif callback:
        callback()


def cambiar_pantalla(frame_destino, callback=None):
    global transicion_activa

    if transicion_activa or frame_actual == frame_destino:
        return

    if frame_destino == estadistica_centro:
        refrescar_tabla_estadisticas()

    transicion_activa = True

    alto = max(ventana.winfo_height(), 1)

    animar_cortina_vertical(
        -alto,
        0,
        lambda: colocar_pantalla_con_transicion(frame_destino, callback)
    )


def colocar_pantalla_con_transicion(frame_destino, callback=None):
    global frame_actual

    frame_destino.place(
        x=0,
        y=0,
        relwidth=1,
        relheight=1
    )

    frame_destino.tkraise()
    frame_actual = frame_destino

    centrar_todo()

    alto = max(ventana.winfo_height(), 1)

    animar_cortina_vertical(
        0,
        alto,
        lambda: finalizar_transicion(callback)
    )


def finalizar_transicion(callback=None):
    global transicion_activa

    cortina_transicion.place_forget()
    transicion_activa = False
    centrar_todo()
    if callback:
        callback()


# ==========================================================
# FUNCIONES DE ESTADISTICAS
# ==========================================================

def agregar_estadistica(nombre, puntuacion, tiempo, posicion=None):
    puesto = len(tabla_estadisticas.get_children()) + 1
    etiqueta = "fila_par" if puesto % 2 == 0 else "fila_impar"

    tabla_estadisticas.insert(
        "",
        END,
        values=(
            puesto,
            nombre,
            puntuacion,
            tiempo,
            formatear_posicion(posicion)
        ),
        tags=(
            etiqueta,
        )
    )

    ventana.after(
        10,
        actualizar_lineas_tabla
    )


def actualizar_puestos_estadisticas():
    for indice, elemento in enumerate(
        tabla_estadisticas.get_children(),
        start=1
    ):
        valores = tabla_estadisticas.item(
            elemento,
            "values"
        )

        if len(valores) >= 1:
            valores_actualizados = (
                indice,
                *valores[1:]
            )
        else:
            valores_actualizados = (indice,)

        etiqueta = "fila_par" if indice % 2 == 0 else "fila_impar"

        tabla_estadisticas.item(
            elemento,
            values=valores_actualizados,
            tags=(
                etiqueta,
            )
        )


def actualizar_lineas_tabla(event=None):
    for linea in lineas_tabla:
        linea.place_forget()

    for linea in lineas_horizontales_tabla:
        linea.place_forget()

    tabla_estadisticas.update_idletasks()

    posicion_x = 0
    alto = max(tabla_estadisticas.winfo_height(), 1)
    ancho = max(tabla_estadisticas.winfo_width(), 1)

    for indice, columna in enumerate(columnas[:-1]):
        posicion_x += tabla_estadisticas.column(
            columna,
            "width"
        )

        lineas_tabla[indice].place(
            x=posicion_x - 1,
            y=0,
            width=2,
            height=alto
        )

    for indice, elemento in enumerate(tabla_estadisticas.get_children()):
        if indice >= len(lineas_horizontales_tabla):
            break

        caja = tabla_estadisticas.bbox(elemento)

        if not caja:
            continue

        lineas_horizontales_tabla[indice].place(
            x=0,
            y=caja[1] + caja[3] - 1,
            width=ancho,
            height=2
        )


def eliminar_estadistica():
    seleccion = tabla_estadisticas.selection()

    if not seleccion:
        messagebox.showwarning(
            "Estadísticas",
            "Seleccione una estadística para eliminar."
        )
        return

    respuesta = messagebox.askyesno(
        "Eliminar estadística",
        "¿Desea eliminar la estadística seleccionada?"
    )

    if respuesta:
        for elemento in seleccion:
            try:
                # estadisticas_db.eliminar_partida(elemento)
                pass
            except Exception as error:
                print(f"Error eliminando estadistica: {error}")

            tabla_estadisticas.delete(elemento)

        actualizar_puestos_estadisticas()

        ventana.after(
            10,
            actualizar_lineas_tabla
        )


def limpiar_estadisticas():
    registros = tabla_estadisticas.get_children()

    if not registros:
        messagebox.showinfo(
            "Estadísticas",
            "La tabla ya está vacía."
        )
        return

    respuesta = messagebox.askyesno(
        "Limpiar estadísticas",
        "¿Desea eliminar todas las estadísticas?"
    )

    if respuesta:
        try:
            # estadisticas_db.limpiar_partidas()
            pass
        except Exception as error:
            print(f"Error limpiando estadisticas: {error}")

        for elemento in registros:
            tabla_estadisticas.delete(elemento)

        ventana.after(
            10,
            actualizar_lineas_tabla
        )


# ==========================================================
# VENTANA PRINCIPAL
# ==========================================================

ventana = Tk()

# La ventana permanece oculta mientras se maximiza
ventana.withdraw()

ventana.title("DONKEY KONG")
ventana.configure(bg="black")
ventana.protocol("WM_DELETE_WINDOW", salir)

ancho_pantalla = ventana.winfo_screenwidth()
alto_pantalla = ventana.winfo_screenheight()

ventana.geometry(
    f"{ancho_pantalla}x{alto_pantalla}+0+0"
)


# ==========================================================
# CONTENEDOR PRINCIPAL
# ==========================================================

contenedor = Frame(
    ventana,
    bg="black"
)

contenedor.pack(
    fill="both",
    expand=True
)


# ==========================================================
# PANTALLAS
# ==========================================================

frame_menu = Frame(
    contenedor,
    bg=COLOR_MENU
)

frame_juego = Frame(
    contenedor,
    bg="black"
)

frame_estadisticas = Frame(
    contenedor,
    bg="#0F172A"
)

for frame in (
    frame_menu,
    frame_juego,
    frame_estadisticas
):
    frame.place(
        x=0,
        y=0,
        relwidth=1,
        relheight=1
    )


# ==========================================================
# MENU PRINCIPAL
# ==========================================================

fondo_menu_original = cargar_imagen_original(RUTA_FONDO_MENU)

fondo_menu = Label(
    frame_menu,
    bd=0,
    highlightthickness=0
)

fondo_menu.place(
    x=0,
    y=0,
    relwidth=1,
    relheight=1
)

fondo_menu.lower()

frame_menu.bind(
    "<Configure>",
    actualizar_fondo_menu
)


menu_centro = Frame(
    frame_menu,
    bg=COLOR_MENU
)

Label(
    menu_centro,
    text="",
    font=("Arial", 36, "bold"),
    bg=COLOR_MENU,
    fg="#FFD700"
).pack(
    pady=(10, 25)
)


# ==========================================================
# BOTON JUGAR
# ==========================================================

boton_jugar = Button(
    menu_centro,
    text="JUGAR",
    font=("Arial", 20, "bold"),
    width=18,
    height=2,
    bg="#FFD700",
    fg="black",
    activebackground="#FFC300",
    activeforeground="black",
    borderwidth=0,
    highlightthickness=0,
    cursor="hand2",
    command=lambda: cambiar_pantalla(frame_juego, lambda: abrir_dialogo_nombre())
)


boton_jugar.pack(
    pady=8
)


# ==========================================================
# BOTON ESTADISTICAS
# ==========================================================

boton_estadisticas = Button(
    menu_centro,
    text="ESTADÍSTICAS",
    font=("Arial", 20, "bold"),
    width=18,
    height=2,
    bg="white",
    fg="black",
    activebackground="#DCDCDC",
    activeforeground="black",
    borderwidth=0,
    highlightthickness=0,
    cursor="hand2",
    command=lambda: cambiar_pantalla(frame_estadisticas)
)

boton_estadisticas.pack(
    pady=12
)


# ==========================================================
# BOTON SALIR
# ==========================================================

boton_salir = Button(
    menu_centro,
    text="SALIR",
    font=("Arial", 20, "bold"),
    width=18,
    height=2,
    bg="#E53935",
    fg="white",
    activebackground="#B71C1C",
    activeforeground="white",
    borderwidth=0,
    highlightthickness=0,
    cursor="hand2",
    command=salir
)

boton_salir.pack(
    pady=12
)


# ==========================================================
# PANTALLA DEL JUEGO
# ==========================================================

juego_centro = Frame(
    frame_juego,
    bg="black"
)

Label(
    juego_centro,
    text="SELECCIONAR NIVEL",
    font=("Arial", 38, "bold"),
    fg="#FFD700",
    bg="black"
).pack(
    pady=(10, 25)
)


def iniciar_nivel(numero):
    # Preparar ruta y argumentos
    if numero == 1:
        ruta_script = CARPETA_PROYECTO / "lvl1" / "proyectoavanzada" / "nivel1.py"
        directorio_trabajo = CARPETA_PROYECTO / "lvl1" / "proyectoavanzada"
    elif numero == 3:
        ruta_script = CARPETA_PROYECTO / "lvl3" / "Proyecto_Python" / "main.py"
        directorio_trabajo = CARPETA_PROYECTO / "lvl3" / "Proyecto_Python"
    else:
        ruta_script = CARPETA_PROYECTO / f"level{numero}.py"
        directorio_trabajo = CARPETA_PROYECTO

    args = [sys.executable, str(ruta_script)]
    if nombre_jugador_actual:
        args.append(nombre_jugador_actual)

    alto = max(ventana.winfo_height(), 1)

    def on_curtain_closed():
        # Ejecutar el nivel en un hilo para no bloquear la UI
        def run_level():
            try:
                subprocess.run(args, cwd=str(directorio_trabajo))
            except Exception as e:
                print(f"Error ejecutando nivel: {e}")

            # Al terminar, abrir la cortina (animación de salida) en el hilo UI
            ventana.after(0, lambda: animar_cortina_vertical(0, alto, on_level_finished))

        threading.Thread(target=run_level, daemon=True).start()

    def on_level_finished():
        # Mostrar lanzador y asegurar que esté maximizado
        try:
            ventana.deiconify()
            try:
                ventana.state("zoomed")
            except Exception:
                # fallback: maximize by geometry
                try:
                    ancho = ventana.winfo_screenwidth()
                    alto = ventana.winfo_screenheight()
                    ventana.geometry(f"{ancho}x{alto}+0+0")
                except Exception:
                    pass
        except Exception:
            pass

        try:
            dibujar_niveles()
        except Exception:
            pass

        # Procesar resultado si existe
        if RUTA_RUN_RESULT.exists():
            try:
                with open(RUTA_RUN_RESULT, 'r', encoding='utf-8') as archivo:
                    resultado = json.load(archivo)
                if resultado:
                    guardar_estadistica(
                        resultado.get('nombre', nombre_jugador_actual or 'Jugador'),
                        resultado.get('puntos', 0),
                        resultado.get('tiempo', 0),
                        resultado.get('nivel', numero),
                        resultado.get('posicion')
                    )
                    refrescar_tabla_estadisticas()
            except Exception as error:
                print(f"Error leyendo resultado de nivel: {error}")
            finally:
                try:
                    RUTA_RUN_RESULT.unlink()
                except Exception:
                    pass

    # Iniciar animación de cortina para cubrir la ventana y ejecutar el nivel
    animar_cortina_vertical(-alto, 0, on_curtain_closed)


def dibujar_figura_3d(padre, color_principal, color_lateral, color_superior):
    figura = Canvas(
        padre,
        width=114,
        height=124,
        bg="#020617",
        bd=0,
        highlightthickness=0
    )

    figura.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )

    figura.create_oval(
        26,
        88,
        92,
        108,
        fill="#000000",
        outline=""
    )

    figura.create_polygon(
        34,
        45,
        58,
        28,
        84,
        45,
        58,
        62,
        fill=color_superior,
        outline="#F8FAFC",
        width=1
    )

    figura.create_polygon(
        34,
        45,
        58,
        62,
        58,
        94,
        34,
        76,
        fill=color_principal,
        outline="#F8FAFC",
        width=1
    )

    figura.create_polygon(
        58,
        62,
        84,
        45,
        84,
        76,
        58,
        94,
        fill=color_lateral,
        outline="#F8FAFC",
        width=1
    )

    figura.create_line(
        42,
        50,
        58,
        39,
        76,
        50,
        fill="#FFFFFF",
        width=1
    )

    return figura


def crear_tarjeta_nivel(padre, numero, desbloqueado):
    if desbloqueado:
        color_fondo = "#1F2937"
        color_borde = "#FFD700"
        color_texto = "white"
        estado = "DESBLOQUEADO"
        texto_boton = "JUGAR"
        estado_boton = NORMAL
        comando = lambda n=numero: iniciar_nivel(n)
        color_boton = "#FFD700"
        color_boton_activo = "#FFC300"
        color_texto_boton = "black"
        colores_figura = (
            "#FACC15",
            "#D97706",
            "#FDE68A"
        )

    else:
        color_fondo = "#111827"
        color_borde = "#4B5563"
        color_texto = "#9CA3AF"
        estado = "BLOQUEADO"
        texto_boton = "BLOQUEADO"
        estado_boton = DISABLED
        comando = None
        color_boton = "#374151"
        color_boton_activo = "#374151"
        color_texto_boton = "#9CA3AF"
        colores_figura = (
            "#64748B",
            "#334155",
            "#94A3B8"
        )

    tarjeta = Frame(
        padre,
        bg="black",
        bd=0
    )

    linea_izquierda = Frame(
        tarjeta,
        bg=color_borde,
        width=6,
        height=185
    )

    linea_izquierda.grid(
        row=0,
        column=0,
        sticky="ns"
    )

    contenido = Frame(
        tarjeta,
        bg=color_fondo,
        width=330,
        height=185
    )

    contenido.grid(
        row=0,
        column=1,
        padx=12
    )

    contenido.grid_propagate(False)

    linea_derecha = Frame(
        tarjeta,
        bg=color_borde,
        width=6,
        height=185
    )

    linea_derecha.grid(
        row=0,
        column=2,
        sticky="ns"
    )

    espacio_imagen = Frame(
        contenido,
        bg="#020617",
        width=118,
        height=128,
        bd=2,
        relief="solid"
    )

    espacio_imagen.grid(
        row=0,
        column=0,
        rowspan=3,
        padx=(18, 14),
        pady=28
    )

    espacio_imagen.grid_propagate(False)

    dibujar_figura_3d(
        espacio_imagen,
        colores_figura[0],
        colores_figura[1],
        colores_figura[2]
    )

    Label(
        contenido,
        text=f"NIVEL {numero}",
        font=("Arial", 24, "bold"),
        bg=color_fondo,
        fg=color_texto
    ).grid(
        row=0,
        column=1,
        sticky="w",
        pady=(34, 6)
    )

    Label(
        contenido,
        text=estado,
        font=("Arial", 12, "bold"),
        bg=color_fondo,
        fg=color_borde
    ).grid(
        row=1,
        column=1,
        sticky="w",
        pady=(0, 18)
    )

    Button(
        contenido,
        text=texto_boton,
        font=("Arial", 13, "bold"),
        width=13,
        bg=color_boton,
        fg=color_texto_boton,
        activebackground=color_boton_activo,
        activeforeground=color_texto_boton,
        disabledforeground=color_texto_boton,
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2" if desbloqueado else "arrow",
        state=estado_boton,
        command=comando
    ).grid(
        row=2,
        column=1,
        sticky="w"
    )

    return tarjeta


contenedor_niveles = Frame(
    juego_centro,
    bg="black"
)

contenedor_niveles.pack(
    pady=(0, 30)
)

dibujar_niveles()


Button(
    juego_centro,
    text="Volver al menú",
    font=("Arial", 18, "bold"),
    width=18,
    bg="white",
    fg="black",
    activebackground="#DCDCDC",
    activeforeground="black",
    borderwidth=0,
    cursor="hand2",
    command=lambda: cambiar_pantalla(frame_menu)
).pack(
    pady=30
)


# ==========================================================
# PANTALLA DE ESTADISTICAS
# ==========================================================

estadistica_centro = Frame(
    frame_estadisticas,
    bg="#0F172A"
)

Label(
    estadistica_centro,
    text="ESTADÍSTICAS DE JUGADORES",
    font=("Arial", 42, "bold"),
    bg="#0F172A",
    fg="#FFD700"
).pack(
    pady=(0, 12)
)

Label(
    estadistica_centro,
    text="Mejores puntuaciones",
    font=("Arial", 18, "bold"),
    bg="#0F172A",
    fg="#E5E7EB"
).pack(
    pady=(0, 28)
)


# ==========================================================
# ESTILO DE LA TABLA
# ==========================================================

estilo_tabla = ttk.Style()

try:
    estilo_tabla.theme_use("clam")
except TclError:
    pass

estilo_tabla.configure(
    "Estadisticas.Treeview",
    font=("Arial", 14),
    rowheight=38,
    background="#F3F4F6",
    foreground="#111827",
    fieldbackground="#F3F4F6",
    bordercolor="#334155",
    borderwidth=0,
    relief="flat"
)

estilo_tabla.configure(
    "Estadisticas.Treeview.Heading",
    font=("Arial", 17, "bold"),
    background="#FFD400",
    foreground="#111827",
    padding=(10, 12),
    bordercolor="#334155",
    borderwidth=2,
    relief="solid"
)

estilo_tabla.map(
    "Estadisticas.Treeview",
    background=[
        ("selected", "#38BDF8")
    ],
    foreground=[
        ("selected", "#111827")
    ]
)


# ==========================================================
# CONTENEDOR DE LA TABLA
# ==========================================================

contenedor_tabla = Frame(
    estadistica_centro,
    bg="#334155",
    bd=4,
    relief="solid"
)

contenedor_tabla.pack(
    padx=0,
    pady=(0, 30)
)

contenedor_tabla.grid_rowconfigure(
    0,
    weight=1
)

contenedor_tabla.grid_columnconfigure(
    0,
    weight=1
)


# ==========================================================
# TABLA
# ==========================================================

columnas = (
    "puesto",
    "nombre",
    "puntuacion",
    "tiempo",
    "posicion"
)

tabla_estadisticas = ttk.Treeview(
    contenedor_tabla,
    columns=columnas,
    show="headings",
    height=8,
    selectmode="browse",
    style="Estadisticas.Treeview"
)

lineas_tabla = [
    Frame(
        contenedor_tabla,
        bg="#334155",
        width=2
    )
    for _ in columnas[:-1]
]

lineas_horizontales_tabla = [
    Frame(
        contenedor_tabla,
        bg="#334155",
        height=2
    )
    for _ in range(10)
]

tabla_estadisticas.heading(
    "puesto",
    text="#"
)

tabla_estadisticas.heading(
    "nombre",
    text="Nombre del jugador"
)

tabla_estadisticas.heading(
    "puntuacion",
    text="Puntuación"
)

tabla_estadisticas.heading(
    "tiempo",
    text="Tiempo jugado"
)

tabla_estadisticas.heading(
    "posicion",
    text="Posicion"
)

tabla_estadisticas.column(
    "puesto",
    width=85,
    minwidth=60,
    anchor="center",
    stretch=False
)

tabla_estadisticas.column(
    "nombre",
    width=300,
    minwidth=200,
    anchor="center",
    stretch=False
)

tabla_estadisticas.column(
    "puntuacion",
    width=210,
    minwidth=150,
    anchor="center",
    stretch=False
)

tabla_estadisticas.column(
    "tiempo",
    width=205,
    minwidth=150,
    anchor="center",
    stretch=False
)

tabla_estadisticas.column(
    "posicion",
    width=300,
    minwidth=200,
    anchor="center",
    stretch=False
)

tabla_estadisticas.tag_configure(
    "fila_impar",
    background="#F3F4F6"
)

tabla_estadisticas.tag_configure(
    "fila_par",
    background="#E5E7EB"
)


# ==========================================================
# BARRA DE DESPLAZAMIENTO
# ==========================================================

barra_vertical = ttk.Scrollbar(
    contenedor_tabla,
    orient="vertical",
    command=tabla_estadisticas.yview
)

tabla_estadisticas.configure(
    yscrollcommand=barra_vertical.set
)

tabla_estadisticas.grid(
    row=0,
    column=0,
    sticky="nsew"
)

tabla_estadisticas.bind(
    "<Configure>",
    actualizar_lineas_tabla
)

barra_vertical.grid(
    row=0,
    column=1,
    sticky="ns"
)

ventana.after(
    100,
    actualizar_lineas_tabla
)


# ==========================================================
# CARGAR ESTADÍSTICAS
# ==========================================================

refrescar_tabla_estadisticas()


# ==========================================================
# BOTONES DE ESTADISTICAS
# ==========================================================

contenedor_botones_estadisticas = Frame(
    estadistica_centro,
    bg="#0F172A"
)

contenedor_botones_estadisticas.pack(
    pady=(2, 0)
)

Button(
    contenedor_botones_estadisticas,
    text="Eliminar\nseleccionado",
    font=("Arial", 14, "bold"),
    width=15,
    height=1,
    pady=4,
    bg="#E74C3C",
    fg="white",
    activebackground="#C0392B",
    activeforeground="white",
    borderwidth=3,
    relief="raised",
    cursor="hand2",
    command=eliminar_estadistica
).grid(
    row=0,
    column=0,
    padx=16
)

Button(
    contenedor_botones_estadisticas,
    text="Limpiar tabla",
    font=("Arial", 14, "bold"),
    width=12,
    height=1,
    pady=4,
    bg="#F39C12",
    fg="black",
    activebackground="#D68910",
    activeforeground="black",
    borderwidth=3,
    relief="raised",
    cursor="hand2",
    command=limpiar_estadisticas
).grid(
    row=0,
    column=1,
    padx=16
)

Button(
    contenedor_botones_estadisticas,
    text="Volver al menú",
    font=("Arial", 14, "bold"),
    width=12,
    height=1,
    pady=4,
    bg="black",
    fg="white",
    activebackground="#222222",
    activeforeground="white",
    borderwidth=3,
    relief="raised",
    cursor="hand2",
    command=lambda: cambiar_pantalla(frame_menu)
).grid(
    row=0,
    column=2,
    padx=16
)


# ==========================================================
# TRANSICION SIMPLE
# ==========================================================

cortina_transicion = Frame(
    ventana,
    bg="black"
)


# ==========================================================
# AJUSTAR ELEMENTOS
# ==========================================================

def ajustar_pantalla(event=None):
    if event is not None and event.widget != ventana:
        return

    actualizar_fondo_menu()
    centrar_todo()


ventana.bind(
    "<Configure>",
    ajustar_pantalla
)


# ==========================================================
# INICIAR PROGRAMA
# ==========================================================

activar_efecto_en_botones(contenedor)

mostrar_frame_inicial(frame_menu)

ventana.update_idletasks()

ventana.deiconify()
pantalla_completa()

ventana.update_idletasks()

ventana.mainloop()

