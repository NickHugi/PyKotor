import os
from abc import ABC
from pathlib import Path, PureWindowsPath, PurePosixPath, PurePath

def derives_from_purepath(obj):
    cls = obj.__class__
    while cls:
        if cls == PurePath:
            return True
        cls = cls.__base__
    return False

def simple_wrapper(fn_name, wrapped_class_type):
    def wrapped(self, *args, **kwargs):
        orig_fn = wrapped_class_type._original_methods[fn_name]

        # __init__ can only ever take one argument.
        if fn_name == "__init__":
            return orig_fn(self)

        def parse_arg(arg):
            # If it's an instance of the wrapped class, call its original __new__ method
            if derives_from_purepath(arg):
                return wrapped_class_type._original_methods["__new__"](arg.__class__, object.__getattribute__(arg, "__fspath__").lower())
            return arg

        # Parse `self` if it meets the condition
        actual_self = parse_arg(self)

        # Handle positional arguments
        args = tuple(parse_arg(arg) for arg in args)

        # Handle keyword arguments
        kwargs = {k: parse_arg(v) for k, v in kwargs.items()}

        #print(f"Calling: {fn_name}")
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
    ignored_methods = ["__instancecheck__", "__getattribute__", "__setattribute__"]
    
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
        return Path().cwd() / arg

class B(C, Path):
    pass

class A(B):
    _original_methods = {}
wrap_inherited_methods(A)


a = A()
b = B()
print(a.combine_cwd_with_path_test(A("CASESENSITIVETEST/test/TEst/")))
print(b.combine_cwd_with_path_test(A("CASESENSITIVETEST/test/TEst/")))