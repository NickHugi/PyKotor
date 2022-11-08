from pykotor.resource.formats.gff import GFF, GFFStruct, read_gff, GFFFieldType


class DiffGFF:
    def __init__(self, old: GFF, new: GFF):
        self.old: GFF = old
        self.new: GFF = new

    def is_same(self, old_struct: GFFStruct = None, new_struct: GFFStruct = None) -> bool:
        old_struct = self.old.root if old_struct is None else old_struct
        new_struct = self.new.root if new_struct is None else new_struct

        for label, ftype, old_value in old_struct:
            if not new_struct.exists(label):
                print("Missing a field:", label)
                return False

            if new_struct.what_type(label) != ftype:
                print("Field type has changed:", label)
                return False

            new_value = new_struct.value(label)
            if ftype == GFFFieldType.Struct:
                if old_value.struct_id != new_value.struct_id:
                    print("Struct ID has changed:", label)
                    return False

                if not self.is_same(old_value, new_value):
                    return False
            elif ftype == GFFFieldType.List:
                if len(old_value) != len(new_value):
                    print("List counts have changed:", label)
                    return False
                for i, old_child in enumerate(old_value):
                    new_child = new_value.at(i)
                    if not self.is_same(old_child, new_child):
                        return False
            else:
                if new_value != old_value:
                    print("Value has changed:", label, new_value, old_value)
                    return False

        return True
