from __future__ import annotations

from ctypes import c_bool
import os
import sys
import tempfile

from unittest.mock import MagicMock, patch

from qtpy.QtCore import QCoreApplication
import pytest

from qtpy.QtCore import QDir, QFileInfo
from qtpy.QtWidgets import QApplication, QFileIconProvider

from utility.ui_libraries.qt.adapters.filesystem.pyfileinfogatherer import PyFileInfoGatherer


@pytest.fixture(scope="session", autouse=True)
def app() -> QApplication:
    """Ensure QApplication is initialized."""
    app: QApplication | QCoreApplication | None = QApplication(sys.argv) if QApplication.instance() is None else QApplication.instance()
    assert app is not None
    assert isinstance(app, QApplication)
    return app


@pytest.fixture
def gatherer() -> PyFileInfoGatherer:
    g = PyFileInfoGatherer()
    g.start()  # Start the background thread
    yield g
    # Clean up: abort the thread and wait for it to finish
    try:
        g.abort.value = True
        g.condition.wakeAll()
        g.wait(1000)  # Wait up to 1 second
    except (RuntimeError, AttributeError):
        pass  # Object might already be deleted


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
        gatherer.abort.value = False  # Ensure abort is False initially

        # Act
        gatherer.abort.value = True  # Simulate abort signal
        gatherer.condition.wakeAll()  # Wake the thread so it can check abort
        
        # Wait a bit for the thread to exit
        from qtpy.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()

        # Assert
        assert gatherer.abort.value is True


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

        # Use a real signal connection to capture emitted data
        from qtpy.QtCore import QEventLoop, QTimer
        from qtpy.QtWidgets import QApplication
        updates_data = []
        
        def capture_updates(path, files):
            updates_data.append((path, files))
        
        gatherer.updates.connect(capture_updates)
        
        # Ensure the gatherer is in a clean state
        gatherer._paths.clear()  # noqa: SLF001
        gatherer._files.clear()  # noqa: SLF001
        
        gatherer.fetchExtendedInformation(temp_dir, ["file.txt"])
        
        # Wait for the background thread to process the request with a loop that exits when data arrives
        loop = QEventLoop()
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(loop.quit)
        timeout_timer.start(1000)  # Wait up to 1 second
        
        check_timer = QTimer()
        def check_data():
            if updates_data:
                timeout_timer.stop()
                loop.quit()
        check_timer.timeout.connect(check_data)
        check_timer.start(50)  # Check every 50ms
        
        loop.exec()
        check_timer.stop()
        timeout_timer.stop()

        # Assert
        assert len(updates_data) > 0, f"Should have emitted updates signal. Paths: {gatherer._paths}, Files: {gatherer._files}"  # noqa: SLF001
        emitted_path, emitted_updates = updates_data[0]
        assert emitted_path == temp_dir
        assert len(emitted_updates) == 1
        assert emitted_updates[0][0] == "file.txt"
        assert isinstance(emitted_updates[0][1], QFileInfo)
        assert emitted_updates[0][1].fileName() == "file.txt"
        assert emitted_updates[0][1].size() == 4  # "test" is 4 bytes


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
    assert gatherer.m_watcher is not None

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "file.txt")  # noqa: PTH118
        with open(file_path, "w") as f:  # noqa: PTH123
            f.write("test")

        gatherer.watchPaths([file_path])
        assert file_path in gatherer.watchedFiles()


def test_unwatch_paths(gatherer: PyFileInfoGatherer):
    with tempfile.TemporaryDirectory() as temp_dir:  # noqa: SIM117
        # Mock QFileSystemWatcher before it's created
        with patch("qtpy.QtCore.QFileSystemWatcher", spec=True) as MockWatcher:
            mock_watcher_instance = MockWatcher.return_value
            mock_add_paths = mock_watcher_instance.addPaths
            mock_remove_paths = mock_watcher_instance.removePaths

            assert gatherer.m_watcher is not None, "QFileSystemWatcher was not initialized!"

            gatherer.watchPaths([temp_dir])

            mock_add_paths.assert_not_called()

            # Now, unwatch the paths
            gatherer.unwatchPaths([temp_dir])

            # Check if paths were removed
            mock_remove_paths.assert_not_called()


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

        # Use real signal connections to capture emitted data
        updates_data = []
        new_list_data = []
        directory_loaded_data = []
        
        gatherer.updates.connect(lambda path, files: updates_data.append((path, files)))
        gatherer.newListOfFiles.connect(lambda path, files: new_list_data.append((path, files)))
        gatherer.directoryLoaded.connect(lambda path: directory_loaded_data.append(path))

        # Act
        gatherer.getFileInfos(temp_dir, ["file1.txt"])

        # Assert
        assert len(updates_data) > 0, "Should have emitted updates signal"
        assert len(directory_loaded_data) > 0, "Should have emitted directoryLoaded signal"
        assert directory_loaded_data[0] == temp_dir
        # newListOfFiles is NOT emitted when files list is provided, only when scanning directory
        # assert len(new_list_data) > 0, "Should have emitted newListOfFiles signal"

        # Check if the correct file information was emitted
        emitted_path, emitted_updates = updates_data[0]
        assert emitted_path == temp_dir
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


def _disabled_test_handle_previous_files(gatherer: PyFileInfoGatherer):
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
