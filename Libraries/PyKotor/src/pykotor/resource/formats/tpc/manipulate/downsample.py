from __future__ import annotations


def downsample_dxt(data: bytearray, width: int, height: int, bytes_per_block: int) -> bytearray:
    """Downsample DXT compressed image data."""
    blocks_x = (width + 3) // 4
    blocks_y = (height + 3) // 4
    new_blocks_x = (blocks_x + 1) // 2
    new_blocks_y = (blocks_y + 1) // 2
    new_data = bytearray(new_blocks_x * new_blocks_y * bytes_per_block)

    for y in range(new_blocks_y):
        for x in range(new_blocks_x):
            new_block_index = (y * new_blocks_x + x) * bytes_per_block

            # Average color endpoints from up to four source blocks
            color0_sum: list[int] = [0, 0, 0]
            color1_sum: list[int] = [0, 0, 0]
            alpha0_sum = 0
            alpha1_sum = 0
            block_count = 0

            for dy in range(2):
                for dx in range(2):
                    src_x, src_y = x * 2 + dx, y * 2 + dy
                    if src_x < blocks_x and src_y < blocks_y:
                        src_block_index = (src_y * blocks_x + src_x) * bytes_per_block

                        # Extract color endpoints
                        color0 = int.from_bytes(data[src_block_index : src_block_index + 2], "little")
                        color1 = int.from_bytes(data[src_block_index + 2 : src_block_index + 4], "little")

                        # Convert 565 to RGB
                        color0_sum[0] += ((color0 >> 11) & 0x1F) << 3
                        color0_sum[1] += ((color0 >> 5) & 0x3F) << 2
                        color0_sum[2] += (color0 & 0x1F) << 3
                        color1_sum[0] += ((color1 >> 11) & 0x1F) << 3
                        color1_sum[1] += ((color1 >> 5) & 0x3F) << 2
                        color1_sum[2] += (color1 & 0x1F) << 3

                        if bytes_per_block == 16:
                            alpha0_sum += data[src_block_index]
                            alpha1_sum += data[src_block_index + 1]

                        block_count += 1

            # Average the color endpoints
            color0_avg = [c // block_count for c in color0_sum]
            color1_avg = [c // block_count for c in color1_sum]

            # Convert back to 565 format
            color0_565 = ((color0_avg[0] >> 3) << 11) | ((color0_avg[1] >> 2) << 5) | (color0_avg[2] >> 3)
            color1_565 = ((color1_avg[0] >> 3) << 11) | ((color1_avg[1] >> 2) << 5) | (color1_avg[2] >> 3)

            # Write averaged color endpoints to new block
            new_data[new_block_index : new_block_index + 2] = color0_565.to_bytes(2, "little")
            new_data[new_block_index + 2 : new_block_index + 4] = color1_565.to_bytes(2, "little")

            # For DXT5, handle alpha
            if bytes_per_block == 16:
                alpha0_avg = alpha0_sum // block_count
                alpha1_avg = alpha1_sum // block_count
                new_data[new_block_index] = alpha0_avg
                new_data[new_block_index + 1] = alpha1_avg

            # Copy the color indices (simplified approach)
            if block_count == 4:
                # Average the color indices from four blocks
                for i in range(4):
                    indices = 0
                    for dy in range(2):
                        for dx in range(2):
                            src_x, src_y = x * 2 + dx, y * 2 + dy
                            src_block_index = (src_y * blocks_x + src_x) * bytes_per_block
                            src_indices = data[src_block_index + 4 + i]
                            indices += src_indices
                    new_data[new_block_index + 4 + i] = indices // 4
            else:
                # If we don't have all four blocks, just copy from the first available block
                src_block_index = (y * 2 * blocks_x + x * 2) * bytes_per_block
                new_data[new_block_index + 4 : new_block_index + 8] = data[src_block_index + 4 : src_block_index + 8]

            # For DXT5, handle alpha indices (simplified approach)
            if bytes_per_block == 16:
                if block_count == 4:
                    # Average the alpha indices from four blocks
                    for i in range(6):
                        alpha_indices = 0
                        for dy in range(2):
                            for dx in range(2):
                                src_x, src_y = x * 2 + dx, y * 2 + dy
                                src_block_index = (src_y * blocks_x + src_x) * bytes_per_block
                                src_alpha_indices = int.from_bytes(data[src_block_index + 2 + i : src_block_index + 3 + i], "little")
                                alpha_indices += src_alpha_indices
                        new_data[new_block_index + 2 + i] = (alpha_indices // 4).to_bytes(1, "little")[0]
                else:
                    # If we don't have all four blocks, just copy from the first available block
                    src_block_index = (y * 2 * blocks_x + x * 2) * bytes_per_block
                    new_data[new_block_index + 2 : new_block_index + 8] = data[src_block_index + 2 : src_block_index + 8]

    return new_data


def downsample_rgb(data: bytearray, width: int, height: int, bytes_per_pixel: int) -> bytearray:
    """Downsample RGB/RGBA image data."""
    next_width = max(1, width // 2)
    next_height = max(1, height // 2)
    next_size = next_width * next_height * bytes_per_pixel
    next_data = bytearray(next_size)

    for y in range(next_height):
        if y <= 0:
            break
        for x in range(next_width):
            if x <= 0:
                break
            src_x = x * 2
            src_y = y * 2
            src_offset = (src_y * width + src_x) * bytes_per_pixel
            dst_offset = (y * next_width + x) * bytes_per_pixel

            # Average the 2x2 block of pixels
            for p in range(bytes_per_pixel):
                next_data[dst_offset + p] = (
                    data[src_offset + p]
                    + data[src_offset + bytes_per_pixel + p]
                    + data[src_offset + width * bytes_per_pixel + p]
                    + data[src_offset + width * bytes_per_pixel + bytes_per_pixel + p]
                ) // 4

    return next_data
