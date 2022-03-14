import math
from copy import copy
from typing import List, Optional

from pykotor.common.geometry import Vector3, Vector2

from tools.indoormap.indoorkit import KitComponent, KitComponentHook


class IndoorMap:
    def __init__(self):
        self.rooms: List[IndoorMapRoom] = []


class IndoorMapRoom:
    def __init__(self, component: KitComponent, position: Vector3, rotation: float):
        self.component: KitComponent = component
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.hooks: List[Optional[IndoorMapRoom]] = [None] * len(component.hooks)

    def hookPosition(self, hook: KitComponentHook, worldOffset: bool = True):
        pos = copy(hook.position)

        cos = math.cos(math.radians(self.rotation))
        sin = math.sin(math.radians(self.rotation))
        pos.x = (hook.position.x * cos - hook.position.y * sin)
        pos.y = (hook.position.x * sin + hook.position.y * cos)

        if worldOffset:
            pos = pos + self.position

        return pos
