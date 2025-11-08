from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import glm

from OpenGL.GL import glReadPixels
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_BLEND, GL_COLOR_BUFFER_BIT, GL_CULL_FACE, GL_DEPTH_BUFFER_BIT, GL_DEPTH_COMPONENT, glClear, glClearColor, glDisable, glEnable
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_BGRA, GL_UNSIGNED_INT_8_8_8_8
from glm import mat4, vec3, vec4

from pykotor.extract.installation import SearchLocation
from pykotor.gl.models.mdl import Model
from pykotor.gl.scene.scene_base import SceneBase
from pykotor.gl.scene.scene_cache import SceneCache
from pykotor.gl.shader import KOTOR_FSHADER, KOTOR_VSHADER, PICKER_FSHADER, PICKER_VSHADER, PLAIN_FSHADER, PLAIN_VSHADER, Shader
from pykotor.resource.formats.lyt.lyt_data import LYTRoom
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITEncounter, GITInstance, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.gl.models.mdl import Model
    from pykotor.gl.scene import RenderObject

T = TypeVar("T")
SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene(SceneBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picker_shader: Shader = Shader(PICKER_VSHADER, PICKER_FSHADER)
        self.plain_shader: Shader = Shader(PLAIN_VSHADER, PLAIN_FSHADER)
        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)

    def render(self):
        SceneCache.build_cache(self)

        self._prepare_gl_and_shader()
        self.shader.set_bool("enableLightmap", self.use_lightmap)
        group1: list[RenderObject] = [obj for obj in self.objects.values() if obj.model not in self.SPECIAL_MODELS]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        # Draw all instance types that lack a proper model
        glEnable(GL_BLEND)
        self.plain_shader.use()
        self.plain_shader.set_matrix4("view", self.camera.view())
        self.plain_shader.set_matrix4("projection", self.camera.projection())
        self.plain_shader.set_vector4("color", vec4(0.0, 0.0, 1.0, 0.4))
        group2: list[RenderObject] = [obj for obj in self.objects.values() if obj.model in self.SPECIAL_MODELS]
        for obj in group2:
            self._render_object(self.plain_shader, obj, mat4())

        # Draw bounding box for selected objects
        self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
        for obj in self.selection:
            obj.cube(self).draw(self.plain_shader, obj.transform())

        # Draw boundary for selected objects
        glDisable(GL_CULL_FACE)
        self.plain_shader.set_vector4("color", vec4(0.0, 1.0, 0.0, 0.8))
        for obj in self.selection:
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        # Draw non-selected boundaries
        for obj in (obj for obj in self.objects.values() if obj.model == "sound" and not self.hide_sound_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in (obj for obj in self.objects.values() if obj.model == "encounter" and not self.hide_encounter_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in (obj for obj in self.objects.values() if obj.model == "trigger" and not self.hide_trigger_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        if self.show_cursor:
            self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
            self._render_object(self.plain_shader, self.cursor, mat4())

    def should_hide_obj(
        self,
        obj: RenderObject,
    ) -> bool:
        result = False
        if isinstance(obj.data, GITCreature) and self.hide_creatures:
            result = True
        elif isinstance(obj.data, GITPlaceable) and self.hide_placeables:
            result = True
        elif isinstance(obj.data, GITDoor) and self.hide_doors:
            result = True
        elif isinstance(obj.data, GITTrigger) and self.hide_triggers:
            result = True
        elif isinstance(obj.data, GITEncounter) and self.hide_encounters:
            result = True
        elif isinstance(obj.data, GITWaypoint) and self.hide_waypoints:
            result = True
        elif isinstance(obj.data, GITSound) and self.hide_sounds:
            result = True
        elif isinstance(obj.data, GITStore) and self.hide_sounds:
            result = True
        elif isinstance(obj.data, GITCamera) and self.hide_cameras:
            result = True
        return result

    def _render_object(
        self,
        shader: Shader,
        obj: RenderObject,
        transform: mat4,
    ):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        transform = transform * obj.transform()
        model.draw(shader, transform, override_texture=obj.override_texture)

        for child in obj.children:
            self._render_object(shader, child, transform)

    def picker_render(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)  # Sets the clear color for the OpenGL color buffer to pure white
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clears the color and depth buffers. Clean slate for rendering.  # pyright: ignore[reportOperatorIssue]

        if self.backface_culling:
            glEnable(GL_CULL_FACE)  # Enables backface culling to improve rendering performance by ignoring back faces of polygons.
        else:
            glDisable(GL_CULL_FACE)  # Disables backface culling.

        self.picker_shader.use()  # Activates the shader program for rendering.
        self.picker_shader.set_matrix4("view", self.camera.view())  # Sets the view matrix for the shader.
        self.picker_shader.set_matrix4("projection", self.camera.projection())  # Sets the projection matrix for the shader.
        instances: list[RenderObject] = list(self.objects.values())
        for obj in instances:
            int_rgb: int = instances.index(obj)  # Gets the index of the object in the list and converts it to an integer.
            r: int = int_rgb & 0xFF
            g: int = (int_rgb >> 8) & 0xFF
            b: int = (int_rgb >> 16) & 0xFF
            color = vec3(r / 0xFF, g / 0xFF, b / 0xFF)
            self.picker_shader.set_vector3("colorId", color)

            self._picker_render_object(obj, mat4())

    def _picker_render_object(self, obj: RenderObject, transform: mat4):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        model.draw(self.picker_shader, transform * obj.transform())
        for child in obj.children:
            self._picker_render_object(child, obj.transform())

    def pick(
        self,
        x: float,
        y: float,
    ) -> RenderObject | None:
        self.picker_render()
        pixel: int = glReadPixels(x, y, 1, 1, GL_BGRA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8  # type: ignore[]
        instances: list[RenderObject] = list(self.objects.values())
        return instances[pixel] if pixel != 0xFFFFFF else None  # noqa: PLR2004

    def select(
        self,
        target: RenderObject | GITInstance,
        *,
        clear_existing: bool = True,
    ):
        if clear_existing:
            self.selection.clear()

        SceneCache.build_cache(self)
        actual_target: RenderObject
        if isinstance(target, GITInstance):
            for obj in self.objects.values():
                if obj.data is not target:
                    continue
                actual_target = obj
                break
        else:
            actual_target = target

        self.selection.append(actual_target)

    def screen_to_world(
        self,
        x: int,
        y: int,
    ) -> Vector3:
        self._prepare_gl_and_shader()
        group1: list[RenderObject] = [obj for obj in self.objects.values() if isinstance(obj.data, LYTRoom)]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        zpos = glReadPixels(
            x,
            self.camera.height - y,
            1,
            1,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
        )[0][0]  # type: ignore[]
        cursor: vec3 = glm.unProject(
            vec3(x, self.camera.height - y, zpos),
            self.camera.view(),
            self.camera.projection(),
            vec4(0, 0, self.camera.width, self.camera.height),
        )
        return Vector3(cursor.x, cursor.y, cursor.z)

    def _prepare_gl_and_shader(self):
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # type: ignore[]
        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())
