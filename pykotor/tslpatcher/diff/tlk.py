import os
from itertools import zip_longest

from pykotor.resource.formats.tlk import TLK

MAX_CHARS_BEFORE_NEWLINE_FORMAT = 20  # Adjust as needed


def format_text(text):
    if "\n" in text or len(text) > MAX_CHARS_BEFORE_NEWLINE_FORMAT:
        return f'"""{os.linesep}{text}{os.linesep}"""'
    return f"'{text}'"


def first_char_diff_index(str1, str2):
    """Find the index of the first differing character in two strings."""
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[i] != str2[i]:
            return i
    if len(str1) != len(str2):
        return min_length  # Difference due to length
    return -1  # No difference


def generate_diff_marker_line(index, length):
    """Generate a line of spaces with a '^' at the specified index."""
    if index == -1:
        return ""
    return " " * index + "^" + " " * (length - index - 1)


def compare_and_format(old_value, new_value):
    old_text = str(old_value)
    new_text = str(new_value)
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")
    formatted_old = []
    formatted_new = []

    for old_line, new_line in zip(old_lines, new_lines):
        diff_index = first_char_diff_index(old_line, new_line)
        marker_line = generate_diff_marker_line(diff_index, max(len(old_line), len(new_line)))

        formatted_old.append(old_line)
        formatted_new.append(new_line)
        if marker_line:
            formatted_old.append(marker_line)
            formatted_new.append(marker_line)

    return os.linesep.join(formatted_old), os.linesep.join(formatted_new)


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
            if old_stringref is None or old_entry is None:
                if new_stringref is not None and new_entry is not None:
                    extra_new += 1
                    continue
                continue
            if new_stringref is None or new_entry is None:
                if old_stringref is not None and old_entry is not None:
                    extra_old += 1
                    continue
                continue

            if old_entry != new_entry:
                text_mismatch = old_entry.text.lower() != new_entry.text.lower()
                vo_mismatch = old_entry.voiceover.get().lower() != new_entry.voiceover.get().lower()
                if not text_mismatch and not vo_mismatch:
                    self.log("TLK entries are not equal, but no differences could be found?")
                    continue

                self.log(f"Entry mismatch at stringref: {old_stringref}")
                if text_mismatch:
                    self.log(format_text(compare_and_format(old_entry.text, new_entry.text)))
                mismatch_count += 1
                if vo_mismatch:
                    self.log(format_text(compare_and_format(old_entry.voiceover, new_entry.voiceover)))

        # Provide a summary of discrepancies
        if mismatch_count:
            self.log(f"{mismatch_count} entries have mismatches.")
        if extra_old:
            self.log(f"Old TLK has {extra_old} stringrefs that are missing in the new TLK.")
        if extra_new:
            self.log(f"New TLK has {extra_new} extra stringrefs that are not in the old TLK.")

        return not (mismatch_count or extra_old or extra_new)
