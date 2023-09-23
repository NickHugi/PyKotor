import os
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath


from abc import ABC
def is_same_type(obj1, obj2):
    return type(obj1) is type(obj2)

def is_class_or_subclass_but_not_instance(cls, target_cls):
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)

def is_instance_or_subinstance(instance, target_cls):
    if hasattr(instance, "__bases__"):  # instance is a class
        return False  # if instance is a class, always return False
    else:  # instance is not a class
        return type(instance) is target_cls or is_class_or_subclass_but_not_instance(type(instance), target_cls)








class TestABC(ABC):
    pass

class TestClass(TestABC):
    pass

class TestClassChild(TestClass):
    pass

test_instance = TestClass()
test_child_instance = TestClassChild()

assert not is_class_or_subclass_but_not_instance(test_instance, TestClass)
assert is_class_or_subclass_but_not_instance(TestClass, TestClass)
assert not is_class_or_subclass_but_not_instance(test_child_instance, TestClass)
assert is_class_or_subclass_but_not_instance(TestClassChild, TestClass)
assert is_instance_or_subinstance(test_instance, TestClass)
assert not is_instance_or_subinstance(TestClass, TestClass)
assert is_instance_or_subinstance(test_child_instance, TestClass)
assert not is_instance_or_subinstance(TestClassChild, TestClass)

def simple_wrapper(fn_name, wrapped_class_type):
    def wrapped(self, *args, **kwargs):
        orig_fn = wrapped_class_type._original_methods[fn_name]

        # __init__ can only ever take one argument.
        if fn_name == "__init__":
            return orig_fn(self)

        def parse_arg(arg):
            if is_instance_or_subinstance(arg, PurePath):
                return wrapped_class_type._original_methods["__new__"](
                    object.__new__(type(arg)),
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
    ignored_methods = ["__instancecheck__", "__getattribute__", "__setattribute__", "__str__", "__setattr__"]

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
print(a.combine_cwd_with_path_test(B("CASESENSITIVETEST/test/TEst/")))
print(b.combine_cwd_with_path_test(B("CASESENSITIVETEST/test/TEst/")))
