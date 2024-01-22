from __future__ import annotations

import inspect
import sys
import traceback
import types
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from typing_extensions import Literal


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

    err_str = str(e)
    args = getattr(e, "args", [])
    if args and isinstance(args, list):
        err_msg_index: int | Literal[False] = err_str in args and args.index(err_str)
        if err_msg_index:
            del args[err_msg_index]
        if args:
            err_str += "\n  Information:"
            for arg in args:
                err_str += f"\n    {arg}"
    return error_name, err_str

ignore_attrs: set[str] = {
    "__file__",
    "__cached__",
    "__builtins__",
}

def format_exception_with_variables(
    value: BaseException,
    etype: type[BaseException] | None = None,
    tb: types.TracebackType | None = None,
    message: str = "Assertion with Exception Trace",
) -> str:
    etype = etype if etype is not None else type(value)
    tb = tb if tb is not None else value.__traceback__

    # Check if the arguments are of the correct type
    if not issubclass(etype, BaseException):
        msg = f"{etype!r} is not an exception class"
        raise TypeError(msg)
    if not isinstance(value, BaseException):
        msg = f"{value!r} is not an exception instance"
        raise TypeError(msg)
    if not isinstance(tb, types.TracebackType):
        msg = "tb is not a traceback object"
        raise TypeError(msg)

    # Construct the stack trace using traceback
    formatted_traceback: str = "".join(traceback.format_exception(etype, value, tb))

    # Capture the current stack trace
    frames: list[inspect.FrameInfo] = inspect.getinnerframes(tb, context=5)

    # Get default module attributes to filter out built-ins
    default_attrs: set[str] = set(dir(sys.modules["builtins"]))

    # Construct a detailed message with variables from all stack frames
    detailed_message: list[str] = [
        f"{message}: Exception '{value}' of type '{etype}' occurred.",
        "Formatted Traceback:",
        formatted_traceback,
        "Stack Trace Variables:",
    ]
    for frame_info in frames:
        (
            frame,
            filename,
            line_no,
            function,
            code_context,
            index,
        ) = frame_info
        code_context = ""  # type: ignore[assignment]
        #code_context = f"\nContext [{', '.join(code_context)}] " if code_context else ""  # type: ignore[assignment]
        detailed_message.append(f"\nFunction '{function}' at {filename}:{line_no}:{code_context}")

        # Filter out built-in and imported names
        for var, val in frame.f_locals.items():
            if var in default_attrs:
                continue
            if var in ignore_attrs:
                continue
            if sys.getsizeof(val) >= 10240:  # vars over 10KB shouldn't be logged  # noqa: PLR2004
                continue
            try:
                val_repr = repr(val)
            except Exception as e2:  # noqa: BLE001
                try:
                    val_str = str(val)
                except Exception as e3:  # noqa: BLE001
                    val_str = f"<Error in str({var}): {e3}"
                val_repr = f"<Error in repr({var}) (contents: {val_str}): {e2}>"

            detailed_message.append(f"  {var} = {val_repr}")

    return "\n".join(detailed_message)


def assert_with_variable_trace(condition: bool, message: str = "Assertion Failed"):
    if condition:
        return
    # Capture the current stack trace
    frames: list[inspect.FrameInfo] = inspect.getouterframes(inspect.currentframe())

    # Get the line of code calling assert_with_variable_trace
    calling_frame_record: inspect.FrameInfo = frames[1]
    (
        frame,
        filename,
        line_no,
        function,
        code_context,
        frame_type,
    ) = calling_frame_record
    line_of_code = code_context[0].strip() if code_context else "Unknown condition"

    # Get default module attributes to filter out built-ins
    default_attrs: set[str] = set(dir(sys.modules["builtins"]))

    # Construct a detailed message with variables from all stack frames
    detailed_message: list[str] = [
        f"{message}: Expected condition '{line_of_code}' failed at {filename}:{line_no}.",
        "Stack Trace Variables:",
    ]
    for frame_info in frames:
        (
            frame,
            filename,
            line_no,
            function,
            code_context,
            frame_type,
        ) = frame_info

        code_context = ""  # type: ignore[assignment]
        #code_context = f"\nContext [{', '.join(code_context)}] " if code_context else ""  # type: ignore[assignment]
        detailed_message.append(f"\nFunction '{function}' at {filename}:{line_no}:{code_context}")

        # Filter out built-in and imported names
        for var, val in frame.f_locals.items():
            if var in default_attrs:
                continue
            if var in ignore_attrs:
                continue
            if sys.getsizeof(val) >= 10240:  # vars over 10KB shouldn't be logged  # noqa: PLR2004
                continue
            try:
                val_repr = repr(val)
            except Exception as e2:  # noqa: BLE001
                try:
                    val_str = str(val)
                except Exception as e3:  # noqa: BLE001
                    val_str = f"<Error in str({var}): {e3}"
                val_repr = f"<Error in repr({var}) (contents: {val_str}): {e2}>"

            detailed_message.append(f"  {var} = {val_repr}")

    full_message: str = "\n".join(detailed_message)

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
                frames: list[inspect.FrameInfo] = inspect.getouterframes(inspect.currentframe())

                # Get default module attributes to filter out built-ins
                default_attrs = set(dir(sys.modules["builtins"]))

                # Construct a detailed message with variables from all stack frames
                detailed_message: list[str] = [
                    f"Exception caught in function '{f.__name__}': {universal_simplify_exception(e)}",
                    "Stack Trace Variables:",
                ]
                for frame_info in frames:
                    (
                        frame,
                        filename,
                        line_no,
                        function,
                        code_context,
                        frame_type,
                    ) = frame_info
                    if function != f.__name__:
                        continue

                    code_context = ""  # type: ignore[assignment]
                    #code_context = f"\nContext [{', '.join(code_context)}] " if code_context else ""  # type: ignore[assignment]
                    detailed_message.append(f"\nFunction '{function}' at {filename}:{line_no}:{code_context}")
                    # Filter out built-in and imported names
                    for var, val in frame.f_locals.items():
                        if var in default_attrs:
                            continue
                        if var in ignore_attrs:
                            continue
                        if sys.getsizeof(val) >= 10240:  # vars over 10KB shouldn't be logged  # noqa: PLR2004
                            continue
                        try:
                            val_repr = repr(val)
                        except Exception as e2:  # noqa: BLE001
                            try:
                                val_str = str(val)
                            except Exception as e3:  # noqa: BLE001
                                val_str = f"<Error in str({var}): {e3}"
                            val_repr = f"<Error in repr({var}) (contents: {val_str}): {e2}>"

                        detailed_message.append(f"  {var} = {val_repr}")
                full_message: str = "\n".join(detailed_message)

                if action == "stderr":
                    print(full_message, sys.stderr)  # noqa: T201
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
