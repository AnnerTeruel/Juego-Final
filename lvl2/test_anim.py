from direct.actor.Actor import Actor
from ursina import Ursina
import sys

app = Ursina()
try:
    actor = Actor('DIddyKongAnimado/Animation_Step_Forward_and_Push_withSkin.glb')
    print("Animations:", actor.getAnimNames())
except Exception as e:
    print("Error:", e)
sys.exit(0)
