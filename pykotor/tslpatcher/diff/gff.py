from __future__ import annotations

from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFList, GFFStruct
from pykotor.tools.path import PureWindowsPath


class DiffGFF:
    def __init__(self, old: GFF, new: GFF):
        self.old: GFF = old
        self.new: GFF = new

    def is_same(
        self,
        old_struct: GFFStruct | None = None,
        new_struct: GFFStruct | None = None,
        current_path: PureWindowsPath | None = None,
    ) -> bool:
        current_path = PureWindowsPath(current_path or "GFFRoot")
        # Create dictionaries for both old and new structures
        old_dict = {label: (ftype, value) for label, ftype, value in (old_struct or self.old.root)}
        new_dict = {label: (ftype, value) for label, ftype, value in (new_struct or self.new.root)}

        # Union of labels from both old and new structures
        all_labels = set(old_dict.keys()) | set(new_dict.keys())

        is_same_result = True

        for idx, label in enumerate(all_labels):
            child_path = current_path / str(label if label else (-1 * idx))
            old_ftype, old_value = old_dict.get(label, (None, None))
            new_ftype, new_value = new_dict.get(label, (None, None))

            # Check for missing fields/values in either structure
            if old_ftype is None or old_value is None:
                print(f"Extra field found at '{child_path}'. Field Type: '{new_ftype}' Value: '{new_value}'")
                is_same_result = False
                continue
            if new_value is None or new_ftype is None:
                print(f"Missing field at '{child_path}'. Field Type: '{new_ftype}' Value: '{new_value}'")
                is_same_result = False
                continue

            # Check if field types have changed
            if old_ftype != new_ftype:
                print(f"Field type has changed at '{child_path}'. Field Type: '{old_ftype}'-->'{new_ftype}'")
                is_same_result = False
                continue

            # Compare values depending on their types
            if old_ftype == GFFFieldType.Struct:
                if old_value.struct_id != new_value.struct_id:
                    print(
                        f"Struct ID has changed at '{child_path}'. Struct ID: '{old_value.struct_id}'-->'{new_value.struct_id}'",
                    )
                    is_same_result = False

                if not self.is_same(old_value, new_value, child_path):
                    is_same_result = False
                    continue

            elif old_ftype == GFFFieldType.List:
                if not self._output_diff_from_two_lists(old_value, new_value, child_path):
                    is_same_result = False
                    continue

            elif old_value != new_value and str(old_value) != str(new_value):
                print(f"Value has changed at '{child_path}': '{old_value}' --> '{new_value}'")
                is_same_result = False
                continue

        return is_same_result

    def _output_diff_from_two_lists(self, old_gff_list: GFFList, new_gff_list: GFFList, current_path: PureWindowsPath) -> bool:
        is_same_result = True

        if len(old_gff_list) != len(new_gff_list):
            print(f"GFFList counts have changed at: '{current_path}'")
            print(f"Old list length: '{len(old_gff_list)}'")
            print(f"New list length: '{len(new_gff_list)}'")
            print()
            is_same_result = False

        # Convert lists to sets of hashable representations
        old_set: dict[int, GFFStruct] = {}
        for idx, item in enumerate(old_gff_list):
            key = item.struct_id if isinstance(item, GFFStruct) and item.struct_id not in old_set else -1 * idx
            old_set[key] = item

        new_set: dict[int, GFFStruct] = {}
        for idx, item in enumerate(new_gff_list):
            key = item.struct_id if isinstance(item, GFFStruct) and item.struct_id not in new_set else -1 * idx
            new_set[key] = item

        # Detect unique items in both lists
        unique_to_old: set[int] = old_set.keys() - new_set.keys()
        unique_to_new: set[int] = new_set.keys() - old_set.keys()

        for struct_id in unique_to_old:
            struct = old_set[struct_id]
            print(f"Missing GFFStruct with struct ID '{struct.struct_id}' in GFFList: '{current_path}'")
            print("Contents of old struct:")
            for label, field_type, field_value in struct:
                print("Label:", label, "FieldType:", field_type, "Value:", f"'{field_value}'")
            print()
            is_same_result = False

        for struct_id in unique_to_new:
            struct = new_set[struct_id]
            print(f"Extra GFFStruct exists with struct ID '{struct.struct_id}' in GFFList: '{current_path}'")
            print("Contents of new struct:")
            for label, field_type, field_value in struct:
                print("Label:", label, "FieldType:", field_type, "Value:", f"'{field_value}'")
            print()
            is_same_result = False

        # For items present in both lists
        common_items = old_set.keys() & new_set.keys()
        for struct_id in common_items:
            old_child = old_set[struct_id]
            new_child = new_set[struct_id]
            if struct_id != old_child.struct_id:
                child_path = current_path / f"{old_child.struct_id}({struct_id})"
            else:
                child_path = current_path / f"{old_child.struct_id}"

            if isinstance(old_child, GFFStruct) and isinstance(new_child, GFFStruct):
                if not self.is_same(old_child, new_child, child_path):
                    is_same_result = False
                continue
            if old_child != new_child:
                print(f"Value difference at GFFList '{child_path}': '{old_child}'-->'{new_child}'")
                is_same_result = False

        return is_same_result
