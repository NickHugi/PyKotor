from __future__ import annotations

from contextvars import ContextVar
import inspect
import os
import sys
import traceback
import types

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

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
    error_name: str = e.__class__.__name__

    # Handle FileNotFoundError, which has 'filename' attribute
    if isinstance(e, FileNotFoundError):
        filename = getattr(e, "filename", getattr(e, "filename2", None))
        if filename:
            return error_name, f"Could not find the file: '{filename}'"
        if len(e.args) == 1:
            return error_name, f"Could not find the file: '{e.args[0]}'"
        if len(e.args) > 1:
            return error_name, f"{e.args[1]}: {e.args[0]}"

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

    error_messages = [f"- {attr}: {getattr(e, attr)}" for attr in ["strerror", "filename", "filename1", "filename2", "message", "reason"] if getattr(e, attr, None)]
    if error_messages:
        error_details = "\n".join(error_messages)
        return error_name, f"{e}:\n\nDetails:\n{error_details}"

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

# Get default module attributes to filter out built-ins
default_attrs: set[str] = set(dir(sys.modules["builtins"]))

ignore_attrs: set[str] = {
    "__file__",
    "__cached__",
    "__builtins__",
}


class CustomAssertionError(AssertionError):
    def __init__(self, *args, **kwargs):
        self.message: str = kwargs.get("message", args[0])
        super().__init__(*args, **kwargs)

_currently_processing: ContextVar[set] = ContextVar("_currently_processing", default=set())
def safe_repr(obj: Any, max_length: int = 200, indent_level: int = 0) -> str:
    """Safely generate a repr string for objects without a custom __repr__, with line wrapping and indentation."""
    # Retrieve the current set of object ids being processed
    current_set = _currently_processing.get()
    obj_id = id(obj)
    if obj_id in current_set:
        return f"<...recursion of {obj.__class__.__name__}...>"

    # Add the current object id to the set
    current_set.add(obj_id)
    _currently_processing.set(current_set)  # Update the context variable with the modified set

    indent = "    "  # Define the indentation unit (4 spaces).
    try:
        if hasattr(obj, "__class__") and obj.__class__.__repr__ is not object.__repr__:
            # Call the object's __repr__ with _is_safe_repr_call set to True
            try:
                return repr(obj)
            except Exception:  # noqa: BLE001
                # Fallback to the base object __repr__ if an error occurs
                return object.__repr__(obj)
        attrs: list[str] = []
        base_indent = indent * indent_level
        next_indent = indent * (indent_level + 1)
        for attr_name in dir(obj):
            attr_value = getattr(obj, attr_name)
            if not attr_name.startswith("__") and not callable(attr_value):
                try:
                    this_repr = safe_repr(attr_value, max_length, indent_level + 1)
                    # Concatenate attribute name and its representation with appropriate indentation
                    attr_repr = f"{attr_name}={this_repr}"
                        # Check if current attribute representation exceeds the max length
                    if len(attr_repr) > max_length:
                        attr_repr = f"{attr_repr[:max_length]}..."
                    attrs.append(attr_repr)
                except Exception:  # noqa: BLE001
                    attrs.append(f"{attr_name}={object.__repr__(attr_value)}")  # Use repr(obj) as a fallback
        # Join attributes with a comma and a space, and apply next-level indentation
        joined_attrs = (",\n" + next_indent).join(attrs)
    except Exception:  # noqa: BLE001
        # Fallback to the base object __repr__ if an error occurs
        return object.__repr__(obj)
    else:
        return f"{obj.__class__.__name__}(\n{next_indent}{joined_attrs}\n{base_indent})"

def format_var_str(
    var: str,
    val: Any,
    max_length: int = 512,
) -> str | None:
    """Format variable and its value into a string, handling exceptions and length."""
    if var in default_attrs or var in ignore_attrs:
        return None

    val_repr: str | object
    val_str: str | object
    exc = None
    unique_sentinel = object()
    try:
        val_str = str(val)
        if len(val_str) > max_length:
            val_str = f"{val_str[:max_length]}...<truncated>"
    except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
        val_str = unique_sentinel
        exc = e

    try:
        val_repr = safe_repr(val)
        if len(val_repr) > max_length*2:
            val_repr = f"{val_repr[:max_length]}...<truncated>"
    except Exception:  # pylint: disable=W0718  # noqa: BLE001
        val_repr = unique_sentinel

    display_value: str | object = val_repr
    if display_value is unique_sentinel:
        display_value = val_str
    if display_value is unique_sentinel:
        display_value = f"<Error in repr({var}): {exc}>"

    return f"  {var} = {display_value}"


def format_frame_info(frame_info: inspect.FrameInfo) -> list[str]:
    """Extract and format information from a frame."""
    (
        frame,
        filename,
        line_no,
        function,
        code_context,
        index,
    ) = frame_info
    code_context = ""  # type: ignore[assignment]
    # code_context = f"\nContext [{', '.join(code_context)}] " if code_context else ""  # type: ignore[assignment]
    detailed_message: list[str] = [f"\nFunction '{function}' at {filename}:{line_no}:{code_context}"]
    for var, val in frame.f_locals.items():
        formatted_var: str | None = format_var_str(var, val)
        if formatted_var:
            detailed_message.append(formatted_var)
    return detailed_message


def format_exception_with_variables(
    value: BaseException,
    etype: type[BaseException] | None = None,
    tb: types.TracebackType | None = None,
    message: str = "",
) -> str:
    etype = etype if etype is not None else value.__class__
    tb = tb if tb is not None else value.__traceback__

    # Check if the arguments are of the correct type
    if not issubclass(etype, BaseException):
        msg = f"{etype!r} is not an exception class"
        raise TypeError(msg)
    if not isinstance(value, BaseException):
        msg = f"{value!r} is not an exception instance"
        raise TypeError(msg)
    if not isinstance(tb, types.TracebackType):
        try:
            raise value  # noqa: TRY301
        except BaseException as e:  # pylint: disable=W0718  # noqa: BLE001
            tb = e.__traceback__  # Now we have the traceback object
        if tb is None:
            msg = f"Could not determine traceback from {value}"
            raise RuntimeError(msg)

    # Construct the stack trace using traceback
    formatted_traceback: str = "".join(traceback.format_exception(etype, value, tb))

    # Capture the current stack trace
    frames: list[inspect.FrameInfo] = inspect.getinnerframes(tb, context=5)

    # Construct a detailed message with variables from all stack frames
    detailed_message: list[str] = [
        f"{message} Exception '{value}' of type '{etype}' occurred.",
        "Stack Trace Variables:",
    ]
    for frame_info in frames:
        detailed_message.extend(format_frame_info(frame_info))
    if value.__cause__ is not None:
        detailed_message.append("This is the original exception:")
        detailed_message.extend(format_exception_with_variables(value.__cause__, message="Causing Exception's Stack Trace Variables:").split("\n"))

    detailed_message.append(formatted_traceback)
    return "\n".join(detailed_message)


def is_assertion_removal_enabled() -> bool:
    return sys.flags.optimize >= 1

IT = TypeVar("IT")


def enforce_instance_cast(obj: object, type_: type[IT]) -> IT:
    instance_check: bool = isinstance(obj, type_)
    if is_assertion_removal_enabled():
        # don't enforce the instance check if the assertion optimizers are being used.
        if not instance_check:
            print(format_exception_with_variables(AssertionError("isinstance(obj, type_)")))  # noqa: T201
        return obj  # type: ignore[return-value]

    assert_with_variable_trace(isinstance(obj, type_), "enforce_is_instance failed.")
    return obj  # type: ignore[return-value]


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
    line_of_code: str = code_context[0].strip() if code_context else "Unknown condition"

    # Construct a detailed message with variables from all stack frames
    detailed_message: list[str] = [
        f"{message}: Expected condition '{line_of_code}' failed at {filename}:{line_no}.",
        "Stack Trace Variables:",
    ]
    for frame_info in frames:
        detailed_message.extend(format_frame_info(frame_info))

    full_message: str = "\n".join(detailed_message)

    # Raise an exception with the detailed message
    raise AssertionError(full_message)

RT = TypeVar("RT")
unique_sentinel = object()


def with_variable_trace(
    exception_types: type[Exception] | tuple[type[Exception], ...] = Exception,
    return_type: type[RT] = unique_sentinel,  # type: ignore[reportGeneralTypeIssues, assignment]
    *,
    action="print",
    log: bool = True,
    rethrow: bool = False,
) -> Callable[[Callable[..., RT]], Callable[..., RT | None]]:
    # Set default to Exception if no specific types are provided
    if not exception_types:
        exception_types = (Exception,)
    if not isinstance(exception_types, tuple):
        exception_types = (exception_types,)
    exception_types = (*exception_types, CustomAssertionError)

    def decorator(f: Callable[..., RT]) -> Callable[..., RT | None]:
        def wrapper(*args, **kwargs) -> RT | None:
            try:
                result: RT = f(*args, **kwargs)
                if return_type is not unique_sentinel and not isinstance(result, return_type):
                    msg = f"Return type of '{f.__name__}' must be {return_type.__name__}, got {result.__class__}: {result!r}: {result}"
                    raise CustomAssertionError(msg)
            except exception_types as e:

                detailed_message: list[str] = [
                    f"Exception caught in function '{f.__name__}': {e}",
                    "Stack Trace Variables:",
                ]
                for frame_info in inspect.getouterframes(inspect.currentframe()):
                    # if frame_info.function != f.__name__:  # Why did I add this?
                    #    continue
                    detailed_message.extend(format_frame_info(frame_info))
                if e.__cause__ is not None:
                    detailed_message.append("This is the original exception:")
                    detailed_message.extend(format_exception_with_variables(e.__cause__, message="Causing Exception's Stack Trace Variables:").split("\n"))

                full_message: str = "\n".join(detailed_message)

                if action == "stderr":
                    if sys.stderr is None:
                        sys.stderr = open(os.devnull, "w")  # noqa: PTH123, SIM115, PLW1514  # pylint: disable=all
                    print(full_message, sys.stderr)  # noqa: T201
                elif action == "print":
                    print(full_message)  # noqa: T201
                if log:
                    with Path("errorlog.txt", encoding="utf-8").open("a") as outfile:
                        outfile.write(full_message)
                if rethrow:
                    # Raise an exception with the detailed message
                    if isinstance(e, CustomAssertionError):
                        raise AssertionError(e.message) from None
                    raise e.__class__(full_message) from e

                return None
            else:
                return result

        return wrapper

    return decorator
