from __future__ import annotations

import os
import re


def ireplace(original: str, target: str, replacement: str) -> str:
    if not original or not target:
        return original
    # Initialize an empty result string and a pointer to traverse the original string
    result = ""
    i = 0

    # Length of the target string
    target_length = len(target)

    # Convert the target to lowercase for case-insensitive comparison
    target_lower = target.lower()

    while i < len(original):
        # If a potential match is found
        if original[i : i + target_length].lower() == target_lower:
            # Add the replacement to the result
            result += replacement
            # Skip the characters of the target
            i += target_length
        else:
            # Add the current character to the result
            result += original[i]
            i += 1
    return result


def format_text(text, max_chars_before_newline: int = 20) -> str:
    text_str = str(text)
    if "\n" in text_str or len(text_str) > max_chars_before_newline:
        return f'"""{os.linesep}{text_str}{os.linesep}"""'
    return f"'{text_str}'"

def first_char_diff_index(str1, str2) -> int:
    """Find the index of the first differing character in two strings."""
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[i] != str2[i]:
            return i
    if len(str1) != len(str2):
        return min_length  # Difference due to length
    return -1  # No difference

def generate_diff_marker_line(index, length) -> str:
    """Generate a line of spaces with a '^' at the specified index."""
    if index == -1:
        return ""
    return " " * index + "^" + " " * (length - index - 1)

def compare_and_format(old_value, new_value) -> tuple[str, str]:
    """Compares and formats two values for diff display.

    Args:
    ----
        old_value: The old value to compare
        new_value: The new value to compare

    Returns:
    -------
        A tuple of formatted old and new values for diff display

    Processing Logic:
    ----------------
        - Converts old_value and new_value to strings and splits into lines
        - Zips the lines to iterate in parallel
        - Finds index of first differing character between lines
        - Generates a diff marker line based on index
        - Appends lines and marker lines to formatted outputs
        - Joins lines with line separators and returns a tuple.
    """
    old_text = str(old_value)
    new_text = str(new_value)
    old_lines: list[str] = old_text.split("\n")
    new_lines: list[str] = new_text.split("\n")
    formatted_old: list[str] = []
    formatted_new: list[str] = []

    for old_line, new_line in zip(old_lines, new_lines):
        diff_index: int = first_char_diff_index(old_line, new_line)
        marker_line: str = generate_diff_marker_line(diff_index, max(len(old_line), len(new_line)))

        formatted_old.append(old_line)
        formatted_new.append(new_line)
        if marker_line:
            formatted_old.append(marker_line)
            formatted_new.append(marker_line)

    return os.linesep.join(formatted_old), os.linesep.join(formatted_new)

def striprtf(text) -> str:  # noqa: C901, PLR0915, PLR0912
    """Removes RTF tags from a string.

    Strips RTF encoding utterly and completely

    Args:
    ----
        text: {String}: The input text possibly containing RTF tags

    Returns:
    -------
        str: {A plain text string without any RTF tags}

    Processes the input text by:
        1. Using regular expressions to find RTF tags and special characters
        2. Translating RTF tags and special characters to normal text
        3. Ignoring certain tags and characters inside tags marked as "ignorable"
        4. Appending/joining resulting text pieces to output.
    """
    pattern: re.Pattern[str] = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
    # control words which specify a "destination".
    destinations = frozenset(("aftncn", "aftnsep", "aftnsepc", "annotation", "atnauthor", "atndate", "atnicn", "atnid", "atnparent", "atnref", "atntime", "atrfend", "atrfstart", "author", "background", "bkmkend", "bkmkstart", "blipuid", "buptim", "category", "colorschememapping", "colortbl", "comment", "company", "creatim", "datafield", "datastore", "defchp", "defpap", "do", "doccomm", "docvar", "dptxbxtext", "ebcend", "ebcstart", "factoidname", "falt", "fchars", "ffdeftext", "ffentrymcr", "ffexitmcr", "ffformat", "ffhelptext", "ffl", "ffname", "ffstattext", "field", "file", "filetbl", "fldinst", "fldrslt", "fldtype", "fname", "fontemb", "fontfile", "fonttbl", "footer", "footerf", "footerl", "footerr", "footnote", "formfield", "ftncn", "ftnsep", "ftnsepc", "g", "generator", "gridtbl", "header", "headerf", "headerl", "headerr", "hl", "hlfr", "hlinkbase", "hlloc", "hlsrc", "hsv", "htmltag", "info", "keycode", "keywords", "latentstyles", "lchars", "levelnumbers", "leveltext", "lfolevel", "linkval", "list", "listlevel", "listname", "listoverride", "listoverridetable", "listpicture", "liststylename", "listtable", "listtext", "lsdlockedexcept", "macc", "maccPr", "mailmerge", "maln", "malnScr", "manager", "margPr", "mbar", "mbarPr", "mbaseJc", "mbegChr", "mborderBox", "mborderBoxPr", "mbox", "mboxPr", "mchr", "mcount", "mctrlPr", "md", "mdeg", "mdegHide", "mden", "mdiff", "mdPr", "me", "mendChr", "meqArr", "meqArrPr", "mf", "mfName", "mfPr", "mfunc", "mfuncPr", "mgroupChr", "mgroupChrPr", "mgrow", "mhideBot", "mhideLeft", "mhideRight", "mhideTop", "mhtmltag", "mlim", "mlimloc", "mlimlow", "mlimlowPr", "mlimupp", "mlimuppPr", "mm", "mmaddfieldname", "mmath", "mmathPict", "mmathPr", "mmaxdist", "mmc", "mmcJc", "mmconnectstr", "mmconnectstrdata", "mmcPr", "mmcs", "mmdatasource", "mmheadersource", "mmmailsubject", "mmodso", "mmodsofilter", "mmodsofldmpdata", "mmodsomappedname", "mmodsoname", "mmodsorecipdata", "mmodsosort", "mmodsosrc", "mmodsotable", "mmodsoudl", "mmodsoudldata", "mmodsouniquetag", "mmPr", "mmquery", "mmr", "mnary", "mnaryPr", "mnoBreak", "mnum", "mobjDist", "moMath", "moMathPara", "moMathParaPr", "mopEmu", "mphant", "mphantPr", "mplcHide", "mpos", "mr", "mrad", "mradPr", "mrPr", "msepChr", "mshow", "mshp", "msPre", "msPrePr", "msSub", "msSubPr", "msSubSup", "msSubSupPr", "msSup", "msSupPr", "mstrikeBLTR", "mstrikeH", "mstrikeTLBR", "mstrikeV", "msub", "msubHide", "msup", "msupHide", "mtransp", "mtype", "mvertJc", "mvfmf", "mvfml", "mvtof", "mvtol", "mzeroAsc", "mzeroDesc", "mzeroWid", "nesttableprops", "nextfile", "nonesttables", "objalias", "objclass", "objdata", "object", "objname", "objsect", "objtime", "oldcprops", "oldpprops", "oldsprops", "oldtprops", "oleclsid", "operator", "panose", "password", "passwordhash", "pgp", "pgptbl", "picprop", "pict", "pn", "pnseclvl", "pntext", "pntxta", "pntxtb", "printim", "private", "propname", "protend", "protstart", "protusertbl", "pxe", "result", "revtbl", "revtim", "rsidtbl", "rxe", "shp", "shpgrp", "shpinst", "shppict", "shprslt", "shptxt", "sn", "sp", "staticval", "stylesheet", "subject", "sv", "svb", "tc", "template", "themedata", "title", "txe", "ud", "upr", "userprops", "wgrffmtfilter", "windowcaption", "writereservation", "writereservhash", "xe", "xform", "xmlattrname", "xmlattrvalue", "xmlclose", "xmlname", "xmlnstbl", "xmlopen"))
    # Translation of some special characters.
    specialchars: dict[str, str] = {
        "par": "\n",
        "sect": "\n\n",
        "page": "\n\n",
        "line": "\n",
        "tab": "\t",
        "emdash": "\u2014",
        "endash": "\u2013",
        "emspace": "\u2003",
        "enspace": "\u2002",
        "qmspace": "\u2005",
        "bullet": "\u2022",
        "lquote": "\u2018",
        "rquote": "\u2019",
        "ldblquote": "\201C",
        "rdblquote": "\u201D",
    }
    stack: list[tuple[int, bool]] = []
    ignorable = False  # Whether this group (and all inside it) are "ignorable".
    ucskip = 1  # Number of ASCII characters to skip after a unicode character.
    curskip = 0  # Number of ASCII characters left to skip
    out: list[str] = []  # Output buffer.
    for match in pattern.finditer(text):
        word, arg, hexcode, char, brace, tchar = match.groups()
        if brace:
            curskip = 0
            if brace == "{":
                # Push state
                stack.append((ucskip, ignorable))
            elif brace == "}":
                # Pop state
                ucskip, ignorable = stack.pop()
        elif char:  # \x (not a letter)
            curskip = 0
            if char == "~":
                if not ignorable:
                    out.append("\xA0")
            elif char in "{}\\":
                if not ignorable:
                    out.append(char)
            elif char == "*":
                ignorable = True
        elif word:  # \foo
            curskip = 0
            if word in destinations:
                ignorable = True
            elif ignorable:
                pass
            elif word in specialchars:
                out.append(specialchars[word])
            elif word == "uc":
                ucskip = int(arg)
            elif word == "u":
                c = int(arg)
                if c < 0:
                    c += 0x10000
                out.append(chr(c))
                curskip = ucskip
        elif hexcode:  # \'xx
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                c = int(hexcode, 16)
                out.append(chr(c))
        elif tchar:
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                out.append(tchar)
    return "".join(out)


class MutableString(str):

    __slots__: tuple[str, ...] = (
        "__content",
    )

    def __init__(self, content: str = "") -> None:
        # sourcery skip: remove-unnecessary-cast
        if not isinstance(content, str):
            msg = f"{content} must be a string, got {type(content)}"
            raise TypeError(msg)
        self.__content: str = str(content)

    def __deepcopy__(self, memo):
        # Create a new instance with the same content
        new_copy = type(self)(self.__content)
        # Add the new object to the memo dictionary to handle circular references
        memo[id(self)] = new_copy
        return new_copy

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__content})"

    def __str__(self) -> str:
        return self.__content

    def __len__(self) -> int:
        return len(self.__content)

    def __getitem__(self, key) -> str:
        return type(self)(self.__content[key])

    def __iter__(self):
        for i in range(len(self.__content)):
            yield type(self)(self.__content[i])

    def __contains__(self, item) -> bool:
        return item in self.__content

    def __add__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return type(self)(self.__content + other)

    def __mul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        return type(self)(self.__content * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __mod__(self, other):
        return type(self)(self.__content % other)

    def __rmod__(self, other):
        return type(self)(other % self.__content)

    def __eq__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return self.__content == other

    def __ne__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return self.__content != other

    def __lt__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return self.__content < other

    def __le__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return self.__content <= other

    def __gt__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return self.__content > other

    def __ge__(self, other):
        if not isinstance(other, str):
            return NotImplemented
        return self.__content >= other

    def __hash__(self):
        return hash(self.__content)

    # String Methods
    def capitalize(self):
        return type(self)(self.__content.capitalize())

    def casefold(self):
        return type(self)(self.__content.casefold())

    def center(self, __width, __fillchar=" "):
        return type(self)(self.__content.center(__width, __fillchar))

    def count(self, x, __start=0, __end=None):
        return self.__content.count(x, __start, __end)

    def encode(self, encoding="utf-8", errors="strict"):
        return self.__content.encode(encoding, errors)

    def endswith(self, __suffix, __start=0, __end=None):
        return self.__content.endswith(__suffix, __start, __end)

    def expandtabs(self, tabsize=8):
        return type(self)(self.__content.expandtabs(tabsize))

    def find(self, __sub, __start=0, __end=None):
        return self.__content.find(__sub, __start, __end)

    def format(self, *args, **kwargs):  # noqa: A003
        return type(self)(self.__content.format(*args, **kwargs))

    def format_map(self, map):  # noqa: A002
        return type(self)(self.__content.format_map(map))

    def index(self, __sub, __start=0, __end=None):
        return self.__content.index(__sub, __start, __end)

    def isalnum(self):
        return self.__content.isalnum()

    def isalpha(self):
        return self.__content.isalpha()

    def isascii(self):
        return self.__content.isascii()

    def isdecimal(self):
        return self.__content.isdecimal()

    def isdigit(self):
        return self.__content.isdigit()

    def isidentifier(self):
        return self.__content.isidentifier()

    def islower(self):
        return self.__content.islower()

    def isnumeric(self):
        return self.__content.isnumeric()

    def isprintable(self):
        return self.__content.isprintable()

    def isspace(self):
        return self.__content.isspace()

    def istitle(self):
        return self.__content.istitle()

    def isupper(self):
        return self.__content.isupper()

    def join(self, __iterable):
        return type(self)(self.__content.join(__iterable))

    def ljust(self, __width, __fillchar=" "):
        return type(self)(self.__content.ljust(__width, __fillchar))

    def lower(self):
        return type(self)(self.__content.lower())

    def lstrip(self, __chars=None):
        return type(self)(self.__content.lstrip(__chars))

    def partition(self, __sep):
        a, b, c = self.__content.partition(__sep)
        return (type(self)(a), type(self)(b), type(self)(c))

    def replace(self, __old, __new, __count=-1):
        return type(self)(self.__content.replace(__old, __new, __count))

    def rfind(self, __sub, __start=0, __end=None):
        return self.__content.rfind(__sub, __start, __end)

    def rindex(self, __sub, __start=0, __end=None):
        return self.__content.rindex(__sub, __start, __end)

    def rjust(self, __width, __fillchar=" "):
        return type(self)(self.__content.rjust(__width, __fillchar))

    def rpartition(self, __sep):
        a, b, c = self.__content.rpartition(__sep)
        return (type(self)(a), type(self)(b), type(self)(c))

    def rsplit(self, __sep=None, __maxsplit=-1):
        return [type(self)(s) for s in self.__content.rsplit(__sep, __maxsplit)]

    def rstrip(self, __chars=None):
        return type(self)(self.__content.rstrip(__chars))

    def split(self, sep=None, maxsplit=-1):
        return [type(self)(s) for s in self.__content.split(sep, maxsplit)]

    def splitlines(self, keepends=False):
        return [type(self)(s) for s in self.__content.splitlines(keepends)]

    def startswith(self, __prefix, __start=0, __end=None):
        return self.__content.startswith(__prefix, __start, __end)

    def strip(self, __chars=None):
        return type(self)(self.__content.strip(__chars))

    def swapcase(self):
        return type(self)(self.__content.swapcase())

    def title(self):
        return type(self)(self.__content.title())

    def translate(self, __table):
        return type(self)(self.__content.translate(__table))

    def upper(self):
        return type(self)(self.__content.upper())

    def zfill(self, __width):
        return type(self)(self.__content.zfill(__width))

    # Magic methods for string representation
    def __getnewargs__(self):
        return (self.__content,)

    def __getstate__(self):
        return self.__content


class CaseInsensitiveMutStr(MutableString):

    __slots__: tuple[str, ...] = (
        *MutableString.__slots__,
        "__lower_content",
    )

    @staticmethod
    def _coerce_obj(item) -> str:
        if isinstance(item, MutableString):
            item_type = type(item)
            if item_type in (MutableString, CaseInsensitiveMutStr):
                return item.lower()
            return super(item_type, item).lower()
        if isinstance(item, str):
            return item.lower()
        return item

    @staticmethod
    def _coerce_str(item) -> str:
        if isinstance(item, str):
            return str(item).lower()
        return item

    def __init__(self, string):
        super().__init__(string)
        self.__lower_content = str(self).lower()

    def __contains__(self, item):
        return self.__lower_content.__contains__(self._coerce_obj(item).lower())

    def __eq__(self, other):
        return self.__lower_content.__eq__(self._coerce_obj(other))

    def __ne__(self, other):
        return self.__lower_content.__ne__(self._coerce_obj(other))

    def __hash__(self):
        return self.__lower_content.__hash__()

    def find(self, sub: str, start=0, end=None):  # sourcery skip: remove-unnecessary-cast
        return self.__lower_content.find(self._coerce_obj(sub), start, end)

    def lower(self):
        return type(self)(self.__lower_content)

    def partition(self, __sep):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        match: re.Match[str] | None = pattern.search(self.__content)

        if match is None:
            return (type(self)(self.__content), type(self)(""), type(self)(""))

        idx: int = match.start()
        return (
            type(self)(self.__content[:idx]),
            type(self)(self.__content[idx:idx+len(__sep)]),
            type(self)(self.__content[idx+len(__sep):]),
        )


    def replace(self, __old: str, __new: str, __count=-1):
        """Case-insensitive replace function matching the builtin str.replace's functionality."""
        # Check for the special case where 'old' is an empty string
        if __old == "":  # sourcery skip: simplify-empty-collection-comparison
            return super().replace("", self._coerce_str(__new), __count)

        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__old)), re.IGNORECASE)
        return type(self)(pattern.sub(self._coerce_str(__new), self.__content, __count))


    def rpartition(self, __sep: str):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        matches = list(pattern.finditer(self.__content))

        if not matches:
            return (type(self)(""), type(self)(""), type(self)(self.__content))
        match: re.Match[str] = matches[-1]  # Get the last match for rpartition
        idx: int = match.start()
        return (
            type(self)(self.__content[:idx]),
            type(self)(self.__content[idx:idx+len(__sep)]),
            type(self)(self.__content[idx+len(__sep):]),
        )

    def rfind(self, __sub: str, __start=None, __end=None):  # sourcery skip: remove-unnecessary-cast
        return self.__lower_content.rfind(self._coerce_obj(__sub), __start, __end)

    def rsplit(self, __sep = None, __maxsplit=-1):
        if __sep is None:
            # Default split behavior on whitespace
            return super().rsplit(None, __maxsplit)

        # Case-insensitive split using regular expression
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        split_parts: list[int] = [m.start() for m in pattern.finditer(self.__content)]
        return self._split_by_indices(split_parts, __maxsplit, reverse=True)

    def split(self, sep: str | None = None, maxsplit=-1):
        if sep is None:
            # Default split behavior on whitespace
            return super().split(None, maxsplit)

        # Case-insensitive split using regular expression
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(sep)), re.IGNORECASE)
        split_parts: list[int] = [m.start() for m in pattern.finditer(self.__content)]
        return self._split_by_indices(split_parts, maxsplit)

    def _split_by_indices(self, indices, maxsplit, reverse=False):
        # Split the string using indices from the regular expression
        if maxsplit > 0:
            indices = indices[-maxsplit:] if reverse else indices[:maxsplit]

        last_index = 0
        results = []
        for index in reversed(indices) if reverse else indices:
            results.append(type(self)(self.__content[last_index:index]))
            last_index = index + 1

        results.append(type(self)(self.__content[last_index:]))
        return list(reversed(results)) if reverse else results
