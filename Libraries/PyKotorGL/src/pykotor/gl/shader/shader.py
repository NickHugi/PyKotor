from __future__ import annotations

from typing import TYPE_CHECKING

import glm

from OpenGL.GL import glGetUniformLocation, glUniform3fv, glUniform4fv, glUniformMatrix4fv, shaders
from OpenGL.GL.shaders import GL_FALSE
from OpenGL.raw.GL.VERSION.GL_2_0 import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, glUniform1i, glUseProgram

if TYPE_CHECKING:
    from glm import mat4, vec3, vec4



KOTOR_VSHADER = """
#version 330 core

layout (location = 0) in vec3 flags;
layout (location = 1) in vec3 position;
layout (location = 2) in vec3 normal;
layout (location = 3) in vec3 uv;
layout (location = 4) in vec3 uv2;

out vec2 diffuse_uv;
out vec2 lightmap_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model *  vec4(position, 1.0);
    diffuse_uv = vec2(uv.x, uv.y);
    lightmap_uv = vec2(uv2.x, uv2.y);
}
"""


KOTOR_FSHADER = """
#version 420
in vec2 diffuse_uv;
in vec2 lightmap_uv;

out vec4 FragColor;

layout(binding = 0) uniform sampler2D diffuse;
layout(binding = 1) uniform sampler2D lightmap;
uniform int enableLightmap;

void main()
{
    vec4 diffuseColor = texture(diffuse, diffuse_uv);
    vec4 lightmapColor = texture(lightmap, lightmap_uv);

    if (enableLightmap == 1) {
        FragColor = mix(diffuseColor, lightmapColor, 0.5);
    } else {
        FragColor = diffuseColor;
    }
}
"""


PICKER_VSHADER = """
#version 330 core

layout (location = 1) in vec3 position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model *  vec4(position, 1.0);
}
"""


PICKER_FSHADER = """
#version 330

uniform vec3 colorId;

out vec4 FragColor;

void main()
{
    FragColor = vec4(colorId, 1.0);
}
"""


PLAIN_VSHADER = """
#version 330 core

layout (location = 1) in vec3 position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model *  vec4(position, 1.0);
}
"""


PLAIN_FSHADER = """
#version 330

uniform vec4 color;

out vec4 FragColor;

void main()
{
    FragColor = color;
}
"""

class Shader:
    def __init__(
        self,
        vshader: str,
        fshader: str,
    ):
        vertex_shader: int = shaders.compileShader(vshader, GL_VERTEX_SHADER)
        fragment_shader: int = shaders.compileShader(fshader, GL_FRAGMENT_SHADER)
        self._id: int = shaders.compileProgram(vertex_shader, fragment_shader)

    def use(self):
        glUseProgram(self._id)

    def uniform(
        self,
        uniform_name: str,
    ) -> int:
        return glGetUniformLocation(self._id, uniform_name)

    def set_matrix4(
        self,
        uniform: str,
        matrix: mat4,
    ):
        glUniformMatrix4fv(self.uniform(uniform), 1, GL_FALSE, glm.value_ptr(matrix))

    def set_vector4(
        self,
        uniform: str,
        vector: vec4,
    ):
        glUniform4fv(self.uniform(uniform), 1, glm.value_ptr(vector))

    def set_vector3(
        self,
        uniform: str,
        vector: vec3,
    ):
        glUniform3fv(self.uniform(uniform), 1, glm.value_ptr(vector))

    def set_bool(self, uniform: str, boolean: bool):  # noqa: FBT001
        glUniform1i(self.uniform(uniform), boolean)