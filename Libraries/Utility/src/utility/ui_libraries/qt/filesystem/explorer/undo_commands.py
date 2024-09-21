from __future__ import annotations

import shutil

from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtWidgets import QUndoCommand

if TYPE_CHECKING:
    from pathlib import Path

class BaseUndoCommand(QUndoCommand):
    def __init__(self, description: str, redo_after_creation: bool = False):
        super().__init__(description)
        self._first_redo = not redo_after_creation

    def redo(self):
        if self._first_redo:
            self._first_redo = False
            return
        try:
            self._redo()
        except Exception as e:
            RobustLogger().exception(f"Error during redo of {self.text()}: {e!s}")

    def undo(self):
        try:
            self._undo()
        except Exception as e:
            RobustLogger().exception(f"Error during undo of {self.text()}: {e!s}")

    def _redo(self):
        raise NotImplementedError("Subclasses must implement _redo")

    def _undo(self):
        raise NotImplementedError("Subclasses must implement _undo")

class CutCommand(BaseUndoCommand):
    def __init__(self, source_paths: list[Path], destination_path: Path, redo_after_creation: bool = False):
        super().__init__("Cut", redo_after_creation)
        self.source_paths = source_paths
        self.destination_path = destination_path
        self.moved_items = []

    def _redo(self):
        for source in self.source_paths:
            dest = self.destination_path / source.name
            if dest.exists():
                raise FileExistsError(f"Destination path already exists: {dest}")
            shutil.move(str(source), str(dest))
            self.moved_items.append((source, dest))

    def _undo(self):
        for source, dest in reversed(self.moved_items):
            if not dest.exists():
                raise FileNotFoundError(f"File to undo not found: {dest}")
            shutil.move(str(dest), str(source))
        self.moved_items.clear()

class CopyCommand(BaseUndoCommand):
    def __init__(self, source_paths: list[Path], destination_path: Path, redo_after_creation: bool = False):
        super().__init__("Copy", redo_after_creation)
        self.source_paths = source_paths
        self.destination_path = destination_path
        self.copied_paths = []

    def _redo(self):
        for source in self.source_paths:
            dest = self.destination_path / source.name
            if dest.exists():
                raise FileExistsError(f"Destination path already exists: {dest}")
            if source.is_dir():
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            self.copied_paths.append(dest)

    def _undo(self):
        for path in reversed(self.copied_paths):
            if not path.exists():
                raise FileNotFoundError(f"File to undo not found: {path}")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        self.copied_paths.clear()

class MoveCommand(BaseUndoCommand):
    def __init__(self, source_paths: list[Path], destination_path: Path, redo_after_creation: bool = False):
        super().__init__("Move", redo_after_creation)
        self.source_paths = source_paths
        self.destination_path = destination_path
        self.moved_paths = []

    def _redo(self):
        for source in self.source_paths:
            dest = self.destination_path / source.name
            if dest.exists():
                raise FileExistsError(f"Destination path already exists: {dest}")
            shutil.move(str(source), str(dest))
            self.moved_paths.append((source, dest))

    def _undo(self):
        for source, dest in reversed(self.moved_paths):
            if not dest.exists():
                raise FileNotFoundError(f"File to undo not found: {dest}")
            shutil.move(str(dest), str(source))
        self.moved_paths.clear()

class DeleteCommand(BaseUndoCommand):
    def __init__(self, paths: list[Path], redo_after_creation: bool = False):
        super().__init__("Delete", redo_after_creation)
        self.paths = paths
        self.deleted_items = []

    def _redo(self):
        for path in self.paths:
            if not path.exists():
                raise FileNotFoundError(f"File to delete not found: {path}")
            if path.is_dir():
                shutil.rmtree(path)
                self.deleted_items.append(("dir", path))
            else:
                path.unlink()
                self.deleted_items.append(("file", path))

    def _undo(self):
        for item_type, path in reversed(self.deleted_items):
            if path.exists():
                raise FileExistsError(f"Path to restore already exists: {path}")
            if item_type == "dir":
                path.mkdir(parents=True)
            else:
                path.touch()
        self.deleted_items.clear()

class RenameCommand(BaseUndoCommand):
    def __init__(self, old_path: Path, new_path: Path, redo_after_creation: bool = False):
        super().__init__("Rename", redo_after_creation)
        self.old_path = old_path
        self.new_path = new_path

    def _redo(self):
        if not self.old_path.exists():
            raise FileNotFoundError(f"File to rename not found: {self.old_path}")
        if self.new_path.exists():
            raise FileExistsError(f"New path already exists: {self.new_path}")
        self.old_path.rename(self.new_path)

    def _undo(self):
        if not self.new_path.exists():
            raise FileNotFoundError(f"File to undo rename not found: {self.new_path}")
        if self.old_path.exists():
            raise FileExistsError(f"Old path already exists: {self.old_path}")
        self.new_path.rename(self.old_path)
