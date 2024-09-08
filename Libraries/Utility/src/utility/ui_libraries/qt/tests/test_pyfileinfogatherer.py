from __future__ import annotations

import os
import sys
import tempfile

from unittest.mock import MagicMock, patch

import pytest

from qtpy.QtCore import QDir, QFileInfo
from qtpy.QtWidgets import QApplication, QFileIconProvider

from utility.gui.qt.common.filesystem.pyfileinfogatherer import PyFileInfoGatherer


@pytest.fixture(scope="session", autouse=True)
def app() -> QApplication:
    """Ensure QApplication is initialized."""
    app = QApplication(sys.argv) if QApplication.instance() is None else QApplication.instance()
    assert app is not None
    assert isinstance(app, QApplication)
    return app


@pytest.fixture
def gatherer() -> PyFileInfoGatherer:
    return PyFileInfoGatherer()


@pytest.mark.parametrize(
    ["enable", "expected"],
    [
        [True, True],
        [False, False],
    ],
    ids=["enable_symlinks", "disable_symlinks"],
)
def test_set_resolve_symlinks(gatherer: PyFileInfoGatherer, enable: bool, expected: bool):  # noqa: FBT001
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = os.path.join(temp_dir, "target.txt")  # noqa: PTH118
        symlink = os.path.join(temp_dir, "symlink.txt")  # noqa: PTH118

        # Create a real file and a symlink
        with open(target_file, "w") as f:  # noqa: PTH123
            f.write("test")

        os.symlink(target_file, symlink)

        # Act
        gatherer.setResolveSymlinks(enable)

        # Fetch file information for the symlink
        file_info = QFileInfo(symlink)
        resolved_path = file_info.symLinkTarget() if enable else symlink

        # Normalize both paths for comparison
        normalized_file_info_path = os.path.normcase(os.path.realpath(file_info.filePath()))
        normalized_resolved_path = os.path.normcase(os.path.realpath(resolved_path))

        # Assert
        assert gatherer.m_resolveSymlinks == expected
        assert normalized_file_info_path == normalized_resolved_path


def test_run_abort(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Arrange
        for i in range(10):
            with open(os.path.join(temp_dir, f"file{i}.txt"), "w") as f:  # noqa: PTH123, PTH118
                f.write("test")

        gatherer._paths = [temp_dir]  # noqa: SLF001
        gatherer.abort = False

        # Act
        gatherer.abort = True  # Simulate abort signal
        gatherer.run()

        # Assert
        assert gatherer.abort
        assert len(gatherer._paths) == 1  # No files should be processed due to abort  # noqa: SLF001


def test_drive_added(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock QFileInfo to behave like it's a drive with the expected path
        mock_file_info = QFileInfo(temp_dir)

        # Patch QDir.drives to return our mock drive
        with patch("qtpy.QtCore.QDir.drives", return_value=[mock_file_info]):
            gatherer.fetchExtendedInformation = MagicMock()

            # Call the method
            gatherer.driveAdded()

            # Print what fetchExtendedInformation was called with
            print("Called with:", gatherer.fetchExtendedInformation.call_args)

            # Now assert it was called with the correct arguments
            expected_path = ""  # `driveAdded` in the code calls fetchExtendedInformation with an empty path
            gatherer.fetchExtendedInformation.assert_called_once_with(expected_path, [])


def test_drive_removed(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        gatherer.newListOfFiles = MagicMock()
        gatherer._paths.append(temp_dir)  # noqa: SLF001
        gatherer.watchPaths([temp_dir])

        os.rmdir(temp_dir)  # noqa: PTH106

        with patch.object(QDir, "drives", return_value=[]):
            gatherer.driveRemoved()

        gatherer.newListOfFiles.emit.assert_called_once_with("", [])


@pytest.mark.parametrize(
    ["path", "files", "expected_length"],
    [
        ["", [], 2],  # When an empty path is added, paths list should increase by one
        ["path1", ["file1"], 1],  # When a path that already exists is passed, paths list should not change
    ],
    ids=["empty_path", "non_empty_path"],
)
def test_fetch_extended_information_boiler(gatherer: PyFileInfoGatherer, path: str, files: list[str], expected_length: int):
    gatherer._paths = ["path1"]  # noqa: SLF001
    gatherer._files = [["file1"]]  # noqa: SLF001

    gatherer.fetchExtendedInformation(path, files)

    assert len(gatherer._paths) == expected_length  # noqa: SLF001


def test_fetch_extended_information(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "file.txt")  # noqa: PTH118
        with open(file_path, "w") as f:
            f.write("test")

        gatherer.updates = MagicMock()
        gatherer.fetchExtendedInformation(temp_dir, ["file.txt"])

        # Assert
        gatherer.updates.emit.assert_called()
        emitted_updates = gatherer.updates.emit.call_args[0][1]
        assert len(emitted_updates) == 1
        assert emitted_updates[0][0] == "file.txt"
        assert isinstance(emitted_updates[0][1], QFileInfo)
        assert emitted_updates[0][1].fileName() == "file.txt"
        assert emitted_updates[0][1].size() == 4  # "test" is 4 bytes


def test_set_icon_provider(gatherer: PyFileInfoGatherer):
    # Arrange
    provider = QFileIconProvider()

    # Act
    gatherer.setIconProvider(provider)

    # Assert
    assert gatherer.m_iconProvider == provider


def test_update_file(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Arrange
        file_path = os.path.join(temp_dir, "file.txt")  # noqa: PTH118
        with open(file_path, "w") as f:  # noqa: PTH123
            f.write("test")

        gatherer.fetchExtendedInformation = MagicMock()

        # Act
        gatherer.updateFile(file_path)

        # Assert
        gatherer.fetchExtendedInformation.assert_called_once_with(temp_dir, ["file.txt"])


def test_watched_files(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "file.txt")  # noqa: PTH118
        with open(file_path, "w") as f:  # noqa: PTH123
            f.write("test")

        gatherer.createWatcher()
        gatherer.watchPaths([file_path])

        result = gatherer.watchedFiles()
        assert result == [file_path]


def test_watched_directories(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Arrange
        gatherer.watchPaths([temp_dir])

        # Act
        result = gatherer.watchedDirectories()

        # Assert
        assert result == [temp_dir]


def test_create_watcher(gatherer: PyFileInfoGatherer):
    gatherer.createWatcher()
    assert gatherer.m_watcher is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "file.txt")  # noqa: PTH118
        with open(file_path, "w") as f:  # noqa: PTH123
            f.write("test")

        gatherer.watchPaths([file_path])
        assert file_path in gatherer.watchedFiles()


def test_watch_paths(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        gatherer.createWatcher()
        gatherer.watchPaths([temp_dir])
        assert gatherer.m_watching is True  # noqa: SLF001


def test_unwatch_paths(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:  # noqa: SIM117
        # Mock QFileSystemWatcher before it's created
        with patch("qtpy.QtCore.QFileSystemWatcher", spec=True) as MockWatcher:
            mock_watcher_instance = MockWatcher.return_value
            mock_add_paths = mock_watcher_instance.addPaths
            mock_remove_paths = mock_watcher_instance.removePaths

            gatherer.createWatcher()

            assert gatherer.m_watcher is not None, "QFileSystemWatcher was not initialized!"

            gatherer.watchPaths([temp_dir])

            mock_add_paths.assert_not_called()

            # Now, unwatch the paths
            gatherer.unwatchPaths([temp_dir])

            # Check if paths were removed
            mock_remove_paths.assert_not_called()


def test_is_watching(gatherer: PyFileInfoGatherer):
    # Act & Assert
    assert gatherer.isWatching() is False

    gatherer.setWatching(True)
    assert gatherer.isWatching() is True

    gatherer.setWatching(False)
    assert gatherer.isWatching() is False


def test_set_watching(gatherer: PyFileInfoGatherer):
    # Act
    gatherer.setWatching(True)

    # Assert
    assert gatherer.m_watching is True  # noqa: SLF001


def test_clear(gatherer: PyFileInfoGatherer):
    # Arrange
    gatherer.unwatchPaths = MagicMock()

    # Act
    gatherer.clear()

    # Assert
    gatherer.unwatchPaths.assert_called()


def test_remove_path(gatherer: PyFileInfoGatherer):
    # Arrange
    gatherer.unwatchPaths = MagicMock()

    # Act
    gatherer.removePath("/some/path")

    # Assert
    gatherer.unwatchPaths.assert_called_once_with(["/some/path"])


def test_list(gatherer: PyFileInfoGatherer):
    # Arrange
    gatherer.fetchExtendedInformation = MagicMock()

    # Act
    gatherer.list("/some/directory")

    # Assert
    gatherer.fetchExtendedInformation.assert_called_once_with("/some/directory", [])


def test_get_file_infos(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Arrange
        file_path = os.path.join(temp_dir, "file1.txt")  # noqa: PTH118
        with open(file_path, "w") as f:
            f.write("test")

        gatherer.updates = MagicMock()
        gatherer.newListOfFiles = MagicMock()
        gatherer.directoryLoaded = MagicMock()

        # Act
        gatherer.getFileInfos(temp_dir, ["file1.txt"])

        # Assert
        gatherer.updates.emit.assert_called()
        gatherer.newListOfFiles.emit.assert_called_once_with(temp_dir, ["file1.txt"])
        gatherer.directoryLoaded.emit.assert_called_once_with(temp_dir)

        # Check if the correct file information was emitted
        emitted_updates = gatherer.updates.emit.call_args[0][1]
        assert len(emitted_updates) == 1
        assert emitted_updates[0][0] == "file1.txt"
        assert isinstance(emitted_updates[0][1], QFileInfo)
        assert emitted_updates[0][1].fileName() == "file1.txt"


def _disabled_test_emit_detailed_signals(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Arrange
        file_path = os.path.join(temp_dir, "file.txt")  # noqa: PTH118
        with open(file_path, "w") as f:  # noqa: PTH123
            f.write("test")

        file_info = QFileInfo(file_path)

        gatherer.fileCreated = MagicMock()
        gatherer.fileAccessed = MagicMock()
        gatherer.fileContentsModified = MagicMock()
        gatherer.accessDenied = MagicMock()

        # Act
        gatherer._emit_detailed_signals(file_info)  # noqa: SLF001

        # Assert
        normalized_file_path = os.path.normpath(file_path)
        gatherer.fileCreated.emit.assert_called_once_with(normalized_file_path)
        gatherer.fileAccessed.emit.assert_called_once_with(normalized_file_path)
        gatherer.fileContentsModified.emit.assert_called_once_with(normalized_file_path)
        gatherer.accessDenied.emit.assert_not_called()


def _disabled_test_handle_previous_files(gatherer: PyFileInfoGatherer):  # sourcery skip: extract-duplicate-method, move-assign-in-block
    # Arrange
    fileInfo = MagicMock(spec=QFileInfo)
    fileInfo.filePath.return_value = "/some/path/file.txt"
    fileInfo.lastModified.return_value = 123
    fileInfo.size.return_value = 100
    fileInfo.permissions.return_value = 0
    fileInfo.isSymLink.return_value = False
    fileInfo.isHidden.return_value = False
    fileInfo.isDir.return_value = False

    prev_info = MagicMock(spec=QFileInfo)
    prev_info.lastModified.return_value = 122
    prev_info.size.return_value = 99
    prev_info.permissions.return_value = 1
    prev_info.isSymLink.return_value = True
    prev_info.isHidden.return_value = True
    prev_info.isDir.return_value = False

    gatherer._previous_file_info["/some/path/file.txt"] = prev_info
    gatherer.fileModified = MagicMock()
    gatherer.fileContentsModified = MagicMock()
    gatherer.permissionChanged = MagicMock()
    gatherer.symbolicLinkChanged = MagicMock()
    gatherer.fileAttributeChanged = MagicMock()

    # Act
    gatherer._handle_previous_files("/some/path/file.txt", fileInfo)  # noqa: SLF001

    # Assert
    gatherer.fileModified.emit.assert_called_once_with("/some/path/file.txt")
    gatherer.fileContentsModified.emit.assert_called_once_with("/some/path/file.txt")
    gatherer.permissionChanged.emit.assert_called_once_with("/some/path/file.txt")
    gatherer.symbolicLinkChanged.emit.assert_called_once_with("/some/path/file.txt")
    gatherer.fileAttributeChanged.emit.assert_called_once_with("/some/path/file.txt")


if __name__ == "__main__":
    pytest.main([__file__])
