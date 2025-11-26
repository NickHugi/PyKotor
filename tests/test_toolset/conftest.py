import os
import pytest
import sys
import cProfile
import pstats
import signal
import time
from datetime import datetime
from pathlib import Path

# Set Qt API to PyQt5 (default) before any Qt imports
# qtpy will use this to select the appropriate bindings
if "QT_API" not in os.environ:
    os.environ["QT_API"] = "PyQt5"

# Force offscreen (headless) mode for Qt
# This ensures tests don't fail if no display is available (e.g. CI/CD)
# Must be set before any QApplication is instantiated.
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Paths
REPO_ROOT = Path(__file__).parents[2]
TOOLS_PATH = REPO_ROOT / "Tools"
LIBS_PATH = REPO_ROOT / "Libraries"

# Add Toolset src
TOOLSET_SRC = TOOLS_PATH / "HolocronToolset" / "src"
if str(TOOLSET_SRC) not in sys.path:
    sys.path.append(str(TOOLSET_SRC))

# Add KotorDiff src (needed for KotorDiffWindow)
KOTORDIFF_SRC = TOOLS_PATH / "KotorDiff" / "src"
if str(KOTORDIFF_SRC) not in sys.path:
    sys.path.append(str(KOTORDIFF_SRC))

# Add Libraries
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"
PYKOTORGL_PATH = LIBS_PATH / "PyKotorGL" / "src"

if str(PYKOTOR_PATH) not in sys.path:
    sys.path.append(str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.append(str(UTILITY_PATH))
if str(PYKOTORGL_PATH) not in sys.path:
    sys.path.append(str(PYKOTORGL_PATH))

from toolset.data.installation import HTInstallation
from toolset.main_settings import setup_pre_init_settings

# Module-level flag to ensure installation pre-warming happens only once
_installation_prewarmed = False

@pytest.fixture(scope="session")
def k1_path():
    path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
    if not path:
        pytest.skip("K1_PATH environment variable not set")
    return path

def _prewarm_installation(installation: HTInstallation) -> None:
    """Pre-warm installation cache to ensure expensive operations in _setup_installation
    are only performed once across all tests.
    
    This includes:
    - Caching 2DA files (ht_batch_cache_2da is idempotent, but we pre-warm for clarity)
    - Accessing stream resources (_streamwaves, _streamsounds, _streammusic) which triggers scanning
    """
    global _installation_prewarmed
    if _installation_prewarmed:
        return
    
    # Pre-warm 2DA caches for all editors that use _setup_installation
    # DLGEditor (K1)
    installation.ht_batch_cache_2da([
        HTInstallation.TwoDA_VIDEO_EFFECTS,
        HTInstallation.TwoDA_DIALOG_ANIMS,
    ])
    # DLGEditor (K2) and other editors
    installation.ht_batch_cache_2da([
        HTInstallation.TwoDA_EMOTIONS,
        HTInstallation.TwoDA_EXPRESSIONS,
        HTInstallation.TwoDA_VIDEO_EFFECTS,
        HTInstallation.TwoDA_DIALOG_ANIMS,
    ])
    
    # Pre-warm stream resources by accessing them once (triggers scanning, but only once)
    # This is the expensive operation that takes ~16 seconds
    _ = list(installation._streamwaves)  # noqa: SLF001
    _ = list(installation._streamsounds)  # noqa: SLF001
    _ = list(installation._streammusic)  # noqa: SLF001
    
    _installation_prewarmed = True

@pytest.fixture(scope="session")
def installation(k1_path):
    """Creates a shared HTInstallation instance for the session."""
    inst = HTInstallation(k1_path, "Test Installation", tsl=False)
    _prewarm_installation(inst)
    return inst

@pytest.fixture(scope="session", autouse=True)
def setup_settings():
    """Ensure settings are initialized before tests run."""
    setup_pre_init_settings()

# Global shared installation instance for unittest tests
from typing import Union
_shared_k1_installation: Union[HTInstallation, None] = None

# Profiling for conftest.py operations
_conftest_profiler: Union[cProfile.Profile, None] = None

def _rotate_prof_files(prof_dir: Path, keep_count: int = 50) -> None:
    """Rotate prof files, keeping only the most recent ones.
    
    Args:
        prof_dir: Directory containing prof files
        keep_count: Number of most recent prof files to keep (default: 50)
    """
    prof_files = sorted(prof_dir.glob("*.prof"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Remove files beyond the keep_count limit
    for old_file in prof_files[keep_count:]:
        try:
            old_file.unlink()
            print(f"Rotated (deleted) old prof file: {old_file.name}")
        except OSError:
            pass  # File might have been deleted already

def pytest_configure(config):
    """Pre-warm installation cache before any tests run.
    
    This hook runs very early in the pytest lifecycle, before test collection.
    We create and pre-warm a shared installation instance that unittest tests can use.
    """
    global _shared_k1_installation, _conftest_profiler
    
    # Start profiling conftest operations
    _conftest_profiler = cProfile.Profile()
    _conftest_profiler.enable()
    start_time = time.time()
    
    try:
        k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
        if k1_path and os.path.exists(k1_path):
            _shared_k1_installation = HTInstallation(k1_path, "Shared Test Installation", tsl=False)
            _prewarm_installation(_shared_k1_installation)
    finally:
        _conftest_profiler.disable()
        duration = time.time() - start_time
        
        # Only save prof file if execution took 30+ seconds
        if duration >= 30.0:
            # Create flat cProfile directory structure
            conftest_path = Path(__file__)
            tests_root = conftest_path.parents[1]  # tests/
            prof_dir = tests_root / "cProfile"
            prof_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prof_file = prof_dir / f"conftest_{timestamp}.prof"
            _conftest_profiler.dump_stats(str(prof_file))
            print(f"\nConftest profiling saved to {prof_file} (duration: {duration:.2f}s)")
            
            # Rotate old prof files (keep only last 50)
            _rotate_prof_files(prof_dir)

def get_shared_k1_installation() -> Union[HTInstallation, None]:
    """Get the shared pre-warmed K1 installation instance for unittest tests."""
    return _shared_k1_installation

@pytest.fixture(scope="session")
def test_files_dir():
    """Returns the path to the test files directory."""
    path = Path(__file__).parent / "test_files"
    if not path.exists():
        # Fallback to pykotor test files if toolset one doesn't exist or is empty
        # But prefer toolset one as it has baragwin.uti
        # Assuming the user has these files present as they attached them.
        pass
    return path

@pytest.fixture
def mock_installation(mocker):
    """Creates a mock HTInstallation for tests that don't need a real one."""
    mock = mocker.MagicMock(spec=HTInstallation)
    mock.name = "Mock Installation"
    mock.tsl = False
    mock.path.return_value = Path("/mock/path")
    return mock

# Profiling setup
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """
    Profile the test execution.
    Only creates .prof files if execution time is 30+ seconds.
    """
    profiler = cProfile.Profile()
    start_time = time.time()
    
    def signal_handler(sig, frame):
        print(f"\nCaught signal {sig}, dumping profile stats...")
        profiler.disable()
        duration = time.time() - start_time
        
        # Always save interrupted prof files regardless of duration
        # Create flat cProfile directory structure
        conftest_path = Path(__file__)
        tests_root = conftest_path.parents[1]  # tests/
        prof_dir = tests_root / "cProfile"
        prof_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats = pstats.Stats(profiler).sort_stats('cumtime')
        stats.print_stats(50)
        prof_file = prof_dir / f"{item.name}_interrupted_{timestamp}.prof"
        stats.dump_stats(str(prof_file))
        print(f"Profile saved to {prof_file} (duration: {duration:.2f}s)")
        
        # Restore original handler and re-raise or exit
        signal.signal(signal.SIGINT, original_handler)
        sys.exit(1)

    # Save original handler
    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        signal.signal(signal.SIGINT, original_handler)
        
        duration = time.time() - start_time
        
        # Only create .prof file if execution took 30+ seconds
        if duration >= 30.0:
            # Create flat cProfile directory structure
            conftest_path = Path(__file__)
            tests_root = conftest_path.parents[1]  # tests/
            prof_dir = tests_root / "cProfile"
            prof_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prof_file = prof_dir / f"{item.name}_{timestamp}.prof"
            stats = pstats.Stats(profiler).sort_stats('cumtime')
            print(f"\nProfile stats for {item.name} (duration: {duration:.2f}s):")
            stats.print_stats(20)
            stats.dump_stats(str(prof_file))
            print(f"Profile saved to {prof_file}")
            
            # Rotate old prof files (keep only last 50)
            _rotate_prof_files(prof_dir)
        else:
            # Still print stats for debugging, but don't save file
            stats = pstats.Stats(profiler).sort_stats('cumtime')
            print(f"\nProfile stats for {item.name} (duration: {duration:.2f}s, not saved - < 30s):")
            stats.print_stats(20)
