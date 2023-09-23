import os
from abc import ABC
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath


def is_same_type(obj1, obj2):
    return id(obj1) == id(obj2)  # Reverted back to id comparison for class types


def is_type_or_subtype(obj, target_cls):
    return is_same_type(obj, target_cls) or check_mro_without_magic(obj, target_cls)


def check_mro_without_magic(cls, target_cls):
    if id(type(cls)) != id(type):  # Replacing isinstance check
        return False
    if is_same_type(cls, target_cls):
        return True
    return any(check_mro_without_magic(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(instance, target_cls):
    instance_type = type(instance)
    return is_same_type(instance_type, target_cls) or check_mro_without_magic(instance_type, target_cls)


def simple_wrapper(fn_name, wrapped_class_type):
    def wrapped(self, *args, **kwargs):
        orig_fn = wrapped_class_type._original_methods[fn_name]

        # __init__ can only ever take one argument.
        if fn_name == "__init__":
            return orig_fn(self)

        def parse_arg(arg):
            if is_instance_or_subinstance(arg, PurePath):
                return wrapped_class_type._original_methods["__new__"](
                    arg.__class__,
                    str(arg).lower(),
                )
            return arg

        # Parse `self` if it meets the condition
        actual_self = parse_arg(self)

        # Handle positional arguments
        args = tuple(parse_arg(arg) for arg in args)

        # Handle keyword arguments
        kwargs = {k: parse_arg(v) for k, v in kwargs.items()}

        # TODO: when orig_fn doesn't exist, the AttributeException should be raised by
        # the prior stack instead of here, as that's what would normally happen.
        return orig_fn(actual_self, *args, **kwargs)

    return wrapped


def wrap_inherited_methods(cls):
    mro = cls.mro()  # Gets the method resolution order
    parent_classes = mro[1:]  # Exclude the current class itself

    # Store already wrapped methods to avoid wrapping multiple times
    wrapped_methods = set()

    # ignore these methods
    ignored_methods = ["__instancecheck__", "__getattribute__", "__setattribute__", "__str__"]

    for parent in parent_classes:
        for attr_name, attr_value in parent.__dict__.items():
            # Check if it's a method and hasn't been wrapped before
            if callable(attr_value) and attr_name not in wrapped_methods and attr_name not in ignored_methods:
                cls._original_methods[attr_name] = attr_value
                setattr(cls, attr_name, simple_wrapper(attr_name, cls))
                wrapped_methods.add(attr_name)


class C(ABC):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour

    def combine_cwd_with_path_test(self, arg: os.PathLike):
        return self / arg


class B(C, Path):
    pass


class A(B):
    _original_methods = {}


wrap_inherited_methods(A)


a = A.cwd()
b = B.cwd()
print(a.combine_cwd_with_path_test("CASESENSITIVETEST/test/TEst/"))
print(b.combine_cwd_with_path_test("CASESENSITIVETEST/test/TEst/"))
