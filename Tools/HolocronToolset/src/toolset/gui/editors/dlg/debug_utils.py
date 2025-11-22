from __future__ import annotations

import inspect
from typing import Any, Literal

from utility.error_handling import safe_repr


def detailed_extra_info(obj) -> str:
    """Custom function to provide additional details about objects in the graph."""
    try:
        return safe_repr(obj)
    except AttributeError:
        return str(obj)


def custom_extra_info(obj) -> str:
    """Generate a string representation of the object with additional details."""
    return f"{obj.__class__.__name__} id={id(obj)}"


def is_interesting(obj) -> bool:
    """Filter to decide if the object should be included in the graph."""
    # Customize based on the types or characteristics of interest
    return hasattr(obj, "__dict__") or isinstance(obj, (list, dict, set))


def identify_reference_path(obj, max_depth=10):
    """Display a graph of back references for the given target_object,
    focusing on the most likely sources of strong references.
    """
    import objgraph  # pyright: ignore[reportMissingTypeStubs]
    # Define a predicate that returns True for all objects
    def predicate(*__args: Any, **__kwargs: Any) -> Literal[True]:
        return True

    # Find back reference chains leading to 'obj'
    paths = objgraph.find_backref_chain(obj, predicate, max_depth=max_depth)

    # Ensure that paths is a list of lists, even if only one chain is found
    if not paths:  # If no paths found, paths will be just [obj]
        paths = [[obj]]
    elif not isinstance(paths[0], list):  # If single chain found not wrapped in a list
        paths = [paths]

    for path in paths:
        print("Reference Path:")
        for ref in path:
            ref_type = type(ref).__name__
            ref_id = id(ref)
            ref_info = f"Type={ref_type}, ID={ref_id}"

            # Try to get more information about the object's definition
            try:
                if hasattr(ref, "__name__"):
                    ref_info += f", Name={ref.__name__}"
                if hasattr(ref, "__module__"):
                    ref_info += f", Module={ref.__module__}"

                # Source file and line number
                # We can only retrieve source info for function objects
                if inspect.isfunction(ref) or inspect.ismethod(ref):
                    source = inspect.getsourcefile(ref) or "Not available"
                    if source != "Not available":
                        lines, line_no = inspect.getsourcelines(ref)
                        ref_info += f", Defined at {source}:{line_no}"
                    else:
                        ref_info += ", Source not available"
                else:
                    ref_info += ", Source info not applicable"
            except Exception as e:  # noqa: BLE001
                ref_info += f", Detail unavailable ({e!s})"

            print(ref_info)
        print("\n")


def debug_references(obj: Any):
    identify_reference_path(obj)

