"""Tests for GFFList.compare handling of complex field values."""

from __future__ import annotations

import pathlib
import sys


THIS_FILE = pathlib.Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[2]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"

for path in (PYKOTOR_SRC, UTILITY_SRC):
    as_posix = path.as_posix()
    if as_posix not in sys.path:
        sys.path.insert(0, as_posix)

from utility.common.geometry import Vector3
from pykotor.resource.formats.gff.gff_data import GFFList


def _silent_logger(message: object = "") -> None:
    # Helper logger that swallows output during tests.
    _ = message


def test_gfflist_compare_handles_vector_values_without_type_error() -> None:
    """Ensure comparing lists containing Vector3 fields does not raise TypeError."""

    old_list = GFFList()
    old_struct = old_list.add(2)
    old_struct.set_int32("Class", 3)
    old_struct.set_int16("ClassLevel", 8)
    old_struct.set_vector3("Facing", Vector3(1.0, 2.0, 3.0))
    old_known_list = old_struct.set_list("KnownList0", GFFList())
    old_known_entry = old_known_list.add(3)
    old_known_entry.set_int32("Spell", 4)
    old_known_entry.set_int16("SpellMetaMagic", 0)
    old_known_entry.set_int16("SpellFlags", 1)

    new_list = GFFList()
    new_struct_existing = new_list.add(2)
    new_struct_existing.set_int32("Class", 3)
    new_struct_existing.set_int16("ClassLevel", 8)
    new_struct_existing.set_vector3("Facing", Vector3(1.0, 2.0, 3.0))
    new_known_list = new_struct_existing.set_list("KnownList0", GFFList())
    new_known_entry = new_known_list.add(3)
    new_known_entry.set_int32("Spell", 4)
    new_known_entry.set_int16("SpellMetaMagic", 0)
    new_known_entry.set_int16("SpellFlags", 1)

    new_struct_added = new_list.add(5)
    new_struct_added.set_int32("Class", 3)
    new_struct_added.set_int16("ClassLevel", 9)
    new_struct_added.set_vector3("Facing", Vector3(4.0, 5.0, 6.0))
    new_added_known_list = new_struct_added.set_list("KnownList0", GFFList())
    new_added_entry = new_added_known_list.add(7)
    new_added_entry.set_int32("Spell", 53)
    new_added_entry.set_int16("SpellMetaMagic", 0)
    new_added_entry.set_int16("SpellFlags", 1)

    # Should report difference (returns False) but not raise TypeError.
    result = old_list.compare(new_list, log_func=_silent_logger)

    assert result is False

