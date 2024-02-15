from __future__ import annotations

from typing import TYPE_CHECKING

import glm

from OpenGL.GL import glGenTextures, glGetUniformLocation, glTexImage2D, glUniform3fv, glUniform4fv, glUniformMatrix4fv, shaders
from OpenGL.GL.framebufferobjects import glGenerateMipmap
from OpenGL.GL.shaders import GL_FALSE
from OpenGL.raw.GL.EXT.texture_compression_s3tc import GL_COMPRESSED_RGBA_S3TC_DXT5_EXT, GL_COMPRESSED_RGB_S3TC_DXT1_EXT
from OpenGL.raw.GL.VERSION.GL_1_0 import (
    GL_LINEAR,
    GL_NEAREST_MIPMAP_LINEAR,
    GL_REPEAT,
    GL_RGB,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glTexParameteri,
)
from OpenGL.raw.GL.VERSION.GL_1_1 import glBindTexture
from OpenGL.raw.GL.VERSION.GL_1_3 import glCompressedTexImage2D
from OpenGL.raw.GL.VERSION.GL_2_0 import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, glUniform1i, glUseProgram

from pykotor.resource.formats.tpc import TPCTextureFormat

if TYPE_CHECKING:
    from glm import mat4, vec3, vec4
    from pykotor.resource.formats.tpc import TPC

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
    def __init__(self, vshader: str, fshader: str):
        vertex_shader = shaders.compileShader(vshader, GL_VERTEX_SHADER)
        fragment_shader = shaders.compileShader(fshader, GL_FRAGMENT_SHADER)
        self._id: int = shaders.compileProgram(vertex_shader, fragment_shader)

    def use(self):
        glUseProgram(self._id)

    def uniform(self, uniform_name: str):
        return glGetUniformLocation(self._id, uniform_name)

    def set_matrix4(self, uniform: str, matrix: mat4):
        glUniformMatrix4fv(self.uniform(uniform), 1, GL_FALSE, glm.value_ptr(matrix))

    def set_vector4(self, uniform: str, vector: vec4):
        glUniform4fv(self.uniform(uniform), 1, glm.value_ptr(vector))

    def set_vector3(self, uniform: str, vector: vec3):
        glUniform3fv(self.uniform(uniform), 1, glm.value_ptr(vector))

    def set_bool(self, uniform: str, boolean: bool):
        glUniform1i(self.uniform(uniform), boolean)


class Texture:
    def __init__(self, tex_id: int):
        self._id = tex_id

    @classmethod
    def from_tpc(cls, tpc: TPC) -> Texture:
        width, height, tpc_format, data = tpc.get(0)
        image_size = len(data)

        gl_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        if tpc_format == TPCTextureFormat.DXT1:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGB_S3TC_DXT1_EXT, width, height, 0, image_size, data)
        if tpc_format == TPCTextureFormat.DXT5:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGBA_S3TC_DXT5_EXT, width, height, 0, image_size, data)
        if tpc_format == TPCTextureFormat.RGB:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
        if tpc_format == TPCTextureFormat.RGBA:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

        return Texture(gl_id)

    @classmethod
    def from_color(cls, r: int = 0, g: int = 0, b: int = 0) -> Texture:
        # sourcery skip: use-itertools-product
        gl_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        pixels = []
        for _ in range(64):
            for _ in range(64):
                pixels.extend([r, g, b])

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 64, 64, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return Texture(gl_id)

    def use(self):
        glBindTexture(GL_TEXTURE_2D, self._id)
