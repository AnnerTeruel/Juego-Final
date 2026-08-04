from direct.actor.Actor import Actor
from ursina import Ursina
import sys

app = Ursina(window_type='none')

actor = Actor('DIddyKongAnimado/Animation_Step_Forward_and_Push_withSkin.glb')
duration = actor.getDuration('Armature|Step_Forward_and_Push|baselayer')
print("Animation duration:", duration)

sys.exit(0)
