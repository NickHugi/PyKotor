from __future__ import annotations

from qtpy.QtWidgets import QFileDialog

from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qplatformdialoghelper import QFileDialogPlatformHelper


class LinuxFileDialogHelper(QFileDialogPlatformHelper):
    def show_dialog(self) -> bool:
        try:
            import gi

            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
        except ImportError:
            print("GTK is not available. Make sure you have the required dependencies installed.")
            return False

        if self._options.acceptMode() == QFileDialog.AcceptMode.AcceptOpen:
            dialog = Gtk.FileChooserDialog(
                title="Open File",
                action=Gtk.FileChooserAction.OPEN
                if self._options.fileMode() != QFileDialog.FileMode.Directory
                else Gtk.FileChooserAction.SELECT_FOLDER,
            )
            dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        else:
            dialog = Gtk.FileChooserDialog(title="Save File", action=Gtk.FileChooserAction.SAVE)
            dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)

        dialog.set_current_folder(self._current_directory)
        dialog.set_select_multiple(self._options.fileMode() == QFileDialog.FileMode.ExistingFiles)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if dialog.get_select_multiple():
                self._selected_files = dialog.get_filenames()
            else:
                self._selected_files = [dialog.get_filename()]
            dialog.destroy()
            return True
        dialog.destroy()
        return False
