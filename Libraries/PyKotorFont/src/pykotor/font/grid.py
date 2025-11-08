from __future__ import annotations

import math

from dataclasses import dataclass
from typing import NamedTuple


class GridCell(NamedTuple):
    """Represents a cell in the bitmap font grid."""
    x: int
    y: int
    pixel_x1: float
    pixel_y1: float
    pixel_x2: float
    pixel_y2: float
    norm_x1: float
    norm_y1: float
    norm_x2: float
    norm_y2: float


@dataclass
class GridDimensions:
    """Stores the calculated dimensions for the bitmap font grid."""
    characters_per_row: int
    characters_per_column: int
    cell_size: int
    cell_height: float


class BitmapGrid:
    """Handles grid calculations for bitmap font generation."""

    def __init__(
        self,
        resolution: tuple[int, int],
        num_chars: int,
    ):
        """Initialize the bitmap grid calculator.

        Args:
            resolution: Tuple of (width, height) for the bitmap
            num_chars: Number of characters to fit in the grid

        Raises:
            ZeroDivisionError: If resolution contains zero values
        """
        if any(r == 0 for r in resolution):
            msg: str = f"resolution must be nonzero, got {resolution}"
            raise ZeroDivisionError(msg)

        self.resolution: tuple[int, int] = resolution
        self.num_chars: int = num_chars
        self.dimensions: GridDimensions = self._calculate_dimensions()

    def _calculate_dimensions(self) -> GridDimensions:
        """Calculate the grid dimensions based on resolution and character count.

        Returns:
            GridDimensions object containing the calculated dimensions
        """
        # Calculate grid layout
        chars_per_col: int = math.ceil(math.sqrt(self.num_chars))
        chars_per_row: int = math.ceil(math.sqrt(self.num_chars))

        # Calculate cell size to fit within resolution
        cell_size: int = min(
            self.resolution[0] // chars_per_row,
            self.resolution[1] // chars_per_col
        )

        # Calculate cell height
        cell_height: float = self.resolution[1] / chars_per_row

        return GridDimensions(
            characters_per_row=chars_per_row,
            characters_per_column=chars_per_col,
            cell_size=cell_size,
            cell_height=cell_height
        )

    def get_cell(self, index: int) -> GridCell:
        """Get the grid cell information for a given character index.

        Args:
            index: The index of the character in the grid

        Returns:
            GridCell containing position and coordinate information
        """
        # Calculate grid position
        grid_x: int = index % self.dimensions.characters_per_row
        grid_y: int = index // self.dimensions.characters_per_row

        # Calculate normalized coordinates
        norm_x1: float = grid_x / self.dimensions.characters_per_row
        norm_y1: float = (grid_y * self.dimensions.cell_height) / self.resolution[1]
        norm_x2: float = (grid_x + 1) / self.dimensions.characters_per_row
        norm_y2: float = ((grid_y + 1) * self.dimensions.cell_height) / self.resolution[1]

        # Convert to pixel coordinates
        pixel_x1: float = norm_x1 * self.resolution[0]
        pixel_y1: float = norm_y1 * self.resolution[1]
        pixel_x2: float = norm_x2 * self.resolution[0]
        pixel_y2: float = norm_y2 * self.resolution[1]

        return GridCell(
            x=grid_x,
            y=grid_y,
            pixel_x1=pixel_x1,
            pixel_y1=pixel_y1,
            pixel_x2=pixel_x2,
            pixel_y2=pixel_y2,
            norm_x1=norm_x1,
            norm_y1=1 - norm_y1,  # Invert Y-axis normalization
            norm_x2=norm_x2,
            norm_y2=1 - norm_y2   # Invert Y-axis normalization
        )
