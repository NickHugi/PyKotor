from typing import List, Optional

from pykotor.common.geometry import Vector3

from tools.indoormap.indoorkit import KitComponent


class IndoorMap:
    def __init__(self):
        self.rooms: List[IndoorMapRoom] = []


class IndoorMapRoom:
    def __init__(self, component: KitComponent, position: Vector3):
        self.component: KitComponent = component
        self.position: Vector3 = position
        self.hooks: List[Optional[IndoorMapRoom]] = [None] * len(component.hooks)
