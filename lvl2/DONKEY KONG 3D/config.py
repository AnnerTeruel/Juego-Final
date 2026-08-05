import json
import os

sensibilidad = 120.0

def cargar():
    global sensibilidad
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                data = json.load(f)
                sensibilidad = float(data.get('sensibilidad', 120.0))
        except:
            pass

def guardar():
    with open('config.json', 'w') as f:
        json.dump({'sensibilidad': sensibilidad}, f)

cargar()
