from __future__ import annotations

import os
import re

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typing_extensions import LiteralString, Self, SupportsIndex  # pyright: ignore[reportMissingModuleSource]


def insert_newlines(
    text: str,
    length: int = 100,
) -> str:
    words: list[str] = text.split(" ")
    new_string: str = ""
    current_line: str = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= length:
            current_line += f"{word} "
        else:
            new_string += current_line.rstrip() + "\n"
            current_line = f"{word} "

    # Add the last line if there's any content left.
    if current_line:
        new_string += current_line.rstrip()

    return new_string


def ireplace(
    original: str,
    target: str,
    replacement: str,
) -> str:
    if not original or not target:
        return original
    # Initialize an empty result string and a pointer to traverse the original string
    result: str = ""
    i: int = 0

    # Length of the target string
    target_length: int = len(target)

    # Convert the target to lowercase for case-insensitive comparison
    target_lower: str = target.lower()
    original_lower: str = original.lower()

    while i < len(original):
        # If a potential match is found
        if original_lower[i : i + target_length] == target_lower:
            # Add the replacement to the result
            result += replacement
            # Skip the characters of the target
            i += target_length
        else:
            # Add the current character to the result
            result += original[i]
            i += 1
    return result


def format_text(
    text: object,
    max_chars_before_newline: int = 20,
) -> str:
    text_str: str = str(text)
    if "\n" in text_str or len(text_str) > max_chars_before_newline:
        return f'"""{os.linesep}{text_str}{os.linesep}"""'
    return f"'{text_str}'"


def first_char_diff_index(
    str1: str,
    str2: str,
) -> int:
    """Find the index of the first differing character in two strings."""
    min_length: int = min(len(str1), len(str2))
    return next(
        (i for i in range(min_length) if str1[i] != str2[i]),
        min_length if len(str1) != len(str2) else -1,
    )


def generate_diff_marker_line(
    index: int,
    length: int,
) -> str:
    """Generate a line of spaces with a '^' at the specified index."""
    return "" if index == -1 else " " * index + "^" + " " * (length - index - 1)


def compare_and_format(
    old_value: object,
    new_value: object,
) -> tuple[str, str]:
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
    old_text: str = str(old_value)
    new_text: str = str(new_value)
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


def striprtf(text: str) -> str:  # noqa: C901, PLR0915, PLR0912
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
    pattern: re.Pattern[str] = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.IGNORECASE)
    # control words which specify a "destination".
    destinations = frozenset(
        (
            "aftncn",
            "aftnsep",
            "aftnsepc",
            "annotation",
            "atnauthor",
            "atndate",
            "atnicn",
            "atnid",
            "atnparent",
            "atnref",
            "atntime",
            "atrfend",
            "atrfstart",
            "author",
            "background",
            "bkmkend",
            "bkmkstart",
            "blipuid",
            "buptim",
            "category",
            "colorschememapping",
            "colortbl",
            "comment",
            "company",
            "creatim",
            "datafield",
            "datastore",
            "defchp",
            "defpap",
            "do",
            "doccomm",
            "docvar",
            "dptxbxtext",
            "ebcend",
            "ebcstart",
            "factoidname",
            "falt",
            "fchars",
            "ffdeftext",
            "ffentrymcr",
            "ffexitmcr",
            "ffformat",
            "ffhelptext",
            "ffl",
            "ffname",
            "ffstattext",
            "field",
            "file",
            "filetbl",
            "fldinst",
            "fldrslt",
            "fldtype",
            "fname",
            "fontemb",
            "fontfile",
            "fonttbl",
            "footer",
            "footerf",
            "footerl",
            "footerr",
            "footnote",
            "formfield",
            "ftncn",
            "ftnsep",
            "ftnsepc",
            "g",
            "generator",
            "gridtbl",
            "header",
            "headerf",
            "headerl",
            "headerr",
            "hl",
            "hlfr",
            "hlinkbase",
            "hlloc",
            "hlsrc",
            "hsv",
            "htmltag",
            "info",
            "keycode",
            "keywords",
            "latentstyles",
            "lchars",
            "levelnumbers",
            "leveltext",
            "lfolevel",
            "linkval",
            "list",
            "listlevel",
            "listname",
            "listoverride",
            "listoverridetable",
            "listpicture",
            "liststylename",
            "listtable",
            "listtext",
            "lsdlockedexcept",
            "macc",
            "maccPr",
            "mailmerge",
            "maln",
            "malnScr",
            "manager",
            "margPr",
            "mbar",
            "mbarPr",
            "mbaseJc",
            "mbegChr",
            "mborderBox",
            "mborderBoxPr",
            "mbox",
            "mboxPr",
            "mchr",
            "mcount",
            "mctrlPr",
            "md",
            "mdeg",
            "mdegHide",
            "mden",
            "mdiff",
            "mdPr",
            "me",
            "mendChr",
            "meqArr",
            "meqArrPr",
            "mf",
            "mfName",
            "mfPr",
            "mfunc",
            "mfuncPr",
            "mgroupChr",
            "mgroupChrPr",
            "mgrow",
            "mhideBot",
            "mhideLeft",
            "mhideRight",
            "mhideTop",
            "mhtmltag",
            "mlim",
            "mlimloc",
            "mlimlow",
            "mlimlowPr",
            "mlimupp",
            "mlimuppPr",
            "mm",
            "mmaddfieldname",
            "mmath",
            "mmathPict",
            "mmathPr",
            "mmaxdist",
            "mmc",
            "mmcJc",
            "mmconnectstr",
            "mmconnectstrdata",
            "mmcPr",
            "mmcs",
            "mmdatasource",
            "mmheadersource",
            "mmmailsubject",
            "mmodso",
            "mmodsofilter",
            "mmodsofldmpdata",
            "mmodsomappedname",
            "mmodsoname",
            "mmodsorecipdata",
            "mmodsosort",
            "mmodsosrc",
            "mmodsotable",
            "mmodsoudl",
            "mmodsoudldata",
            "mmodsouniquetag",
            "mmPr",
            "mmquery",
            "mmr",
            "mnary",
            "mnaryPr",
            "mnoBreak",
            "mnum",
            "mobjDist",
            "moMath",
            "moMathPara",
            "moMathParaPr",
            "mopEmu",
            "mphant",
            "mphantPr",
            "mplcHide",
            "mpos",
            "mr",
            "mrad",
            "mradPr",
            "mrPr",
            "msepChr",
            "mshow",
            "mshp",
            "msPre",
            "msPrePr",
            "msSub",
            "msSubPr",
            "msSubSup",
            "msSubSupPr",
            "msSup",
            "msSupPr",
            "mstrikeBLTR",
            "mstrikeH",
            "mstrikeTLBR",
            "mstrikeV",
            "msub",
            "msubHide",
            "msup",
            "msupHide",
            "mtransp",
            "mtype",
            "mvertJc",
            "mvfmf",
            "mvfml",
            "mvtof",
            "mvtol",
            "mzeroAsc",
            "mzeroDesc",
            "mzeroWid",
            "nesttableprops",
            "nextfile",
            "nonesttables",
            "objalias",
            "objclass",
            "objdata",
            "object",
            "objname",
            "objsect",
            "objtime",
            "oldcprops",
            "oldpprops",
            "oldsprops",
            "oldtprops",
            "oleclsid",
            "operator",
            "panose",
            "password",
            "passwordhash",
            "pgp",
            "pgptbl",
            "picprop",
            "pict",
            "pn",
            "pnseclvl",
            "pntext",
            "pntxta",
            "pntxtb",
            "printim",
            "private",
            "propname",
            "protend",
            "protstart",
            "protusertbl",
            "pxe",
            "result",
            "revtbl",
            "revtim",
            "rsidtbl",
            "rxe",
            "shp",
            "shpgrp",
            "shpinst",
            "shppict",
            "shprslt",
            "shptxt",
            "sn",
            "sp",
            "staticval",
            "stylesheet",
            "subject",
            "sv",
            "svb",
            "tc",
            "template",
            "themedata",
            "title",
            "txe",
            "ud",
            "upr",
            "userprops",
            "wgrffmtfilter",
            "windowcaption",
            "writereservation",
            "writereservhash",
            "xe",
            "xform",
            "xmlattrname",
            "xmlattrvalue",
            "xmlclose",
            "xmlname",
            "xmlnstbl",
            "xmlopen",
        )
    )
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
        "rdblquote": "\u201d",
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
                    out.append("\xa0")
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
                curskip: int = ucskip
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


def is_string_like(obj: Any) -> bool:  # sourcery skip: use-fstring-for-concatenation
    try:
        _ = obj + ""
    except Exception:  # pylint: disable=W0718  # noqa: BLE001
        return False
    else:
        return True


class StrType(type):
    def __instancecheck__(cls, instance):  # sourcery skip: instance-method-first-arg-name
        instance_type = instance.__class__
        mro = instance_type.__mro__
        if cls in {str, WrappedStr}:
            return instance_type in {WrappedStr, str} or WrappedStr in mro or str in mro
        return cls in mro

    def __subclasscheck__(cls, subclass):  # sourcery skip: instance-method-first-arg-name
        mro = subclass.__mro__
        if cls in {str, WrappedStr}:
            return subclass in {WrappedStr, str} or WrappedStr in mro or str in mro
        return cls in mro


StrictStr = TypeVar("StrictStr", bound=str)


class WrappedStr(str):  # (metaclass=StrType):  # noqa: PLR0904
    __slots__: tuple[str, ...] = ("_content",)

    @classmethod
    def _assert_str_type(
        cls: type[Self],
        var: str,
    ) -> str:  # sourcery skip: remove-unnecessary-cast
        if var is None:
            return None  # type: ignore[return-value]
        if not isinstance(var, (cls, str)):
            msg = f"Expected str-like, got '{var}' of type {var.__class__}"
            raise TypeError(msg)
        return str(var)

    @classmethod
    def cast(
        cls: type[Self],
        unk_str: str,
    ) -> Self:
        return unk_str if isinstance(unk_str, cls) else cls(unk_str)

    def __init__(
        self,
        content: Self | str = "",
    ):
        if content is None:
            msg = f"Cannot initialize {self.__class__.__name__}(None), expected a str-like argument"
            raise RuntimeError(msg)
        if isinstance(content, WrappedStr):
            content = content._content  # noqa: SLF001
        self._content: str = content

    @classmethod
    def maketrans(
        cls,
        __x: Self | str,
        __y: Self | str,
        __z: Self | str,
        /,
    ) -> dict[int, int | None]:
        return super().maketrans(cls._assert_str_type(__x), cls._assert_str_type(__y), cls._assert_str_type(__z))

    def __setattr__(
        self,
        __name: str,
        __value: Any,
        /,
    ):
        if hasattr(self, __name):
            msg = f"{self.__class__.__name__} is immutable, cannot evaluate `{self!r}.setattr({__name!r}, {__value!r})`"
            raise RuntimeError(msg)
        return super().__setattr__(__name, __value)

    def __len__(self):
        return len(self._content)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._content})"

    def __str__(self):
        return self._content

    def __eq__(
        self,
        __value: object,
        /,
    ):
        if self is __value:
            return True
        return self._content == self._assert_str_type(__value)  # pyright: ignore[reportArgumentType]

    def __hash__(self):
        return hash(self._content)

    def __ne__(
        self,
        __value: object,
        /,
    ):
        return self._content != self._assert_str_type(__value)  # pyright: ignore[reportArgumentType]

    def __iter__(self):
        for i in range(len(self._content)):
            yield self.__class__(self._content[i])

    def __deepcopy__(
        self,
        memo: Any,
    ):
        # Create a new instance with the same content
        new_copy = self.__class__(self._content)
        # Add the new object to the memo dictionary to handle circular references
        memo[id(self)] = new_copy
        return new_copy

    def __getitem__(
        self,
        __key: SupportsIndex | slice,
        /,
    ):
        return self.__class__(self._content[__key])

    def __contains__(
        self,
        __key: str | WrappedStr,  # type: ignore[override]
        /,
    ) -> bool:
        return self._assert_str_type(__key) in self._content

    def __add__(
        self,
        __value: LiteralString | str | WrappedStr,
        /,
    ):
        return self.__class__(self._content + self._assert_str_type(__value))

    def __radd__(
        self,
        __value: LiteralString | str | WrappedStr,
        /,
    ):
        return self.__class__(self._assert_str_type(__value) + self._content)

    def __mod__(
        self,
        __value: LiteralString | str | WrappedStr | tuple[LiteralString, ...] | tuple[str, ...] | tuple[WrappedStr, ...],
        /,
    ):
        parsed_value: tuple[str, ...] | str = tuple(self._assert_str_type(s) for s in __value) if isinstance(__value, tuple) else self._assert_str_type(__value)
        return self.__class__(self._content % parsed_value)

    def __mul__(
        self,
        __value: SupportsIndex,
        /,
    ):
        return self.__class__(self._content * __value)

    def __rmul__(
        self,
        __value: SupportsIndex,
        /,
    ):
        return self.__class__(__value * self._content)

    def __lt__(
        self,
        __value: str | WrappedStr,
        /,
    ):
        return self._content < self._assert_str_type(__value)

    def __le__(
        self,
        __value: str | WrappedStr,
        /,
    ):
        return self._content <= self._assert_str_type(__value)

    def __gt__(
        self,
        __value: str | WrappedStr,
        /,
    ):
        return self._content > self._assert_str_type(__value)

    def __ge__(
        self,
        __value: str | WrappedStr,
        /,
    ):
        return self._content >= self._assert_str_type(__value)

    # String Methods
    def capitalize(self) -> Self:
        """Return a capitalized version of the string.

        More specifically, make the first character have upper case and the rest lower case.
        """
        return self.__class__(self._content.capitalize())

    def casefold(self) -> Self:
        """Return a version of the string suitable for caseless comparisons."""
        return self.__class__(self._content.casefold())

    def center(
        self,
        __width: SupportsIndex,
        __fillchar: WrappedStr | str = " ",
        /,
    ) -> Self:
        """Return a centered string of length width.

        Padding is done using the specified fill character (default is a space).
        """
        return self.__class__(self._content.center(__width, self._assert_str_type(__fillchar)))

    def count(
        self,
        x: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> int:
        """S.count(sub[, start[, end]]) -> int

        Return the number of non-overlapping occurrences of substring sub in
        string S[start:end]. Optional arguments start and end are interpreted as in slice notation.
        """  # noqa: D415, D402, D400
        return self._content.count(self._assert_str_type(x), __start, __end)

    def encode(
        self,
        encoding: WrappedStr | str = "utf-8",
        errors: WrappedStr | str = "strict",
        /,
    ) -> bytes:
        """Encode the string using the codec registered for encoding.

        encoding
            The encoding in which to encode the string.
        errors
            The error handling scheme to use for encoding errors. The default is 'strict' meaning that encoding errors raise a UnicodeEncodeError. Other possible values are 'ignore', 'replace' and 'xmlcharrefreplace' as well as any other name registered with codecs.register_error that can handle UnicodeEncodeErrors.
        """  # noqa: E501, W505
        return self._content.encode(self._assert_str_type(encoding), self._assert_str_type(errors))

    def endswith(
        self,
        __suffix: WrappedStr | str | tuple[WrappedStr | str, ...],
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> bool:
        """S.endswith(suffix[, start[, end]]) -> bool

        Return True if S ends with the specified suffix, False otherwise. With optional start, test S beginning at that position. With optional end, stop comparing S at that position. suffix can also be a tuple of strings to try.
        """  # noqa: D415, D400, D402, E501, W505
        parsed_suffix: tuple[str, ...] | str = tuple(self._assert_str_type(s) for s in __suffix) if isinstance(__suffix, tuple) else self._assert_str_type(__suffix)
        return self._content.endswith(parsed_suffix, __start, __end)

    def expandtabs(
        self,
        tabsize: int = 8,
        /,
    ) -> Self:
        """Return a copy where all tab characters are expanded using spaces.

        If tabsize is not given, a tab size of 8 characters is assumed.
        """
        return self.__class__(self._content.expandtabs(tabsize))

    def find(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> int:
        """S.find(sub[, start[, end]]) -> int

        Return the lowest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice notation.

        Return -1 on failure.
        """  # noqa: D415, D400, D402
        return self._content.find(self._assert_str_type(__sub), __start, __end)

    def format(
        self,
        *args: object,
        **kwargs: object,
    ) -> Self:
        """S.format(*args, **kwargs) -> str

        Return a formatted version of S, using substitutions from args and kwargs. The substitutions are identified by braces ('{' and '}').
        """  # noqa: D415, D400, D402
        return self.__class__(self._content.format(*args, **kwargs))

    def format_map(
        self,
        map,  # noqa: A002, ANN001
    ) -> Self:
        """S.format_map(mapping) -> str

        Return a formatted version of S, using substitutions from mapping. The substitutions are identified by braces ('{' and '}').
        """  # noqa: D415, D402, D400
        return self.__class__(self._content.format_map(map))

    def index(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> int:
        """S.index(sub[, start[, end]]) -> int

        Return the lowest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice notation.

        Raises ValueError when the substring is not found.
        """  # noqa: D415, D400, D402
        return self._content.index(self._assert_str_type(__sub), __start, __end)

    def isalnum(self) -> bool:
        """Return True if the string is an alpha-numeric string, False otherwise.

        A string is alpha-numeric if all characters in the string are alpha-numeric and there is at least one character in the string.
        """
        return self._content.isalnum()

    def isalpha(self) -> bool:
        """Return True if the string is an alphabetic string, False otherwise.

        A string is alphabetic if all characters in the string are alphabetic and there is at least one character in the string.
        """
        return self._content.isalpha()

    def isascii(self) -> bool:
        """Return True if all characters in the string are ASCII, False otherwise.

        ASCII characters have code points in the range U+0000-U+007F. Empty string is ASCII too.
        """
        return self._content.isascii()

    def isdecimal(self) -> bool:
        """Return True if the string is a decimal string, False otherwise.

        A string is a decimal string if all characters in the string are decimal and there is at least one character in the string.
        """
        return self._content.isdecimal()

    def isdigit(self) -> bool:
        """Return True if the string is a digit string, False otherwise.

        A string is a digit string if all characters in the string are digits and there is at least one character in the string.
        """
        return self._content.isdigit()

    def isidentifier(self) -> bool:
        """Return True if the string is a valid Python identifier, False otherwise.

        Call keyword.iskeyword(s) to test whether string s is a reserved identifier, such as "def" or "class".
        """
        return self._content.isidentifier()

    def islower(self) -> bool:
        """Return True if the string is a lowercase string, False otherwise.

        A string is lowercase if all cased characters in the string are lowercase and there is at least one cased character in the string.
        """
        return self._content.islower()

    def isnumeric(self) -> bool:
        """Return True if the string is a numeric string, False otherwise.

        A string is numeric if all characters in the string are numeric and there is at least one character in the string.
        """
        return self._content.isnumeric()

    def isprintable(self) -> bool:
        """Return True if the string is printable, False otherwise.

        A string is printable if all of its characters are considered printable in repr() or if it is empty.
        """
        return self._content.isprintable()

    def isspace(self) -> bool:
        """Return True if the string is a whitespace string, False otherwise.

        A string is whitespace if all characters in the string are whitespace and there is at least one character in the string.
        """
        return self._content.isspace()

    def istitle(self) -> bool:
        """Return True if the string is a title-cased string, False otherwise.

        In a title-cased string, upper- and title-case characters may only follow uncased characters and lowercase characters only cased ones.
        """
        return self._content.istitle()

    def isupper(self) -> bool:
        """Return True if the string is an uppercase string, False otherwise.

        A string is uppercase if all cased characters in the string are uppercase and there is at least one cased character in the string.
        """
        return self._content.isupper()

    def join(
        self,
        __iterable: Iterable[str] | Iterable[WrappedStr] | Iterable[str | WrappedStr],
        /,
    ) -> Self:
        """Concatenate any number of strings.

        The string whose method is called is inserted in between each given string. The result is returned as a new string.

        Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'
        """
        return self.__class__(self._content.join(self._assert_str_type(s) for s in __iterable))

    def ljust(
        self,
        __width: SupportsIndex,
        __fillchar: WrappedStr | str = " ",
        /,
    ) -> Self:
        """Return a left-justified string of length width.

        Padding is done using the specified fill character (default is a space).
        """
        return self.__class__(self._content.ljust(__width, self._assert_str_type(__fillchar)))

    def lower(self) -> Self:
        """Return a copy of the string converted to lowercase."""
        return self.__class__(self._content.lower())

    def lstrip(
        self,
        __chars: WrappedStr | str | None = None,
        /,
    ) -> Self:
        """Return a copy of the string with leading whitespace removed.

        If chars is given and not None, remove characters in chars instead.
        """
        return self.__class__(self._content.lstrip(self._assert_str_type(__chars or "")))

    def partition(
        self,
        __sep: WrappedStr | str,
        /,
    ) -> tuple[Self, Self, Self]:
        """Partition the string into three parts using the given separator.

        This will search for the separator in the string. If the separator is found, returns a 3-tuple containing the part before the separator, the separator itself, and the part after it.

        If the separator is not found, returns a 3-tuple containing the original string and two empty strings.
        """
        a, b, c = self._content.partition(self._assert_str_type(__sep))
        return (self.__class__(a), self.__class__(b), self.__class__(c))

    def removeprefix(
        self,
        __prefix: WrappedStr | str,
        /,
    ) -> Self:
        parsed_prefix: str = self._assert_str_type(__prefix)
        if self._content.startswith(parsed_prefix):
            return self.__class__(self._content[: len(parsed_prefix)])
        return self.__class__(self._content)

    def removesuffix(
        self,
        __suffix: WrappedStr | str,
        /,
    ) -> Self:
        parsed_suffix: str = self._assert_str_type(__suffix)
        if self._content.endswith(parsed_suffix):
            return self.__class__(self._content[-len(parsed_suffix) :])
        return self.__class__(self._content)

    def replace(
        self,
        __old: WrappedStr | str,
        __new: WrappedStr | str,
        __count: SupportsIndex = -1,
        /,
    ) -> Self:
        """Return a copy with all occurrences of substring old replaced by new.

        count
            Maximum number of occurrences to replace. -1 (the default value) means replace all occurrences.

        If the optional argument count is given, only the first count occurrences are replaced.
        """
        return self.__class__(
            self._content.replace(
                self._assert_str_type(__old),
                self._assert_str_type(__new),
                __count,
            ),
        )

    def rfind(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> int:
        """S.rfind(sub[, start[, end]]) -> int

        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice notation.

        Return -1 on failure.
        """  # noqa: D415, D402, D400
        return self._content.rfind(self._assert_str_type(__sub), __start, __end)

    def rindex(
        self,
        __sub: WrappedStr | str,
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> int:
        """S.rindex(sub[, start[, end]]) -> int

        Return the highest index in S where substring sub is found,
        such that sub is contained within S[start:end]. Optional arguments start and end are interpreted as in slice notation.

        Raises ValueError when the substring is not found.
        """  # noqa: D415, D400, D402
        return self._content.rindex(self._assert_str_type(__sub), __start, __end)

    def rjust(
        self,
        __width: SupportsIndex,
        __fillchar: WrappedStr | str = " ",
        /,
    ) -> Self:
        """Return a right-justified string of length width.

        Padding is done using the specified fill character (default is a space).
        """
        return self.__class__(self._content.rjust(__width, self._assert_str_type(__fillchar)))

    def rpartition(
        self,
        __sep: WrappedStr | str,
        /,
    ) -> tuple[Self, Self, Self]:
        """Partition the string into three parts using the given separator.

        This will search for the separator in the string, starting at the end. If the separator is found, returns a 3-tuple containing the part before the separator, the separator itself, and the part after it.

        If the separator is not found, returns a 3-tuple containing two empty strings and the original string.
        """
        a, b, c = self._content.rpartition(self._assert_str_type(__sep))
        return (self.__class__(a), self.__class__(b), self.__class__(c))

    def rsplit(  # type: ignore[override]
        self,
        __sep: WrappedStr | str | None = None,
        __maxsplit: SupportsIndex = -1,
        /,
    ) -> list[Self]:
        """Return a list of the words in the string, using sep as the delimiter string.

        sep
            The delimiter according which to split the string. None (the default value) means split according to any whitespace, and discard empty strings from the result.
        maxsplit
            Maximum number of splits to do. -1 (the default value) means no limit.

        Splits are done starting at the end of the string and working to the front.
        """
        cls: type[Self] = self.__class__
        return [cls(s) for s in self._content.rsplit(self._assert_str_type(__sep or ""), __maxsplit)]

    def rstrip(
        self,
        __chars: WrappedStr | str | None = None,
        /,
    ) -> Self:
        """Return a copy of the string with trailing whitespace removed.

        If chars is given and not None, remove characters in chars instead.
        """
        return self.__class__(self._content.rstrip(self._assert_str_type(__chars or "")))

    def split(  # type: ignore[override]
        self,
        sep: WrappedStr | str | None = None,
        maxsplit: SupportsIndex = -1,
        /,
    ) -> list[Self]:
        """Return a list of the words in the string, using sep as the delimiter string.

        sep
          The delimiter according which to split the string. None (the default value) means split according to any whitespace, and discard empty strings from the result.
        maxsplit
          Maximum number of splits to do. -1 (the default value) means no limit.
        """
        return [self.__class__(s) for s in self._content.split(self._assert_str_type(sep or ""), maxsplit)]

    def splitlines(  # type: ignore[override]
        self,
        keepends: bool = False,  # noqa: FBT001, FBT002
        /,
    ) -> list[Self]:
        """Return a list of the lines in the string, breaking at line boundaries.

        Line breaks are not included in the resulting list unless keepends is given and true.
        """
        return [self.__class__(s) for s in self._content.splitlines(keepends)]

    def startswith(
        self,
        __prefix: WrappedStr | str | tuple[WrappedStr | str, ...],
        __start: SupportsIndex | None = None,
        __end: SupportsIndex | None = None,
        /,
    ) -> bool:
        """S.startswith(prefix[, start[, end]]) -> bool

        Return True if S starts with the specified prefix, False otherwise. With optional start, test S beginning at that position. With optional end, stop comparing S at that position. prefix can also be a tuple of strings to try.
        """  # noqa: D415, D402, D400
        if isinstance(__prefix, tuple):
            __prefix = tuple(self._assert_str_type(item) for item in __prefix)
        else:
            __prefix = self._assert_str_type(__prefix)
        return self._content.startswith(__prefix, __start, __end)

    def strip(
        self,
        __chars: WrappedStr | str | None = None,
        /,
    ) -> Self:
        """Return a copy of the string with leading and trailing whitespace removed.

        If chars is given and not None, remove characters in chars instead.
        """
        return self.__class__(self._content.strip(self._assert_str_type(__chars or "")))

    def swapcase(self) -> Self:
        """Convert uppercase characters to lowercase and lowercase characters to uppercase."""
        return self.__class__(self._content.swapcase())

    def title(self) -> Self:
        """Return a version of the string where each word is titlecased.

        More specifically, words start with uppercased characters and all remaining cased characters have lower case.
        """
        return self.__class__(self._content.title())

    def translate(
        self,
        __table,  # noqa: ANN001
    ) -> Self:
        """Replace each character in the string using the given translation table.

        table
            Translation table, which must be a mapping of Unicode ordinals to Unicode ordinals, strings, or None.

        The table must implement lookup/indexing via __getitem__, for instance a dictionary or list. If this operation raises LookupError, the character is left untouched. Characters mapped to None are deleted.
        """
        return self.__class__(self._content.translate(__table))

    def upper(self) -> Self:
        """Return a copy of the string converted to uppercase."""
        return self.__class__(self._content.upper())

    def zfill(
        self,
        __width: SupportsIndex,
        /,
    ) -> Self:
        """Pad a numeric string with zeros on the left, to fill a field of the given width.

        The string is never truncated.
        """
        return self.__class__(self._content.zfill(__width))

    # Magic methods for string representation
    def __getnewargs__(self) -> tuple[str]:
        return (self._content,)

    def __getstate__(self) -> str:
        return self._content


class CaseInsensitiveWrappedStr(WrappedStr):
    __slots__: tuple[str, ...] = ("_lower_content",)

    @classmethod
    def _coerce_str(
        cls,
        item: Any,
    ) -> str:  # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(item, WrappedStr):
            return str(item._content).casefold()  # noqa: SLF001
        if isinstance(item, str):
            return str(item).casefold()
        return item

    def __init__(
        self,
        content: str | WrappedStr,
    ):
        super().__init__(content)
        self._lower_content: str = str(content).casefold()

    def __contains__(
        self,
        __key,
        /,
    ):
        return self._lower_content.__contains__(self._coerce_str(__key))

    def __eq__(
        self,
        __value,
        /,
    ):
        if self is __value:
            return True
        return self._lower_content.__eq__(self._coerce_str(__value))

    def __ne__(
        self,
        __value,
        /,
    ):
        return self._lower_content.__ne__(self._coerce_str(__value))

    def __hash__(self):
        return hash(self._lower_content)

    def find(
        self,
        sub,
        start=0,
        end=None,
        /,
    ):
        return self._lower_content.find(self._coerce_str(sub), start, end)

    def partition(
        self,
        __sep,
        /,
    ):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        match: re.Match[str] | None = pattern.search(self._content)

        if match is None:
            return (self.__class__(self._content), self.__class__(""), self.__class__(""))

        idx: int = match.start()
        return (
            self.__class__(self._content[:idx]),
            self.__class__(self._content[idx : idx + len(__sep)]),
            self.__class__(self._content[idx + len(__sep) :]),
        )

    def replace(
        self,
        __old,
        __new,
        __count=-1,
        /,
    ):
        """Case-insensitive replace function matching the builtin str.replace's functionality."""
        # Replace each backslash in __new with two backslashes
        __new_escaped = self._coerce_str(__new).replace("\\", "\\\\")

        # Check for the special case where 'old' is an empty string
        if not __old:
            return super().replace("", self._coerce_str(__new), __count)

        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__old)), re.IGNORECASE)
        return self.__class__(pattern.sub(__new_escaped, self._content, int(__count)))

    def rpartition(
        self,
        __sep,
        /,
    ):
        # Find the position of the separator in a case-insensitive manner
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        matches = list(pattern.finditer(self._content))

        if not matches:
            return (self.__class__(""), self.__class__(""), self.__class__(self._content))
        match: re.Match[str] = matches[-1]  # Get the last match for rpartition
        idx: int = match.start()
        return (
            self.__class__(self._content[:idx]),
            self.__class__(self._content[idx : idx + len(__sep)]),
            self.__class__(self._content[idx + len(__sep) :]),
        )

    def rfind(
        self,
        __sub,
        __start=None,
        __end=None,
        /,
    ):  # sourcery skip: remove-unnecessary-cast
        return self._lower_content.rfind(self._coerce_str(__sub), __start, __end)

    def rsplit(
        self,
        __sep=None,
        __maxsplit=-1,
        /,
    ):
        if __sep is None:
            # Default split behavior on whitespace
            return super().rsplit(None, __maxsplit)

        # Case-insensitive split using regular expression
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(__sep)), re.IGNORECASE)
        split_parts: list[int] = [m.start() for m in pattern.finditer(self._content)]
        return self._split_by_indices(split_parts, int(__maxsplit), reverse=True)

    def split(
        self,
        sep=None,
        maxsplit=-1,
        /,
    ):
        if sep is None:
            # Default split behavior on whitespace
            return super().split(None, maxsplit)

        # Case-insensitive split using regular expression
        pattern: re.Pattern[str] = re.compile(re.escape(self._coerce_str(sep)), re.IGNORECASE)
        split_parts: list[int] = [m.start() for m in pattern.finditer(self._content)]
        return self._split_by_indices(split_parts, int(maxsplit))

    def _split_by_indices(
        self,
        indices: list[int],
        maxsplit: int,
        reverse: bool = False,  # noqa: FBT001, FBT002
    ) -> list[Self]:
        # Split the string using indices from the regular expression
        if maxsplit > 0:
            indices = indices[-maxsplit:] if reverse else indices[:maxsplit]

        last_index: int = 0
        results: list[Self] = []
        for index in reversed(indices) if reverse else indices:
            results.append(self.__class__(self._content[last_index:index]))
            last_index = index + 1

        results.append(self.__class__(self._content[last_index:]))
        return list(reversed(results)) if reverse else results
