from pykotor.resource.formats.tlk import TLK


class DiffTLK:
    def __init__(self, old: TLK, new: TLK):
        self.old: TLK = old
        self.new: TLK = new

    def is_same(self) -> bool:
        if len(self.old) != len(self.new):
            print("TLK row counts do not match")
            return False

        for stringref, entry in self.old:
            if entry.text != self.new.get(stringref).text:
                print("Entry text does not match:", stringref)
                return False
            if entry.voiceover != self.new.get(stringref).voiceover:
                print("Entry voiceover does not match:", stringref)
                return False

        return True
