from itertools import zip_longest

from pykotor.resource.formats.tlk import TLK


class DiffTLK:
    def __init__(self, old: TLK, new: TLK, log_func=print):
        self.old: TLK = old
        self.new: TLK = new
        self.log = log_func

    def is_same(self) -> bool:
        if len(self.old) != len(self.new):
            self.log(f"TLK row count mismatch. Old: {len(self.old)}, New: {len(self.new)}")

        mismatch_count, extra_old, extra_new = 0, 0, 0

        for (old_stringref, old_entry), (new_stringref, new_entry) in zip_longest(self.old, self.new, fillvalue=(None, None)):
            # Both TLKs have the entry but with different content
            if old_stringref is not None:
                if new_stringref is not None:
                    if old_entry != new_entry:
                        mismatch_count += 1
                        self.log(f"Entry mismatch at stringref: {old_stringref}")
                        self.log(f"Old Text: {old_entry.text}, Old Voiceover: {old_entry.voiceover}")
                        self.log(f"New Text: {new_entry.text}, New Voiceover: {new_entry.voiceover}")
                    continue

                extra_old += 1
                continue

            if new_stringref is not None:
                extra_new += 1
                continue

        # Provide a summary of discrepancies
        if mismatch_count:
            self.log(f"{mismatch_count} entries have mismatches.")
        if extra_old:
            self.log(f"Old TLK has {extra_old} stringrefs that are missing in the new TLK.")
        if extra_new:
            self.log(f"New TLK has {extra_new} extra stringrefs that are not in the old TLK.")

        return not (mismatch_count or extra_old or extra_new)
