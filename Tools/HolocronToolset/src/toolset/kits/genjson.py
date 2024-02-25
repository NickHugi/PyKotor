from __future__ import annotations

import json
import sys

from pathlib import Path
from typing import TYPE_CHECKING

# import config
# import pyperclip
from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPixmap, QTransform
from PyQt5.QtWidgets import QApplication

from pykotor.common.geometry import SurfaceMaterial, Vector2
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.mdl import read_mdl
from pykotor.tools import model

if TYPE_CHECKING:
    import os

TOOLSET_KIT_PATH = Path("toolset", "kits")

material_color = {
    SurfaceMaterial.GRASS: QColor(0, 255, 0, 255),
    SurfaceMaterial.STONE: QColor(120, 120, 120, 255),
    SurfaceMaterial.METAL: QColor(120, 120, 120, 255),
    SurfaceMaterial.NON_WALK: QColor(25, 0, 0, 255),
    SurfaceMaterial.OBSCURING: QColor(0, 0, 0, 0),
    SurfaceMaterial.NON_WALK_GRASS: QColor(0, 127, 0, 255),
}


def minimap(bwm_path: os.PathLike | str, png_path: os.PathLike | str):
    png_path = Path(png_path)
    bwm = read_bwm(bwm_path)
    box = bwm.box()

    width = int(box[1].x * 10 - box[0].x * 10) + int(box[1].x * 10 - box[0].x * 10) * 3 / 2
    height = int(box[1].y * 10 - box[0].y * 10) + int(box[1].y * 10 - box[0].y * 10) * 3 / 2
    dim = Vector2(width, height)

    pixmap = QPixmap(int(width), int(height))
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setPen(QtCore.Qt.NoPen)  # type: ignore[attr-defined, reportGeneralTypeIssues]

    for face in bwm.unwalkable_faces():
        painter.setBrush(material_color[face.material])

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
        painter.setBrush(material_color[face.material])

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

    if not png_path.exists():
        pixmap.transformed(QTransform().scale(1, -1)).save(str(png_path))

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


def roomdict(filepath: os.PathLike | str):
    filepath = Path(filepath)
    mdl = read_mdl(filepath)
    assert mdl
    version = model.detect_version(BinaryReader.load_file(filepath))

    hooks = []
    for node in mdl.all_nodes():
        if "ht_hook" in node.name:
            trans, door, rot = get_nums(node.name)
            hooks.append((trans, door, mdl.global_position(node), rot))

    roomdict = {}
    roomdict["name"] = filepath.stem.replace("_", " ").title()
    roomdict["id"] = filepath.stem
    roomdict["native"] = 1 if version.K1 else 2  # type: ignore[assignment]
    roomdict["doorhooks"] = []  # type: ignore[assignment]
    for hook in hooks:
        hookdict = {}
        hookdict["x"] = hook[2].x
        hookdict["y"] = hook[2].y
        hookdict["z"] = hook[2].z
        hookdict["rotation"] = hook[3]
        hookdict["door"] = hook[1]
        hookdict["edge"] = hook[0] + 20
        roomdict["doorhooks"].append(hookdict)  # type: ignore[attr-defined]

    return roomdict


def kitdict(name: str, kit_id: str, version: int, doordata: list[tuple[float, float]]):
    kitdict = {}

    kitdict["name"] = name
    kitdict["id"] = kit_id
    kitdict["ht"] = "3.0.0"
    kitdict["version"] = version  # type: ignore[assignment]
    kitdict["components"] = []  # type: ignore[assignment]
    this_kit_path = TOOLSET_KIT_PATH / kit_id
    for component_id in [file.stem for file in this_kit_path.iterdir() if file.suffix.lower == ".mdl"]:
        minimap(this_kit_path / f"{component_id}.wok", this_kit_path / f"{component_id}.png")
        kitdict["components"].append(roomdict(this_kit_path / f"{component_id}.mdl"))  # type: ignore[attr-defined]

    kitdict["doors"] = []  # type: ignore[assignment]
    for i, door in enumerate(doordata):
        doordict = {}
        doordict["utd_k1"] = f"door{i}_k1"
        doordict["utd_k2"] = f"door{i}_k2"
        doordict["width"] = door[0]  # type: ignore[assignment]
        doordict["height"] = door[1]  # type: ignore[assignment]
        kitdict["doors"].append(doordict)  # type: ignore[attr-defined]

    return kitdict


doors_sith_base = [(4.49, 2.9), (3.75, 2.9)]
doors_enclave_surface = [(6.6, 2.5)]
doors_hidden_bek = [(3.6, 2.5)]
doors_dantooine_estate = [(4.5, 2.63), (2.18, 2.8)]


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # x = kitdict("Hidden Bek", "hiddenbek", 1, doors_hiddenBek)
    x = kitdict("Black Vulkar", "blackvulkar", 1, doors_hidden_bek)
    # x = kitdict("Endar Spire", "endarspire", 1, doors_enclaveSurface)
    # x = kitdict("Enclave Surface", "enclavesurface", 1, doors_enclaveSurface)
    # x = kitdict("Dantooine Estate", "dantooineestate", 1, doors_dantooineEstate)

    fn = x["id"]
    json.dump(x, Path(TOOLSET_KIT_PATH / fn).with_suffix(".json").open("w"), indent=4)
    # dump = json.dumps(x, indent=4)

    # print(dump)
    # pyperclip.copy(dump)

    # app.exec_()
