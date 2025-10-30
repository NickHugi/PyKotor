#!/usr/bin/env python3
"""3-way diff and merge utilities using merge3.

This module provides 3-way diff support for KOTOR files, enabling
merge operations between three versions (base, mine, yours).
"""
from __future__ import annotations

import difflib
import traceback

from typing import TYPE_CHECKING, Callable

import merge3

from pykotor.resource.formats import gff, tlk, twoda
from pykotor.tools.misc import is_capsule_file
from pykotor.tslpatcher.diff.engine import ext_of, read_text_lines
from utility.error_handling import universal_simplify_exception
from utility.system.path import Path, PureWindowsPath

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource
    from pykotor.resource.formats.tlk.tlk_data import TLK


gff_types: list[str] = list(gff.GFFContent.get_extensions())


def diff3_files_udiff(  # noqa: C901, PLR0912, PLR0915
    mine: Path,
    older: Path,
    yours: Path,
    log_func: Callable[[str], None],
) -> None:
    """Print a diff3-style output: show conflicts and changes between three files.

    Uses merge3 for all supported formats, including text, TLK, and capsule-contained text resources.
    Respects resolution order: automatically loads .rim files as composite when compared with .mod.
    
    Args:
        mine: Path to base/mine version
        older: Path to older/base version  
        yours: Path to yours/target version
        log_func: Function to call for logging output
    """
    ext = ext_of(yours)

    if is_capsule_file(yours.name):
        try:
            # Import composite loading utilities
            from pykotor.tslpatcher.diff.engine import determine_composite_loading, load_container_capsule  # noqa: PLC0415

            # Determine composite loading for each file based on siblings AND other files
            use_composite_older_siblings, _, module_root_older = determine_composite_loading(older)
            use_composite_mine_siblings, _, module_root_mine = determine_composite_loading(mine)
            use_composite_yours_siblings, _, module_root_yours = determine_composite_loading(yours)

            # Check if any file is a .mod (triggers composite loading for all .rim files)
            has_mod_file: bool = (
                older.suffix.lower() == ".mod"
                or mine.suffix.lower() == ".mod"
                or yours.suffix.lower() == ".mod"
            )

            # Apply resolution order: if comparing with .mod, all .rim files get composite loading
            use_composite_older: bool = (
                use_composite_older_siblings
                or (has_mod_file and older.suffix.lower() == ".rim")
            )
            use_composite_mine: bool = (
                use_composite_mine_siblings
                or (has_mod_file and mine.suffix.lower() == ".rim")
            )
            use_composite_yours: bool = (
                use_composite_yours_siblings
                or (has_mod_file and yours.suffix.lower() == ".rim")
            )

            # Log composite loading if used
            if use_composite_older:
                log_func(f"Using composite module loading for {older.name} ({module_root_older}.rim + _s.rim + _dlg.erf)")
            if use_composite_mine:
                log_func(f"Using composite module loading for {mine.name} ({module_root_mine}.rim + _s.rim + _dlg.erf)")
            if use_composite_yours:
                log_func(f"Using composite module loading for {yours.name} ({module_root_yours}.rim + _s.rim + _dlg.erf)")

            # Load capsules with appropriate loading method
            cap_old = load_container_capsule(older, use_composite=use_composite_older, log_func=log_func)
            cap_mine = load_container_capsule(mine, use_composite=use_composite_mine, log_func=log_func)
            cap_new = load_container_capsule(yours, use_composite=use_composite_yours, log_func=log_func)

            if cap_old is None or cap_mine is None or cap_new is None:
                log_func("[Error] Failed to load one or more capsules")
                return

        except (ValueError, OSError) as e:
            log_func(f"[Error] diff3 capsule: {universal_simplify_exception(e)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            return

        old_dict = {res.resname(): res for res in cap_old}
        mine_dict = {res.resname(): res for res in cap_mine}
        new_dict = {res.resname(): res for res in cap_new}
        keys = sorted(set(old_dict) | set(mine_dict) | set(new_dict))

        for k in keys:
            r_old = old_dict.get(k)
            r_mine = mine_dict.get(k)
            r_new = new_dict.get(k)
            log_func(f"==== {yours.name}/{k} ====")

            # If all three are missing, skip
            if r_old is None and r_mine is None and r_new is None:
                continue

            # If only present in one, print addition/removal
            if r_old is None and r_mine is not None and r_new is None:
                log_func(f"Only in mine: {mine.name}/{k}")
                continue
            if r_old is None and r_mine is None and r_new is not None:
                log_func(f"Only in yours: {yours.name}/{k}")
                continue
            if r_old is not None and r_mine is None and r_new is None:
                log_func(f"Only in older: {older.name}/{k}")
                continue

            # For all other cases, treat as text and use merge3
            def _res_lines(res: FileResource | None, kk: str = k) -> list[str]:
                """Extract text lines from a resource, handling encoding issues.

                Args:
                    res: FileResource from capsule, or None if resource doesn't exist
                    kk: Resource key for logging

                Returns:
                    List of text lines, empty list if resource is None or can't be decoded
                """
                if res is None:
                    return []
                try:
                    return res.data().decode("utf-8", errors="ignore").splitlines(keepends=True)
                except Exception as e:  # noqa: BLE001
                    log_func(f"[Warning] UTF-8 decode failed for {kk}, trying Windows-1252: {universal_simplify_exception(e)}")
                    log_func("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        log_func(f"  {line}")
                    try:
                        return res.data().decode("windows-1252", errors="ignore").splitlines(keepends=True)
                    except Exception as e2:  # noqa: BLE001
                        log_func(f"[Error] Failed to decode resource {kk} as text: {universal_simplify_exception(e2)}")
                        log_func("Full traceback:")
                        for line in traceback.format_exc().splitlines():
                            log_func(f"  {line}")
                        return []

            a = _res_lines(r_old)
            b = _res_lines(r_mine)
            c = _res_lines(r_new)
            try:
                m3 = merge3.Merge3(a, b, c, is_cherrypick=True, sequence_matcher=difflib.SequenceMatcher)
                for line_bytes in m3.merge_lines():
                    log_func(line_bytes if isinstance(line_bytes, str) else line_bytes.decode("utf-8", errors="ignore"))
            except Exception as merge3_error:  # noqa: BLE001
                log_func(f"[Error] merge3 failed for {k}: {universal_simplify_exception(merge3_error)}")
                log_func("Full traceback:")
                for line in traceback.format_exc().splitlines():
                    log_func(f"  {line}")
        return

    # Non-capsule files
    if ext in {"txt", "nss", "utp", "uti", "utc", "dlg"}:
        a = read_text_lines(older)
        b = read_text_lines(mine)
        c = read_text_lines(yours)
        try:
            m3 = merge3.Merge3(a, b, c)
            for line_bytes in m3.merge_lines():
                log_func(line_bytes if isinstance(line_bytes, str) else line_bytes.decode("utf-8", errors="ignore"))
        except Exception as merge3_error:  # noqa: BLE001
            log_func(f"[Error] merge3 unavailable/failure ({universal_simplify_exception(merge3_error)})")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
        return

    if ext == "2da":
        # Always use typed TwoDA compare
        try:
            twoda_old = twoda.read_2da(older)
            twoda_mine = twoda.read_2da(mine)
            twoda_new = twoda.read_2da(yours)
        except Exception as twoda_error:  # noqa: BLE001
            log_func(f"[Error] reading 2DA: {universal_simplify_exception(twoda_error)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            return
        log_func(f"--- (old){older}")
        log_func(f"+++ (mine){mine}")
        twoda_old.compare(twoda_mine, log_func)
        log_func(f"--- (old){older}")
        log_func(f"+++ (new){yours}")
        twoda_old.compare(twoda_new, log_func)
        return

    if ext in gff_types:
        # For GFF, we can't do a line-based merge, so just show both diffs
        try:
            gff_old = gff.read_gff(older)
            gff_mine = gff.read_gff(mine)
            gff_new = gff.read_gff(yours)
        except Exception as gff_error:  # noqa: BLE001
            log_func(f"[Error] reading GFF: {universal_simplify_exception(gff_error)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            return
        log_func(f"--- (old){older}")
        log_func(f"+++ (mine){mine}")
        gff_old.compare(gff_mine, log_func, PureWindowsPath(mine.name))
        log_func(f"--- (old){older}")
        log_func(f"+++ (new){yours}")
        gff_old.compare(gff_new, log_func, PureWindowsPath(yours.name))
        return

    if ext == "tlk":
        try:
            tlk_old = tlk.read_tlk(older)
            tlk_mine = tlk.read_tlk(mine)
            tlk_new = tlk.read_tlk(yours)
        except Exception as tlk_error:  # noqa: BLE001
            log_func(f"[Error] reading TLK: {universal_simplify_exception(tlk_error)}")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
            return

        def tlk_lines(tlk_obj: TLK) -> list[str]:
            """Convert TLK to line-based format for merge3.
            
            Args:
                tlk_obj: TLK object to convert
                
            Returns:
                List of lines in format: "index\ttext\tvoiceover\n"
            """
            lines = []
            for i in range(len(tlk_obj)):
                try:
                    e = tlk_obj.get(i)
                    lines.append(f"{i}\t{e.text}\t{e.voiceover}\n") if e else lines.append(f"{i}\t\n")
                except Exception as tlk_error:  # noqa: BLE001, PERF203
                    log_func(f"[Error] reading TLK entry {i}: {universal_simplify_exception(tlk_error)}")
                    log_func("Full traceback:")
                    for line in traceback.format_exc().splitlines():
                        log_func(f"  {line}")
                    lines.append(f"{i}\t\n")
            return lines

        a = tlk_lines(tlk_old)
        b = tlk_lines(tlk_mine)
        c = tlk_lines(tlk_new)
        try:
            m3 = merge3.Merge3(a, b, c)
            for line_bytes in m3.merge_lines():
                log_func(line_bytes if isinstance(line_bytes, str) else line_bytes.decode("utf-8", errors="ignore"))
        except Exception as merge3_error:  # noqa: BLE001
            log_func(f"[Error] merge3 unavailable/failure ({universal_simplify_exception(merge3_error)})")
            log_func("Full traceback:")
            for line in traceback.format_exc().splitlines():
                log_func(f"  {line}")
        return

    # Fallback to raw text diff3 using merge3
    a = read_text_lines(older)
    b = read_text_lines(mine)
    c = read_text_lines(yours)
    try:
        m3 = merge3.Merge3(a, b, c)
        for line_bytes in m3.merge_lines():
            log_func(line_bytes if isinstance(line_bytes, str) else line_bytes.decode("utf-8", errors="ignore"))
    except Exception as merge3_error:  # noqa: BLE001
        log_func(f"[Error] merge3 unavailable/failure ({universal_simplify_exception(merge3_error)})")
        log_func("Full traceback:")
        for line in traceback.format_exc().splitlines():
            log_func(f"  {line}")

