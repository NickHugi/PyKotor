from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from PIL import ImageFont


class FontMetrics:
    """Handles font metric calculations for bitmap font generation."""

    def __init__(
        self,
        pil_font: ImageFont.FreeTypeFont,
        charset_list: list[str],
        baseline_char: str = "0",
    ):
        """Initialize font metrics calculator.

        Args:
            pil_font: The PIL FreeType font to calculate metrics for
            charset_list: List of characters to consider for metrics
            baseline_char: Character to use for baseline calculations (default: "0")
        """
        self.pil_font: ImageFont.FreeTypeFont = pil_font
        self.charset_list: list[str] = charset_list
        self.baseline_char: str = baseline_char

        # Calculate metrics on initialization
        self.baseline_height: int
        self.max_underhang_height: int
        self.max_char_height: int
        self.baseline_height, self.max_underhang_height, self.max_char_height = self._calculate_metrics()

    def _calculate_metrics(self) -> tuple[int, int, int]:
        """Calculate font metrics including baseline height, underhang height, and max character height.

        Returns:
            Tuple of (baseline_height, max_underhang_height, max_char_height)
        """
        # Create a temporary image for measurements
        temp_image: Image.Image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        temp_draw: ImageDraw.ImageDraw = ImageDraw.Draw(temp_image)

        # Get the bounding box of the baseline character
        baseline_bbox: tuple[int, int, int, int] = temp_draw.textbbox((0, 0), self.baseline_char, font=self.pil_font)
        baseline_height: int = int(baseline_bbox[3] - baseline_bbox[1])

        max_underhang_height = 0
        max_char_height = 0

        # Calculate metrics for each character
        for char in self.charset_list:
            if not char:  # Skip empty characters
                continue

            char_bbox: tuple[int, int, int, int] = temp_draw.textbbox((0, 0), char, font=self.pil_font)

            underhang_height = int(char_bbox[3] - baseline_bbox[3])
            char_height = int(char_bbox[3] - char_bbox[1])

            max_underhang_height: int = max(max_underhang_height, underhang_height)
            max_char_height: int = max(max_char_height, char_height + underhang_height)

        return baseline_height, max_underhang_height, max_char_height
