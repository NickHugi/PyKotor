from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from OpenGL.GL import GL_NO_ERROR, glGenTextures, glGetError, glTexImage2D
from OpenGL.GL.framebufferobjects import glGenerateMipmap
from OpenGL.GLU import gluErrorString
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

from pykotor.resource.formats.tpc import TPCTextureFormat

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc import TPC, TPCMipmap


class Texture:
    def __init__(
        self,
        tex_id: int,
    ):
        self._id: int = tex_id

    @classmethod
    def from_tpc(
        cls,
        tpc: TPC,
    ) -> Texture:
        mm: TPCMipmap = tpc.get(0, 0)
        image_size: int = len(mm.data)

        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        if mm.tpc_format == TPCTextureFormat.DXT1:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGB_S3TC_DXT1_EXT, mm.width, mm.height, 0, image_size, mm.data)
        elif mm.tpc_format == TPCTextureFormat.DXT5:
            glCompressedTexImage2D(GL_TEXTURE_2D, 0, GL_COMPRESSED_RGBA_S3TC_DXT5_EXT, mm.width, mm.height, 0, image_size, mm.data)
        elif mm.tpc_format == TPCTextureFormat.RGB:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, mm.width, mm.height, 0, GL_RGB, GL_UNSIGNED_BYTE, mm.data)
        elif mm.tpc_format == TPCTextureFormat.RGBA:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, mm.width, mm.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, mm.data)
        else:
            raise ValueError(f"Unsupported texture format: {mm.tpc_format!r}")

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)

        return Texture(gl_id)

    @classmethod
    def from_color(
        cls,
        r: int = 0,
        g: int = 0,
        b: int = 0,
    ) -> Texture:
        gl_id: int = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, gl_id)

        # Create pixel data using numpy for better performance and alignment
        pixels: np.ndarray = np.full((64, 64, 3), [r, g, b], dtype=np.uint8)

        # Immediate error checking before and after glTexImage2D
        errno: int | None = glGetError()
        if errno is not None and errno != GL_NO_ERROR:
            print(f"Error before glTexImage2D: {gluErrorString(errno)}")

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 64, 64, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return Texture(gl_id)

    def use(self):
        glBindTexture(GL_TEXTURE_2D, self._id)
