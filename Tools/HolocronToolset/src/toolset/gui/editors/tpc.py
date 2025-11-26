from __future__ import annotations

import warnings

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from qtpy.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QBuffer, QIODevice  # type: ignore[attr-defined]
from qtpy.QtGui import (
    QIcon,
    QImage,
    QImageReader,
    QPixmap,
    QWheelEvent,
    QDrag,
)
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QFileDialog,
    QMenu,
    QMessageBox,
    QStyle,
)

from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.tpc.tpc_data import TPCMipmap


class TPCEditor(Editor):
    """A modern, streamlined TPC texture editor with intuitive controls and clear organization."""

    def __init__(
        self,
        parent: QWidget | None,
        installation: Installation | None = None,
    ):
        supported: list[ResourceType] = [
            ResourceType.TPC,
            ResourceType.TGA,
            ResourceType.JPG,
            ResourceType.PNG,
            ResourceType.BMP,
        ]
        super().__init__(parent, "Texture Viewer", "none", supported, supported, installation)  # type: ignore[arg-type]

        self._tpc: TPC = TPC.from_blank()
        self._current_frame: int = 0
        self._current_mipmap: int = 0
        self._zoom_factor: float = 1.0
        self._fit_to_window: bool = False

        from toolset.uic.qtpy.editors.tpc import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._setup_ui()
        self._setup_actions()
        self._add_help_action()
        self._setup_signals()
        self._setup_icons()
        self._setup_context_menu()
        self._setup_drag_drop()
        self._setup_properties_panel()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.new()

    def _setup_ui(self) -> None:
        """Configure UI elements and initial state."""
        # Configure texture display
        self.ui.textureLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.textureLabel.setMinimumSize(1, 1)
        self.ui.textureScrollArea.setWidgetResizable(True)
        self.ui.textureScrollArea.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configure zoom slider
        self.ui.zoomSlider.setRange(10, 500)
        self.ui.zoomSlider.setValue(100)
        self.ui.zoomSlider.setPageStep(10)

        # Configure status bar
        self._update_status_bar()

        # Initially hide docks if needed
        self.ui.txiDockWidget.setVisible(self.ui.actionToggleTXIEditor.isChecked())
        self.ui.propertiesDockWidget.setVisible(self.ui.actionToggleProperties.isChecked())

    def _setup_actions(self) -> None:
        """Set up menu actions and keyboard shortcuts."""
        # File menu
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.saveAs)
        self.ui.actionRevert.triggered.connect(self.revert)
        self.ui.actionExit.triggered.connect(self.close)

        # Edit menu
        self.ui.actionCopy.triggered.connect(self._copy_to_clipboard)
        self.ui.actionPaste.triggered.connect(self._paste_from_clipboard)
        self.ui.actionRotateLeft.triggered.connect(self._rotate_left)
        self.ui.actionRotateRight.triggered.connect(self._rotate_right)
        self.ui.actionFlipHorizontal.triggered.connect(self._flip_horizontal)
        self.ui.actionFlipVertical.triggered.connect(self._flip_vertical)

        # View menu
        self.ui.actionZoomIn.triggered.connect(self._zoom_in)
        self.ui.actionZoomOut.triggered.connect(self._zoom_out)
        self.ui.actionZoomFit.triggered.connect(self._zoom_fit)
        self.ui.actionZoom100.triggered.connect(self._zoom_reset)
        self.ui.actionToggleTXIEditor.triggered.connect(self._toggle_txi_editor)
        self.ui.actionToggleProperties.triggered.connect(self._toggle_properties)

        # Format menu
        self.ui.actionConvertFormat.triggered.connect(self._show_convert_format_menu)

        # Export
        self.ui.actionExport.triggered.connect(self._export_texture)

    def _setup_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Zoom controls
        self.ui.zoomSlider.valueChanged.connect(self._on_zoom_slider_changed)
        self.ui.zoomInButton.clicked.connect(self._zoom_in)
        self.ui.zoomOutButton.clicked.connect(self._zoom_out)

        # Frame navigation
        self.ui.framePrevButton.clicked.connect(lambda: self._navigate_frame(-1))
        self.ui.frameNextButton.clicked.connect(lambda: self._navigate_frame(1))

        # Mipmap navigation
        self.ui.mipmapSpinBox.valueChanged.connect(self._on_mipmap_changed)

        # Alpha test
        self.ui.alphaTestSpinBox.valueChanged.connect(self._on_alpha_test_changed)

    def _setup_icons(self) -> None:
        """Set up icons for toolbar actions."""
        style: QStyle | None = self.style()
        if style is None:
            return

        # File operations
        self.ui.actionNew.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.ui.actionOpen.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.ui.actionSave.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.ui.actionExport.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))

        # Clipboard operations
        self.ui.actionCopy.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DriveCDIcon))
        self.ui.actionPaste.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirLinkIcon))

        # View operations
        self.ui.actionZoomIn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.ui.actionZoomOut.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        self.ui.actionZoomFit.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
        self.ui.actionZoom100.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))

        # Transform operations
        self.ui.actionRotateLeft.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.ui.actionRotateRight.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
        self.ui.actionFlipHorizontal.setIcon(QIcon.fromTheme("object-flip-horizontal"))
        self.ui.actionFlipVertical.setIcon(QIcon.fromTheme("object-flip-vertical"))

        # Other
        self.ui.actionToggleTXIEditor.setIcon(
            style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )

    def _setup_context_menu(self) -> None:
        """Set up context menu for texture display."""
        self.ui.textureLabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.textureLabel.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_drag_drop(self) -> None:
        """Set up drag and drop support for the texture label."""
        self.ui.textureLabel.setAcceptDrops(False)  # We'll handle drag, not drop
        self.ui.textureLabel.mousePressEvent = self._on_texture_mouse_press  # type: ignore[method-assign]

    def _setup_properties_panel(self) -> None:
        """Set up the properties panel with texture information."""
        # Update properties when texture changes
        self._update_properties_panel()

    def _on_texture_mouse_press(self, event) -> None:
        """Handle mouse press on texture for drag operation."""
        if event.button() == Qt.MouseButton.LeftButton and self._tpc.layers:
            # Start drag operation
            self._start_drag_operation(event.pos())

    def _start_drag_operation(self, position: QPoint) -> None:
        """Start a drag operation with the current texture."""
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            return

        # Get the current texture as QPixmap
        pixmap = self._get_current_texture_pixmap()
        if pixmap.isNull():
            return

        # Create drag object
        drag = QDrag(self)
        mime_data = drag.mimeData()
        
        # Set image data
        image = pixmap.toImage()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        if mime_data is not None:
            mime_data.setData("image/png", buffer.data())
            mime_data.setImageData(image)

        # Create a smaller preview for dragging
        preview_pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        drag.setPixmap(preview_pixmap)
        drag.setHotSpot(position)

        # Animate the drag start
        self._animate_drag_start()

        # Execute drag
        drag.exec(Qt.DropAction.CopyAction)

    def _animate_drag_start(self) -> None:
        """Animate the texture label when starting a drag operation."""
        original_opacity = self.ui.textureLabel.windowOpacity()
        animation = QPropertyAnimation(self.ui.textureLabel, b"windowOpacity", self)
        animation.setDuration(150)
        animation.setStartValue(1.0)
        animation.setEndValue(0.7)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: self._animate_drag_end(original_opacity))
        animation.start()

    def _animate_drag_end(self, original_opacity: float) -> None:
        """Restore opacity after drag animation."""
        animation = QPropertyAnimation(self.ui.textureLabel, b"windowOpacity", self)
        animation.setDuration(150)
        animation.setStartValue(0.7)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        animation.start()

    def _copy_to_clipboard(self) -> None:
        """Copy the current texture to clipboard with animation."""
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            QMessageBox.warning(self, "No Texture", "No texture loaded to copy.")
            return

        try:
            pixmap = self._get_current_texture_pixmap()
            if pixmap.isNull():
                return

            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)

            # Animate copy action
            self._animate_copy_action()

            from toolset.gui.common.localization import translate as tr, trf
            self.ui.statusbar.showMessage(tr("Texture copied to clipboard"), 2000)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, tr("Copy Failed"), trf("Failed to copy texture:\n{error}", error=str(e)))

    def _animate_copy_action(self) -> None:
        """Animate the texture label when copying."""
        original_style = self.ui.textureLabel.styleSheet()
        
        # Flash effect
        animation = QPropertyAnimation(self.ui.textureLabel, b"styleSheet", self)
        animation.setDuration(200)
        animation.setStartValue(original_style)
        animation.setEndValue(f"{original_style} border: 3px solid #4CAF50;")
        
        def restore_style():
            self.ui.textureLabel.setStyleSheet(original_style)
        
        animation.finished.connect(restore_style)
        animation.start()

    def _paste_from_clipboard(self) -> None:
        """Paste texture from clipboard with animation."""
        clipboard = QApplication.clipboard()
        image = clipboard.image()

        if image.isNull():
            # Try getting pixmap
            pixmap = clipboard.pixmap()
            if pixmap.isNull():
                from toolset.gui.common.localization import translate as tr
                QMessageBox.warning(self, tr("No Image"), tr("Clipboard does not contain an image."))
                return
            image = pixmap.toImage()

        try:
            # Convert QImage to TPC
            width = image.width()
            height = image.height()

            # Convert to RGBA format
            if image.format() != QImage.Format.Format_RGBA8888:
                image = image.convertToFormat(QImage.Format.Format_RGBA8888, Qt.ImageConversionFlag.AutoColor)

            # Extract image data
            const_bits = image.constBits()
            if const_bits is None:
                raise ValueError("Failed to extract image data")

            bytes_per_pixel = 4  # RGBA
            data_size = width * height * bytes_per_pixel
            image_bytes = bytearray(const_bits.asarray(data_size))  # type: ignore[attr-defined]

            # Create new TPC from pasted image
            self._tpc.set_single(image_bytes, TPCTextureFormat.RGBA, width, height)
            self._current_frame = 0
            self._current_mipmap = 0

            # Animate paste action
            self._animate_paste_action()

            self._update_texture_display()
            self._update_frame_controls()
            self._update_mipmap_controls()
            self._update_status_bar()
            self._update_properties_panel()

            from toolset.gui.common.localization import translate as tr, trf
            self.ui.statusbar.showMessage(tr("Texture pasted from clipboard"), 2000)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, tr("Paste Failed"), trf("Failed to paste texture:\n{error}", error=str(e)))

    def _animate_paste_action(self) -> None:
        """Animate the texture label when pasting."""
        original_style = self.ui.textureLabel.styleSheet()
        
        # Flash effect with different color
        animation = QPropertyAnimation(self.ui.textureLabel, b"styleSheet", self)
        animation.setDuration(200)
        animation.setStartValue(original_style)
        animation.setEndValue(f"{original_style} border: 3px solid #2196F3;")
        
        def restore_style():
            self.ui.textureLabel.setStyleSheet(original_style)
        
        animation.finished.connect(restore_style)
        animation.start()

    def _get_current_texture_pixmap(self) -> QPixmap:
        """Get the current texture as a QPixmap."""
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            return QPixmap()

        layer_index = 0
        if self._tpc.is_animated or self._tpc.is_cube_map:
            layer_index = max(0, min(self._current_frame, len(self._tpc.layers) - 1))

        mipmap_index = max(0, min(self._current_mipmap, len(self._tpc.layers[layer_index].mipmaps) - 1))
        mipmap: TPCMipmap = self._tpc.layers[layer_index].mipmaps[mipmap_index].copy()
        display_format = mipmap.tpc_format

        # Convert to displayable format
        if display_format == TPCTextureFormat.DXT1:
            mipmap.convert(TPCTextureFormat.RGB)
        elif display_format in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5, TPCTextureFormat.BGRA):
            mipmap.convert(TPCTextureFormat.RGBA)
        elif display_format == TPCTextureFormat.BGR:
            mipmap.convert(TPCTextureFormat.RGB)
        elif display_format == TPCTextureFormat.Greyscale:
            mipmap.convert(TPCTextureFormat.RGBA)

        target_format = mipmap.tpc_format

        # Create QImage from mipmap data
        image = QImage(
            bytes(mipmap.data),
            mipmap.width,
            mipmap.height,
            target_format.to_qimage_format(),
        )
        image = image.mirrored(False, True)  # Flip vertically for correct display

        return QPixmap.fromImage(image)

    def _show_context_menu(self, position) -> None:
        """Show context menu at the given position."""
        menu = QMenu(self)
        menu.addAction(self.ui.actionCopy)
        menu.addAction(self.ui.actionPaste)
        menu.addSeparator()
        menu.addAction(self.ui.actionZoomIn)
        menu.addAction(self.ui.actionZoomOut)
        menu.addAction(self.ui.actionZoomFit)
        menu.addAction(self.ui.actionZoom100)
        menu.addSeparator()
        menu.addAction(self.ui.actionRotateLeft)
        menu.addAction(self.ui.actionRotateRight)
        menu.addAction(self.ui.actionFlipHorizontal)
        menu.addAction(self.ui.actionFlipVertical)
        menu.addSeparator()
        menu.addAction(self.ui.actionExport)
        menu.exec(self.ui.textureLabel.mapToGlobal(position))

    def _show_convert_format_menu(self) -> None:
        """Show format conversion menu at the convert format button position."""
        menu = QMenu(self)
        menu.setTitle("Convert Format")

        current_format = self._tpc.format()
        for format_name, format_value in TPCTextureFormat.__members__.items():
            if format_value == TPCTextureFormat.Invalid:
                continue

            action = QAction(format_name, self)
            action.setData(format_value)
            action.setCheckable(True)
            action.setChecked(format_value == current_format)
            action.triggered.connect(lambda checked, fmt=format_value: self._convert_format(fmt))
            menu.addAction(action)

        # Show menu below the convert format action button
        button = self.ui.mainToolBar.widgetForAction(self.ui.actionConvertFormat)
        if button:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        else:
            menu.exec(self.mapToGlobal(self.rect().center()))

    def _convert_format(self, target_format: TPCTextureFormat) -> None:
        """Convert the texture to the specified format."""
        if self._tpc.format() == target_format:
            return

        try:
            self._tpc.convert(target_format)
            self._update_texture_display()
            self._update_status_bar()
            self._update_properties_panel()
            QMessageBox.information(
                self,
                "Format Converted",
                f"Texture format converted to {target_format.name}.",
            )
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "Conversion Failed",
                f"Failed to convert texture format:\n{str(e)}",
            )

    def _update_status_bar(self) -> None:
        """Update the status bar with current texture information."""
        if not self._tpc.layers:
            self.ui.statusbar.showMessage("No texture loaded")
            return

        width, height = self._tpc.dimensions()
        format_name = self._tpc.format().name
        frame_count = len(self._tpc.layers)
        frame_info = f" | Frame {self._current_frame + 1}/{frame_count}" if frame_count > 1 else ""
        mipmap_info = ""
        if self._tpc.layers and len(self._tpc.layers[0].mipmaps) > 1:
            mipmap_info = f" | Mipmap {self._current_mipmap + 1}/{len(self._tpc.layers[0].mipmaps)}"

        status_text = f"Dimensions: {width}×{height} | Format: {format_name}{frame_info}{mipmap_info}"
        self.ui.statusbar.showMessage(status_text)

    def _update_frame_controls(self) -> None:
        """Update frame navigation controls based on texture state."""
        frame_count = len(self._tpc.layers) if self._tpc.layers else 0
        has_multiple_frames = frame_count > 1

        self.ui.framePrevButton.setEnabled(has_multiple_frames)
        self.ui.frameNextButton.setEnabled(has_multiple_frames)

        if has_multiple_frames:
            self.ui.frameInfoLabel.setText(f"Frame: {self._current_frame + 1}/{frame_count}")
        else:
            self.ui.frameInfoLabel.setText("Frame: 1/1")

    def _update_mipmap_controls(self) -> None:
        """Update mipmap navigation controls."""
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            self.ui.mipmapSpinBox.setMaximum(0)
            self.ui.mipmapSpinBox.setEnabled(False)
            return

        mipmap_count = len(self._tpc.layers[0].mipmaps)
        self.ui.mipmapSpinBox.setMaximum(max(0, mipmap_count - 1))
        self.ui.mipmapSpinBox.setValue(self._current_mipmap)
        self.ui.mipmapSpinBox.setEnabled(mipmap_count > 1)

    def _on_mipmap_changed(self, value: int) -> None:
        """Handle mipmap selection change."""
        self._current_mipmap = value
        self._update_texture_display()
        self._update_status_bar()

    def _on_alpha_test_changed(self, value: float) -> None:
        """Handle alpha test threshold change."""
        self._tpc.alpha_test = value
        self._update_properties_panel()

    def _update_properties_panel(self) -> None:
        """Update the properties panel with current texture information."""
        if not self._tpc.layers:
            self.ui.dimensionsValue.setText("—")
            self.ui.formatValue.setText("—")
            self.ui.layersValue.setText("—")
            self.ui.mipmapsValue.setText("—")
            self.ui.compressedValue.setText("—")
            self.ui.animatedValue.setText("—")
            self.ui.cubeMapValue.setText("—")
            return

        width, height = self._tpc.dimensions()
        self.ui.dimensionsValue.setText(f"{width} × {height}")
        self.ui.formatValue.setText(self._tpc.format().name)
        self.ui.layersValue.setText(str(len(self._tpc.layers)))
        
        mipmap_count = len(self._tpc.layers[0].mipmaps) if self._tpc.layers else 0
        self.ui.mipmapsValue.setText(str(mipmap_count))
        self.ui.alphaTestSpinBox.setValue(self._tpc.alpha_test)
        self.ui.compressedValue.setText("Yes" if self._tpc.is_compressed() else "No")
        self.ui.animatedValue.setText("Yes" if self._tpc.is_animated else "No")
        self.ui.cubeMapValue.setText("Yes" if self._tpc.is_cube_map else "No")

    def _navigate_frame(self, direction: int) -> None:
        """Navigate to the previous or next frame."""
        frame_count = len(self._tpc.layers)
        if frame_count == 0:
            return

        self._current_frame = max(0, min(self._current_frame + direction, frame_count - 1))
        self._update_texture_display()
        self._update_frame_controls()
        self._update_status_bar()

    def _zoom_in(self) -> None:
        """Increase zoom level."""
        current_value = self.ui.zoomSlider.value()
        new_value = min(500, current_value + 10)
        self.ui.zoomSlider.setValue(new_value)

    def _zoom_out(self) -> None:
        """Decrease zoom level."""
        current_value = self.ui.zoomSlider.value()
        new_value = max(10, current_value - 10)
        self.ui.zoomSlider.setValue(new_value)

    def _zoom_fit(self) -> None:
        """Fit texture to window."""
        self._fit_to_window = True
        self.ui.zoomPercentLabel.setText("Fit")
        self._update_texture_display()

    def _zoom_reset(self) -> None:
        """Reset zoom to 100%."""
        self._fit_to_window = False
        self.ui.zoomSlider.setValue(100)
        self.ui.zoomPercentLabel.setText("100%")

    def _on_zoom_slider_changed(self, value: int) -> None:
        """Handle zoom slider value change."""
        self._fit_to_window = False
        self._zoom_factor = value / 100.0
        self.ui.zoomPercentLabel.setText(f"{value}%")
        self._update_texture_display()

    def _rotate_left(self) -> None:
        """Rotate texture 90° counter-clockwise."""
        self._tpc.rotate90(-1)
        self._update_texture_display()
        self._update_status_bar()
        self._update_properties_panel()

    def _rotate_right(self) -> None:
        """Rotate texture 90° clockwise."""
        self._tpc.rotate90(1)
        self._update_texture_display()
        self._update_status_bar()
        self._update_properties_panel()

    def _flip_horizontal(self) -> None:
        """Flip texture horizontally."""
        self._tpc.flip_horizontally()
        self._update_texture_display()

    def _flip_vertical(self) -> None:
        """Flip texture vertically."""
        self._tpc.flip_vertically()
        self._update_texture_display()

    def _toggle_txi_editor(self, checked: bool) -> None:
        """Toggle TXI editor dock widget visibility."""
        self.ui.txiDockWidget.setVisible(checked)

    def _toggle_properties(self, checked: bool) -> None:
        """Toggle properties dock widget visibility."""
        self.ui.propertiesDockWidget.setVisible(checked)

    def _export_texture(self) -> None:
        """Export texture to a standard image format."""
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            QMessageBox.warning(self, "No Texture", "No texture loaded to export.")
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Texture",
            "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TGA (*.tga)",
        )

        if not file_path:
            return

        try:
            layer_index = 0
            if self._tpc.is_animated or self._tpc.is_cube_map:
                layer_index = max(0, min(self._current_frame, len(self._tpc.layers) - 1))

            mipmap_index = max(0, min(self._current_mipmap, len(self._tpc.layers[layer_index].mipmaps) - 1))
            mipmap: TPCMipmap = self._tpc.layers[layer_index].mipmaps[mipmap_index].copy()
            export_format = mipmap.tpc_format

            # Convert to displayable format
            if export_format == TPCTextureFormat.DXT1:
                mipmap.convert(TPCTextureFormat.RGB)
            elif export_format in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5, TPCTextureFormat.BGRA):
                mipmap.convert(TPCTextureFormat.RGBA)
            elif export_format == TPCTextureFormat.BGR:
                mipmap.convert(TPCTextureFormat.RGB)
            elif export_format == TPCTextureFormat.Greyscale:
                mipmap.convert(TPCTextureFormat.RGBA)

            image = Image.frombytes(
                mipmap.tpc_format.to_pil_mode(),
                (mipmap.width, mipmap.height),
                bytes(mipmap.data),
            )
            image.save(file_path)
            QMessageBox.information(self, "Export Successful", f"Texture exported to:\n{file_path}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Failed to export texture:\n{str(e)}")

    def _update_texture_display(self) -> None:
        """Update the texture display with current zoom and frame."""
        if not self._tpc.layers or not self._tpc.layers[0].mipmaps:
            self.ui.textureLabel.clear()
            return

        # Get the appropriate layer and mipmap
        layer_index = 0
        if self._tpc.is_animated or self._tpc.is_cube_map:
            layer_index = max(0, min(self._current_frame, len(self._tpc.layers) - 1))

        mipmap_index = max(0, min(self._current_mipmap, len(self._tpc.layers[layer_index].mipmaps) - 1))
        mipmap: TPCMipmap = self._tpc.layers[layer_index].mipmaps[mipmap_index].copy()
        display_format = mipmap.tpc_format

        # Convert to displayable format
        if display_format == TPCTextureFormat.DXT1:
            mipmap.convert(TPCTextureFormat.RGB)
        elif display_format in (TPCTextureFormat.DXT3, TPCTextureFormat.DXT5, TPCTextureFormat.BGRA):
            mipmap.convert(TPCTextureFormat.RGBA)
        elif display_format == TPCTextureFormat.BGR:
            mipmap.convert(TPCTextureFormat.RGB)
        elif display_format == TPCTextureFormat.Greyscale:
            mipmap.convert(TPCTextureFormat.RGBA)

        target_format = mipmap.tpc_format

        # Create QImage from mipmap data
        image = QImage(
            bytes(mipmap.data),
            mipmap.width,
            mipmap.height,
            target_format.to_qimage_format(),
        )
        image = image.mirrored(False, True)  # Flip vertically for correct display

        # Calculate display size
        if self._fit_to_window:
            viewport = self.ui.textureScrollArea.viewport()
            if viewport is None:
                return
            scroll_area_size = viewport.size()
            available_width = scroll_area_size.width() - 20
            available_height = scroll_area_size.height() - 20

            aspect_ratio = mipmap.width / mipmap.height if mipmap.height else 1.0
            if available_width / available_height > aspect_ratio:
                display_height = available_height
                display_width = int(display_height * aspect_ratio)
            else:
                display_width = available_width
                display_height = int(display_width / aspect_ratio)

            image = image.scaled(
                display_width,
                display_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            # Apply zoom factor
            display_width = int(mipmap.width * self._zoom_factor)
            display_height = int(mipmap.height * self._zoom_factor)

            image = image.scaled(
                display_width,
                display_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        pixmap = QPixmap.fromImage(image)
        self.ui.textureLabel.setPixmap(pixmap)
        self.ui.textureLabel.setMinimumSize(1, 1)

        # Update TXI editor
        self.ui.txiEdit.setPlainText(self._tpc.txi)

    def wheelEvent(self, a0: QWheelEvent) -> None:
        """Handle mouse wheel events for zooming."""
        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = a0.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            elif delta < 0:
                self._zoom_out()
            a0.accept()
        else:
            super().wheelEvent(a0)

    def new(self) -> None:
        """Create a new blank texture."""
        super().new()
        self._tpc = TPC.from_blank()
        self._current_frame = 0
        self._current_mipmap = 0
        self._zoom_factor = 1.0
        self._fit_to_window = False
        self.ui.zoomSlider.setValue(100)
        self._update_texture_display()
        self._update_frame_controls()
        self._update_mipmap_controls()
        self._update_status_bar()
        self._update_properties_panel()

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes | bytearray,
    ) -> None:
        """Load a texture from file data."""
        super().load(filepath, resref, restype, data)

        self._tpc = TPC()
        if restype in {ResourceType.TPC, ResourceType.TGA}:
            txi_path = Path(filepath).with_suffix(".txi")
            self._tpc = read_tpc(data, txi_source=txi_path if txi_path.exists() else None)
        else:
            # Load from standard image format
            supported_formats: list[str] = [
                x.data().decode().strip().lstrip(".") for x in QImageReader.supportedImageFormats()  # pyright: ignore[reportGeneralTypeIssues]
            ]
            if restype.extension.lstrip(".") not in supported_formats:
                warnings.warn(f"Unsupported image format: {restype.extension!r}", stacklevel=1)

            image = QImage.fromData(data)
            if image.isNull():
                raise ValueError(f"Failed to load image data for resource of type {restype!r}")

            width = image.width()
            height = image.height()

            # Determine target format and convert image if needed
            tpc_format = TPCTextureFormat.from_qimage_format(image.format())
            if tpc_format == TPCTextureFormat.Invalid:
                # Default to RGBA if format is not directly supported
                tpc_format = TPCTextureFormat.RGBA
                image = image.convertToFormat(QImage.Format.Format_RGBA8888, Qt.ImageConversionFlag.AutoColor)
            elif image.format() != tpc_format.to_qimage_format():
                # Convert to the appropriate format
                image = image.convertToFormat(tpc_format.to_qimage_format(), Qt.ImageConversionFlag.AutoColor)

            # Extract image data
            const_bits = image.constBits()
            if const_bits is None:
                raise ValueError("Failed to extract image data")
            
            bytes_per_pixel = tpc_format.bytes_per_pixel()
            data_size = width * height * bytes_per_pixel
            image_bytes = bytearray(const_bits.asarray(data_size))  # type: ignore[attr-defined]

            self._tpc.set_single(image_bytes, tpc_format, width, height)

        self._current_frame = 0
        self._current_mipmap = 0
        self._zoom_factor = 1.0
        self._fit_to_window = False
        self.ui.zoomSlider.setValue(100)
        self._update_texture_display()
        self._update_frame_controls()
        self._update_mipmap_controls()
        self._update_status_bar()
        self._update_properties_panel()

    def build(self) -> tuple[bytes, bytes]:
        """Build the texture data for saving."""
        self._tpc.txi = self.ui.txiEdit.toPlainText()

        data: bytes | bytearray = bytearray()

        if self._restype in {ResourceType.TPC, ResourceType.TGA}:
            write_tpc(self._tpc, data, self._restype)
            return bytes(data), b""

        return bytes(data), b""
