from __future__ import annotations



    @staticmethod
    def swizzle(data: bytes | bytearray, width: int, height: int, bytes_per_pixel: int) -> bytearray:
        """Swizzle the pixel data for optimized GPU access.

        :param data: Original pixel data
        :param width: Image width
        :param height: Image height
        :param bytes_per_pixel: Number of bytes per pixel
        :return: Swizzled pixel data
        """

        def swizzle_offset(x: int, y: int, width: int, height: int) -> int:
            width = int(math.log2(width))
            height = int(math.log2(height))
            offset = 0
            shift_count = 0
            while width | height:
                if width:
                    offset |= (x & 0x01) << shift_count
                    x >>= 1
                    shift_count += 1
                    width -= 1
                if height:
                    offset |= (y & 0x01) << shift_count
                    y >>= 1
                    shift_count += 1
                    height -= 1
            return offset

        swizzled = bytearray(width * height * bytes_per_pixel)
        for y, x in itertools.product(range(height), range(width)):
            src_offset = (y * width + x) * bytes_per_pixel
            dst_offset = swizzle_offset(x, y, width, height) * bytes_per_pixel
            for i in range(bytes_per_pixel):
                swizzled[dst_offset + i] = data[src_offset + i]

        return swizzled

    @staticmethod
    def deswizzle(data: bytes | bytearray, width: int, height: int, bytes_per_pixel: int) -> bytearray:
        """Deswizzle the pixel data from optimized GPU format to standard linear format.

        :param data: Swizzled pixel data
        :param width: Image width
        :param height: Image height
        :param bytes_per_pixel: Number of bytes per pixel
        :return: Deswizzled pixel data
        """

        def deswizzle_offset(x: int, y: int, width: int, height: int) -> int:
            width = int(math.log2(width))
            height = int(math.log2(height))
            offset = 0
            shift_count = 0
            while width | height:
                if width:
                    offset |= (x & 0x01) << shift_count
                    x >>= 1
                    shift_count += 1
                    width -= 1
                if height:
                    offset |= (y & 0x01) << shift_count
                    y >>= 1
                    shift_count += 1
                    height -= 1
            return offset

        deswizzled = bytearray(width * height * bytes_per_pixel)
        for y, x in itertools.product(range(height), range(width)):
            src_offset = deswizzle_offset(x, y, width, height) * bytes_per_pixel
            dst_offset = (y * width + x) * bytes_per_pixel
            for i in range(bytes_per_pixel):
                deswizzled[dst_offset + i] = data[src_offset + i]

        return deswizzled