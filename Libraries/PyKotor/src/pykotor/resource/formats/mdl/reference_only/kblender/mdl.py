# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
from __future__ import annotations

import os

from typing import TYPE_CHECKING

import bpy

from bpy_extras import find_objects, is_dwk_root, is_mdl_root, is_pwk_root

from pykotor.resource.formats.mdl.reference_only.aabb import AabbNode
from pykotor.resource.formats.mdl.reference_only.constants import ANIM_FPS
from pykotor.resource.formats.mdl.reference_only.model import Model
from pykotor.resource.formats.mdl.reference_only.reader import MdlReader
from pykotor.resource.formats.mdl.reference_only.walkmesh import Walkmesh
from pykotor.resource.formats.mdl.reference_only.writer import MdlWriter

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions


def load_mdl(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
    position: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    operator.report({"INFO"}, f"Loading model from '{filepath}'")
    mdl = MdlReader(filepath)
    model = mdl.load()

    pwk_walkmesh = None
    dwk_walkmesh1 = None
    dwk_walkmesh2 = None
    dwk_walkmesh3 = None

    if options.import_geometry and options.import_walkmeshes:
        wok_path = filepath[:-4] + ".wok"
        if os.path.exists(wok_path):  # noqa: PTH110
            wok = BwmReader(wok_path, model.name)
            walkmesh = wok.load()
            aabb = model.find_node(lambda n: isinstance(n, AabbNode))
            aabb_wok = walkmesh.find_node(lambda n: isinstance(n, AabbNode))
            if aabb and aabb_wok:
                aabb.roomlinks = aabb_wok.roomlinks
                aabb.compute_lyt_position(aabb_wok)

        pwk_path = filepath[:-4] + ".pwk"
        if os.path.exists(pwk_path):  # noqa: PTH110
            operator.report({"INFO"}, f"Loading walkmesh from '{pwk_path}'")
            pwk = BwmReader(pwk_path, model.name)
            pwk_walkmesh = pwk.load()

        dwk0_path = filepath[:-4] + "0.dwk"
        dwk1_path = filepath[:-4] + "1.dwk"
        dwk2_path = filepath[:-4] + "2.dwk"
        if (
            os.path.exists(dwk0_path)  # noqa: PTH110
            and os.path.exists(dwk1_path)  # noqa: PTH110
            and os.path.exists(dwk2_path)  # noqa: PTH110
        ):
            operator.report({"INFO"}, f"Loading walkmesh from '{dwk0_path}'")
            dwk1 = BwmReader(dwk0_path, model.name)
            operator.report({"INFO"}, f"Loading walkmesh from '{dwk1_path}'")
            dwk2 = BwmReader(dwk1_path, model.name)
            operator.report({"INFO"}, f"Loading walkmesh from '{dwk2_path}'")
            dwk3 = BwmReader(dwk2_path, model.name)
            dwk_walkmesh1 = dwk1.load()
            dwk_walkmesh2 = dwk2.load()
            dwk_walkmesh3 = dwk3.load()

    collection = bpy.context.collection
    model_root = model.add_to_collection(collection, options, position)

    if pwk_walkmesh:
        pwk_walkmesh.add_to_collection(model_root, collection, options)
    if dwk_walkmesh1 and dwk_walkmesh2 and dwk_walkmesh3:
        dwk_walkmesh1.add_to_collection(model_root, collection, options)
        dwk_walkmesh2.add_to_collection(model_root, collection, options)
        dwk_walkmesh3.add_to_collection(model_root, collection, options)

    bpy.context.scene.render.fps = ANIM_FPS

    # Reset Pose
    bpy.context.scene.frame_set(0)


def save_mdl(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
):
    # Reset pose
    bpy.context.scene.frame_set(0)

    # Find MDL root
    mdl_root = next(
        iter(obj for obj in bpy.context.selected_objects if is_mdl_root(obj)),
        None,
    )
    if not mdl_root:
        mdl_root = next(
            iter(obj for obj in bpy.context.collection.objects if is_mdl_root(obj)),
            None,
        )
    if not mdl_root:
        return

    # Ensure MDL root is selected and is in OBJECT mode
    mdl_root.select_set(True)
    bpy.context.view_layer.objects.active = mdl_root
    bpy.ops.object.mode_set(mode="OBJECT")

    # Export MDL
    model = Model.from_mdl_root(mdl_root, options)
    operator.report({"INFO"}, f"Saving model to '{filepath}'")
    mdl = MdlWriter(
        filepath,
        model,
        options.export_for_tsl,
        options.export_for_xbox,
        options.compress_quaternions,
    )
    mdl.save()

    if options.export_walkmeshes:
        # Export WOK
        aabb_node = model.find_node(lambda node: isinstance(node, AabbNode))
        if aabb_node:
            base_path, _ = os.path.splitext(filepath)  # noqa: PTH122
            wok_path = base_path + ".wok"
            walkmesh = Walkmesh.from_aabb_node(aabb_node)
            operator.report({"INFO"}, f"Saving walkmesh to '{wok_path}'")
            bwm = BwmWriter(wok_path, walkmesh)
            bwm.save()

        # Export PWK or DWK
        xwk_roots = find_objects(
            mdl_root, lambda obj: is_pwk_root(obj) or is_dwk_root(obj)
        )
        for xwk_root in xwk_roots:
            base_path, _ = os.path.splitext(filepath)  # noqa: PTH122
            if is_pwk_root(xwk_root):
                xwk_path = base_path + ".pwk"
            else:
                if xwk_root.name.endswith("open1"):
                    dwk_state = 1
                elif xwk_root.name.endswith("open2"):
                    dwk_state = 2
                elif xwk_root.name.endswith("closed"):
                    dwk_state = 0
                xwk_path = f"{base_path}{dwk_state}.dwk"
            walkmesh = Walkmesh.from_root_object(xwk_root, options)
            operator.report({"INFO"}, f"Saving walkmesh to '{xwk_path}'")
            bwm = BwmWriter(xwk_path, walkmesh)
            bwm.save()
