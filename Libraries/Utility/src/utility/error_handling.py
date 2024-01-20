from __future__ import annotations

import inspect as ___inspect___
import sys as ___sys___
import traceback as ___traceback___
import types as ___types___
from pathlib import Path
from typing import Callable, TypeVar


def universal_simplify_exception(e: BaseException) -> tuple[str, str]:
    """Simplify exceptions into a standardized format.

    Args:
    ----
        e: Exception - The exception to simplify

    Returns:
    -------
        error_name: str - The name of the exception
        error_message: str - A human-readable message for the exception

    Processing Logic:
    ----------------
        - Extract the exception name from the type
        - Handle specific exception types differently
        - Try common exception attributes for a message
        - Return a general fallback if nothing else better was determined.
    """
    error_name: str = type(e).__name__

    # Handle FileNotFoundError, which has 'filename' attribute
    if isinstance(e, FileNotFoundError):
        if len(e.args) > 1:
            return error_name, f"{e.args[1]}: {e.args[0]}"
        if hasattr(e, "filename"):
            return error_name, f"Could not find the file: '{e.filename}'"
        if len(e.args) == 1:
            return error_name, f"Could not find the file: '{e.args[0]}'"

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
            return error_name, f"{e}: {msg}"

    return error_name, str(e) + str(getattr(e, "args", ""))


def format_exception_with_variables(
    ___value___: BaseException,
    ___etype___: type[BaseException] | None = None,
    ___tb___: ___types___.TracebackType | None = None,
    ___message___: str = "Assertion with Exception Trace",
) -> str:
    ___etype___ = ___etype___ if ___etype___ is not None else type(___value___)
    ___tb___ = ___tb___ if ___tb___ is not None else ___value___.__traceback__

    # Check if the arguments are of the correct type
    if not issubclass(___etype___, BaseException):
        msg = f"{___etype___!r} is not an exception class"
        raise TypeError(msg)
    if not isinstance(___value___, BaseException):
        msg = f"{___value___!r} is not an exception instance"
        raise TypeError(msg)
    if not isinstance(___tb___, ___types___.TracebackType):
        msg = "___tb___ is not a traceback object"
        raise TypeError(msg)

    # Construct the stack trace using traceback
    ___formatted_traceback___: str = "".join(___traceback___.format_exception(___etype___, ___value___, ___tb___))

    # Capture the current stack trace
    ___frames___: list[___inspect___.FrameInfo] = ___inspect___.getinnerframes(___tb___, context=5)

    # Get default module attributes to filter out built-ins
    ___default_attrs___: set[str] = set(dir(___sys___.modules["builtins"]))

    # Construct a detailed message with variables from all stack frames
    ___detailed_message___: list[str] = [
        f"{___message___}: Exception '{___value___}' of type '{___etype___}' occurred.",
        "Formatted Traceback:",
        ___formatted_traceback___,
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
        ___code_context___ = f"\nContext [{', '.join(___code_context___)}] " if ___code_context___ else ""  # type: ignore[assignment]
        ___detailed_message___.append(f"\nFunction '{___function___}' at {___filename___}:{___line_no___}:{___code_context___}")

        # Filter out built-in and imported names
        ___detailed_message___.extend(
            f"  {___var___} = {___val___!r}"
            for ___var___, ___val___ in ___frame___.f_locals.items()
            if ___var___ not in ___default_attrs___
            and ___sys___.getsizeof(___val___) <= 10240  # vars over 10KB shouldn't be logged  # noqa: PLR2004
            and ___var___ not in {
                "___var___",
                "___detailed_message___",
                "___formatted_traceback___",
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
            }
        )

    return "\n".join(___detailed_message___)


def assert_with_variable_trace(___condition___: bool, ___message___: str = "Assertion Failed"):
    if ___condition___:
        return
    # Capture the current stack trace
    ___frames___: list[___inspect___.FrameInfo] = ___inspect___.getouterframes(___inspect___.currentframe())

    # Get the line of code calling assert_with_variable_trace
    ___calling_frame_record___: ___inspect___.FrameInfo = ___frames___[1]
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

        ___code_context___ = f"\nContext [{', '.join(___code_context___)}] " if ___code_context___ else ""  # type: ignore[assignment]
        ___detailed_message___.append(f"\nFunction '{___function___}' at {___filename_errorhandler___}:{___line_no___}:{___code_context___}")

        # Filter out built-in and imported names
        ___detailed_message___.extend(
            f"  {var} = {___val___}"
            for var, ___val___ in ___frame___.f_locals.items()
            if var not in ___default_attrs___
            and ___sys___.getsizeof(___val___) <= 10240  # vars over 10KB shouldn't be logged  # noqa: PLR2004
            and var not in [
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

RT = TypeVar("RT")
unique_sentinel = object()
def with_variable_trace(
    exception_types: type[Exception] | tuple[type[Exception], ...] = Exception,
    return_type: type[RT] = unique_sentinel,  # type: ignore[reportGeneralTypeIssues, assignment]
    action="log",
) -> Callable[[Callable[..., RT]], Callable[..., RT | None]]:
    # Set default to Exception if no specific types are provided
    if not exception_types:
        exception_types = (Exception,)
    if not isinstance(exception_types, tuple):
        exception_types = (exception_types,)
    exception_types = (*exception_types, AssertionError)

    def decorator(f: Callable[..., RT]) -> Callable[..., RT | None]:
        def wrapper(*args, **kwargs) -> RT | None:
            try:
                result: RT = f(*args, **kwargs)
                if return_type is not unique_sentinel and not isinstance(result, return_type):
                    raise AssertionError(f"Return type of '{f.__name__}' must be {return_type.__name__}, got {type(result)}: {result!r}: {result}")
            except exception_types as e:
                # Capture the current stack trace
                ___frames___: list[___inspect___.FrameInfo] = ___inspect___.getouterframes(___inspect___.currentframe())

                # Get default module attributes to filter out built-ins
                ___default_attrs___ = set(dir(___sys___.modules["builtins"]))

                # Construct a detailed message with variables from all stack frames
                ___detailed_message___: list[str] = [
                    f"Exception caught in function '{f.__name__}': {universal_simplify_exception(e)}",
                    "Stack Trace Variables:",
                ]
                for ___frame_info___ in ___frames___:
                    ___frame___, ___filename___, ___line_no___, ___function___, ___code_context___, _ = ___frame_info___
                    if ___function___ != f.__name__:
                        continue

                    ___code_context___ = f"\nContext [{', '.join(___code_context___)}] " if ___code_context___ else ""  # type: ignore[assignment]
                    ___detailed_message___.append(f"\nFunction '{___function___}' at {___filename___}:{___line_no___}:{___code_context___}")

                    # Filter out built-in and imported names
                    ___detailed_message___.extend(
                        f"  {var} = {___val___}"
                        for var, ___val___ in ___frame___.f_locals.items()
                        if var not in ___default_attrs___
                        and ___sys___.getsizeof(___val___) <= 10240  # vars over 10KB shouldn't be logged  # noqa: PLR2004
                        and var not in [
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
                            "with_variable_trace",
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

                if action == "stderr":
                    print(full_message, ___sys___.stderr)  # noqa: T201
                elif action == "print":
                    print(full_message)  # noqa: T201
                elif action == "log":
                    with Path("errorlog.txt").open("w") as outfile:
                        outfile.write(full_message)
                elif action == "raise":
                    raise Exception(full_message) from None

                return None
            else:
                return result

        return wrapper
    return decorator
