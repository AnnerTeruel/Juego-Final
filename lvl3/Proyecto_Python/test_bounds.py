from ursina import *
app = Ursina()
m = Entity(model='assets/Models/toy_hammer.glb')
print('BOUNDS:', m.bounds)
print('MIN:', m.model.bounds[0] if m.model else 'None')
print('MAX:', m.model.bounds[1] if m.model else 'None')
application.quit()
