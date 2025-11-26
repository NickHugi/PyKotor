from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

from pykotor.resource.generics.dlg import DLGAnimation
from toolset.data.installation import HTInstallation

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.twoda import TwoDA


class EditAnimationDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        animation_arg: DLGAnimation | None = None,
    ):
        animation: DLGAnimation = DLGAnimation() if animation_arg is None else animation_arg
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        from toolset.uic.qtpy.dialogs.edit_animation import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        anim_list: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_DIALOG_ANIMS)
        assert anim_list is not None
        self.ui.animationSelect.set_items(anim_list.get_column("name"), sort_alphabetically=True, cleanup_strings=True, ignore_blanks=True)

        self.ui.animationSelect.setCurrentIndex(animation.animation_id)
        self.ui.animationSelect.set_context(anim_list, installation, HTInstallation.TwoDA_DIALOG_ANIMS)
        self.ui.participantEdit.setText(animation.participant)

    def animation(self) -> DLGAnimation:
        animation = DLGAnimation()
        animation.animation_id = self.ui.animationSelect.currentIndex()
        animation.participant = self.ui.participantEdit.text()
        return animation
