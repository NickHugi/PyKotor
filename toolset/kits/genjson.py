import json
import math
import os
import sys
from typing import List

import pyperclip
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QColor, QTransform
from PyQt5.QtWidgets import QApplication
from pykotor.common.geometry import AxisAngle, Vector2, SurfaceMaterial
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import BWM, read_bwm
from pykotor.resource.formats.mdl import MDL, read_mdl
from pykotor.tools import model

#import config


materialColor = {
    SurfaceMaterial.GRASS: QColor(0, 255, 0, 255),
    SurfaceMaterial.STONE: QColor(120, 120, 120, 255),
    SurfaceMaterial.METAL: QColor(120, 120, 120, 255),
    SurfaceMaterial.NON_WALK: QColor(25, 0, 0, 255),
    SurfaceMaterial.OBSCURING: QColor(0, 0, 0, 0),
    SurfaceMaterial.NON_WALK_GRASS: QColor(0, 127, 0, 255),
}


def minimap(bwm_path: str, png_path: str):
    bwm = read_bwm(bwm_path)
    box = bwm.box()

    width = int(box[1].x*10 - box[0].x*10) + int(box[1].x*10 - box[0].x*10)*3/2
    height = int(box[1].y*10 - box[0].y*10) + int(box[1].y*10 - box[0].y*10)*3/2
    dim = Vector2(width, height)

    pixmap = QPixmap(int(width), int(height))
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setPen(QtCore.Qt.NoPen)

    for face in bwm.unwalkable_faces():
        painter.setBrush(materialColor[face.material])

        v1 = Vector2(face.v1.x, face.v1.y) * 10 + dim / 2
        v2 = Vector2(face.v2.x, face.v2.y) * 10 + dim / 2
        v3 = Vector2(face.v3.x, face.v3.y) * 10 + dim / 2

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()

        painter.drawPath(path)

    for face in bwm.walkable_faces():
        painter.setBrush(materialColor[face.material])

        v1 = Vector2(face.v1.x, face.v1.y) * 10 + dim/2
        v2 = Vector2(face.v2.x, face.v2.y) * 10 + dim/2
        v3 = Vector2(face.v3.x, face.v3.y) * 10 + dim/2

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()

        painter.drawPath(path)

    if not os.path.exists(png_path):
        pixmap.transformed(QTransform().scale(1, -1)).save(png_path)

    del painter
    del pixmap


def get_nums(node_name: str):
    string = ""
    nums = []
    for char in node_name + " ":
        if char.isdigit():
            string += char
        elif string != "":
            nums.append(int(string))
            string = ""
    return nums


def roomdict(filepath: str):
    mdl = read_mdl(filepath)
    version = model.detect_version(BinaryReader.load_file(filepath))

    hooks = []
    for node in mdl.all_nodes():
        if "ht_hook" in node.name:
            trans, door, rot = get_nums(node.name)
            hooks.append((trans, door, mdl.global_position(node), rot))

    roomdict = {}
    roomdict["name"] = os.path.basename(filepath).replace(".mdl", "").replace("_", " ").title()
    roomdict["id"] = os.path.basename(filepath).replace(".mdl", "")
    roomdict["native"] = 1 if version.K1 else 2
    roomdict["doorhooks"] = []
    for hook in hooks:
        hookdict = {}
        hookdict["x"] = hook[2].x
        hookdict["y"] = hook[2].y
        hookdict["z"] = hook[2].z
        hookdict["rotation"] = hook[3]
        hookdict["door"] = hook[1]
        hookdict["edge"] = hook[0] + 20
        roomdict["doorhooks"].append(hookdict)

    return roomdict


def kitdict(name: str, kit_id: str, version: int, doordata: List):
    kitdict = {}

    kitdict["name"] = name
    kitdict["id"] = kit_id
    kitdict["ht"] = "3.0.0"
    kitdict["version"] = version
    kitdict["components"] = []
    for component_id in [file.replace(".mdl", "") for file in os.listdir(kit_id) if file.endswith(".mdl")]:
        minimap("{}/{}.wok".format(kit_id, component_id), "{}/{}.png".format(kit_id, component_id))
        kitdict["components"].append(roomdict("{}/{}.mdl".format(kit_id, component_id)))

    kitdict["doors"] = []
    for i, door in enumerate(doordata):
        doordict = {}
        doordict["utd_k1"] = "door{}_k1".format(i)
        doordict["utd_k2"] = "door{}_k2".format(i)
        doordict["width"] = door[0]
        doordict["height"] = door[1]
        kitdict["doors"].append(doordict)

    return kitdict


doors_sithBase = [(4.49, 2.9), (3.75, 2.9)]
doors_enclaveSurface = [(6.6, 2.5)]
doors_hiddenBek = [(3.6, 2.5)]
doors_dantooineEstate = [(4.5, 2.63), (2.18, 2.8)]



if __name__ == '__main__':
    app = QApplication(sys.argv)

    #x = kitdict("Hidden Bek", "hiddenbek", 1, doors_hiddenBek)
    x = kitdict("Black Vulkar", "blackvulkar", 1, doors_hiddenBek)
    #x = kitdict("Endar Spire", "endarspire", 1, doors_enclaveSurface)
    #x = kitdict("Enclave Surface", "enclavesurface", 1, doors_enclaveSurface)
    #x = kitdict("Dantooine Estate", "dantooineestate", 1, doors_dantooineEstate)

    fn = x["id"]
    json.dump(x, open("C:\\Users\\hugin\\Documents\\Apps\\Holocron Toolset\\kits\\" + fn + ".json", 'w'), indent=4)
    #dump = json.dumps(x, indent=4)

    # print(dump)
    #pyperclip.copy(dump)

    # app.exec_()
