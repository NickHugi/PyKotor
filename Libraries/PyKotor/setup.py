from __future__ import annotations
import os
import sys

from pathlib import Path
from typing import Any

from setuptools import setup

def main():
    HERE = Path(__file__).resolve().parent
    # Load information from pyproject.toml
    with HERE.joinpath("pyproject.toml").open() as toml_file:
        setup_params = load_toml(toml_file)

    # Extract project metadata
    project_metadata: dict[str, Any] = setup_params.get("project", {})
    build_system: dict[str, dict] = setup_params.get("build-system", {})
    AUTHORS: list[dict[str, str]] = project_metadata.get("authors", [{"name": ""}])
    README: dict[str, str] = project_metadata.get("readme", {"file": "", "content-type": ""})

    # Extract and extend requirements
    REQUIREMENTS = {*build_system.get("requires", [])}
    requirements_txt_path = HERE.joinpath("requirements.txt")
    if requirements_txt_path.exists():
        REQUIREMENTS.update(requirements_txt_path.read_text().splitlines())
    # Check if the installation is from PyPI or local source
    if len(sys.argv) < 2:
        sys.argv.append("install")

    for key in ("authors", "readme"):  # Remove keys that are not needed in setup()
        if key in project_metadata:
            project_metadata.pop(key)

    setup(
        **project_metadata,
        author=AUTHORS[0]["name"],
        install_requires=list(REQUIREMENTS),
        long_description=README["file"],
        long_description_content_type=README["content-type"],
        include_dirs=[str(HERE)],
    )


import contextlib
import datetime
import re

TIME_RE = re.compile(r"([0-9]{2}):([0-9]{2}):([0-9]{2})(\.([0-9]{3,6}))?")
_number_with_underscores = re.compile("([0-9])(_([0-9]))*")
_escapes = ["0", "b", "f", "n", "r", "t", '"']
_escapedchars = ["\0", "\b", "\f", "\n", "\r", "\t", '"']
_escape_to_escapedchars = dict(zip(_escapes, _escapedchars))
_groupname_re = re.compile(r"^[A-Za-z0-9_-]+$")
unicode = str
_range = range
basestring = str
unichr = chr


def _load_unicode_escapes(v, hexbytes, prefix):
    skip = False
    i = len(v) - 1
    while i > -1 and v[i] == "\\":
        skip = not skip
        i -= 1
    for hx in hexbytes:
        if skip:
            skip = False
            i = len(hx) - 1
            while i > -1 and hx[i] == "\\":
                skip = not skip
                i -= 1
            v += prefix
            v += hx
            continue
        hxb = ""
        i = 0
        hxblen = 4
        if prefix == "\\U":
            hxblen = 8
        hxb = "".join(hx[i:i + hxblen]).lower()
        if hxb.strip("0123456789abcdef"):
            raise ValueError("Invalid escape sequence: " + hxb)
        if hxb[0] == "d" and hxb[1].strip("01234567"):
            raise ValueError("Invalid escape sequence: " + hxb +
                             ". Only scalar unicode points are allowed.")
        v += unichr(int(hxb, 16))
        v += unicode(hx[len(hxb):])
    return v


def _unescape(v):
    """Unescape characters in a TOML string."""
    i = 0
    backslash = False
    while i < len(v):
        if backslash:
            backslash = False
            if v[i] in _escapes:
                v = v[:i - 1] + _escape_to_escapedchars[v[i]] + v[i + 1:]
            elif v[i] == "\\":
                v = v[:i - 1] + v[i:]
            elif v[i] == "u" or v[i] == "U":
                i += 1
            else:
                raise ValueError("Reserved escape sequence used")
            continue
        if v[i] == "\\":
            backslash = True
        i += 1
    return v


class TomlTz(datetime.tzinfo):
    def __init__(self, toml_offset):
        if toml_offset == "Z":
            self._raw_offset = "+00:00"
        else:
            self._raw_offset = toml_offset
        self._sign = -1 if self._raw_offset[0] == "-" else 1
        self._hours = int(self._raw_offset[1:3])
        self._minutes = int(self._raw_offset[4:6])

    def __deepcopy__(self, memo):
        return self.__class__(self._raw_offset)

    def tzname(self, dt):
        return f"UTC{self._raw_offset}"

    def utcoffset(self, dt):
        return self._sign * datetime.timedelta(hours=self._hours, minutes=self._minutes)

    def dst(self, dt):
        return datetime.timedelta(0)


def _load_date(val):
    microsecond = 0
    tz = None
    try:
        if len(val) > 19:
            if val[19] == ".":
                if val[-1].upper() == "Z":
                    subsecondval = val[20:-1]
                    tzval = "Z"
                else:
                    subsecondvalandtz = val[20:]
                    if "+" in subsecondvalandtz:
                        splitpoint = subsecondvalandtz.index("+")
                        subsecondval = subsecondvalandtz[:splitpoint]
                        tzval = subsecondvalandtz[splitpoint:]
                    elif "-" in subsecondvalandtz:
                        splitpoint = subsecondvalandtz.index("-")
                        subsecondval = subsecondvalandtz[:splitpoint]
                        tzval = subsecondvalandtz[splitpoint:]
                    else:
                        tzval = None
                        subsecondval = subsecondvalandtz
                if tzval is not None:
                    tz = TomlTz(tzval)
                microsecond = int(int(subsecondval) *
                                  (10 ** (6 - len(subsecondval))))
            else:
                tz = TomlTz(val[19:])
    except ValueError:
        tz = None
    if "-" not in val[1:]:
        return None
    try:
        if len(val) == 10:
            d = datetime.date(
                int(val[:4]), int(val[5:7]),
                int(val[8:10]))
        else:
            d = datetime.datetime(
                int(val[:4]), int(val[5:7]),
                int(val[8:10]), int(val[11:13]),
                int(val[14:16]), int(val[17:19]), microsecond, tz)
    except ValueError:
        return None
    return d


class InlineTableDict:
    """Sentinel subclass of dict for inline tables."""


class TomlDecoder:

    def __init__(self, _dict=dict):
        self._dict = _dict

    def get_empty_table(self):
        return self._dict()

    def get_empty_inline_table(self):
        class DynamicInlineTableDict(self._dict, InlineTableDict):
            pass

        return DynamicInlineTableDict()

    def load_inline_object(self, line, currentlevel, multikey=False, multibackslash=False):
        candidate_groups = line[1:-1].split(",")
        groups = []
        if len(candidate_groups) == 1 and not candidate_groups[0].strip(): candidate_groups.pop()
        while len(candidate_groups) > 0:
            candidate_group = candidate_groups.pop(0)
            try: _, value = candidate_group.split("=", 1)
            except ValueError: raise ValueError("Invalid inline table encountered")
            value = value.strip()
            if ((value[0] == value[-1] and value[0] in {'"', "'"}) or (value[0] in "-0123456789" or value in {"true", "false"} or (value[0] == "[" and value[-1] == "]") or (value[0] == "{" and value[-1] == "}"))):
                groups.append(candidate_group)
            elif len(candidate_groups) > 0:
                candidate_groups[0] = f"{candidate_group},{candidate_groups[0]}"
            else: raise ValueError("Invalid inline table value encountered")
        for group in groups:
            status = self.load_line(group, currentlevel, multikey, multibackslash)
            if status is not None:
                break

    def _get_split_on_quotes(self, line):
        doublequotesplits = line.split('"')
        quoted = False
        quotesplits = []
        if len(doublequotesplits) > 1 and "'" in doublequotesplits[0]:
            singlequotesplits = doublequotesplits[0].split("'")
            doublequotesplits = doublequotesplits[1:]
            while len(singlequotesplits) % 2 == 0 and len(doublequotesplits):
                singlequotesplits[-1] += f'"{doublequotesplits[0]}'
                doublequotesplits = doublequotesplits[1:]
                if "'" in singlequotesplits[-1]:
                    singlequotesplits = (singlequotesplits[:-1] + singlequotesplits[-1].split("'"))
            quotesplits += singlequotesplits
        for doublequotesplit in doublequotesplits:
            if quoted:
                quotesplits.append(doublequotesplit)
            else:
                quotesplits += doublequotesplit.split("'")
                quoted = not quoted
        return quotesplits

    def load_line(self, line, currentlevel, multikey, multibackslash):
        i = 1
        quotesplits = self._get_split_on_quotes(line)
        quoted = False
        for quotesplit in quotesplits:
            if not quoted and "=" in quotesplit:
                break
            i += quotesplit.count("=")
            quoted = not quoted
        pair = line.split("=", i)
        strictly_valid = _strictly_valid_num(pair[-1])
        if _number_with_underscores.match(pair[-1]):
            pair[-1] = pair[-1].replace("_", "")
        while len(pair[-1]) and (pair[-1][0] != " " and pair[-1][0] != "\t" and pair[-1][0] != "'" and pair[-1][0] != '"' and pair[-1][0] != "[" and pair[-1][0] != "{" and pair[-1].strip() != "true" and pair[-1].strip() != "false"):
            try:
                float(pair[-1])
                break
            except ValueError:
                pass
            if _load_date(pair[-1]) is not None:
                break
            if TIME_RE.match(pair[-1]):
                break
            i += 1
            prev_val = pair[-1]
            pair = line.split("=", i)
            if prev_val == pair[-1]: raise ValueError("Invalid date or number")
            if strictly_valid:
                strictly_valid = _strictly_valid_num(pair[-1])
        pair = ["=".join(pair[:-1]).strip(), pair[-1].strip()]
        if "." in pair[0]:
            if '"' in pair[0] or "'" in pair[0]:
                quotesplits, quoted, levels = self._get_split_on_quotes(pair[0]), False, []
                for quotesplit in quotesplits:
                    if quoted:
                        levels.append(quotesplit)
                    else:
                        levels += [level.strip() for level in quotesplit.split(".")]
                    quoted = not quoted
            else: levels = pair[0].split(".")
            while levels[-1] == "": levels = levels[:-1]
            for level in levels[:-1]:
                if level == "": continue
                if level not in currentlevel: currentlevel[level] = self.get_empty_table()
                currentlevel = currentlevel[level]
            pair[0] = levels[-1].strip()
        elif pair[0][0] in {'"', "'"} and pair[0][-1] == pair[0][0]:
            pair[0] = _unescape(pair[0][1:-1])
        k, koffset = self._load_line_multiline_str(pair[1])
        if k > -1:
            while k > -1 and pair[1][k + koffset] == "\\":
                multibackslash = not multibackslash
                k -= 1
            multilinestr = pair[1][:-1] if multibackslash else pair[1] + "\n"
            multikey = pair[0]
        else:
            value, vtype = self.load_value(pair[1], strictly_valid)
        try:
            currentlevel[pair[0]]
            raise ValueError("Duplicate keys!")
        except TypeError as e: raise ValueError("Duplicate keys!") from e
        except KeyError:
            if multikey:
                return multikey, multilinestr, multibackslash
            currentlevel[pair[0]] = value

    def _load_line_multiline_str(self, p):
        poffset = 0
        if len(p) < 3: return -1, poffset
        if p[0] == "[" and (p.strip()[-1] != "]" and self._load_array_isstrarray(p)):
            newp = p[1:].strip().split(",")
            while len(newp) > 1 and newp[-1][0] != '"' and newp[-1][0] != "'": newp = newp[:-2] + [newp[-2] + "," + newp[-1]]
            newp = newp[-1]
            poffset = len(p) - len(newp)
            p = newp
        if p[0] != '"' and p[0] != "'": return -1, poffset
        if p[1] != p[0] or p[2] != p[0]: return -1, poffset
        if len(p) > 5 and p[-1] == p[0] and p[-2] == p[0] and p[-3] == p[0]: return -1, poffset
        return len(p) - 1, poffset

    def load_value(self, v, strictly_valid=True):
        if not v: raise ValueError("Empty value is invalid")
        if v == "true":
            return (True, "bool")
        if v.lower() == "true": raise ValueError("Only all lowercase booleans allowed")
        if v == "false":
            return (False, "bool")
        if v.lower() == "false": raise ValueError("Only all lowercase booleans allowed")
        if v[0] == '"' or v[0] == "'":
            quotechar = v[0]
            testv = v[1:].split(quotechar)
            triplequote, triplequotecount = False, 0
            if len(testv) > 1 and testv[0] == "" and testv[1] == "":
                testv = testv[2:]
                triplequote = True
            closed = False
            for tv in testv:
                if tv == "":
                    if triplequote:
                        triplequotecount += 1
                    else:
                        closed = True
                else:
                    oddbackslash = False
                    try:
                        i = -1
                        j = tv[i]
                        while j == "\\":
                            oddbackslash = not oddbackslash
                            i -= 1
                            j = tv[i]
                    except IndexError:
                        pass
                    if not oddbackslash:
                        if closed:
                            raise ValueError("Found tokens after a closed string. Invalid TOML.")
                        if not triplequote or triplequotecount > 1:
                            closed = True
                        else:
                            triplequotecount = 0
            if quotechar == '"':
                escapeseqs = v.split("\\")[1:]
                backslash = False
                for i in escapeseqs:
                    if i == "":
                        backslash = not backslash
                    else:
                        if i[0] not in _escapes and (i[0] != "u" and i[0] != "U" and not backslash):
                            raise ValueError("Reserved escape sequence used")
                        if backslash:
                            backslash = False
                for prefix in ["\\u", "\\U"]:
                    if prefix in v:
                        hexbytes = v.split(prefix)
                        v = _load_unicode_escapes(hexbytes[0], hexbytes[1:],
                                                  prefix)
                v = _unescape(v)
            if len(v) > 1 and v[1] == quotechar and (len(v) < 3 or
                                                     v[1] == v[2]):
                v = v[2:-2]
            return (v[1:-1], "str")
        if v[0] == "[":
            return (self.load_array(v), "array")
        if v[0] == "{":
            inline_object = self.get_empty_inline_table()
            self.load_inline_object(v, inline_object)
            return (inline_object, "inline_object")
        if TIME_RE.match(v):
            h, m, s, _, ms = TIME_RE.match(v).groups()
            time = datetime.time(int(h), int(m), int(s), int(ms) if ms else 0)
            return (time, "time")
        parsed_date = _load_date(v)
        if parsed_date is not None: return (parsed_date, "date")
        if not strictly_valid: raise ValueError("Weirdness with leading zeroes or underscores in your number.")
        itype = "int"
        neg = False
        if v[0] == "-":
            neg = True
            v = v[1:]
        elif v[0] == "+":
            v = v[1:]
        v = v.replace("_", "")
        lowerv = v.lower()
        if "." in v or ("x" not in v and ("e" in v or "E" in v)):
            if "." in v and v.split(".", 1)[1] == "": raise ValueError("This float is missing digits after the point")
            if v[0] not in "0123456789": raise ValueError("This float doesn't have a leading digit")
            v = float(v)
            itype = "float"
        elif len(lowerv) == 3 and (lowerv in {"inf", "nan"}):
            v = float(v)
            itype = "float"
        if itype == "int":
            v = int(v, 0)
        if neg:
            return (0 - v, itype)
        return (v, itype)

    def bounded_string(self, s):
        if len(s) == 0:
            return True
        if s[-1] != s[0]:
            return False
        i = -2
        backslash = False
        while len(s) + i > 0:
            if s[i] == "\\":
                backslash = not backslash
                i -= 1
            else:
                break
        return not backslash

    def _load_array_isstrarray(self, a):
        a = a[1:-1].strip()
        if a != "" and (a[0] == '"' or a[0] == "'"):
            return True
        return False

    def load_array(self, a):
        atype = None
        retval = []
        a = a.strip()
        if "[" not in a[1:-1] or a[1:-1].split("[")[0].strip() != "":
            strarray = self._load_array_isstrarray(a)
            if not a[1:-1].strip().startswith("{"):
                a = a[1:-1].split(",")
            else:
                # a is an inline object, we must find the matching parenthesis
                # to define groups
                new_a = []
                start_group_index = 1
                end_group_index = 2
                open_bracket_count = 1 if a[start_group_index] == "{" else 0
                in_str = False
                while end_group_index < len(a[1:]):
                    if a[end_group_index] == '"' or a[end_group_index] == "'":
                        if in_str:
                            backslash_index = end_group_index - 1
                            while (backslash_index > -1 and
                                   a[backslash_index] == "\\"):
                                in_str = not in_str
                                backslash_index -= 1
                        in_str = not in_str
                    if not in_str and a[end_group_index] == "{":
                        open_bracket_count += 1
                    if in_str or a[end_group_index] != "}":
                        end_group_index += 1
                        continue
                    if a[end_group_index] == "}" and open_bracket_count > 1:
                        open_bracket_count -= 1
                        end_group_index += 1
                        continue

                    # Increase end_group_index by 1 to get the closing bracket
                    end_group_index += 1

                    new_a.append(a[start_group_index:end_group_index])

                    # The next start index is at least after the closing
                    # bracket, a closing bracket can be followed by a comma
                    # since we are in an array.
                    start_group_index = end_group_index + 1
                    while (start_group_index < len(a[1:]) and
                           a[start_group_index] != "{"):
                        start_group_index += 1
                    end_group_index = start_group_index + 1
                a = new_a
            b = 0
            if strarray:
                while b < len(a) - 1:
                    ab = a[b].strip()
                    while (not self.bounded_string(ab) or
                           (len(ab) > 2 and
                            ab[0] == ab[1] == ab[2] and
                            ab[-2] != ab[0] and
                            ab[-3] != ab[0])):
                        a[b] = a[b] + "," + a[b + 1]
                        ab = a[b].strip()
                        a = a[:b + 1] + a[b + 2:] if b < len(a) - 2 else a[:b + 1]
                    b += 1
        else:
            al = list(a[1:-1])
            a = []
            openarr = 0
            j = 0
            for i in _range(len(al)):
                if al[i] == "[":
                    openarr += 1
                elif al[i] == "]":
                    openarr -= 1
                elif al[i] == "," and not openarr:
                    a.append("".join(al[j:i]))
                    j = i + 1
            a.append("".join(al[j:]))
        for i in _range(len(a)):
            a[i] = a[i].strip()
            if a[i] != "":
                nval, ntype = self.load_value(a[i])
                if atype:
                    if ntype != atype:
                        raise ValueError("Not a homogeneous array")
                else:
                    atype = ntype
                retval.append(nval)
        return retval

    def preserve_comment(self, line_no, key, comment, beginline):
        pass

    def embed_comments(self, idx, currentlevel):
        pass


def _strictly_valid_num(n):
    n = n.strip()
    if not n:
        return False
    if n[0] == "_":
        return False
    if n[-1] == "_":
        return False
    if "_." in n or "._" in n:
        return False
    if len(n) == 1:
        return True
    if n[0] == "0" and n[1] not in {".", "o", "b", "x"}:
        return False
    if n[0] == "+" or n[0] == "-":
        n = n[1:]
        if len(n) > 1 and n[0] == "0" and n[1] != ".":
            return False
    if "__" in n:
        return False
    return True


def load_toml(f, _dict=dict, decoder=None):
    if isinstance(f, (os.PathLike, str)):
        with Path(f).open(encoding="utf-8") as ffile:
            return loads(ffile.read(), _dict, decoder)
    elif isinstance(f, list):
        from os import path as op
        from warnings import warn
        if not [path for path in f if op.exists(path)]:
            error_msg = "Load expects a list to contain filenames only."
            error_msg += os.linesep
            error_msg += ("The list needs to contain the path of at least one existing file.")
            raise OSError(error_msg)
        if decoder is None:
            decoder = TomlDecoder(_dict)
        d = decoder.get_empty_table()
        for l in f:  # noqa: E741
            if Path.exists(l):
                d.update(load_toml(l, _dict, decoder))
            else:
                warn("Non-existent filename in list with at least one valid filename")
        return d
    else:
        try:
            return loads(f.read(), _dict, decoder)
        except AttributeError:
            raise TypeError("You can only load a file descriptor, filename or list")


def loads(s, _dict=dict, decoder=None):
    implicitgroups = []
    if decoder is None:
        decoder = TomlDecoder(_dict)
    retval = decoder.get_empty_table()
    currentlevel = retval
    if not isinstance(s, basestring):
        raise TypeError("Expecting something like a string")

    if not isinstance(s, unicode):
        s = s.decode("utf8")

    original, sl, openarr, openstring, openstrchar, multilinestr, arrayoftables, beginline, keygroup, dottedkey, keyname, key, prev_key, line_no = s, list(s), 0, False, "", False, False, True, False, False, 0, "", "", 1
    for i, item in enumerate(sl):
        if item == "\r" and sl[i + 1] == "\n":
            sl[i] = " "
            continue
        if keyname:
            key += item
            if item == "\n":
                raise ValueError("Key name found without value. Reached end of line.", original, i)
            if openstring:
                if item == openstrchar:
                    oddbackslash = False
                    k = 1
                    while i >= k and sl[i - k] == "\\":
                        oddbackslash = not oddbackslash
                        k += 1
                    if not oddbackslash:
                        keyname = 2
                        openstring = False
                        openstrchar = ""
                continue
            if keyname == 1:
                if item.isspace():
                    keyname = 2
                    continue
                if item == ".":
                    dottedkey = True
                    continue
                if item.isalnum() or item == "_" or item == "-":
                    continue
                if (dottedkey and sl[i - 1] == "." and (item in {'"', "'"})):
                    openstring, openstrchar = True, item
                    continue
            elif keyname == 2:
                if item.isspace():
                    if dottedkey:
                        nextitem = sl[i + 1]
                        if not nextitem.isspace() and nextitem != ".":
                            keyname = 1
                    continue
                if item == ".":
                    dottedkey = True
                    nextitem = sl[i + 1]
                    if not nextitem.isspace() and nextitem != ".":
                        keyname = 1
                    continue
            if item == "=":
                keyname = 0
                prev_key = key[:-1].rstrip()
                key = ""
                dottedkey = False
            else:
                raise ValueError("Found invalid character in key name: '" +
                                      item + "'. Try quoting the key name.",
                                      original, i)
        if item == "'" and openstrchar != '"':
            k = 1
            try:
                while sl[i - k] == "'":
                    k += 1
                    if k == 3:
                        break
            except IndexError:
                pass
            if k == 3:
                multilinestr = not multilinestr
                openstring = multilinestr
            else:
                openstring = not openstring
            openstrchar = "'" if openstring else ""
        if item == '"' and openstrchar != "'":
            oddbackslash = False
            k = 1
            tripquote = False
            try:
                while sl[i - k] == '"':
                    k += 1
                    if k == 3:
                        tripquote = True
                        break
                if k == 1 or (k == 3 and tripquote):
                    while sl[i - k] == "\\":
                        oddbackslash = not oddbackslash
                        k += 1
            except IndexError:
                pass
            if not oddbackslash:
                if tripquote:
                    multilinestr = not multilinestr
                    openstring = multilinestr
                else:
                    openstring = not openstring
            openstrchar = '"' if openstring else ""
        if item == "#" and (not openstring and not keygroup and
                            not arrayoftables):
            j = i
            comment = ""
            try:
                while sl[j] != "\n":
                    comment += s[j]
                    sl[j] = " "
                    j += 1
            except IndexError:
                break
            if not openarr:
                decoder.preserve_comment(line_no, prev_key, comment, beginline)
        if item == "[" and (not openstring and not keygroup and
                            not arrayoftables):
            if beginline:
                if len(sl) > i + 1 and sl[i + 1] == "[":
                    arrayoftables = True
                else:
                    keygroup = True
            else:
                openarr += 1
        if item == "]" and not openstring:
            if keygroup:
                keygroup = False
            elif arrayoftables:
                if sl[i - 1] == "]":
                    arrayoftables = False
            else:
                openarr -= 1
        if item == "\n":
            if openstring or multilinestr:
                if not multilinestr:
                    raise ValueError("Unbalanced quotes", original, i)
                if ((sl[i - 1] == "'" or sl[i - 1] == '"') and (
                        sl[i - 2] == sl[i - 1])):
                    sl[i] = sl[i - 1]
                    if sl[i - 3] == sl[i - 1]:
                        sl[i - 3] = " "
            elif openarr:
                sl[i] = " "
            else:
                beginline = True
            line_no += 1
        elif beginline and sl[i] != " " and sl[i] != "\t":
            beginline = False
            if not keygroup and not arrayoftables:
                if sl[i] == "=":
                    raise ValueError("Found empty keyname. ", original, i)
                keyname = 1
                key += item
    if keyname:
        raise ValueError("Key name found without value. Reached end of file.", original, len(s))
    if openstring:  # reached EOF and have an unterminated string
        raise ValueError("Unterminated string found. Reached end of file.", original, len(s))
    s = "".join(sl)
    s = s.split("\n")
    multikey = None
    multilinestr = ""
    multibackslash = False
    pos = 0
    for idx, line in enumerate(s):
        if idx > 0:
            pos += len(s[idx - 1]) + 1

        decoder.embed_comments(idx, currentlevel)

        if not multilinestr or multibackslash or "\n" not in multilinestr:
            line = line.strip()
        if line == "" and (not multikey or multibackslash):
            continue
        if multikey:
            if multibackslash:
                multilinestr += line
            else:
                multilinestr += line
            multibackslash = False
            closed = False
            if multilinestr[0] == "[":
                closed = line[-1] == "]"
            elif len(line) > 2:
                closed = (line[-1] == multilinestr[0] and
                          line[-2] == multilinestr[0] and
                          line[-3] == multilinestr[0])
            if closed:
                try:
                    value, vtype = decoder.load_value(multilinestr)
                except ValueError as err:
                    raise ValueError(str(err), original, pos)
                currentlevel[multikey] = value
                multikey = None
                multilinestr = ""
            else:
                k = len(multilinestr) - 1
                while k > -1 and multilinestr[k] == "\\":
                    multibackslash = not multibackslash
                    k -= 1
                if multibackslash:
                    multilinestr = multilinestr[:-1]
                else:
                    multilinestr += "\n"
            continue
        if line[0] == "[":
            arrayoftables = False
            if len(line) == 1:
                raise ValueError("Opening key group bracket on line by "
                                      "itself.", original, pos)
            if line[1] == "[":
                arrayoftables = True
                line = line[2:]
                splitstr = "]]"
            else:
                line = line[1:]
                splitstr = "]"
            i = 1
            quotesplits = decoder._get_split_on_quotes(line)
            quoted = False
            for quotesplit in quotesplits:
                if not quoted and splitstr in quotesplit:
                    break
                i += quotesplit.count(splitstr)
                quoted = not quoted
            line = line.split(splitstr, i)
            if len(line) < i + 1 or line[-1].strip() != "":
                raise ValueError("Key group not on a line by itself.",
                                      original, pos)
            groups = splitstr.join(line[:-1]).split(".")
            i = 0
            while i < len(groups):
                groups[i] = groups[i].strip()
                if len(groups[i]) > 0 and (groups[i][0] == '"' or
                                           groups[i][0] == "'"):
                    groupstr = groups[i]
                    j = i + 1
                    while ((groupstr[0] != groupstr[-1]) or
                           len(groupstr) == 1):
                        j += 1
                        if j > len(groups) + 2:
                            raise ValueError("Invalid group name '" +
                                                  groupstr + "' Something " +
                                                  "went wrong.", original, pos)
                        groupstr = ".".join(groups[i:j]).strip()
                    groups[i] = groupstr[1:-1]
                    groups[i + 1:j] = []
                elif not _groupname_re.match(groups[i]):
                    raise ValueError("Invalid group name '" +
                                          groups[i] + "'. Try quoting it.",
                                          original, pos)
                i += 1
            currentlevel = retval
            for i in _range(len(groups)):
                group = groups[i]
                if group == "":
                    raise ValueError("Can't have a keygroup with an empty "
                                          "name", original, pos)
                try:
                    currentlevel[group]
                    if i == len(groups) - 1:
                        if group in implicitgroups:
                            implicitgroups.remove(group)
                            if arrayoftables:
                                raise ValueError("An implicitly defined "
                                                      "table can't be an array",
                                                      original, pos)
                        elif arrayoftables:
                            currentlevel[group].append(decoder.get_empty_table(),
                                                       )
                        else:
                            raise ValueError("What? " + group +
                                                  " already exists?" +
                                                  str(currentlevel),
                                                  original, pos)
                except TypeError:
                    currentlevel = currentlevel[-1]
                    if group not in currentlevel:
                        currentlevel[group] = decoder.get_empty_table()
                        if i == len(groups) - 1 and arrayoftables:
                            currentlevel[group] = [decoder.get_empty_table()]
                except KeyError:
                    if i != len(groups) - 1:
                        implicitgroups.append(group)
                    currentlevel[group] = decoder.get_empty_table()
                    if i == len(groups) - 1 and arrayoftables:
                        currentlevel[group] = [decoder.get_empty_table()]
                currentlevel = currentlevel[group]
                if arrayoftables:
                    with contextlib.suppress(KeyError):
                        currentlevel = currentlevel[-1]
        elif line[0] == "{":
            if line[-1] != "}":
                raise ValueError("Line breaks are not allowed in inlineobjects", original, pos)
            try:
                decoder.load_inline_object(line, currentlevel, multikey,
                                           multibackslash)
            except ValueError as err: raise ValueError(str(err), original, pos)
        elif "=" in line:
            try:
                ret = decoder.load_line(line, currentlevel, multikey,
                                        multibackslash)
            except ValueError as err: raise ValueError(str(err), original, pos)
            if ret is not None:
                multikey, multilinestr, multibackslash = ret
    return retval

main()
