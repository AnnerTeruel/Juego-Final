from ursina import *
app = Ursina()
e = Entity(model='martillo.glb')
print("HIJOS DEL MODELO:")
def imprimir_hijos(ent, nivel=0):
    for c in ent.children:
        print("  " * nivel + "-", c.name)
        imprimir_hijos(c, nivel + 1)
imprimir_hijos(e)
app.destroy()
