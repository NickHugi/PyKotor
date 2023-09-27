from __future__ import annotations

from itertools import zip_longest

from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFList, GFFStruct


class DiffGFF:
    def __init__(self, old: GFF, new: GFF):
        self.old: GFF = old
        self.new: GFF = new

    def is_same(
        self,
        old_struct: GFFStruct | None = None,
        new_struct: GFFStruct | None = None,
    ) -> bool:
        old_struct = self.old.root if old_struct is None else old_struct
        new_struct = self.new.root if new_struct is None else new_struct

        is_same_result = True
        for (old_label, old_ftype, old_value), (new_label, new_ftype, new_value) in zip_longest(
            old_struct,
            new_struct,
            fillvalue=(None, None, None),
        ):
            # Check if a field is missing in either struct
            if old_label is None or old_value is None:
                if old_value is None:
                    print(f"Extra value for label: '{new_label}': '{new_value}'")
                if old_label is None:
                    print(f"Extra field for label: '{new_label}'")
                is_same_result = False
                continue
            if new_label is None or new_value is None:
                if new_value is None:
                    print(f"Missing value in label '{old_label}': '{old_value}'")
                if new_label is None:
                    print(f"Missing field in field: '{old_label}'")
                is_same_result = False
                continue

            # Check if field types have changed
            if old_ftype != new_ftype:
                print(f"Field type has changed for '{old_label}': {old_ftype}->{new_ftype}")
                is_same_result = False
                continue

            # Compare values depending on their types
            if old_ftype == GFFFieldType.Struct:
                if old_value.struct_id != new_value.struct_id:
                    print(f"Struct ID has changed for '{old_label}'")
                    is_same_result = False

                if not self.is_same(old_value, new_value):
                    is_same_result = False
                    continue

            elif old_ftype == GFFFieldType.List:
                if not self._output_diff_from_two_lists(old_value, new_value, old_label):
                    is_same_result = False
                    continue

            elif old_value != new_value:
                print(f"Value has changed for '{old_label}': '{old_value}' --> '{new_value}'")
                is_same_result = False
                continue

        return is_same_result

    def _output_diff_from_two_lists(self, old_gff_list: GFFList, new_gff_list: GFFList, label: str) -> bool:
        is_same_result = True

        if len(old_gff_list) != len(new_gff_list):
            print(f"List counts have changed for field: '{label}'")
            print(f"Old list length: {len(old_gff_list)}")
            print(f"New list length: {len(new_gff_list)}")
            is_same_result = False

        for i, (old_child, new_child) in enumerate(zip_longest(old_gff_list, new_gff_list, fillvalue=None)):
            if old_child is None:
                print(f"Extra item in new list at index {i} for field: '{label}'")
                is_same_result = False
                continue

            if new_child is None:
                print(f"Missing {len(old_gff_list) - len(new_gff_list)} items in new gff list, at index {i} for field: '{label}'")
                is_same_result = False
                break

            if isinstance(old_child, GFFStruct) and isinstance(new_child, GFFStruct):
                if not self.is_same(old_child, new_child):
                    is_same_result = False
            elif isinstance(old_child, GFFList) and isinstance(new_child, GFFList):
                nested_label = f"{label}[{i}]"
                if not self._output_diff_from_two_lists(old_child, new_child, nested_label):
                    is_same_result = False
            elif old_child != new_child:
                print(f"Value difference at index {i} for field: '{label}': Old: '{old_child}', New: '{new_child}'")
                is_same_result = False

        return is_same_result
