from itertools import zip_longest

from pykotor.resource.formats.tlk import TLK

MAX_CHARS_BEFORE_NEWLINE_FORMAT = 50


def format_text(text):
    if "\n" in text or len(text) > MAX_CHARS_BEFORE_NEWLINE_FORMAT:
        return f'"""\n{text}\n"""'
    return f"'{text}'"


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
            if old_stringref is None and new_stringref is not None:
                extra_new += 1
                continue
            if new_stringref is not None and old_stringref is None:
                extra_old += 1
                continue

            assert old_entry is not None
            assert new_entry is not None
            if old_entry != new_entry:
                text_mismatch = old_entry.text.lower() != new_entry.text.lower()
                vo_mismatch = old_entry.voiceover.get().lower() != new_entry.voiceover.get().lower()
                if not text_mismatch and not vo_mismatch:
                    continue

                self.log(f"Entry mismatch at stringref: {old_stringref}")
                if text_mismatch:
                    self.log(f">>OLD Text: {format_text(old_entry.text)}")
                    self.log(f">>NEW Text: {format_text(new_entry.text)}")
                mismatch_count += 1
                if vo_mismatch:
                    self.log(f"OLD Voiceover: {format_text(old_entry.voiceover)}")
                    self.log(f"NEW Voiceover: {format_text(new_entry.voiceover)}")

        # Provide a summary of discrepancies
        if mismatch_count:
            self.log(f"{mismatch_count} entries have mismatches.")
        if extra_old:
            self.log(f"Old TLK has {extra_old} stringrefs that are missing in the new TLK.")
        if extra_new:
            self.log(f"New TLK has {extra_new} extra stringrefs that are not in the old TLK.")

        return not (mismatch_count or extra_old or extra_new)
