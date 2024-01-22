"""Read documents from RTF 1.5.

http://www.biblioscape.com/rtf15_spec.htm

This module is potentially compatible with RTF versions up to 1.9.1,
but may not ignore all necessary control groups.
"""

from __future__ import annotations

import io
import re
import string

from utility.pyth3 import document
from utility.pyth3.format import PythReader

_CONTROLCHARS = set(string.ascii_letters + string.digits + "-*")
_DIGITS = set(string.digits)


_CODEPAGES = {
    0: "cp1252",  # ANSI
    1: "cp1252",  # Default (this is wrong, but there is no right)
    2: "symbol",  # Symbol
    77: "mac-roman",  # Mac Roman
    # Does Python have built-in support for these? What is it?
    # 78: "10001", # Mac Shift Jis
    # 79: "10003", # Mac Hangul
    # 80: "10008", # Mac GB2312
    # 81: "10002", # Mac Big5
    # 83: "10005", # Mac Hebrew
    84: "mac-arabic",  # Mac Arabic
    85: "mac-greek",  # Mac Greek
    86: "mac-turkish",  # Mac Turkish
    # 87: "10021", # Mac Thai
    # 88: "10029", # Mac East Europe
    # 89: "10007", # Mac Russian
    128: "cp932",  # Shift JIS
    129: "cp949",  # Hangul
    130: "cp1361",  # Johab
    134: "cp936",  # GB2312
    136: "cp950",  # Big5
    161: "cp1253",  # Greek
    162: "cp1254",  # Turkish
    163: "cp1258",  # Vietnamese
    177: "cp1255",  # Hebrew
    178: "cp1256",  # Arabic
    186: "cp1257",  # Baltic
    204: "cp1251",  # Russian
    222: "cp874",  # Thai
    238: "cp1250",  # Eastern European
    254: "cp437",  # PC 437
    255: "cp850",  # OEM
}

# All the ones named by number in my 2.6 encodings dir
_CODEPAGES_BY_NUMBER = {
    x: f"cp{x}"
    for x in ( 37, 1006, 1026, 1140, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258,
              424, 437, 500, 737, 775, 850, 852, 855, 856, 857, 860, 861, 862, 863, 864, 865,
              866, 869, 874, 875, 932, 949, 950)
}

# Miscellaneous, incomplete
_CODEPAGES_BY_NUMBER.update(
    {
        10000: "mac-roman",
        10007: "mac-greek",
    },
)


class BackslashEscapeError(Exception):
    pass


class StrWrapperBytesIO(io.BytesIO):
    def __init__(self, source: io.BytesIO):
        # Copy the buffer from the source BytesIO object
        super().__init__(source.getbuffer())

    def read(self, *args, **kwargs) -> str:
        # Decode the bytes read from the buffer
        return super().read(*args, **kwargs).decode(errors="ignore")

    def read_bytes(self, *args, **kwargs):
        return super().read(*args, **kwargs)


class Rtf15Reader(PythReader):
    @classmethod
    def read(cls, source: io.BytesIO, errors="strict", clean_paragraphs=True) -> document.Document:
        """source: A list of P objects."""
        reader = Rtf15Reader(source, errors, clean_paragraphs)
        return reader.go()

    def __init__(self, source: io.BytesIO, errors="strict", clean_paragraphs=True):
        self.source = StrWrapperBytesIO(source)
        self.errors: str = errors
        self.clean_paragraphs: bool = clean_paragraphs
        self.document = document.Document

    def go(self) -> document.Document:
        self.source.seek(0)

        if self.source.read(5) != r"{\rtf":
            from utility.pyth3.errors import WrongFileType

            msg = "Doesn't look like an RTF file"
            raise WrongFileType(msg)

        self.source.seek(0)

        self.charset_table = None
        self.charset: str = "cp1252"
        self.group: Group = Group(self)
        self.stack: list[Group] = [self.group]
        self.parse()
        return self.build()

    def parse(self):
        while True:
            next_byte = self.source.read_bytes(1)
            next_char = next_byte.decode(errors="ignore")

            if not next_char:
                break

            if next_char in "\r\n":
                continue
            if next_char == "{":
                subGroup = Group(self, self.group, self.charset_table)
                self.stack.append(subGroup)
                subGroup.skip = self.group.skip
                self.group = subGroup
            elif next_char == "}":
                subGroup: Group = self.stack.pop()
                self.group = self.stack[-1]
                subGroup.finalize()

                if subGroup.special_meaning == "FONT_TABLE":
                    self.charset_table = subGroup.charset_table
                self.group.content.append(subGroup)

            elif self.group.skip:
                # Avoid crashing on stuff we can't handle
                # inside groups we don't care about anyway
                continue

            elif next_char == "\\":
                control, digits = self.getControl()
                self.group.handle(control, digits)
            else:
                self.group.char(next_byte)

    def getControl(self) -> tuple[str, str]:
        chars: list[str] = []
        digits: list[str] = []
        current: list[str] = chars
        first = True
        while True:
            next_char: str = self.source.read(1)

            if not next_char:
                break

            if first and next_char in "\\{}":
                chars.extend("control_symbol")
                digits.append(next_char)
                break

            if first and next_char in "\r\n":
                # Special-cased in RTF, equivalent to a \par
                chars.extend("par")
                break

            first = False

            if next_char == "'":
                # ANSI escape, takes two hex digits
                chars.extend("ansi_escape")
                digits.extend(self.source.read(2))
                break

            if next_char == " ":
                # Don't rewind, the space is just a delimiter
                break

            if next_char not in _CONTROLCHARS:
                # Rewind, it's a meaningful character
                self.source.seek(-1, 1)
                break

            if next_char in _DIGITS:
                current = digits

            current.append(next_char)

        return "".join(chars), "".join(digits)

    def build(self) -> document.Document:
        doc = document.Document()

        ctx = DocBuilder(doc, self.clean_paragraphs)

        for bit in self.group.flatten():
            typeName = type(bit).__name__
            getattr(ctx, f"handle_{typeName}", lambda x: str(x))(bit)

        ctx.flushParagraph()

        return doc


class DocBuilder:
    def __init__(
        self,
        doc: document.Document,
        clean_paragraphs: bool = True,
    ):
        self.run: list = []
        self.prop_stack: list[dict] = [{}]
        self.block: document.Paragraph | None = None

        self.isImage: bool = False
        self.list_level: int | None = None
        self.list_stack: list[document.List | document.Document] = [doc]

        self.clean_paragraphs: bool = clean_paragraphs

    def flushRun(self):
        if self.block is None:
            self.block = document.Paragraph()

        if self.isImage:
            self.block.content.append(document.Image(self.prop_stack[-1].copy(), ["".join(self.run)]))
            self.isImage = False
        else:
            self.block.content.append(document.Text(self.prop_stack[-1].copy(), ["".join(self.run)]))

        self.run[:] = []

    def cleanParagraph(self):
        """Compress text runs, remove whitespace at start and end,
        skip empty blocks, etc.
        """
        runs = self.block.content

        if not runs:
            self.block = None
            return

        if not self.clean_paragraphs:
            return

        joined_runs = []
        has_content = False

        for run in runs:
            if run.content[0]:
                has_content = True
            else:
                continue

            # For whitespace-only groups, remove any property stuff,
            # to avoid extra markup in output
            if not run.content[0].strip():
                run.properties = {}

            # Join runs only if their properties match
            if joined_runs and (run.properties == joined_runs[-1].properties):
                joined_runs[-1].content[0] += run.content[0]
            else:
                joined_runs.append(run)

        if has_content:
            # Strip beginning of paragraph
            joined_runs[0].content[0] = joined_runs[0].content[0].lstrip()
            # And then strip the end
            joined_runs[-1].content[0] = joined_runs[-1].content[0].rstrip()
            self.block.content = joined_runs
        else:
            self.block = None

    def flushParagraph(self):
        self.flushRun()
        if self.block.content:
            self.cleanParagraph()
            if self.block is not None:
                self.list_stack[-1].append(self.block)

    def handle_unicode(self, bit):
        self.run.append(bit)

    def handle_Push(self, _):
        self.prop_stack.append(self.prop_stack[-1].copy())

    def handle_Pop(self, _):
        self.flushRun()
        self.prop_stack.pop()

    def handle_Para(self, para: Para):
        self.flushParagraph()

        prev_list_level: int | None = self.list_level
        self.list_level = para.list_level

        if self.list_level > prev_list_level:
            list_doc_obj = document.List()
            self.list_stack.append(list_doc_obj)

        elif self.list_level < prev_list_level:
            list_doc_obj = self.list_stack.pop()
            self.list_stack[-1].append(list_doc_obj)

        self.block = None

    def handle_Pict(self, pict):
        self.flushRun()
        self.isImage = True

    def handle_Reset(self, _):
        self.flushRun()
        self.prop_stack[-1].clear()

    def handle_ReadableMarker(self, marker: ImageMarker):
        self.flushRun()
        if marker.val:
            # RTF needs underline markers for hyperlinks,
            # but nothing else does. If we're in a hyperlink,
            # ignore underlines.
            if "url" in self.prop_stack[-1] and marker.name == "underline":
                return

            self.prop_stack[-1][marker.name] = marker.val
        elif marker.name in self.prop_stack[-1]:
            del self.prop_stack[-1][marker.name]

    def handle_ImageMarker(self, marker: ImageMarker):
        if marker.val:
            self.prop_stack[-1][marker.name] = marker.val
        elif marker.name in self.prop_stack[-1]:
            # Is there any toggle that is applied to images?
            del self.prop_stack[-1][marker.name]
        else:
            self.prop_stack[-1][marker.name] = True


class Group:
    def __init__(self, reader, parent=None, charset_table: dict[int, str] | None =None):
        self.reader = reader
        self.parent = parent

        if parent:
            self.props = parent.props.copy()
            self.charset = self.parent.charset
        else:
            self.props = {}
            self.charset = self.reader.charset

        self.special_meaning = None
        self.skip: bool = False
        self.url = None
        self.image = None
        self.current_para_tag = None
        self.destination: bool = False

        self.charset_table: dict[int, str] | None = charset_table

        self.content: list = []

    def handle(self, control, digits):
        if control == "*":
            self.destination = True
            return

        if self.image and control in {"emfblip", "pngblip", "jpegblip", "macpict", "pmmetafile", "wmetafile", "dibitmap", "wbitmap",
                                      "wbmbitspixel", "wbmplanes", "wbmwidthbytes", "picw", "pich", "picwgoal", "pichgoal", "picscalex",
                                      "picscaley", "picscaled", "piccropt", "piccropb", "piccropr", "piccropl", "picbmp", "picbpp", "bin",
                                      "blipupi", "blipuid", "bliptag"}:
            self.content.append(ImageMarker(control, digits))
            return

        handler = getattr(self, f"handle_{control}", None)
        if handler is None:
            return

        if digits:
            handler(digits)
        else:
            handler()

    def char(self, char: bytes):
        self.content.append(char.decode(self.charset, self.reader.errors))

    def _finalize(self):
        if self.destination:
            self.skip = True

        if self.special_meaning is not None:
            self.skip = True

        if self.skip:
            return

        stuff = []
        i: int = 0
        while i < len(self.content):
            thing = self.content[i]
            if isinstance(thing, Skip):
                i += thing.count
            else:
                stuff.append(thing)
            i += 1

        self.content = stuff

    # This is only the default,
    # and is overridden by some controls
    finalize = _finalize

    def flatten(self):
        if self.skip:
            return []

        stuff: list[type[Push | Pop]] = [Push]
        for thing in self.content:
            if isinstance(thing, Group):
                stuff.extend(thing.flatten())
            else:
                stuff.append(thing)
        stuff.append(Pop)

        return stuff

    # Header stuff
    def handle_ansi(self):
        self.charset = self.reader.charset = "cp1252"

    def handle_mac(self):
        self.charset = self.reader.charset = "mac-roman"

    def handle_pc(self):
        self.charset = self.reader.charset = "cp437"

    def handle_pca(self):
        self.charset = self.reader.charset = "cp850"

    def handle_ansicpg(self, codepage):
        codepage = int(codepage)
        if codepage in _CODEPAGES_BY_NUMBER:
            self.charset = self.reader.charset = _CODEPAGES_BY_NUMBER[codepage]
        else:
            raise ValueError(f"Unknown codepage {codepage}")

    def handle_fonttbl(self):
        self.special_meaning = "FONT_TABLE"
        self.charset_table = {}

    def _setFontCharset(self, charset=None):
        if charset is None:
            charset = self.reader.charset
        # XXX Todo: Figure out a more graceful way to handle the fact that
        # RTF font declarations can be in their own groups or not
        if self.parent.charset_table is not None:
            self.parent.charset_table[self.font_num] = charset
        else:
            self.charset_table[self.font_num] = charset

    def handle_f(self, font_num):
        if "FONT_TABLE" in (self.parent.special_meaning, self.special_meaning):
            self.font_num = int(font_num)
            self._setFontCharset()
        elif self.charset_table is not None:
            try:
                self.charset = self.charset_table[int(font_num)]
            except KeyError:
                # font_num not found in charset_table, ignore if requested
                if self.reader.errors != "ignore":
                    raise

    def handle_fcharset(self, charset_num):
        if "FONT_TABLE" in (self.parent.special_meaning, self.special_meaning):
            # Theoretically, \fN should always be before \fcharsetN
            # I don't really expect that will always be true, but let's crash
            # if it's not, and see if it happens in the real world.
            charset: str | None = _CODEPAGES.get(int(charset_num))

            if charset is None:
                raise ValueError(f"Unsupported charset {charset_num}")
            self._setFontCharset(charset)

    def handle_ansi_escape(self, code):
        code = int(code, 16)

        if isinstance(self.charset, dict):
            uni_code = self.charset.get(code)
            char = "?" if uni_code is None else chr(uni_code)

        else:
            char = bytes([code]).decode(self.charset, self.reader.errors)

        self.content.append(char)

    def handle_control_symbol(self, symbol):
        # Ignore ~, -, and _, since they are optional crap.
        if symbol in "\\{}":
            self.content.append(str(symbol))

    def handle_u(self, codepoint):
        codepoint = int(codepoint)
        try:
            char = chr(codepoint)
        except ValueError:
            if self.reader.errors == "replace":
                char = "?"
            else:
                raise

        self.content.append(char)
        self.content.append(Skip(self.props.get("unicode_skip", 1)))

    def handle_par(self):
        p = Para()
        self.content.append(p)
        self.current_para_tag = p

    def handle_pard(self):
        self.content.append(Reset)

    def handle_plain(self):
        self.content.append(Reset)

    def handle_line(self):
        self.content.append("\n")

    def handle_b(self, on_off=None):
        val = on_off in (None, "", "1")
        self.content.append(ReadableMarker("bold", val))

    def handle_i(self, on_off=None):
        val = on_off in (None, "", "1")
        self.content.append(ReadableMarker("italic", val))

    def handle_ul(self, on_off=None):
        val = on_off in (None, "", "1")
        self.content.append(ReadableMarker("underline", val))

    def handle_ilvl(self, level):
        if self.current_para_tag is not None:
            self.current_para_tag.list_level = level
        else:
            # Well, now we're in trouble. But I'm pretty sure this
            # isn't supposed to happen anyway.
            ...

    def handle_up(self, amount):
        self.content.append(ReadableMarker("super", val=True))

    def handle_super(self):
        self.content.append(ReadableMarker("super", val=True))

    # Turns off superscripting or subscripting
    def handle_nosupersub(self):
        self.content.append(ReadableMarker("sub", val=False))
        self.content.append(ReadableMarker("super", val=False))

    def handle_dn(self, amount):
        self.content.append(ReadableMarker("sub", val=True))

    def handle_sub(self):
        self.content.append(ReadableMarker("sub", val=True))

    def handle_emdash(self):
        self.content.append("\u2014")

    def handle_endash(self):
        self.content.append("\u2013")

    def handle_lquote(self):
        self.content.append("\u2018")

    def handle_rquote(self):
        self.content.append("\u2019")

    def handle_ldblquote(self):
        self.content.append("\u201C")

    def handle_rdblquote(self):
        self.content.append("\u201D")

    def handle_tab(self):
        self.content.append("\t")

    def handle_trowd(self):
        self.content.append("\n")

    # Handle the image tag
    def handle_pict(self):
        p = Pict()
        self.content.append(p)
        self.image = p
        # Remove the destination control group of the parent, so that the image is preserved
        self.parent.destination = False

    def handle_field(self):
        def finalize():
            if len(self.content) != 2:
                return ""

            destination, content = self.content

            # The destination isn't allowed to contain any controls,
            # so this should be safe.
            # Except when it isn't, like this:
            # {\field{\*\fldinst {\rtlch\fcs1 \af0 \ltrch\fcs0 \insrsid15420660  PAGE   \\* MERGEFORMAT }}
            try:
                destination = "".join(destination.content)
            except Exception:  # noqa: BLE001
                return ""

            match: re.Match[str] | None = re.match(r'HYPERLINK "(.*)"', destination)
            if match is not None:
                content.skip = False
                self.content = [ReadableMarker("url", match.group(1)), content]
                return None
            return ""

        self.finalize = finalize

    def __repr__(self):
        return f"G({self.content!r})"

    def ignore(self, _=None):
        self.skip = True

    # Header
    handle_filetbl = ignore
    handle_colortbl = ignore
    handle_stylesheet = ignore
    handle_listtable = ignore
    handle_listoverridetable = ignore
    handle_revtbl = ignore

    handle_mmath = ignore

    handle_header = ignore
    handle_footer = ignore
    handle_headerl = ignore
    handle_headerr = ignore
    handle_headerf = ignore
    handle_footerl = ignore
    handle_footerr = ignore
    handle_footerf = ignore

    # Document
    handle_info = ignore
    handle_docfmt = ignore
    handle_pgdsctbl = ignore
    handle_listtext = ignore

    # Revision hacks
    handle_revauthdel = ignore


class Skip:
    def __init__(self, count: int):
        self.count: int = count


class ReadableMarker:
    def __init__(self, name=None, val=None):
        if name is not None:
            self.name = name
        self.val = val

    def __repr__(self):
        if self.val is None:
            return f"!{self.name}!"
        return f"!{self.name}::{self.val}!"


class ImageMarker(ReadableMarker):
    pass


class Pict(ImageMarker):
    def __init__(self):
        ImageMarker.__init__(self, "Pict")

    def __repr__(self):
        return "!Image!"


class Para(ReadableMarker):
    list_level: int | None = None

    def __init__(self):
        ReadableMarker.__init__(self, "Para")

    def __repr__(self):
        return f"!Para:{self.list_level}!"


class Reset(ReadableMarker):
    name = "Reset"


class Push(ReadableMarker):
    name = "Push"


class Pop(ReadableMarker):
    name = "Pop"


# Yes, yes, I know, I'll clean it up later.
Reset = Reset()
Push = Push()
Pop = Pop()
