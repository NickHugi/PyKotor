import math
import os
import sys
import time
from typing import Optional, List

import glfw
import glm
from glm import vec3
from pykotor.extract.installation import Installation

from pykotor.gl.scene import Scene


class PyKotorWindow:
    def __init__(self):
        if not glfw.init():
            raise Exception("Unable to initialize glfw.")

        self.scene: Optional[Scene] = None
        self.delta: float = 0.0

        self.mouse_x: int = 0
        self.mouse_y: int = 0
        self.mouse_down: List[bool] = [False, False, False]

        self.key_turn_up: bool = False
        self.key_turn_down: bool = False
        self.key_turn_right: bool = False
        self.key_turn_left: bool = False
        self.key_move_forward: bool = False
        self.key_move_backward: bool = False
        self.key_move_left: bool = False
        self.key_move_right: bool = False
        self.key_move_up: bool = False
        self.key_move_down: bool = False
        self.key_move_boost: bool = False

    def open(self, module_root: str, installation: Installation):
        window = glfw.create_window(1280, 720, "PyKotorGL", None, None)
        if not window:
            glfw.terminate()
            raise Exception("Unable to open glfw window.")

        glfw.make_context_current(window)

        self.scene = Scene(module_root, installation)
        last = time.process_time()

        while not glfw.window_should_close(window):
            glfw.poll_events()
            glfw.set_key_callback(window, self.process_key)
            glfw.set_cursor_pos_callback(window, self.mouse_move)
            glfw.set_mouse_button_callback(window, self.mouse_click)
            glfw.set_scroll_callback(window, self.mouse_scroll)

            delta = time.process_time() - last
            last = time.process_time()

            speed = 8 if self.key_move_boost else 3
            if self.key_move_forward:
                xy_forward = self.scene.camera.forward() * delta * speed
                xy_forward.z = 0
                xy_forward = glm.normalize(xy_forward) * delta * speed
                self.scene.camera.translate(xy_forward)
            elif self.key_move_backward:
                xy_forward = self.scene.camera.forward() * delta * speed
                xy_forward.z = 0
                xy_forward = glm.normalize(xy_forward) * delta * speed
                self.scene.camera.translate(-xy_forward)
            if self.key_move_right:
                xy_sideward = self.scene.camera.sideward()
                xy_sideward.z = 0
                xy_sideward = glm.normalize(xy_sideward) * delta * speed
                self.scene.camera.translate(-xy_sideward)
            elif self.key_move_left:
                xy_sideward = self.scene.camera.sideward()
                xy_sideward.z = 0
                xy_sideward = glm.normalize(xy_sideward) * delta * speed
                self.scene.camera.translate(xy_sideward)
            if self.key_move_up:
                z_upward = vec3(0, 0, delta * speed)
                self.scene.camera.translate(z_upward)
            elif self.key_move_down:
                z_upward = vec3(0, 0, delta*speed)
                self.scene.camera.translate(-z_upward)

            if self.key_turn_right:
                self.scene.camera.rotate(math.pi*2*delta, 0)
            elif self.key_turn_left:
                self.scene.camera.rotate(-math.pi*2*delta, 0)
            if self.key_turn_up:
                self.scene.camera.rotate(0, math.pi/2*delta)
            elif self.key_turn_down:
                self.scene.camera.rotate(0, -math.pi/2*delta)

            glfw.swap_buffers(window)
            self.scene.render()

        glfw.terminate()

    def process_key(self, window, key, scancode, action, mods):
        if key == glfw.KEY_W:
            self.key_move_forward = action != 0
        if key == glfw.KEY_A:
            self.key_move_right = action != 0
        if key == glfw.KEY_S:
            self.key_move_backward = action != 0
        if key == glfw.KEY_D:
            self.key_move_left = action != 0
        if key == glfw.KEY_Q:
            self.key_turn_left = action != 0
        if key == glfw.KEY_E:
            self.key_turn_right = action != 0
        if key == glfw.KEY_R:
            self.key_move_up = action != 0
        if key == glfw.KEY_F:
            self.key_move_down = action != 0
        if key == glfw.KEY_Z:
            self.key_turn_up = action != 0
        if key == glfw.KEY_X:
            self.key_turn_down = action != 0
        if key == glfw.KEY_LEFT_SHIFT:
            self.key_move_boost = action != 0
        if key == glfw.KEY_DOWN:
            self.scene.camera.rotate(0, -3.14)

    def mouse_move(self, window, x, y):
        delta_x = x - self.mouse_x
        delta_y = y - self.mouse_y
        self.mouse_x = int(x)
        self.mouse_y = int(y)

        if self.mouse_down[1]:
            xy_forward = self.scene.camera.forward()
            xy_forward.z = 0
            xy_forward = glm.normalize(xy_forward) / 80 * delta_y
            self.scene.camera.translate(xy_forward)

            xy_sideward = self.scene.camera.sideward()
            xy_sideward.z = 0
            xy_sideward = glm.normalize(xy_sideward) / 80 * delta_x
            self.scene.camera.translate(-xy_sideward)

        if self.mouse_down[2]:
            self.scene.camera.rotate(delta_x/110, 0)

    def mouse_click(self, window, button, action, mods):
        self.mouse_down[button] = bool(action)

        if button == 0 and action == 1:
            height = glfw.get_window_size(window)[1]
            obj = self.scene.pick(self.mouse_x, height - self.mouse_y)
            if obj is not None:
                self.scene.select(obj)

    def mouse_scroll(self, window, x, y):
        z_upward = vec3(0, 0, y * 0.4)
        self.scene.camera.translate(-z_upward)


if __name__ == "__main__":
    kotor_path = str(sys.argv[1])
    is_tsl = bool(sys.argv[2])
    module = str(sys.argv[3])

    installation = Installation(kotor_path, "KotOR", is_tsl)
    PyKotorWindow().open(module, installation)
