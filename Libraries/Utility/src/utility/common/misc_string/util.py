from __future__ import annotations

import os
import re


def insert_newlines(text: str, length: int = 100) -> str:
    words = text.split(" ")
    new_string = ""
    current_line = ""

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


def ireplace(original: str, target: str, replacement: str) -> str:
    if not original or not target:
        return original
    # Initialize an empty result string and a pointer to traverse the original string
    result: str = ""
    i = 0

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


def format_text(text: object, max_chars_before_newline: int = 20) -> str:
    text_str = str(text)
    if "\n" in text_str or len(text_str) > max_chars_before_newline:
        return f'"""{os.linesep}{text_str}{os.linesep}"""'
    return f"'{text_str}'"


def first_char_diff_index(str1: str, str2: str) -> int:
    """Find the index of the first differing character in two strings."""
    min_length = min(len(str1), len(str2))
    return next(
        (i for i in range(min_length) if str1[i] != str2[i]),
        min_length if len(str1) != len(str2) else -1,
    )


def generate_diff_marker_line(index: int, length: int) -> str:
    """Generate a line of spaces with a '^' at the specified index."""
    return "" if index == -1 else " " * index + "^" + " " * (length - index - 1)


def compare_and_format(old_value: object, new_value: object) -> tuple[str, str]:
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
            "aftncn", "aftnsep", "aftnsepc", "annotation", "atnauthor", "atndate", "atnicn", "atnid", "atnparent", "atnref", "atntime", "atrfend", "atrfstart",
            "author", "background", "bkmkend", "bkmkstart", "blipuid", "buptim", "category", "colorschememapping", "colortbl", "comment", "company", "creatim",
            "datafield", "datastore", "defchp", "defpap", "do", "doccomm", "docvar", "dptxbxtext", "ebcend", "ebcstart", "factoidname", "falt", "fchars", "ffdeftext",
            "ffentrymcr", "ffexitmcr", "ffformat", "ffhelptext", "ffl", "ffname", "ffstattext", "field", "file", "filetbl", "fldinst", "fldrslt", "fldtype", "fname",
            "fontemb", "fontfile", "fonttbl", "footer", "footerf", "footerl", "footerr", "footnote", "formfield", "ftncn", "ftnsep", "ftnsepc", "g", "generator", "gridtbl",
            "header", "headerf", "headerl", "headerr", "hl", "hlfr", "hlinkbase", "hlloc", "hlsrc", "hsv", "htmltag", "info", "keycode", "keywords", "latentstyles",
            "lchars", "levelnumbers", "leveltext", "lfolevel", "linkval", "list", "listlevel", "listname", "listoverride", "listoverridetable", "listpicture", "liststylename",
            "listtable", "listtext", "lsdlockedexcept", "macc", "maccPr", "mailmerge", "maln", "malnScr", "manager", "margPr", "mbar", "mbarPr", "mbaseJc", "mbegChr",
            "mborderBox", "mborderBoxPr", "mbox", "mboxPr", "mchr", "mcount", "mctrlPr", "md", "mdeg", "mdegHide", "mden", "mdiff", "mdPr", "me", "mendChr", "meqArr",
            "meqArrPr", "mf", "mfName", "mfPr", "mfunc", "mfuncPr", "mgroupChr", "mgroupChrPr", "mgrow", "mhideBot", "mhideLeft", "mhideRight", "mhideTop", "mhtmltag",
            "mlim", "mlimloc", "mlimlow", "mlimlowPr", "mlimupp", "mlimuppPr", "mm", "mmaddfieldname", "mmath", "mmathPict", "mmathPr", "mmaxdist", "mmc", "mmcJc",
            "mmconnectstr", "mmconnectstrdata", "mmcPr", "mmcs", "mmdatasource", "mmheadersource", "mmmailsubject", "mmodso", "mmodsofilter", "mmodsofldmpdata",
            "mmodsomappedname", "mmodsoname", "mmodsorecipdata", "mmodsosort", "mmodsosrc", "mmodsotable", "mmodsoudl", "mmodsoudldata", "mmodsouniquetag", "mmPr",
            "mmquery", "mmr", "mnary", "mnaryPr", "mnoBreak", "mnum", "mobjDist", "moMath", "moMathPara", "moMathParaPr", "mopEmu", "mphant", "mphantPr", "mplcHide",
            "mpos", "mr", "mrad", "mradPr", "mrPr", "msepChr", "mshow", "mshp", "msPre", "msPrePr", "msSub", "msSubPr", "msSubSup", "msSubSupPr", "msSup", "msSupPr",
            "mstrikeBLTR", "mstrikeH", "mstrikeTLBR", "mstrikeV", "msub", "msubHide", "msup", "msupHide", "mtransp", "mtype", "mvertJc", "mvfmf", "mvfml", "mvtof",
            "mvtol", "mzeroAsc", "mzeroDesc", "mzeroWid", "nesttableprops", "nextfile", "nonesttables", "objalias", "objclass", "objdata", "object", "objname", "objsect",
            "objtime", "oldcprops", "oldpprops", "oldsprops", "oldtprops", "oleclsid", "operator", "panose", "password", "passwordhash", "pgp", "pgptbl", "picprop",
            "pict", "pn", "pnseclvl", "pntext", "pntxta", "pntxtb", "printim", "private", "propname", "protend", "protstart", "protusertbl", "pxe", "result", "revtbl",
            "revtim", "rsidtbl", "rxe", "shp", "shpgrp", "shpinst", "shppict", "shprslt", "shptxt", "sn", "sp", "staticval", "stylesheet", "subject", "sv", "svb", "tc",
            "template", "themedata", "title", "txe", "ud", "upr", "userprops", "wgrffmtfilter", "windowcaption", "writereservation", "writereservhash", "xe", "xform",
            "xmlattrname", "xmlattrvalue", "xmlclose", "xmlname", "xmlnstbl", "xmlopen"
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
