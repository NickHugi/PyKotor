from __future__ import annotations
from enum import Enum
import sys


from typing import Literal

class PlatformEnum(str, Enum):
    """Enumeration of possible platforms for sys.platform."""
    linux = "linux"
    """Linux distributions (e.g., Ubuntu, Fedora, CentOS) - Initial Release: September 17, 1991"""

    darwin = "darwin"
    """macOS (formerly OS X) - Initial Release: March 24, 2001"""

    win32 = "win32"
    """Windows (including 64-bit) - Initial Release: November 20, 1985"""

    cygwin = "cygwin"
    """Cygwin POSIX on Windows - Initial Release: October 18, 1995"""

    msys = "msys"
    """MSYS/MinGW on Windows - Initial Release: 2005"""

    aix = "aix"
    """IBM AIX - Initial Release: 1986"""

    sunos5 = "sunos5"
    """Solaris (SunOS 5) - Initial Release: 1992"""

    solaris = "solaris"
    """Solaris (SunOS) - Initial Release: 1983"""

    freebsd = "freebsd"
    """FreeBSD - Initial Release: June 19, 1993"""

    openbsd = "openbsd"
    """OpenBSD - Initial Release: October 18, 1996"""

    netbsd = "netbsd"
    """NetBSD - Initial Release: March 21, 1993"""

    os2 = "os2"
    """IBM OS/2 - Initial Release: December 1987"""

    osf1 = "osf1"
    """Digital UNIX (OSF/1) - Initial Release: January 1992"""

    irix = "irix"
    """SGI IRIX - Initial Release: 1988"""

    hp_ux = "hp-ux"
    """HP-UX (Hewlett-Packard) - Initial Release: 1983"""

    vxworks = "vxworks"
    """VxWorks RTOS - Initial Release: 1987"""

    riscos = "riscos"
    """RISC OS - Initial Release: October 1987"""

    atheos = "atheos"
    """AtheOS - Initial Release: 2000"""

    gnu = "gnu"
    """GNU/Hurd - Initial Release: May 14, 1996"""

    android = "android"
    """Android - Initial Release: September 23, 2008"""

    amiga = "amiga"
    """AmigaOS (Amiga computers) - Initial Release: July 23, 1985"""

    beos = "beos"
    """BeOS (older operating system) - Initial Release: October 1995"""

    dragonfly = "dragonfly"
    """DragonFly BSD - Initial Release: June 16, 2003"""

    haiku = "haiku"
    """Haiku (BeOS successor) - Initial Release: September 14, 2009"""

    mint = "mint"
    """Atari MiNT (multi-tasking OS for Atari ST) - Initial Release: 1990"""

    nacl = "nacl"
    """Native Client (Google's NaCl) - Initial Release: 2010"""

    qnx = "qnx"
    """QNX (real-time operating system) - Initial Release: 1980"""

    symbian = "symbian"
    """Symbian OS (older mobile OS) - Initial Release: 1997"""

    tru64 = "tru64"
    """Tru64 UNIX (formerly Digital UNIX) - Initial Release: 1995"""

    unixware = "unixware"
    """UnixWare (a UNIX System V release) - Initial Release: 1992"""

    vos = "vos"
    """Stratus VOS (fault-tolerant OS) - Initial Release: 1982"""

    zos = "zos"
    """IBM z/OS (mainframe OS) - Initial Release: March 30, 2001"""

    midnightbsd = "midnightbsd"
    """MidnightBSD (BSD-derived OS) - Initial Release: February 17, 2007"""

    interix = "interix"
    """Interix (Microsoft POSIX subsystem for Windows) - Initial Release: 1996"""

    sysv = "sysv"
    """System V UNIX - Initial Release: 1983"""

    isc = "isc"
    """Interactive UNIX (by ISC) - Initial Release: 1985"""

    xenix = "xenix"
    """Xenix (a UNIX version by Microsoft) - Initial Release: 1980"""

    plan9 = "plan9"
    """Plan 9 from Bell Labs - Initial Release: 1992"""

    unknown = "unknown"
    """Unknown or unlisted platforms"""


PossiblePlatforms = Literal[
    "linux", "darwin", "win32", "cygwin", "msys", "aix", "sunos5", "solaris", "freebsd", "openbsd",
    "netbsd", "os2", "osf1", "irix", "hp-ux", "vxworks", "riscos", "atheos", "gnu", "android",
    "amiga", "beos", "dragonfly", "haiku", "mint", "nacl", "qnx", "symbian", "tru64", "unixware",
    "vos", "midnightbsd", "interix", "sysv", "isc", "xenix", "plan9", "unknown"
]


#change PossiblePlatforms to a list (remove the word 'Literal') to test these.
#for member in PlatformEnum:
#    assert member.value in PossiblePlatforms
#for platform_str in PossiblePlatforms:
#    assert platform_str.replace("-", "_") in PlatformEnum.__members__, platform_str


_PfEnum = PlatformEnum


def check_platform(
    platform: PossiblePlatforms,
) -> Literal[
    "Linux", "Darwin", "Windows", "Android", "Solaris", "AIX", "BSD", "HP-UX", "Real-Time", "Legacy-PC", "Legacy-Unix", "Legacy-Micro",
    "Legacy-Experimental", "Legacy-Embedded", "Legacy-Mobile", "Supported-Legacy", "Unknown"
]:
    if platform == _PfEnum.linux.value:
        return "Linux"
    if platform == _PfEnum.darwin.value:
        return "Darwin"
    if platform == _PfEnum.win32.value:
        return "Windows"
    if platform == _PfEnum.android.value:
        return "Android"
    if platform in [_PfEnum.sunos5.value, _PfEnum.solaris.value]:
        return "Solaris"
    if platform == "aix":
        return "AIX"
    if platform in [_PfEnum.freebsd.value, _PfEnum.openbsd.value, _PfEnum.netbsd.value, _PfEnum.dragonfly.value, _PfEnum.midnightbsd.value]:
        return "BSD"
    if platform == _PfEnum.hp_ux.value:
        return "HP-UX"
    if platform in [_PfEnum.vxworks.value, _PfEnum.qnx.value]:
        return "Real-Time"

    # Legacy platforms that probably at least support Tkinter
    if platform in [_PfEnum.os2.value, _PfEnum.unixware.value, _PfEnum.xenix.value, _PfEnum.isc.value, _PfEnum.osf1.value, _PfEnum.tru64.value,
                    _PfEnum.irix.value, _PfEnum.sysv.value]:
        return "Supported-Legacy"

    # Platforms that are more niche and experimental
    if platform in [_PfEnum.riscos.value, _PfEnum.amiga.value, _PfEnum.beos.value, _PfEnum.haiku.value, _PfEnum.mint.value]:
        return "Legacy-Micro"
    if platform in [_PfEnum.atheos.value, _PfEnum.plan9.value, _PfEnum.interix.value]:
        return "Legacy-Experimental"
    if platform in [_PfEnum.nacl.value, _PfEnum.vos.value]:
        return "Legacy-Embedded"
    if platform == [_PfEnum.symbian.value]:
        return "Legacy-Mobile"

    raise RuntimeError(f"Unsupported platform: '{platform}'")


def is_legacy_platform(platform: PossiblePlatforms) -> bool:
    return platform in [
        _PfEnum.os2.value,
        _PfEnum.unixware.value,
        _PfEnum.xenix.value,
        _PfEnum.isc.value,
        _PfEnum.osf1.value,
        _PfEnum.tru64.value,
        _PfEnum.irix.value,
        _PfEnum.sysv.value,
        _PfEnum.riscos.value,
        _PfEnum.amiga.value,
        _PfEnum.beos.value,
        _PfEnum.haiku.value,
        _PfEnum.mint.value,
        _PfEnum.atheos.value,
        _PfEnum.plan9.value,
        _PfEnum.interix.value,
        _PfEnum.nacl.value,
        _PfEnum.vos.value,
        _PfEnum.symbian.value,
        _PfEnum.unknown.value,
    ]


def is_supported_python_platform(platform: PossiblePlatforms) -> bool:
    return platform in [
        _PfEnum.linux.value,
        _PfEnum.darwin.value,
        _PfEnum.win32.value,
        _PfEnum.cygwin.value,
        _PfEnum.msys.value,
        _PfEnum.aix.value,
        _PfEnum.sunos5.value,
        _PfEnum.solaris.value,
        _PfEnum.freebsd.value,
        _PfEnum.openbsd.value,
        _PfEnum.netbsd.value,
        _PfEnum.hp_ux.value,
        _PfEnum.vxworks.value,
        _PfEnum.android.value,
    ]


if sys.platform == "linux":
    from utility.system.Linux.file_folder_browser import *  # noqa: F403
    from utility.system.Linux.messagebox import *  # noqa: F403
elif sys.platform == "darwin":
    from utility.system.MacOS.file_folder_browser import *  # noqa: F403
    from utility.system.MacOS.messagebox import *  # noqa: F403
elif sys.platform == "win32":
    from utility.system.win32.file_folder_browser import *  # noqa: F403
    from utility.system.win32.messagebox import *  # noqa: F403
else:
    raise RuntimeError(f"Unsupported platform: '{sys.platform}'")
