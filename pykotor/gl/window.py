import math
import time
from typing import Optional

import glfw
from pykotor.extract.installation import Installation

from pykotor.gl.scene import Scene


class PyKotorWindow:
    def __init__(self):
        if not glfw.init():
            raise Exception("Unable to initialize glfw.")

        self.scene: Optional[Scene] = None
        self.delta: float = 0.0

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

            delta = time.process_time() - last
            last = time.process_time()

            speed = 6 if self.key_move_boost else 2
            if self.key_move_forward:
                self.scene.camera.translate(self.scene.camera.forward()*delta*speed)
            elif self.key_move_backward:
                self.scene.camera.translate(-self.scene.camera.forward()*delta*speed)
            if self.key_move_right:
                self.scene.camera.translate(self.scene.camera.sideward()*delta*speed)
            elif self.key_move_left:
                self.scene.camera.translate(-self.scene.camera.sideward()*delta*speed)
            if self.key_move_up:
                self.scene.camera.translate(self.scene.camera.upward()*delta*speed)
            elif self.key_move_down:
                self.scene.camera.translate(-self.scene.camera.upward()*delta*speed)

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

    def mouse_move(self, window, x, y):
        ...

    def mouse_click(self, window, button, action, mods):
        ...
