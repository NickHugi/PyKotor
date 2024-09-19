from __future__ import annotations

from ctypes import POINTER, addressof, c_uint, c_void_p, cast as cast_with_ctypes, pointer
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ctypes import _CData, _Pointer as PointerType

if not TYPE_CHECKING:
    PointerType = POINTER(c_uint).__class__


PREVENT_GC: list[Any] = []


class PointerHandlerMode(IntEnum):
    CTYPES_CAST = 0
    CTYPES_ARRAY = 1
    NUMPY = 2


def create_pointer(
    address: CPointer,
    mode: PointerHandlerMode = PointerHandlerMode.CTYPES_CAST,
) -> CPointer:
    if mode is PointerHandlerMode.CTYPES_CAST:
        new_pointer = CPointer(addressof(address))
    elif mode is PointerHandlerMode.CTYPES_ARRAY:
        pointer_array = (CPointer * 1)(address)
        new_pointer = CPointer(addressof(pointer_array))
        PREVENT_GC.append(pointer_array)
    elif mode is PointerHandlerMode.NUMPY:
        import numpy as np
        np_array = np.array([address.value], dtype=np.uintp)
        new_pointer = CPointer(np_array.ctypes.data)
        PREVENT_GC.append(np_array)
    PREVENT_GC.append(new_pointer)
    return new_pointer

def follow_pointer(
    address: CPointer | _CData,
    mode: PointerHandlerMode = PointerHandlerMode.CTYPES_CAST,
) -> CPointer:
    if not isinstance(address, c_void_p):
        address = c_void_p.from_address(addressof(address))
    if address.value == 0xDDDDDDDDDDDDDDDD:  # noqa: PLR2004
        raise OSError("INVALID pointer (Unallocated memory)")
    if not address.value:
        raise OSError(f"NULL pointer (address.value == {address.value})")
    if mode is PointerHandlerMode.CTYPES_CAST:
        return cast_with_ctypes(address, POINTER(CPointer)).contents
    if mode is PointerHandlerMode.CTYPES_ARRAY:
        # I have no early idea why this throws an exception... it's the same code?
        # deref_obj = CPointer.from_address(address.value)
        # dereferenced_address = deref_obj.value
        dereferenced_address = CPointer.from_address(address.value).value
        print(f"follow_address: Following address {hex(address.value)} to {hex(dereferenced_address or 0)}")
        assert dereferenced_address is not None, f"Dereferenced address should not be None: {hex(address.value)}"
        return CPointer(dereferenced_address)
    if mode is PointerHandlerMode.NUMPY:
        import numpy as np
        np_array = np.ctypeslib.as_array((c_uint * 1).from_address(address.value or 0))
        return CPointer(np_array[0])
    raise ValueError("Invalid/unsupported mode")

class CPointer(c_void_p):
    """A custom pointer type mirroring ctypes pointer functionality supporting original object return."""
    resolve: Callable[..., _CData]
    def __init__(self, address: int, *args, reinit: bool = False):
        if not reinit:
            super().__init__(address)
        self._address: int = address
        PREVENT_GC.append(self)

    def __hash__(self) -> int:
        return hash((self._address, self.value))

    def follow(self, *, mode: PointerHandlerMode = PointerHandlerMode.CTYPES_CAST) -> CPointer:
        return follow_pointer(self, mode=mode)

    def new_pointer(self, *, mode: PointerHandlerMode = PointerHandlerMode.CTYPES_CAST) -> CPointer:
        return create_pointer(self, mode=mode)


def adjust_pointer_depth(  # noqa: C901, ANN201
    obj: _CData | PointerType,
    pointer_depth: int,
    *,
    mode: PointerHandlerMode = PointerHandlerMode.CTYPES_CAST,
    max_depth: int = 255,
):
    """Create a custom pointer to the given object with the specified depth. Negative values mean resolving/following pointers.

    Args:
        obj: The object to create the pointer to.
        pointer_depth (int): The depth of pointers to create or follow.

    Returns:
        CPointer: A custom pointer to the object with the specified depth.
            or obj: the real object at the end of the pointer trail.
    """
    global PREVENT_GC  # noqa: PLW0602

    # Step 1: Dereference the pointers to get the actual data.
    actual_obj = obj
    while isinstance(actual_obj, PointerType):
        actual_obj = actual_obj.contents
        pointer_depth += 1
    # We now have the actual object.
    assert not isinstance(actual_obj, PointerType)
    if not pointer_depth:
        return actual_obj  # pointer_depth of 0 doesn't make sense past this point.


    actual_obj_type = actual_obj.__class__
    orig_addr = addressof(actual_obj)

    def resolve(self: CPointer) -> _CData:
        """Follow the pointer to return the original object."""
        current = self
        cur_depth = 1
        last_ptr = None
        while addressof(current) != orig_addr:
            print("Resolving to type:", actual_obj_type.__name__, "Address of Current:", hex(addressof(current)), "Current Address:", hex(0 if current.value is None else current.value), "Current Depth Level:", cur_depth)
            last_ptr = current
            current = follow_pointer(current, mode=mode)
            assert isinstance(current, (PointerType, c_void_p)), current.__class__.__name__
            cur_depth += 1
            if cur_depth >= max_depth:
                raise RuntimeError(f"Max pointer depth {max_depth} reached!")
        assert last_ptr is not None
        return cast_with_ctypes(last_ptr, POINTER(actual_obj_type)).contents
    CPointer.resolve = resolve

    # Initialize pointer storage and pointer
    current_ptr: CPointer = CPointer(orig_addr)
    depth = abs(pointer_depth)

    # Adjust pointer based on depth
    for _ in range(depth):
        current_ptr = create_pointer(current_ptr, mode=mode) if pointer_depth > 0 else follow_pointer(current_ptr, mode=mode)
        PREVENT_GC.append(current_ptr)

    retptr = CPointer(addressof(current_ptr))
    PREVENT_GC.append(retptr)

    deref_obj = current_ptr
    for _ in range(depth+1):
        deref_obj = follow_pointer(deref_obj, mode=mode)
    deref_addr = addressof(deref_obj)

    print(f"levels: {pointer_depth}, deref: {hex(deref_addr)}, orig: {hex(orig_addr)}")
    assert orig_addr == deref_addr, f"Original address DOES NOT match dereferenced address! ({hex(orig_addr)} == {hex(deref_addr)})"
    return retptr


if __name__ == "__main__":
    print(adjust_pointer_depth(c_uint(5), 2).resolve())
    print(adjust_pointer_depth(c_uint(5), 1).resolve())
    print(adjust_pointer_depth(c_uint(5), 0))
    print(adjust_pointer_depth(c_void_p(addressof(c_uint(5))), -1))
    print(adjust_pointer_depth(pointer(c_uint(5)), -1))
    print(adjust_pointer_depth(c_uint(5), 5).resolve())
    print(adjust_pointer_depth(pointer(c_uint(5)), 0))
    #print(adjust_pointer_depth(pointer(c_uint(5)), 1).resolve())  # Seems to only fail in 'run without debugging' mode...