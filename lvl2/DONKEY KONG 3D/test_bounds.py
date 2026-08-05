from ursina import Ursina, Entity
from direct.actor.Actor import Actor
import sys

app = Ursina(window_type='none')

actor1 = Actor('diddykong.glb')
bounds1 = actor1.getTightBounds()
print("diddykong bounds:", bounds1)

actor2 = Actor('DIddyKongAnimado/Animation_Step_Forward_and_Push_withSkin.glb')
bounds2 = actor2.getTightBounds()
print("Animado bounds:", bounds2)

sys.exit(0)
