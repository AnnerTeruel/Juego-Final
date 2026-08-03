import sys
import os
from ursina import *

app = Ursina()

camera.position = (0, 0, -5)

pivot = Entity(position=(0, 0, 0))
martillo = Entity(
    parent=pivot,
    model='assets/Models/toy_hammer.glb',
    scale=0.0005
)

rotations = [
    (0, 0, 0),
    (90, 0, 0),
    (-90, 0, 0),
    (0, 90, 0),
    (0, -90, 0),
    (0, 0, 90),
    (0, 0, -90),
    (-90, 90, 0),
    (-90, -90, 0),
]

current_rot = 0
out_dir = 'C:/Users/anner/.gemini/antigravity-ide/brain/7b2ab41a-6700-49da-b688-40da5d9506d1/scratch'
os.makedirs(out_dir, exist_ok=True)

def take_next_screenshot():
    global current_rot
    if current_rot >= len(rotations):
        application.quit()
        return
        
    rot = rotations[current_rot]
    martillo.rotation = rot
    base.screenshot(f'{out_dir}/hammer_{rot[0]}_{rot[1]}_{rot[2]}.png')
    current_rot += 1
    invoke(take_next_screenshot, delay=0.2)

invoke(take_next_screenshot, delay=1)
app.run()
