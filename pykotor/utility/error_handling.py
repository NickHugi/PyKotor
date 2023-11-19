from __future__ import annotations

import inspect as ___inspect___
import sys as ___sys___
import traceback as ___traceback___
import types as ___types___


def universal_simplify_exception(e) -> tuple[str, str]:
    """Simplify exceptions into a standardized format
    Args:
        e: Exception - The exception to simplify
    Returns:
        error_name: str - The name of the exception
        error_message: str - A human-readable message for the exception
    Processing Logic:
    - Extract the exception name from the type
    - Handle specific exception types differently
      - FileNotFoundError uses filename attribute
      - PermissionError uses filename attribute
      - TimeoutError uses args[0]
      - InterruptedError uses errno attribute
      - ConnectionError uses request attribute if available
    - Try common exception attributes for a message
    - Return exception name and args joined as a string if no other info available.
    """
    error_name = type(e).__name__
    # Fallback: use the exception type name itself
    if not e.args:
        return error_name, repr(e)

    # Handle FileNotFoundError, which has 'filename' attribute
    if isinstance(e, FileNotFoundError):
        if len(e.args) > 1:
            return error_name, f"{e.args[1]}: {e.filename if hasattr(e, 'filename') else e.args[0]}"
        return error_name, f"Could not find the file: '{e.filename if hasattr(e, 'filename') else e.args[0]}'"

    # Handle PermissionError, which may have a 'filename' attribute
    if isinstance(e, PermissionError):
        return error_name, f"Permission Denied: {e.filename if hasattr(e, 'filename') else e.args[0]}"

    # Handle TimeoutError
    if isinstance(e, TimeoutError):
        return error_name, f"Operation timed out: {e.args[0]}"

    # Handle InterruptedError, which may have an 'errno' attribute
    if isinstance(e, InterruptedError):
        return error_name, f"Interrupted: {e.errno}"

    # Handle ConnectionError, which may have a 'request' attribute if it's from the `requests` library
    if isinstance(e, ConnectionError):
        return error_name, f"Connection Error: {getattr(e, 'request', lambda: {'method': e.args[0]})().get('method', '')}"

    # Add more oddball exception handling here as needed

    # Try commonly used attributes for human-readable messages
    for attr in ["strerror", "message", "reason", "filename", "filename1", "filename2"]:
        msg = getattr(e, attr, None)
        if msg:
            return error_name, f"{error_name}: {msg}"

    # Check if 'args' attribute has any information
    return error_name, repr(e)


def format_exception_with_variables(___etype___, ___value___, ___tb___, ___message___: str = "Assertion with Exception Trace") -> str:
    # Check if the arguments are of the correct type
    if not issubclass(___etype___, BaseException):
        msg = "___etype___ is not an exception class"
        raise TypeError(msg)
    if not isinstance(___value___, BaseException):
        msg = "___value___ is not an exception instance"
        raise TypeError(msg)
    if not isinstance(___tb___, ___types___.TracebackType):
        msg = "___tb___ is not a traceback object"
        raise TypeError(msg)

    # Construct the stack trace using traceback
    formatted_traceback = "".join(___traceback___.format_exception(___etype___, ___value___, ___tb___))

    # Capture the current stack trace
    ___frames___ = ___inspect___.getinnerframes(___tb___, context=5)

    # Get default module attributes to filter out built-ins
    ___default_attrs___: set[str] = set(dir(___sys___.modules["builtins"]))

    # Construct a detailed message with variables from all stack frames
    ___detailed_message___: list[str] = [
        f"{___message___}: Exception '{___value___}' of type '{___etype___}' occurred.",
        "Formatted Traceback:",
        formatted_traceback,
        "Stack Trace Variables:",
    ]
    for ___frame_info___ in ___frames___:
        (
            ___frame___,
            ___filename___,
            ___line_no___,
            ___function___,
            ___code_context___,
            ___index___,
        ) = ___frame_info___
        ___detailed_message___.append(f"\nFunction '{___function___}' at {___filename___}:{___line_no___}:")

        # Filter out built-in and imported names
        ___detailed_message___.extend(
            f"  {___var___} = {___val___!r}"
            for ___var___, ___val___ in ___frame___.f_locals.items()
            if ___var___ not in ___default_attrs___
            and ___var___ not in [
                "___var___",
                "___detailed_message___",
                "___message___",
                "___default_attrs___",
                "___frames___",
                "___filename___",
                "___line_no___",
                "___function___",
                "___frame_info___",
                "__builtins__",
                "___inspect___",
                "___sys___",
                "format_exception_with_variables",
                "___etype___",
                "___value___",
                "___tb___",
                "___index___",
                "___code_context___",
                "___frame___",
                "___traceback___",
                "___types___",
            ]
        )

    return "\n".join(___detailed_message___)


def assert_with_variable_trace(___condition___: bool, ___message___: str = "Assertion Failed"):
    if ___condition___:
        return
    # Capture the current stack trace
    ___frames___: list[___inspect___.FrameInfo] = ___inspect___.getouterframes(___inspect___.currentframe())

    # Get the line of code calling assert_with_variable_trace
    ___calling_frame_record___ = ___frames___[1]
    (
        ___unused_frame_type___,
        ___filename_errorhandler___,
        ___line_no___,
        ___unused_str_thing___,
        ___code_context___,
        ___unused_frame_type___,
    ) = ___calling_frame_record___
    ___line_of_code___ = ___code_context___[0].strip() if ___code_context___ else "Unknown condition"

    # Get default module attributes to filter out built-ins
    ___default_attrs___: set[str] = set(dir(___sys___.modules["builtins"]))

    # Construct a detailed message with variables from all stack frames
    ___detailed_message___: list[str] = [
        f"{___message___}: Expected condition '{___line_of_code___}' failed at {___filename_errorhandler___}:{___line_no___}.",
        "Stack Trace Variables:",
    ]
    for ___frame_info___ in ___frames___:
        (
            ___frame___,
            ___filename_errorhandler___,
            ___line_no___,
            ___function___,
            ___code_context___,
            ___unused_index___,
        ) = ___frame_info___
        ___detailed_message___.append(f"\nFunction '{___function___}' at {___filename_errorhandler___}:{___line_no___}:")

        # Filter out built-in and imported names
        ___detailed_message___.extend(
            f"  {var} = {val}"
            for var, val in ___frame___.f_locals.items()
            if var not in ___default_attrs___
            and var
            not in [
                "___detailed_message___",
                "___default_attrs___",
                "___line_of_code___",
                "___calling_frame_record___",
                "___code_context___",
                "___frames___",
                "___filename_errorhandler___",
                "___line_no___",
                "___function___",
                "___frame_info___",
                "__builtins__",
                "___inspect___",
                "___sys___",
                "assert_with_variable_trace",
                "___condition___",
                "___frame___",
                "___message___",
                "___value___",
                "___unused_str_thing___",
                "___unused_index___",
                "___unused_frame_type___",
            ]
        )
    full_message: str = "\n".join(___detailed_message___)

    # Raise an exception with the detailed message
    raise AssertionError(full_message)
