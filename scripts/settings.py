# scripts/settings.py
# Allows easy importing of the pykotor library for end user convenience
import sys
from pathlib import Path

import pkg_resources

# whether to use the PIP pykotor package or the local folder in project root (./scripts/../pykotor). If set to None, will use default behavior.
PYKOTOR_LIBRARY_LOOKUP = "pip"  # set to either "pip", "local", or None.
SHOW_DEBUG_OUTPUT = False


def setup_environment():
    project_root_dir = Path(__file__).parent.parent.resolve()
    local_pykotor_dir = project_root_dir / "pykotor"
    pip_pykotor_dir = None

    if SHOW_DEBUG_OUTPUT:
        print("Project root:", project_root_dir)
        print("pykotor local library dir:", local_pykotor_dir) if local_pykotor_dir.exists() else None

        try:
            distribution = pkg_resources.get_distribution("pykotor")
            pip_pykotor_dir = distribution.location
            print(f"The pip package 'pykotor' is located at '{pip_pykotor_dir}'")
        except pkg_resources.DistributionNotFound:
            print("The pip package 'pykotor' is not installed.")

    if PYKOTOR_LIBRARY_LOOKUP == "pip":
        if str(project_root_dir) in sys.path:
            sys.path.remove(str(project_root_dir))

        # Try to import pykotor from pip installations
        try:
            import pykotor
        except ImportError as e:
            # If import fails, revert to local pykotor
            if local_pykotor_dir.exists() and str(project_root_dir) not in sys.path:
                sys.path.insert(0, str(project_root_dir))
            else:
                msg = f"No local pykotor found in expected directory: {local_pykotor_dir} and no pip package installed."
                raise ImportError(msg) from e

    elif PYKOTOR_LIBRARY_LOOKUP == "local":
        if local_pykotor_dir.exists():
            if str(project_root_dir) not in sys.path:
                sys.path.insert(0, str(project_root_dir))
        else:
            msg = f"No local pykotor found in expected directory: {local_pykotor_dir}"
            raise ImportError(msg)

    elif PYKOTOR_LIBRARY_LOOKUP is None:
        # Default behavior: Prefer local, then fallback to pip.
        if local_pykotor_dir.exists() and str(project_root_dir) not in sys.path:
            sys.path.insert(0, str(project_root_dir))
    else:
        msg = f"Invalid value for PYKOTOR_LIBRARY_LOOKUP: '{PYKOTOR_LIBRARY_LOOKUP}'. It should be 'pip', 'local', or None."
        raise ValueError(msg)

    # Check if pykotor can be imported
    try:
        import pykotor  # noqa: F811, F401
    except ImportError as exc:
        msg = "No valid pykotor source found. Ensure local pykotor exists or set PYKOTOR_LIBRARY_LOOKUP appropriately."
        raise ImportError(msg) from exc
