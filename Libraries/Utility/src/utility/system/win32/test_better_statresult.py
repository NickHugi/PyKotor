from __future__ import annotations

import ctypes
import inspect
import os
import shutil
import struct
import sys
import typing
import unittest

from ctypes import (
    POINTER,
    Array,
    GetLastError,
    Structure,
    WinError,
    addressof,
    byref,
    c_uint64,
    c_ulong,
    c_ulonglong,
    c_void_p,
    c_wchar,
    c_wchar_p,
    cast,
    create_string_buffer,
    create_unicode_buffer,
    get_last_error,
    memmove,
    memset,
    sizeof,
    string_at,
    windll,
    wstring_at,
)
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, IntFlag
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Any, ClassVar, Sequence, TypeVar

from semver import Version

from utility.system.path import WindowsPath
from utility.system.win32.com.com_types import GUID
from utility.system.win32.hresult import HRESULT
from utility.system.win32.winapi.device_iocontrol import FSCTL

if TYPE_CHECKING:
    from ctypes import (
        _CArgObject,
        _CData,
        _Pointer,
        c_char,
    )

    from typing_extensions import Self

    from utility.system.win32.winapi.device_iocontrol import IOCTL
    T = TypeVar("T", bound=_CData)
else:
    T = TypeVar("T")


class PlatformSpecificDataClass:
    supported_platforms: ClassVar[list[str]] = []

    def __new__(cls, *args, **kwargs) -> Self:
        if sys.platform not in cls.supported_platforms:
            raise RuntimeError(f"{cls.__name__} can only be instantiated on the following platforms: {', '.join(cls.supported_platforms)}")
        if cls.__base__ is object or cls is not PlatformSpecificDataClass:
            return super().__new__(cls)
        return super().__new__(cls, *args, **kwargs)


if os.name == "nt":
    from ctypes import wintypes

    # Constants
    class FileObjectFlags(IntFlag):
        SE_FILE_OBJECT = 0x00000001
        SE_UNKNOWN_OBJECT = 0x00000002  # Often used for generic file object references

    class SecurityInformationFlags(IntFlag):
        OWNER_SECURITY_INFORMATION = 0x00000001
        GROUP_SECURITY_INFORMATION = 0x00000002
        DACL_SECURITY_INFORMATION = 0x00000004
        SACL_SECURITY_INFORMATION = 0x00000008
        LABEL_SECURITY_INFORMATION = 0x00000010
        ATTRIBUTE_SECURITY_INFORMATION = 0x00000020
        SCOPE_SECURITY_INFORMATION = 0x00000040
        PROCESS_TRUST_LABEL_SECURITY_INFORMATION = 0x00000080
        ACCESS_FILTER_SECURITY_INFORMATION = 0x00000100
        BACKUP_SECURITY_INFORMATION = 0x00000200
        PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
        PROTECTED_SACL_SECURITY_INFORMATION = 0x40000000
        UNPROTECTED_DACL_SECURITY_INFORMATION = 0x20000000
        UNPROTECTED_SACL_SECURITY_INFORMATION = 0x10000000

    class FileCreationDisposition(IntFlag):
        CREATE_NEW = 0x00000001
        CREATE_ALWAYS = 0x00000002
        OPEN_EXISTING = 0x00000003
        OPEN_ALWAYS = 0x00000004
        TRUNCATE_EXISTING = 0x00000005

    class DesiredAccessFlags(IntFlag):
        NONE = 0x00000000
        FILE_READ_DATA = 0x00000001
        FILE_WRITE_DATA = 0x00000002
        FILE_APPEND_DATA = 0x00000004
        FILE_READ_EA = 0x00000008
        FILE_EXECUTE = 0x00000020
        FILE_READ_ATTRIBUTES = 0x00000080
        FILE_WRITE_ATTRIBUTES = 0x00000100
        DELETE = 0x00010000
        READ_CONTROL = 0x00020000
        WRITE_DAC = 0x00040000
        WRITE_OWNER = 0x00080000
        SYNCHRONIZE = 0x00100000
        GENERIC_ALL = 0x10000000
        GENERIC_EXECUTE = 0x20000000
        GENERIC_WRITE = 0x40000000
        GENERIC_READ = 0x80000000

    class FileFlags(IntFlag):
        NONE = 0x00000000
        FILE_FLAG_FIRST_PIPE_INSTANCE = 0x00080000
        FILE_FLAG_OPEN_NO_RECALL = 0x00100000
        FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
        FILE_FLAG_POSIX_SEMANTICS = 0x01000000
        FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
        FILE_FLAG_DELETE_ON_CLOSE = 0x04000000
        FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000
        FILE_FLAG_RANDOM_ACCESS = 0x10000000
        FILE_FLAG_NO_BUFFERING = 0x20000000
        FILE_FLAG_OVERLAPPED = 0x40000000
        FILE_FLAG_WRITE_THROUGH = 0x80000000

    class ShareModeFlags(IntFlag):
        NONE = 0x00000000
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        FILE_SHARE_DELETE = 0x00000004

    class LOCK_INFO(Structure):  # noqa: N801
        _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
            ("Offset", wintypes.LARGE_INTEGER),
            ("Length", wintypes.LARGE_INTEGER),
            ("ProcessId", wintypes.DWORD),
            ("Flags", wintypes.DWORD),
        ]

    FILE_READ_ATTRIBUTES = 0x0080

    # NTFS File Record Header (partial structure)
    class NTFS_FILE_RECORD_HEADER(ctypes.Structure):  # noqa: N801
        _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
            ("Signature", wintypes.DWORD),
            ("UpdateSequenceArrayOffset", wintypes.WORD),
            ("UpdateSequenceArraySize", wintypes.WORD),
            ("LogFileSequenceNumber", wintypes.LARGE_INTEGER),
            ("SequenceNumber", wintypes.WORD),
            ("HardLinkCount", wintypes.WORD),
            ("FirstAttributeOffset", wintypes.WORD),
            ("Flags", wintypes.WORD),
            ("RealSize", wintypes.DWORD),
            ("AllocatedSize", wintypes.DWORD),
            ("BaseFileRecord", wintypes.LARGE_INTEGER),
            ("NextAttributeID", wintypes.WORD),
            ("Padding", wintypes.WORD),
            ("MFTRecordNumber", wintypes.DWORD),
        ]
        Signature: int

    # NTFS File Name Attribute (partial structure)
    class NTFS_FILE_NAME_ATTRIBUTE(ctypes.Structure):  # noqa: N801
        _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
            ("ParentDirectory", wintypes.LARGE_INTEGER),
            ("CreationTime", wintypes.LARGE_INTEGER),
            ("LastModificationTime", wintypes.LARGE_INTEGER),
            ("LastChangeTime", wintypes.LARGE_INTEGER),
            ("LastAccessTime", wintypes.LARGE_INTEGER),
            ("AllocatedSize", wintypes.LARGE_INTEGER),
            ("RealSize", wintypes.LARGE_INTEGER),
            ("Flags", wintypes.DWORD),
            ("ReparsePointTag", wintypes.DWORD),
            ("FileNameLength", ctypes.c_ubyte),
            ("FileNameNamespace", ctypes.c_ubyte),
            # FileName follows in memory, need manual parsing
        ]
    class BY_HANDLE_FILE_INFORMATION(Structure):  # noqa: N801
        _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    class SECURITY_ATTRIBUTES(Structure):  # noqa: N801
        _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", wintypes.LPVOID),
            ("bInheritHandle", wintypes.BOOL),
        ]

        def __init__(
            self,
            inherit_handle: bool = False,  # noqa: FBT002, FBT001
            security_descriptor: _Pointer[wintypes.LPVOID] | None = None,
        ):
            super().__init__()
            self.nLength = sizeof(self)
            self.lpSecurityDescriptor = security_descriptor
            self.bInheritHandle = inherit_handle


    class OVERLAPPED(Structure):  # Define the OVERLAPPED structure
        _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
            ("Internal", wintypes.PULONG),
            ("InternalHigh", wintypes.PULONG),
            ("Offset", wintypes.DWORD),
            ("OffsetHigh", wintypes.DWORD),
            ("hEvent", wintypes.HANDLE),
        ]

    class WindowsDataClass(PlatformSpecificDataClass):
        supported_platforms: ClassVar[list[str]] = ["win32"]
        @classmethod
        def device_io_control(  # noqa: PLR0913
            cls,
            handle: wintypes.HANDLE,
            control_code: FSCTL | IOCTL = FSCTL.FSCTL_GET_OBJECT_ID,
            in_buffer: wintypes.LPVOID | Array[c_char] | _CArgObject | None = None,
            in_buffer_size: wintypes.DWORD | int = 0,
            out_buffer: Array[c_char] | _CArgObject | None = None,
            out_buffer_size: wintypes.DWORD | int = 1024,
            bytes_returned: wintypes.DWORD | _CArgObject | None = None,
            overlapped: _Pointer[OVERLAPPED] | None = None,
            *,
            err_msg: str | None = None
        ) -> HRESULT | bytes:
            """Executes a device-specific operation using the Windows `DeviceIoControl` API.

            Args:
                handle (wintypes.HANDLE): A handle to the device or file on which the operation is to be performed.
                control_code (FSCTL): The control code for the operation. Defaults to FSCTL_GET_OBJECT_ID.
                in_buffer (wintypes.LPVOID | _CArgObject | None, optional): A pointer to the input buffer containing
                    the data required to perform the operation. If None, no input buffer is provided. Defaults to None.
                in_buffer_size (wintypes.DWORD | int, optional): The size of the input buffer in bytes. Defaults to 0 if
                    no input buffer is provided. Defaults to 0.
                out_buffer (Array[c_char] | _CArgObject | None, optional): A pointer to the output buffer
                    to receive the data. If None, a buffer is created. Defaults to None.
                out_buffer_size (wintypes.DWORD | int, optional): The size of the output buffer in bytes. Defaults to 1024.
                bytes_returned (wintypes.DWORD | _CArgObject | None, optional): A pointer to a DWORD that receives
                    the size of the data returned. If None, it is created. Defaults to None.
                overlapped (_Pointer[OVERLAPPED] | None, optional): A pointer to an OVERLAPPED structure for asynchronous
                    operations, or None for synchronous operations. Defaults to None.
                err_msg (str | None, optional): A custom error message to use if the operation fails. If None, a system error
                    message is used. Defaults to None.

            Returns:
                hresult_or_array:
                    int: An integer indicating success (non-zero) or failure (zero).
                        or
                    bytes: The result stored in out_buffer.value.
                    The specific return value is denoted by whether out_buffer was passed or not, and if it was passed with byref() or not.

            Raises:
                OSError: If the `DeviceIoControl` operation fails, an OSError is raised with the provided custom error message or
                    the system error message.
            """
            # Create the output buffer if not provided
            if out_buffer is None:
                buffer_size = out_buffer_size.value if isinstance(out_buffer_size, wintypes.DWORD) else out_buffer_size
                out_buffer = create_string_buffer(buffer_size)

            # Create the bytes_returned DWORD if not provided
            if bytes_returned is None:
                bytes_returned = wintypes.DWORD()

            # Function to ensure that arguments are properly passed as pointers
            def to_byref_if_needed(param: T | _CArgObject) -> T | _CArgObject:
                if param.__class__.__name__ == "CArgObject":
                    return param
                return byref(typing.cast(T, param))

            # Call DeviceIoControl with appropriate parameters
            success = ctypes.windll.kernel32.DeviceIoControl(
                handle,
                control_code,
                None if in_buffer is None else to_byref_if_needed(in_buffer),
                in_buffer_size,
                to_byref_if_needed(out_buffer),
                out_buffer_size,
                to_byref_if_needed(bytes_returned),
                overlapped,
            )

            if success == wintypes.HANDLE(-1).value:
                raise WinError(get_last_error(), err_msg)

            if isinstance(out_buffer, Array):
                assert isinstance(out_buffer.value, bytes)
                return out_buffer.value
            return success

        @classmethod
        def get_file_handle_win32(  # noqa: PLR0913
            cls,
            filepath: str | wintypes.LPCWSTR,
            access: DesiredAccessFlags = DesiredAccessFlags.NONE,
            share_mode: ShareModeFlags = ShareModeFlags.NONE,
            security_attributes: SECURITY_ATTRIBUTES | None = None,
            creation_disposition: FileCreationDisposition = FileCreationDisposition.OPEN_EXISTING,
            flags: FileFlags = FileFlags.NONE,
            template_file: wintypes.HANDLE | None = None,
            *,
            err_msg: str | None = None
        ) -> wintypes.HANDLE:
            """Retrieves a handle to an existing file using the Windows API.

            :param filepath: The path to the file to open.
            :param access: Desired access rights. Use DesiredAccessFlags.NONE if no access is required.
            :param share_mode: Sharing mode for the file. Use ShareModeFlags.NONE to prevent sharing.
            :param security_attributes: A SECURITY_ATTRIBUTES structure that specifies the security attributes.
                                        If None, default security settings are used.
            :param creation_disposition: An action to take on the file. For example, OPEN_EXISTING opens the file if it exists.
            :param flags: Additional flags and attributes. For example, FILE_FLAG_BACKUP_SEMANTICS allows opening directories.
            :param template_file: A HANDLE to a template file with the GENERIC_READ access right.
                                Can be None if no template file is used.
            :param error_message: A custom error message to use if the file handle cannot be obtained. If None, a system error message is used.
            :return: A HANDLE to the opened file. Raises an exception on failure.
            """
            handle = windll.kernel32.CreateFileW(
                filepath,
                access,
                share_mode,
                byref(security_attributes) if security_attributes else None,
                creation_disposition,
                FileCreationDisposition.OPEN_EXISTING,
                flags,
                template_file,
            )

            if handle == wintypes.HANDLE(-1).value:
                raise WinError(get_last_error(), err_msg or "Failed to get the file handle.")

            # Validate the handle
            file_info = BY_HANDLE_FILE_INFORMATION()
            if not windll.kernel32.GetFileInformationByHandle(handle, byref(file_info)):
                windll.kernel32.CloseHandle(handle)
                raise WinError(get_last_error(), "Invalid file handle.")

            return handle

        @staticmethod
        def array_to_bytes(ctypes_array: Array[c_char] | bytes) -> bytes:
            """Convert a ctypes Array to bytes.

            Args:
                ctypes_array (Array): The ctypes array to convert.

            Returns:
                bytes: The byte representation of the ctypes array.
            """
            if isinstance(ctypes_array, bytes):
                return ctypes_array
            if not isinstance(ctypes_array, Array):
                raise TypeError(f"The input must be a Array, not {ctypes_array.__class__.__name__}")
            if isinstance(ctypes_array.value, bytes):
                return ctypes_array.value
            raise ValueError(f"The input's value attr must be a bytes, not {ctypes_array.value.__class__.__name__}")


    @dataclass(frozen=True)
    class WindowsExtendedAttributes(WindowsDataClass):
        extended_attributes: dict[str, bytes]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> WindowsExtendedAttributes:
            filepath = str(WindowsPath(filepath))
            attributes = {}
            buffer = create_string_buffer(1024)
            size = wintypes.DWORD(1024)

            # Open file handle
            hFile = cls.get_file_handle_win32(filepath)
            if hFile == wintypes.HANDLE(-1).value:
                raise OSError("Failed to open file handle")

            # Initialize context pointer for BackupRead
            context = POINTER(c_void_p)()

            try:
                more = windll.kernel32.BackupRead(
                    hFile,
                    byref(buffer),
                    size,
                    byref(size),
                    False,  # Process the data  # noqa: FBT003
                    True,   # Start reading from the beginning  # noqa: FBT003
                    byref(context)
                )

                while more:
                    ea = buffer.raw[:size.value].split(b"\x00")
                    if ea[0]:
                        attributes[ea[0].decode()] = ea[1]
                    more = windll.kernel32.BackupRead(
                        hFile,
                        byref(buffer),
                        size,
                        byref(size),
                        False,  # Process the data  # noqa: FBT003
                        False,  # Continue reading  # noqa: FBT003
                        byref(context)
                    )
            finally:
                # Clean up the context and handle
                windll.kernel32.BackupRead(
                    hFile,
                    None,
                    wintypes.DWORD(0),
                    None,
                    True,   # End the read operation  # noqa: FBT003
                    False,  # noqa: FBT003
                    byref(context)
                )
                windll.kernel32.CloseHandle(hFile)

            return cls(extended_attributes=attributes)

    @dataclass(frozen=True)
    class WindowsFileIntegrity(WindowsDataClass):
        integrity_status: bytes | None

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle = cls.get_file_handle_win32(filepath)
            buffer = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()

            success = cls.device_io_control(
                handle,
                FSCTL.FSCTL_GET_INTEGRITY_INFORMATION,
                None,
                0,
                buffer,
                1024,
                byref(bytes_returned),
                None,
            )

            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve integrity information for {filepath}")

            return cls(integrity_status=buffer.raw[:bytes_returned.value])


    @dataclass(frozen=True)
    class WindowsFileIndex(WindowsDataClass):
        file_index: int

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle = cls.get_file_handle_win32(filepath)
            file_info = BY_HANDLE_FILE_INFORMATION()

            success = windll.kernel32.GetFileInformationByHandle(handle, byref(file_info))
            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve file index for {filepath}")

            file_index = (file_info.nFileIndexHigh << 32) | file_info.nFileIndexLow
            return cls(file_index=file_index)


    @dataclass(frozen=True)
    class WindowsSparseFileRegions(WindowsDataClass):
        regions: list[tuple[int, int]]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle = cls.get_file_handle_win32(filepath)
            buffer = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()

            success = cls.device_io_control(
                handle,
                FSCTL.FSCTL_QUERY_ALLOCATED_RANGES,
                None,
                0,
                buffer,
                1024,
                byref(bytes_returned),
                None,
            )

            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve sparse file regions for {filepath}")

            regions = []
            for i in range(0, bytes_returned.value, sizeof(wintypes.LARGE_INTEGER) * 2):
                offset = c_ulonglong.from_buffer_copy(buffer.raw[i:i + 8])
                length = c_ulonglong.from_buffer_copy(buffer.raw[i + 8:i + 16])
                regions.append((offset.value, length.value))

            return cls(regions=regions)


    @dataclass(frozen=True)
    class WindowsFileLocks(WindowsDataClass):
        locks: list[dict[str, Any]]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle = cls.get_file_handle_win32(filepath)
            buffer = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()

            success = cls.device_io_control(
                handle,
                FSCTL.FSCTL_QUERY_LOCKS,
                None,
                0,
                buffer,
                1024,
                byref(bytes_returned),
                None,
            )

            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve file locks for {filepath}")

            locks = []
            for i in range(0, bytes_returned.value, sizeof(LOCK_INFO)):
                lock_info = LOCK_INFO.from_buffer_copy(buffer.raw[i:i + sizeof(LOCK_INFO)])
                locks.append(
                    {
                        "offset": lock_info.Offset,
                        "length": lock_info.Length,
                        "process_id": lock_info.ProcessId,
                        "flags": lock_info.Flags,
                    }
                )

            return cls(locks=locks)

    @dataclass(frozen=True)
    class WindowsAlternateDataStreams(WindowsDataClass):
        alternate_data_streams: list[str]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            ads_list = []

            class WIN32_FIND_STREAM_DATA(Structure):  # noqa: N801
                MAX_PATH = 260
                STREAMNAME_SIZE = MAX_PATH + 36
                _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
                    ("StreamName", c_wchar * STREAMNAME_SIZE),
                    ("StreamSize", wintypes.LARGE_INTEGER),
                ]

            stream_data = WIN32_FIND_STREAM_DATA()
            handle = windll.kernel32.FindFirstStreamW(filepath, 0, byref(stream_data), 0)
            if handle != wintypes.HANDLE(-1).value:
                try:
                    ads_list.append(stream_data.StreamName)
                    stream_data = WIN32_FIND_STREAM_DATA()
                    windll.kernel32.FindNextStreamW.argtypes = [wintypes.HANDLE, wintypes.LPVOID]
                    windll.kernel32.FindNextStreamW.restype = wintypes.BOOL
                    while windll.kernel32.FindNextStreamW(wintypes.HANDLE(handle), stream_data):
                        ads_list.append(stream_data.StreamName)
                        stream_data = WIN32_FIND_STREAM_DATA()
                finally:
                    windll.kernel32.FindClose(handle)

            return cls(alternate_data_streams=ads_list)


    @dataclass(frozen=True)
    class WindowsHardLinks(WindowsDataClass):
        hard_link_count: int
        hard_link_paths: list[str]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath_str = str(WindowsPath(filepath))
            hard_link_paths = []
            handle: wintypes.HANDLE = cls.get_file_handle_win32(
                filepath_str,
                DesiredAccessFlags.NONE,  # No access to the file is required
                ShareModeFlags.NONE,  # Do not share the file
                None,  # lpSecurityAttributes is None
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                None,  # hTemplateFile is None
            )

            if handle != wintypes.HANDLE(-1).value:
                file_info = BY_HANDLE_FILE_INFORMATION()
                success = windll.kernel32.GetFileInformationByHandle(handle, byref(file_info))
                windll.kernel32.CloseHandle(handle)

                if success:
                    hard_link_count = file_info.nNumberOfLinks
                    buffer_size = c_ulong(1024)
                    buffer = create_unicode_buffer(buffer_size.value)

                    search_handle = windll.kernel32.FindFirstFileNameW(filepath, 0, buffer_size, buffer)

                    if search_handle != wintypes.HANDLE(-1).value:
                        more_names = True

                        while more_names:
                            hard_link_paths.append(buffer.value)
                            result = windll.kernel32.FindNextFileNameW(search_handle, buffer_size, buffer)
                            more_names = result != 0

                        windll.kernel32.FindClose(search_handle)

            return cls(hard_link_count=hard_link_count, hard_link_paths=hard_link_paths)


    @dataclass(frozen=True)
    class WindowsVolumeInformation(WindowsDataClass):
        volume_serial_number: int
        file_system_type: str
        maximum_component_length: int
        file_system_flags: int

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            drive = os.path.splitdrive(str(WindowsPath(filepath)))[0]
            volume_serial_number = wintypes.DWORD()
            max_component_length = wintypes.DWORD()
            file_system_flags = wintypes.DWORD()
            file_system_name_buffer = create_unicode_buffer(256)
            windll.kernel32.GetVolumeInformationW(
                drive,
                None,
                0,
                byref(volume_serial_number),
                byref(max_component_length),
                byref(file_system_flags),
                file_system_name_buffer,
                len(file_system_name_buffer),
            )
            return cls(
                volume_serial_number=volume_serial_number.value,
                file_system_type=file_system_name_buffer.value,
                maximum_component_length=max_component_length.value,
                file_system_flags=file_system_flags.value,
            )


    @dataclass(frozen=True)
    class WindowsFileCompression(WindowsDataClass):
        compression_format: bytes | None

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle: wintypes.HANDLE = cls.get_file_handle_win32(
                filepath,
                DesiredAccessFlags.NONE,  # No access to the file is required
                ShareModeFlags.NONE,  # Do not share the file
                None,
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                None,
            )
            if handle == -1:
                raise OSError(f"Failed to open file handle for {filepath}")

            buffer: Array[c_char] = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()
            success = cls.device_io_control(handle, FSCTL.FSCTL_GET_COMPRESSION, None, 0, buffer, 1024, byref(bytes_returned), None)
            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve compression information for {filepath}")

            return cls(compression_format=buffer.raw[: bytes_returned.value])


    @dataclass(frozen=True)
    class WindowsFileEncryption(WindowsDataClass):
        encryption_status: bytes | None

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle: wintypes.HANDLE = cls.get_file_handle_win32(
                filepath,
                DesiredAccessFlags.NONE,  # No access to the file is required
                ShareModeFlags.NONE,  # Do not share the file
                None,
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                None,
            )
            if handle == -1:
                raise OSError(f"Failed to open file handle for {filepath}")

            buffer: Array[c_char] = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()
            success = cls.device_io_control(handle, FSCTL.FSCTL_GET_ENCRYPTION, None, 0, buffer, 1024, byref(bytes_returned), None)
            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve encryption information for {filepath}")

            return cls(encryption_status=buffer.raw[: bytes_returned.value])


    @dataclass(frozen=True)
    class WindowsFileSparsity(WindowsDataClass):
        sparse_status: bytes | None

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle: wintypes.HANDLE = cls.get_file_handle_win32(
                filepath,
                DesiredAccessFlags.NONE,  # No access to the file is required
                ShareModeFlags.NONE,  # Do not share the file
                None,
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                None,
            )
            if handle == -1:
                raise OSError(f"Failed to open file handle for {filepath}")

            buffer: Array[c_char] = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()
            success = cls.device_io_control(handle, FSCTL.FSCTL_QUERY_ALLOCATED_RANGES, None, 0, buffer, 1024, byref(bytes_returned), None)
            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve sparsity information for {filepath}")

            return cls(sparse_status=buffer.raw[: bytes_returned.value])


    @dataclass(frozen=True)
    class WindowsFileQuotas(WindowsDataClass):
        quota_information: bytes | None

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            handle: wintypes.HANDLE = cls.get_file_handle_win32(
                filepath,
                DesiredAccessFlags.NONE,  # No access to the file is required
                ShareModeFlags.NONE,  # Do not share the file
                None,
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                None,
            )
            if handle == -1:
                raise OSError(f"Failed to open file handle for {filepath}")

            buffer: Array[c_char] = create_string_buffer(1024)
            bytes_returned = wintypes.DWORD()
            success = cls.device_io_control(handle, FSCTL.FSCTL_GET_QUOTA_INFORMATION, None, 0, buffer, 1024, byref(bytes_returned), None)
            windll.kernel32.CloseHandle(handle)

            if success == 0:
                raise OSError(f"Failed to retrieve quota information for {filepath}")

            return cls(quota_information=buffer.raw[: bytes_returned.value])


    @dataclass(frozen=True)
    class WindowsFileResources(WindowsDataClass):
        resources: list[dict[str, Any]]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            resources = []
            filepath = str(WindowsPath(filepath))
            module = windll.kernel32.LoadLibraryW(filepath)
            if not module:
                raise OSError(f"Failed to load library for {filepath}")
            resource_types = []
            windll.kernel32.EnumResourceTypesW(module, lambda hModule, lpType, lParam: resource_types.append(lpType), 0)  # noqa: ARG005, N803, ARG005, N803, N803, ARG005, N803, ARG005, N803
            for res_type in resource_types:
                resource_names = []
                windll.kernel32.EnumResourceNamesW(module, res_type, lambda hModule, lpType, lpName, lParam: resource_names.append(lpName), 0)  # noqa: N803, ARG005, N803, ARG005, N803, ARG005, N803, ARG005, N803, ARG005, N803, ARG005, N803, B023
                for res_name in resource_names:
                    res_handle = windll.kernel32.FindResourceW(module, res_name, res_type)
                    res_data_handle = windll.kernel32.LoadResource(module, res_handle)
                    res_data = windll.kernel32.LockResource(res_data_handle)
                    res_size = windll.kernel32.SizeofResource(module, res_handle)
                    resources.append({"type": res_type, "name": res_name, "data": string_at(res_data, res_size)})
            windll.kernel32.FreeLibrary(module)
            return cls(resources=resources)


    @dataclass(frozen=True)
    class WindowsFileVersion(WindowsDataClass):
        file_version: str | None
        product_name: str | None
        product_version: str | None
        company_name: str | None
        file_description: str | None

        supported_platforms: ClassVar[list[str]] = ["win32"]
        VERSION_KEYS: ClassVar[list[str]] = [
            "\\StringFileInfo\\040904b0\\ProductName",
            "\\StringFileInfo\\040904b0\\ProductVersion",
            "\\StringFileInfo\\040904b0\\CompanyName",
            "\\StringFileInfo\\040904b0\\FileDescription",
        ]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            filepath_unicode = create_unicode_buffer(filepath)

            size = windll.version.GetFileVersionInfoSizeW(filepath_unicode, None)
            if size <= 0:
                # No version information available, return dataclass with None values
                return cls(
                    file_version=None,
                    product_name=None,
                    product_version=None,
                    company_name=None,
                    file_description=None,
                )

            res = create_string_buffer(size)
            success = windll.version.GetFileVersionInfoW(filepath_unicode, 0, size, res)
            if not success:
                raise OSError("GetFileVersionInfoW failed to retrieve the version information.")

            r = c_void_p()
            length = wintypes.UINT()
            ver_info = {}

            for key in cls.VERSION_KEYS:
                if windll.version.VerQueryValueW(res, key, byref(r), byref(length)):
                    ver_info[key.split("\\")[-1]] = wstring_at(r, length.value)
                else:
                    ver_info[key.split("\\")[-1]] = None

            return cls(
                file_version=ver_info.get("FileVersion"),
                product_name=ver_info.get("ProductName"),
                product_version=ver_info.get("ProductVersion"),
                company_name=ver_info.get("CompanyName"),
                file_description=ver_info.get("FileDescription"),
            )


    @dataclass(frozen=True)
    class WindowsFileSecurityInfo(WindowsDataClass):
        owner: str
        dacl: list[str]

        supported_platforms: ClassVar[list[str]] = ["win32"]

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath = str(WindowsPath(filepath))
            security_info = c_void_p()
            owner_sid = c_void_p()
            group_sid = c_void_p()
            dacl = c_void_p()
            sacl = c_void_p()

            result = windll.advapi32.GetNamedSecurityInfoW(
                filepath,
                FileObjectFlags.SE_FILE_OBJECT,
                SecurityInformationFlags.OWNER_SECURITY_INFORMATION | SecurityInformationFlags.DACL_SECURITY_INFORMATION,
                byref(owner_sid),
                byref(group_sid),
                byref(dacl),
                byref(sacl),
                byref(security_info),
            )

            if result != 0:  # ERROR_SUCCESS
                raise OSError(f"Failed to get security information for {filepath}")

            owner = cls._lookup_account_sid(owner_sid)
            dacl_entries = cls._get_dacl_entries(dacl)

            return cls(owner=owner, dacl=dacl_entries)

        @staticmethod
        def _lookup_account_sid(sid: c_void_p) -> str:
            name = create_unicode_buffer(256)
            domain = create_unicode_buffer(256)
            name_size = wintypes.DWORD(256)
            domain_size = wintypes.DWORD(256)
            sid_type = wintypes.DWORD()

            windll.advapi32.LookupAccountSidW(None, sid, name, byref(name_size), domain, byref(domain_size), byref(sid_type))
            return f"{domain.value}\\{name.value}"

        @staticmethod
        def _get_dacl_entries(dacl: c_void_p) -> list[str]:
            ace_count = c_ulong()
            windll.advapi32.GetAclInformation(dacl, byref(ace_count), sizeof(ace_count), 2)  # AclSizeInformation
            entries = []

            for i in range(ace_count.value):
                ace = c_void_p()
                if windll.advapi32.GetAce(dacl, i, byref(ace)):
                    sid = WindowsFileSecurityInfo._get_sid_from_ace(ace)
                    if sid:
                        entries.append(sid)

            return entries

        @staticmethod
        def _get_sid_from_ace(ace: c_void_p) -> str:
            sid_start = addressof(ace) + 8  # Skip ACE header
            sid = cast(sid_start, POINTER(c_void_p))
            return WindowsFileSecurityInfo._lookup_account_sid(sid.contents)


    class CompressionFormat(IntEnum):
        NONE = 0
        DEFAULT = 1
        LZNT1 = 2
        XPRESS = 3
        XPRESS_HUFF = 4


    class UsnReason(IntEnum):
        NONE = 0x00000000  # e.g. when the entry represents a file creation or deletion event where no other specific reason is applicable
        DATA_OVERWRITE = 0x00000001
        DATA_EXTEND = 0x00000002
        DATA_TRUNCATION = 0x00000004
        NAMED_DATA_OVERWRITE = 0x00000010
        NAMED_DATA_EXTEND = 0x00000020
        NAMED_DATA_TRUNCATION = 0x00000040
        FILE_CREATE = 0x00000100
        FILE_DELETE = 0x00000200
        EA_CHANGE = 0x00000400
        SECURITY_CHANGE = 0x00000800
        RENAME_OLD_NAME = 0x00001000
        RENAME_NEW_NAME = 0x00002000
        INDEXABLE_CHANGE = 0x00004000
        BASIC_INFO_CHANGE = 0x00008000
        HARD_LINK_CHANGE = 0x00010000
        COMPRESSION_CHANGE = 0x00020000
        ENCRYPTION_CHANGE = 0x00040000
        OBJECT_ID_CHANGE = 0x00080000
        REPARSE_POINT_CHANGE = 0x00100000
        STREAM_CHANGE = 0x00200000
        TRANSACTED_CHANGE = 0x00400000
        INTEGRITY_CHANGE = 0x00800000
        CLOSE = 0x80000000


    class FileHandle(int):
        def __new__(cls, handle: int | None) -> Self:
            if handle is None or handle == windll.kernel32.INVALID_HANDLE_VALUE:
                raise ValueError("Invalid handle value.")
            return super().__new__(cls, handle)

        def __init__(self, handle: int | None):
            self.handle = handle

        @classmethod
        def from_handle_value(cls, handle_value: int) -> Self:
            """Creates a FileHandle object from a raw handle value."""
            return cls(handle_value)

        def is_valid(self) -> bool:
            """Check if the handle is valid."""
            return self != windll.kernel32.INVALID_HANDLE_VALUE

        def read(self, num_bytes: int) -> bytes:
            """Reads data from the file handle."""
            if not self.is_valid():
                raise ValueError("Invalid file handle.")

            buffer = create_string_buffer(num_bytes)
            bytes_read = c_ulong(0)

            success = windll.kernel32.ReadFile(
                self.handle,
                buffer,
                num_bytes,
                byref(bytes_read),
                None
            )

            if not success:
                raise WinError()

            return buffer.raw[:bytes_read.value]

        def close(self) -> None:
            """Close the file handle."""
            if self.is_valid():
                windll.kernel32.CloseHandle(self.handle)
                self.handle = windll.kernel32.INVALID_HANDLE_VALUE

        def __enter__(self) -> Self:
            """Support for context manager."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            """Ensure the handle is closed when exiting the context."""
            self.close()

        def __str__(self) -> str:
            return f"FileHandle({self.handle})"

    @dataclass
    class FileReference:
        value: int

        @classmethod
        def from_int(cls, value: int) -> Self:
            return cls(value)

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            if len(data) != 8:
                raise ValueError("File reference number must be 8 bytes long.")
            value = int.from_bytes(data, "little")
            return cls(value)

        def to_bytes(self) -> bytes:
            return self.value.to_bytes(8, "little")

        def get_mft_record_number(self) -> int:
            return self.value & 0xFFFFFFFFFFFF

        def get_sequence_number(self) -> int:
            return (self.value >> 48) & 0xFFFF

        def open_file_by_reference(self, volume_path: str) -> FileHandle:
            """Opens a file by its reference and returns a FileHandle object."""
            volume_handle = WindowsDataClass.get_file_handle_win32(
                volume_path,
                DesiredAccessFlags.GENERIC_READ,
                ShareModeFlags.FILE_SHARE_READ | ShareModeFlags.FILE_SHARE_WRITE,
                None,
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.NONE,
                None,
            )

            if volume_handle == windll.kernel32.INVALID_HANDLE_VALUE:
                raise WinError()

            file_id_descriptor = create_string_buffer(24)
            memset(file_id_descriptor, 0, 24)
            memmove(file_id_descriptor, self.to_bytes(), 8)

            handle = WindowsDataClass.get_file_handle_win32(
                c_wchar_p(None),
                DesiredAccessFlags.GENERIC_READ,
                ShareModeFlags.FILE_SHARE_READ | ShareModeFlags.FILE_SHARE_WRITE,
                None,
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                volume_handle
            )

            windll.kernel32.CloseHandle(volume_handle)

            return FileHandle.from_handle_value(handle.value)

    class FileAttributes(IntFlag):
        NONE = 0x00000000
        READONLY = 0x00000001
        HIDDEN = 0x00000002
        SYSTEM = 0x00000004
        DIRECTORY = 0x00000010
        ARCHIVE = 0x00000020
        DEVICE = 0x00000040
        NORMAL = 0x00000080
        TEMPORARY = 0x00000100
        SPARSE_FILE = 0x00000200
        REPARSE_POINT = 0x00000400
        COMPRESSED = 0x00000800
        OFFLINE = 0x00001000
        NOT_CONTENT_INDEXED = 0x00002000
        ENCRYPTED = 0x00004000
        INTEGRITY_STREAM = 0x00008000
        VIRTUAL = 0x00010000
        NO_SCRUB_DATA = 0x00020000
        RECALL_ON_OPEN = 0x00040000
        PINNED = 0x00080000
        UNPINNED = 0x00100000
        RECALL_ON_DATA_ACCESS = 0x00400000

        def __repr__(self) -> str:
            active_flags = [name for name, value in self.__class__.__members__.items()
                            if self & value]
            if not active_flags:
                return f"{self.__class__.__name__}.NONE"
            return f"{' | '.join(f'{self.__class__.__name__}.{flag}' for flag in active_flags)}"

    class SourceInfo(IntFlag):
        DATA_MODIFIED = 0x00000001  # Data was written by the user
        SYSTEM_MODIFIED = 0x00000002  # Data was modified by the system
        NON_JOURNAL_CHANGE = 0x00000004  # Changes that did not cause a change in the file (e.g., defragmentation)

    @dataclass(frozen=True)
    class UsnJournalData(WindowsDataClass):
        record_length: int
        version: Version
        file_reference_number: FileReference
        parent_file_reference_number: FileReference
        usn: Usn
        timestamp: datetime
        reason: UsnReason
        source_info: int
        security_id: int
        file_attributes: FileAttributes
        filename: str

        MIN_SIZE: int = 60

        class USN_JOURNAL_DATA_V0(Structure):  # noqa: N801
            """define and hold information about the USN (Update Sequence Number) Journal on a volume.

            This structure is essential for querying the state of the USN Journal using the FSCTL_QUERY_USN_JOURNAL control code.
            """
            _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
                ("UsnJournalID", wintypes.LARGE_INTEGER),
                ("FirstUsn", wintypes.LARGE_INTEGER),
                ("NextUsn", wintypes.LARGE_INTEGER),
                ("LowestValidUsn", wintypes.LARGE_INTEGER),
                ("MaxUsn", wintypes.LARGE_INTEGER),
                ("MaxSize", wintypes.DWORD),
                ("AllocationDelta", wintypes.DWORD)
            ]
            NextUsn: int
        class USN_JOURNAL_DATA_V1(Structure):  # noqa: N801
            """USN_JOURNAL_DATA_V1 structure, used for querying the state of the USN Journal with additional fields."""
            _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
                ("UsnJournalID", wintypes.LARGE_INTEGER),
                ("FirstUsn", wintypes.LARGE_INTEGER),
                ("NextUsn", wintypes.LARGE_INTEGER),
                ("LowestValidUsn", wintypes.LARGE_INTEGER),
                ("MaxUsn", wintypes.LARGE_INTEGER),
                ("MaximumSize", c_uint64),    # Changed from DWORD in V0
                ("AllocationDelta", c_uint64), # Changed from DWORD in V0
                ("MinSupportedMajorVersion", wintypes.WORD),  # New in V1
                ("MaxSupportedMajorVersion", wintypes.WORD)   # New in V1
            ]
        class USN_JOURNAL_DATA_V2(Structure):  # noqa: N801
            """USN_JOURNAL_DATA_V2 structure, which includes flags for the journal and adds new fields."""
            _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
                ("UsnJournalID", wintypes.LARGE_INTEGER),
                ("FirstUsn", wintypes.LARGE_INTEGER),
                ("NextUsn", wintypes.LARGE_INTEGER),
                ("LowestValidUsn", wintypes.LARGE_INTEGER),
                ("MaxUsn", wintypes.LARGE_INTEGER),
                ("MaximumSize", c_uint64),
                ("AllocationDelta", c_uint64),
                ("MinSupportedMajorVersion", wintypes.WORD),
                ("MaxSupportedMajorVersion", wintypes.WORD),
                ("Flags", wintypes.DWORD),  # New in V2, contains flags for the journal
                ("RangeTrackChunkSize", wintypes.DWORD),  # New in V2, for managing tracking ranges
                ("RangeTrackFileSizeThreshold", wintypes.LARGE_INTEGER)  # New in V2, threshold size for file tracking
            ]

        class MFT_ENUM_DATA_V0(Structure):  # noqa: N801, D106
            _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
                ("FileReferenceNumber", wintypes.LARGE_INTEGER),
                ("NextFileReferenceNumber", wintypes.LARGE_INTEGER),
            ]
            FileReferenceNumber: int
            NextFileReferenceNumber: int
        class MFT_ENUM_DATA_V1(Structure):  # noqa: N801
            """MFT_ENUM_DATA_V1 structure, used to enumerate the MFT with more control and granularity."""
            _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
                ("FileReferenceNumber", wintypes.LARGE_INTEGER),
                ("LowUsn", wintypes.LARGE_INTEGER),  # New in V1, low USN for filtering
                ("HighUsn", wintypes.LARGE_INTEGER),  # New in V1, high USN for filtering
                ("Flags", wintypes.DWORD)  # New in V1, to control enumeration behavior
            ]
            FileReferenceNumber: int

        @classmethod
        def resolve_full_path(cls, handle: wintypes.HANDLE, record: UsnJournalData) -> WindowsPath:
            """Does not currently work."""
            parts = [record.filename]
            current_ref = record.parent_file_reference_number

            while current_ref.value != 0:  # Assuming 0 means the root, adjust as needed
                parent_record = cls.find_record_by_reference(handle, current_ref)  # Implement this function
                parts.insert(0, parent_record.filename)
                current_ref = parent_record.parent_file_reference_number

            return WindowsPath("\\").joinpath(*parts)

        @classmethod
        def find_record_by_reference(cls, handle: wintypes.HANDLE, reference: FileReference) -> UsnJournalData:
            """Does not currently work."""
            # Prepare the input buffer with the reference number
            input_buffer = ctypes.create_string_buffer(reference.value.to_bytes(8, "little"))

            # Create an output buffer large enough to hold the file record
            output_buffer_size = 1024 * 16  # 16 KB buffer, adjust as necessary
            output_buffer = ctypes.create_string_buffer(output_buffer_size)

            # Call DeviceIoControl to get the file record
            bytes_returned = wintypes.DWORD(0)
            success = cls.device_io_control(
                handle,
                FSCTL.FSCTL_GET_NTFS_FILE_RECORD,
                input_buffer,
                ctypes.sizeof(input_buffer),
                output_buffer,
                output_buffer_size,
                ctypes.byref(bytes_returned),
                None
            )

            if not success:
                raise ctypes.WinError(ctypes.get_last_error())

            # Parse the NTFS file record header
            record_header = NTFS_FILE_RECORD_HEADER.from_buffer_copy(output_buffer)

            ascii_for_FILE = 0x454C4946
            if record_header.Signature != ascii_for_FILE:
                raise ValueError("Invalid NTFS file record signature")

            # Locate the first attribute
            attr_offset = record_header.FirstAttributeOffset
            filename = None
            parent_ref = None

            while attr_offset < record_header.RealSize:
                attr_type, attr_length = struct.unpack("<II", output_buffer.value[attr_offset:attr_offset + 8])

                if attr_type == 0x30:  # File Name Attribute
                    filename_attr = NTFS_FILE_NAME_ATTRIBUTE.from_buffer_copy(output_buffer.value[attr_offset + 16:])
                    name_length = filename_attr.FileNameLength
                    parent_ref = FileReference(filename_attr.ParentDirectory)
                    filename = ctypes.wstring_at(ctypes.addressof(filename_attr) + ctypes.sizeof(NTFS_FILE_NAME_ATTRIBUTE), name_length)
                    break

                # Move to the next attribute
                attr_offset += attr_length

            if filename is None or parent_ref is None:
                raise ValueError("Failed to parse file name attribute from MFT record")

            return cls(filename=filename, parent_file_reference_number=parent_ref)

        @classmethod
        def get_changes_since_timestamp(
            cls,
            handle: wintypes.HANDLE,
            path: WindowsPath = None,  # The optional part is currently broken.
            timestamp: datetime | None = None,
        ) -> dict[WindowsPath, UsnJournalData]:
            """Retrieves the changes from the USN Journal since the provided timestamp."""
            changes: dict[WindowsPath, UsnJournalData] = {}

            usn_journal_data = cls.USN_JOURNAL_DATA_V0()
            bytes_returned = wintypes.DWORD(0)
            cls.device_io_control(
                handle,
                FSCTL.FSCTL_QUERY_USN_JOURNAL,
                None,
                0,
                ctypes.byref(usn_journal_data),
                ctypes.sizeof(cls.USN_JOURNAL_DATA_V0),
                ctypes.byref(bytes_returned),
                None
            )

            mft_enum_data = cls.MFT_ENUM_DATA_V0(
                FileReferenceNumber=0,
                NextFileReferenceNumber=usn_journal_data.NextUsn
            )

            buffer_size = 65536
            buffer = ctypes.create_string_buffer(buffer_size)

            while True:
                success = cls.device_io_control(
                    handle,
                    FSCTL.FSCTL_READ_USN_JOURNAL,
                    ctypes.byref(mft_enum_data),
                    ctypes.sizeof(cls.MFT_ENUM_DATA_V0),
                    buffer,
                    buffer_size,
                    ctypes.byref(bytes_returned),
                    None
                )
                if not success or bytes_returned.value == 0:
                    break

                offset = 0
                while offset < bytes_returned.value:
                    usn_record = cls.from_bytes(buffer.raw[offset:])
                    if isinstance(usn_record, ValueError):
                        print(usn_record)
                        continue
                    if timestamp is not None and usn_record.timestamp < timestamp:
                        continue
                    offset += usn_record.record_length
                    changes[path / usn_record.filename] = usn_record
                    mft_enum_data.FileReferenceNumber = usn_record.file_reference_number.value


            return changes

        @classmethod
        def _get_handle_from_path(cls, path: WindowsPath) -> c_void_p:
            path_str = str(path)
            if path.parent.name or path.is_file():  # volume path
                return cls.get_file_handle_win32(path_str)
            return cls.get_file_handle_win32(
                path_str,
                DesiredAccessFlags.GENERIC_READ,
                ShareModeFlags.FILE_SHARE_READ | ShareModeFlags.FILE_SHARE_WRITE,  # FILE_SHARE_READ | FILE_SHARE_WRITE
                None,  # SECURITY_ATTRIBUTES
                FileCreationDisposition.OPEN_EXISTING,
                FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                None,  # No template file.
            )

        @classmethod
        def from_path(
            cls,
            file_or_volume_path: os.PathLike | str,
            *,
            handle: wintypes.HANDLE | None = None,
        ) -> Self | ValueError:
            path = WindowsPath(file_or_volume_path).resolve()
            if handle is None:
                handle = cls._get_handle_from_path(path)
                err_msg = f"Failed to retrieve USN journal information for path '{path}'"
                if not path.parent.name and not path.exists() and not path.is_file():  # volume path
                    data = cls.device_io_control(handle, FSCTL.FSCTL_QUERY_USN_JOURNAL, out_buffer_size=sizeof(cls.USN_JOURNAL_DATA_V0), overlapped=None, err_msg=err_msg)
                else:
                    data = cls.device_io_control(handle, FSCTL.FSCTL_READ_FILE_USN_DATA, err_msg=err_msg)
                windll.kernel32.CloseHandle(handle)
            assert isinstance(data, bytes)
            assert not isinstance(data, HRESULT)

            return cls.from_bytes(data)

        @classmethod
        def from_bytes(cls, data: bytes) -> Self | ValueError:
            if len(data) < cls.MIN_SIZE:
                stack_info = "\n".join([f'File "{frame.filename}", line {frame.lineno}, in {frame.function}' for frame in inspect.stack()])
                return ValueError(f"Insufficient data for USN record: {len(data)}\nTraceback (most recent call last):\n{stack_info}")

            # Decode filename from the data
            filename_start = int.from_bytes(data[58:60], "little")
            filename_end = filename_start + int.from_bytes(data[56:58], "little")
            filename = data[filename_start:filename_end].decode("utf-16")

            # Construct the UsnJournalData object with meaningful types
            return cls(
                record_length=int.from_bytes(data[:4], "little"),
                version=Version(int.from_bytes(data[4:6], "little"), int.from_bytes(data[6:8], "little")),
                file_reference_number=FileReference.from_bytes(data[8:16]),
                parent_file_reference_number=FileReference.from_bytes(data[16:24]),
                usn=int.from_bytes(data[24:32], "little"),
                timestamp=datetime.fromtimestamp(int.from_bytes(data[32:40], "little") / 10**7),  # Assuming timestamp is in 100-nanosecond intervals since 1601-01-01  # noqa: DTZ006
                reason=UsnReason(int.from_bytes(data[40:44], "little")),
                source_info=SourceInfo(int.from_bytes(data[44:48], "little")),
                security_id=int.from_bytes(data[48:52], "little"),
                file_attributes=FileAttributes(int.from_bytes(data[52:56], "little")),
                filename=filename
            )

        def __str__(self) -> str:
            return f"USN Journal Record: {self.filename} (USN: {self.usn})"

    class Usn(int):
        def __new__(cls, value: int) -> Self:
            if value < 0:
                raise ValueError("USN must be a non-negative integer.")
            return super().__new__(cls, value)

        def __init__(self, value: int):
            self.value = value

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            if len(data) != 8:
                raise ValueError("USN must be 8 bytes long.")
            return cls(int.from_bytes(data, "little"))

        def to_bytes(self) -> bytes:
            return self.value.to_bytes(8, "little")

        def __str__(self) -> str:
            return f"USN({self.value})"

    class SecurityId(int):
        def __new__(cls, value: int) -> Self:
            if value < 0:
                raise ValueError("Security ID must be a non-negative integer.")
            return super().__new__(cls, value)

        def __init__(self, value: int):
            self.value = value

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            if len(data) != 4:
                raise ValueError("Security ID must be 4 bytes long.")
            return cls(int.from_bytes(data, "little"))

        def to_bytes(self) -> bytes:
            return self.value.to_bytes(4, "little")

        def __str__(self) -> str:
            return f"SecurityId({self.value})"


    @dataclass(frozen=True)
    class QuotaInformationEntry:
        quota_threshold: int
        quota_limit: int
        used_space: int
        sid_length: int
        sid: str

        @classmethod
        def from_bytes(cls, data: bytes) -> list[QuotaInformationEntry]:
            records = []
            offset = 0
            while offset < len(data):
                entry_length = int.from_bytes(data[offset:offset + 4], "little")
                if entry_length == 0:
                    break

                sid_start = offset + 36
                sid_end = sid_start + int.from_bytes(data[offset + 32:offset + 36], "little")
                sid = data[sid_start:sid_end].hex()

                records.append(
                    cls(
                        quota_threshold=int.from_bytes(data[offset + 8 : offset + 16], "little"),
                        quota_limit=int.from_bytes(data[offset + 16 : offset + 24], "little"),
                        used_space=int.from_bytes(data[offset + 24 : offset + 32], "little"),
                        sid_length=int.from_bytes(data[offset + 32 : offset + 36], "little"),
                        sid=sid,
                    )
                )

                offset += entry_length

            return records

    @dataclass(frozen=True)
    class IntegrityInformation:
        checksum_algorithm: int
        flags: int
        reserved: int

        @classmethod
        def from_bytes(cls, data: bytes) -> IntegrityInformation:
            if len(data) < 8:
                return cls(checksum_algorithm=0, flags=0, reserved=0)

            return cls(
                checksum_algorithm=int.from_bytes(data[:2], "little"),
                flags=int.from_bytes(data[2:4], "little"),
                reserved=int.from_bytes(data[4:8], "little")
            )

    @dataclass(frozen=True)
    class ReparsePointFlags:
        is_symlink: bool = False

        @classmethod
        def from_int(cls, flags: int) -> ReparsePointFlags:
            return cls(
                is_symlink=bool(flags & 0x00000001)
            )

    @dataclass(frozen=True)
    class ReparseData:
        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            raise NotImplementedError("This method should be implemented in subclasses")

    @dataclass(frozen=True)
    class MountPointReparseData(ReparseData):
        substitute_name: str
        print_name: str

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            substitute_name_offset = int.from_bytes(data[8:10], "little")
            substitute_name_length = int.from_bytes(data[10:12], "little")
            print_name_offset = int.from_bytes(data[12:14], "little")
            print_name_length = int.from_bytes(data[14:16], "little")

            return cls(
                substitute_name=data[substitute_name_offset:substitute_name_offset + substitute_name_length].decode("utf-16"),
                print_name=data[print_name_offset:print_name_offset + print_name_length].decode("utf-16")
            )

    @dataclass(frozen=True)
    class SymLinkReparseData(MountPointReparseData):
        flags: ReparsePointFlags

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            base = MountPointReparseData.from_bytes(data)
            flags = ReparsePointFlags.from_int(int.from_bytes(data[16:20], "little"))
            return cls(
                substitute_name=base.substitute_name,
                print_name=base.print_name,
                flags=flags
            )

    class HSMFileIdentifier:
        def __init__(self):
            self.identifier: int
        @classmethod
        def from_null(cls) -> Self:
            return cls.__new__(cls)
        @classmethod
        def from_bytes(cls, identifier: bytes) -> Self:
            if not isinstance(identifier, bytes) or len(identifier) != 12:
                raise ValueError("Identifier must be a 12-byte sequence.")
            instance = cls.from_null()
            instance.identifier = int.from_bytes(identifier, byteorder="big")
            return instance

        @classmethod
        def from_int(cls, identifier: int):
            instance = cls.from_null()
            instance.identifier = identifier
            return instance

        def __str__(self):
            if isinstance(self.identifier, bytes):
                return f"0x{self.identifier.hex}"
            if isinstance(self.identifier, int):
                return f"0x{self.identifier:x}"  # Convert int to hex string with '0x' prefix
            return str(self.identifier)

        def perform_device_io_control(self, file_handle: wintypes.HANDLE, ioctl_command: int) -> bool:
            BUFFER_SIZE = len(self.identifier)

            # Create a buffer with self.identifier
            buffer = create_string_buffer(self.identifier)

            bytes_returned = wintypes.DWORD()

            # Call DeviceIoControl
            result = WindowsDataClass.device_io_control(
                file_handle,
                ioctl_command,
                buffer,
                BUFFER_SIZE,
                None,
                0,
                byref(bytes_returned),
                None
            )

            if not result:
                error_code = GetLastError()
                print(f"DeviceIoControl failed with error code {error_code}")
                return False

            return True

    @dataclass(frozen=True)
    class HsmReparseData(ReparseData):
        version: int
        file_identifier: HSMFileIdentifier

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            version = int.from_bytes(data[8:12], "little")
            file_identifier = data[12:24]  # Typical length for file identifier, but depends on HSM system as each will be different
            return cls(version=version, file_identifier=HSMFileIdentifier(file_identifier))

    @dataclass(frozen=True)
    class SisReparseData(ReparseData):
        checksum: int
        file_reference: int

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:
            checksum = int.from_bytes(data[8:12], "little")
            file_reference = int.from_bytes(data[12:20], "little")
            return cls(checksum=checksum, file_reference=file_reference)

    @dataclass(frozen=True)
    class WimReparseData(ReparseData):
        image_name: str
        image_guid: GUID

        @classmethod
        def from_bytes(cls, data: bytes) -> WimReparseData:
            image_name = data[8:40].decode("utf-16").strip("\x00")
            image_guid = data[40:56].hex()  # Assuming GUID is stored as bytes
            return cls(image_name=image_name, image_guid=GUID(image_guid))

    @dataclass(frozen=True)
    class DfsReparseData(ReparseData):
        dfs_path: PureWindowsPath

        @classmethod
        def from_bytes(cls, data: bytes) -> DfsReparseData:
            dfs_path = data[8:].decode("utf-16").strip("\x00")
            return cls(dfs_path=PureWindowsPath(dfs_path))

    @dataclass(frozen=True)
    class AppExecLinkReparseData(ReparseData):
        exec_path: str
        arguments: str

    @dataclass(frozen=True)
    class UnknownReparseData(ReparseData):
        data: bytes
        exc: Exception | None

    @dataclass(frozen=True)
    class NoReparseData(ReparseData):
        def __str__(self):
            return ""
        def __bool__(self):
            return False

    @dataclass(frozen=True)
    class ReparsePointInformation:
        tag: int
        data: ReparseData | None = None

        MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16 * 1024
        IO_REPARSE_TAG_RESERVED_ZERO = 0x00000000
        IO_REPARSE_TAG_RESERVED_ONE = 0x00000001
        IO_REPARSE_TAG_SYMBOLIC_LINK = 0x80000000
        IO_REPARSE_TAG_NSS = 0x80000002
        IO_REPARSE_TAG_FILTER_MANAGER = 0x80000007
        IO_REPARSE_TAG_DFS = 0x8000000A
        IO_REPARSE_TAG_SIS = 0x8000000B
        IO_REPARSE_TAG_HSM = 0xC0000004
        IO_REPARSE_TAG_NSSRECOVER = 0xC0000008
        IO_REPARSE_TAG_RESERVED_MS_RANGE = 0x10000000
        IO_REPARSE_TAG_RESERVED_RANGE = 0x20000000
        IO_COMPLETION_MODIFY_STATE = 0x00000002
        IO_REPARSE_TAG_HSM2 = 0x80000006
        IO_REPARSE_TAG_WIM = 0x80000008
        IO_REPARSE_TAG_DFSR = 0x80000012

        IO_REPARSE_TAG_SYMLINK: int = 0xA000000C
        IO_REPARSE_TAG_MOUNT_POINT: int = 0xA0000003
        IO_REPARSE_TAG_APPEXECLINK: int = 0x8000001B

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath_str = str(WindowsPath(filepath))
            handle = WindowsDataClass.get_file_handle_win32(filepath_str)

            try:
                reparse_point_information = WindowsDataClass.device_io_control(
                    handle, FSCTL.FSCTL_GET_REPARSE_POINT, err_msg=f"Failed to retrieve reparse point information for {filepath}"
                )
                assert not isinstance(reparse_point_information, HRESULT)

            finally:
                windll.kernel32.CloseHandle(handle)

            return cls.from_bytes(WindowsDataClass.array_to_bytes(reparse_point_information))

        @classmethod
        def from_bytes(cls, data: bytes) -> Self:  # noqa: PLR0911
            tag = int.from_bytes(data[:4], "little")

            try:
                if tag == 0:
                    return cls(tag=tag, data=NoReparseData())
                if tag == cls.IO_REPARSE_TAG_SYMLINK:
                    return cls(tag=tag, data=SymLinkReparseData.from_bytes(data))
                if tag == cls.IO_REPARSE_TAG_MOUNT_POINT:
                    return cls(tag=tag, data=MountPointReparseData.from_bytes(data))
                if tag in (cls.IO_REPARSE_TAG_HSM, cls.IO_REPARSE_TAG_HSM2):
                    return cls(tag=tag, data=HsmReparseData.from_bytes(data))
                if tag == cls.IO_REPARSE_TAG_SIS:
                    return cls(tag=tag, data=SisReparseData.from_bytes(data))
                if tag == cls.IO_REPARSE_TAG_WIM:
                    return cls(tag=tag, data=WimReparseData.from_bytes(data))
                if tag in (cls.IO_REPARSE_TAG_DFS, cls.IO_REPARSE_TAG_DFSR):
                    return cls(tag=tag, data=DfsReparseData.from_bytes(data))
                if tag == cls.IO_REPARSE_TAG_APPEXECLINK:
                    return cls(tag=tag, data=AppExecLinkReparseData.from_bytes(data))
            except Exception as e:  # noqa: BLE001
                return cls(tag=tag, data=UnknownReparseData(data=data, exc=e))

            raise ValueError(f"Invalid tag: '{tag}'")


    @dataclass(frozen=True)
    class WindowsFSCTLResult(WindowsDataClass):
        object_id: str | None = None
        reparse_point_information: ReparsePointInformation | None = None
        usn_journal_data: UsnJournalData | ValueError | None = None
        quota_information: list[QuotaInformationEntry] | None = None
        sparse_status: list[tuple[int, int]] | None = None
        encryption_status: bool | None = None
        compression_format: CompressionFormat | None = None
        integrity_status: IntegrityInformation | None = None

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath_str = str(WindowsPath(filepath))
            handle = cls.get_file_handle_win32(filepath_str)

            try:
                object_id = cls.device_io_control(
                    handle, FSCTL.FSCTL_GET_OBJECT_ID, err_msg=f"Failed to retrieve object ID for {filepath_str}",
                )
                #assert not isinstance(object_id, HRESULT)
                #assert object_id, f"could not retrieve object id from device_io_control. (object_id: {object_id}, type: {object_id.__class__.__name__})"

                reparse_point_information = cls.device_io_control(
                    handle, FSCTL.FSCTL_GET_REPARSE_POINT, err_msg=f"Failed to retrieve reparse point information for {filepath}"
                )
                usn_journal_data = cls.device_io_control(
                    handle, FSCTL.FSCTL_READ_FILE_USN_DATA, err_msg=f"Failed to retrieve USN journal information for {filepath}"
                )
                quota_information = cls.device_io_control(
                    handle, FSCTL.FSCTL_GET_QUOTA_INFORMATION, err_msg=f"Failed to retrieve quota information for {filepath}"
                )
                sparse_status = cls.device_io_control(
                    handle, FSCTL.FSCTL_QUERY_ALLOCATED_RANGES, err_msg=f"Failed to retrieve sparsity information for {filepath}"
                )
                encryption_status = cls.device_io_control(
                    handle, FSCTL.FSCTL_GET_ENCRYPTION, err_msg=f"Failed to retrieve encryption information for {filepath}"
                )
                compression_format = cls.device_io_control(
                    handle, FSCTL.FSCTL_GET_COMPRESSION, err_msg=f"Failed to retrieve compression information for {filepath}"
                )
                integrity_status = cls.device_io_control(
                    handle, FSCTL.FSCTL_GET_INTEGRITY_INFORMATION, err_msg=f"Failed to retrieve integrity information for {filepath}"
                )

                assert not isinstance(integrity_status, HRESULT)
                assert not isinstance(compression_format, HRESULT)
                assert not isinstance(encryption_status, HRESULT)
                assert not isinstance(sparse_status, HRESULT)
                assert not isinstance(quota_information, HRESULT)
                assert not isinstance(usn_journal_data, HRESULT)
                assert not isinstance(reparse_point_information, HRESULT)

            finally:
                windll.kernel32.CloseHandle(handle)

            return cls(
                object_id=cls.parse_object_id(cls.array_to_bytes(object_id)),
                reparse_point_information=ReparsePointInformation.from_bytes(cls.array_to_bytes(reparse_point_information)),
                usn_journal_data=UsnJournalData.from_bytes(cls.array_to_bytes(usn_journal_data)),
                quota_information=QuotaInformationEntry.from_bytes(cls.array_to_bytes(quota_information)),
                sparse_status=cls.parse_sparse_ranges(cls.array_to_bytes(sparse_status)),
                encryption_status=cls.parse_encryption_status(cls.array_to_bytes(encryption_status)),
                compression_format=cls.parse_compression_format(cls.array_to_bytes(compression_format)),
                integrity_status=IntegrityInformation.from_bytes(cls.array_to_bytes(integrity_status)),
            )

        @staticmethod
        def parse_sparse_ranges(data: bytes) -> list[tuple[int, int]]:
            ranges = []
            for i in range(0, len(data), 16):
                offset = int.from_bytes(data[i:i + 8], "little")
                length = int.from_bytes(data[i + 8:i + 16], "little")
                ranges.append((offset, length))
            return ranges

        @staticmethod
        def parse_encryption_status(data: bytes) -> bool:
            return bool(data[0]) if data else False

        @staticmethod
        def parse_compression_format(data: bytes) -> CompressionFormat:
            format_value = int.from_bytes(data[:2], "little")
            return CompressionFormat(format_value)

        @staticmethod
        def parse_object_id(data: bytes) -> str | None:
            hex_size = 16
            if len(data) >= hex_size:
                return data[:hex_size].hex()
            return None


    @dataclass(frozen=True)
    class WindowsObjectIDInfo(WindowsDataClass):
        object_id: bytes | None

        @classmethod
        def from_path(cls, filepath: os.PathLike | str) -> Self:
            filepath_str = str(WindowsPath(filepath))
            handle: wintypes.HANDLE = cls.get_file_handle_win32(
                filepath_str,
                flags=FileFlags.FILE_FLAG_BACKUP_SEMANTICS,
                err_msg=f"Failed to open file handle for {filepath_str}"
            )

            buffer: Array[c_char] = create_string_buffer(1024)
            bytes_returned = c_ulong()
            success = cls.device_io_control(
                handle,
                FSCTL.FSCTL_GET_OBJECT_ID,
                None,
                0,
                buffer,
                1024,
                byref(bytes_returned),
                None,
                err_msg=f"Failed to retrieve object ID for {filepath_str}",
            )
            windll.kernel32.CloseHandle(handle)

            return cls(object_id=buffer.raw[: bytes_returned.value])


@dataclass(frozen=True)
class CompleteFileInfo:
    size: int
    creation_time: float
    modification_time: float
    access_time: float
    attributes: int
    permissions: int
    extended_attributes: WindowsExtendedAttributes
    index: WindowsFileIndex
    sparse_regions: WindowsSparseFileRegions
    locks: WindowsFileLocks
    integrity: WindowsFileIntegrity
    version: WindowsFileVersion
    security_info: WindowsFileSecurityInfo
    reparse_point_info: ReparsePointInformation
    object_id_info: WindowsObjectIDInfo
    ads_info: WindowsAlternateDataStreams
    hard_link_info: WindowsHardLinks
    volume_info: WindowsVolumeInformation
    compression_info: WindowsFileCompression
    encryption_info: WindowsFileEncryption
    sparsity_info: WindowsFileSparsity
    quotas_info: WindowsFileQuotas
    usn_journal: UsnJournalData
    resources: WindowsFileResources

    @classmethod
    def from_path(cls, filepath: os.PathLike | str) -> Self:
        filepath = WindowsPath(filepath)
        stat_info = filepath.stat()
        return cls(
            size=stat_info.st_size,
            creation_time=stat_info.st_ctime,
            modification_time=stat_info.st_mtime,
            access_time=stat_info.st_atime,
            attributes=stat_info.st_mode,
            permissions=stat_info.st_mode,
            extended_attributes=WindowsExtendedAttributes.from_path(filepath),
            index=WindowsFileIndex.from_path(filepath),
            sparse_regions=WindowsSparseFileRegions.from_path(filepath),
            locks=WindowsFileLocks.from_path(filepath),
            integrity=WindowsFileIntegrity.from_path(filepath),
            version=WindowsFileVersion.from_path(filepath),
            security_info=WindowsFileSecurityInfo.from_path(filepath),
            reparse_point_info=ReparsePointInformation.from_path(filepath),
            object_id_info=WindowsObjectIDInfo.from_path(filepath),
            ads_info=WindowsAlternateDataStreams.from_path(filepath),
            hard_link_info=WindowsHardLinks.from_path(filepath),
            volume_info=WindowsVolumeInformation.from_path(filepath),
            compression_info=WindowsFileCompression.from_path(filepath),
            encryption_info=WindowsFileEncryption.from_path(filepath),
            sparsity_info=WindowsFileSparsity.from_path(filepath),
            quotas_info=WindowsFileQuotas.from_path(filepath),
            usn_journal=UsnJournalData.from_path(filepath),
            resources=WindowsFileResources.from_path(filepath),
        )


@dataclass(frozen=True)
class CompleteDirInfo:
    size: int
    creation_time: float
    modification_time: float
    access_time: float
    attributes: int
    file_permissions: int
    extended_attributes: WindowsExtendedAttributes
    index: WindowsFileIndex
    locks: WindowsFileLocks
    integrity: WindowsFileIntegrity
    version: WindowsFileVersion
    security_info: WindowsFileSecurityInfo
    reparse_point_info: ReparsePointInformation
    object_id_info: WindowsObjectIDInfo
    volume_info: WindowsVolumeInformation

    @classmethod
    def from_folder(cls, folderpath: os.PathLike | str) -> CompleteDirInfo:
        folderpath = WindowsPath(folderpath)
        stat_info = folderpath.stat()
        return cls(
            size=stat_info.st_size,
            creation_time=stat_info.st_ctime,
            modification_time=stat_info.st_mtime,
            access_time=stat_info.st_atime,
            attributes=stat_info.st_mode,
            file_permissions=stat_info.st_mode,
            extended_attributes=WindowsExtendedAttributes.from_path(folderpath),
            index=WindowsFileIndex.from_path(folderpath),
            locks=WindowsFileLocks.from_path(folderpath),
            integrity=WindowsFileIntegrity.from_path(folderpath),
            version=WindowsFileVersion.from_path(folderpath),
            security_info=WindowsFileSecurityInfo.from_path(folderpath),
            reparse_point_info=ReparsePointInformation.from_path(folderpath),
            object_id_info=WindowsObjectIDInfo.from_path(folderpath),
            volume_info=WindowsVolumeInformation.from_path(folderpath),
        )


class TestWindowsFSCTLResult(unittest.TestCase):

    def setUp(self):
        # Define a common directory accessible by all users
        self.common_dir: WindowsPath = WindowsPath("C:/Users/Public/TestFSCTL")
        self.common_dir.mkdir(parents=True, exist_ok=True)

        self.test_file_path: WindowsPath = self.common_dir / "test_file.txt"
        self.test_folder_path: WindowsPath = self.common_dir / "test_folder"
        self.test_symlink_path: WindowsPath = self.common_dir / "test_symlink"
        self.test_hardlink_path: WindowsPath = self.common_dir / "test_hardlink.txt"

        # Create the test file with initial content
        self.test_file_path.touch()
        with self.test_file_path.open("w") as f:
            f.write("test contents")

        # Create a test folder
        self.test_folder_path.mkdir(exist_ok=True)

        # Create a symlink to the test file
        if not self.test_symlink_path.exists():
            self.test_symlink_path.symlink_to(self.test_file_path)

        # Create a hardlink to the test file (only works on NTFS)
        if not self.test_hardlink_path.exists():
            os.link(self.test_file_path, self.test_hardlink_path)

    @staticmethod
    def schedule_file_for_deletion(file_path: os.PathLike | str):
        """Schedule a file for deletion on reboot."""
        path_str = str(WindowsPath(file_path).resolve())
        MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004
        result = windll.kernel32.MoveFileExW(path_str, None, MOVEFILE_DELAY_UNTIL_REBOOT)
        if not result:
            raise OSError(f"Failed to schedule file for deletion: {GetLastError()}")

    @staticmethod
    def close_open_handles(path: os.PathLike | str):
        """Close any open file handles using psutil."""
        import psutil
        path_str = str(WindowsPath(path).resolve())
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                handle_gen = (h for h in proc.open_files() if path_str.lower().strip() == h.path.lower().strip())
                next(handle_gen)
            except (StopIteration, psutil.AccessDenied):  # noqa: S112, PERF203
                continue
            else:
                while handle_gen:
                    print(f"Found process {proc.pid} holding handle to {path_str}")
                    proc.kill()
                    proc.wait()
                    print(f"Terminated process {proc.pid} holding handle to {path_str}")

    def tearDown(self):
        # List of paths to handle
        paths: list[WindowsPath] = [
            self.test_hardlink_path,
            self.test_symlink_path,
            self.test_file_path,
            self.test_folder_path,
            self.common_dir
        ]

        for path in paths:
            try:
                if path.exists():
                    path.unlink(missing_ok=True)
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
            except OSError:  # noqa: PERF203
                if not path.exists() or path.is_dir():
                    continue
                try:
                    self.schedule_file_for_deletion(path)
                except OSError:
                    self.close_open_handles(path)
            assert not path.exists()

    def test_reparse_point_information(self):
        reparse_info = ReparsePointInformation.from_path(self.test_file_path)
        assert isinstance(reparse_info, ReparsePointInformation)
        assert reparse_info.tag == ReparsePointInformation.IO_REPARSE_TAG_RESERVED_ZERO
        assert not reparse_info.data, f"Expected no reparse data on a standard file, got {reparse_info.data.__class__.__name__} (bool {bool(reparse_info.data)})"

    def test_complete_file_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info, CompleteFileInfo), "Failed to create CompleteFileInfo instance."
        assert file_info.size == os.path.getsize(self.test_file_path), f"Expected size: {os.path.getsize(self.test_file_path)}, got: {file_info.size}"
        assert isinstance(file_info.creation_time, float), f"Expected creation_time to be float, got: {type(file_info.creation_time).__name__}"
        assert isinstance(file_info.modification_time, float), f"Expected modification_time to be float, got: {type(file_info.modification_time).__name__}"
        assert isinstance(file_info.access_time, float), f"Expected access_time to be float, got: {type(file_info.access_time).__name__}"
        assert isinstance(file_info.attributes, int), f"Expected attributes to be int, got: {type(file_info.attributes).__name__}"
        assert isinstance(file_info.permissions, int), f"Expected permissions to be int, got: {type(file_info.permissions).__name__}"
        assert isinstance(file_info.extended_attributes, WindowsExtendedAttributes), "Failed to get WindowsExtendedAttributes."
        assert isinstance(file_info.index, WindowsFileIndex), "Failed to get WindowsFileIndex."
        assert isinstance(file_info.sparse_regions, WindowsSparseFileRegions), "Failed to get WindowsSparseFileRegions."
        assert isinstance(file_info.locks, WindowsFileLocks), "Failed to get WindowsFileLocks."

    def test_complete_dir_info(self):
        dir_info = CompleteDirInfo.from_folder(self.test_folder_path)
        assert isinstance(dir_info, CompleteDirInfo), "Failed to create CompleteDirInfo instance."
        assert dir_info.size == os.path.getsize(self.test_folder_path), f"Expected size: {os.path.getsize(self.test_folder_path)}, got: {dir_info.size}"
        assert isinstance(dir_info.creation_time, float), f"Expected creation_time to be float, got: {type(dir_info.creation_time).__name__}"
        assert isinstance(dir_info.modification_time, float), f"Expected modification_time to be float, got: {type(dir_info.modification_time).__name__}"
        assert isinstance(dir_info.access_time, float), f"Expected access_time to be float, got: {type(dir_info.access_time).__name__}"
        assert isinstance(dir_info.attributes, int), f"Expected attributes to be int, got: {type(dir_info.attributes).__name__}"
        assert isinstance(dir_info.file_permissions, int), f"Expected file_permissions to be int, got: {type(dir_info.file_permissions).__name__}"
        assert isinstance(dir_info.extended_attributes, WindowsExtendedAttributes), "Failed to get WindowsExtendedAttributes."
        assert isinstance(dir_info.index, WindowsFileIndex), "Failed to get WindowsFileIndex."
        assert isinstance(dir_info.locks, WindowsFileLocks), "Failed to get WindowsFileLocks."
        assert isinstance(dir_info.integrity, WindowsFileIntegrity), "Failed to get WindowsFileIntegrity."

    def test_symlink_info(self):
        symlink_info = CompleteFileInfo.from_path(self.test_symlink_path)
        assert isinstance(symlink_info, CompleteFileInfo), "Failed to create CompleteFileInfo for symlink."
        assert symlink_info.reparse_point_info.tag == ReparsePointInformation.IO_REPARSE_TAG_SYMLINK, "Expected symlink reparse tag, got different."
        assert isinstance(symlink_info.size, int), f"Expected size to be int, got: {type(symlink_info.size).__name__}"
        assert symlink_info.size == 0, f"Expected symlink size to be 0, got: {symlink_info.size}"
        assert isinstance(symlink_info.modification_time, float), f"Expected modification_time to be float, got: {type(symlink_info.modification_time).__name__}"
        assert isinstance(symlink_info.attributes, int), f"Expected attributes to be int, got: {type(symlink_info.attributes).__name__}"
        assert isinstance(symlink_info.permissions, int), f"Expected permissions to be int, got: {type(symlink_info.permissions).__name__}"
        assert isinstance(symlink_info.extended_attributes, WindowsExtendedAttributes), "Failed to get WindowsExtendedAttributes."
        assert isinstance(symlink_info.index, WindowsFileIndex), "Failed to get WindowsFileIndex."
        assert isinstance(symlink_info.hard_link_info, WindowsHardLinks), "Failed to get WindowsHardLinks."

    def test_hardlink_info(self):
        hardlink_info = CompleteFileInfo.from_path(self.test_hardlink_path)
        assert isinstance(hardlink_info, CompleteFileInfo), "Failed to create CompleteFileInfo for hardlink."
        assert hardlink_info.index.file_index == os.stat(self.test_hardlink_path).st_ino, "Hardlink file index mismatch."
        assert isinstance(hardlink_info.size, int), f"Expected size to be int, got: {type(hardlink_info.size).__name__}"
        assert hardlink_info.size == os.path.getsize(self.test_hardlink_path), f"Expected size to be {os.path.getsize(self.test_hardlink_path)}, got: {hardlink_info.size}"
        assert isinstance(hardlink_info.creation_time, float), f"Expected creation_time to be float, got: {type(hardlink_info.creation_time).__name__}"
        assert isinstance(hardlink_info.modification_time, float), f"Expected modification_time to be float, got: {type(hardlink_info.modification_time).__name__}"
        assert isinstance(hardlink_info.access_time, float), f"Expected access_time to be float, got: {type(hardlink_info.access_time).__name__}"
        assert isinstance(hardlink_info.attributes, int), f"Expected attributes to be int, got: {type(hardlink_info.attributes).__name__}"
        assert isinstance(hardlink_info.extended_attributes, WindowsExtendedAttributes), "Failed to get WindowsExtendedAttributes."
        assert isinstance(hardlink_info.volume_info, WindowsVolumeInformation), "Failed to get WindowsVolumeInformation."
        assert isinstance(hardlink_info.compression_info, WindowsFileCompression), "Failed to get WindowsFileCompression."

    def test_extended_attributes(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.extended_attributes, WindowsExtendedAttributes), "Failed to retrieve extended attributes."
        assert isinstance(file_info.extended_attributes.extended_attributes, dict), "Extended attributes should be a dictionary."
        assert all(isinstance(key, str) for key in file_info.extended_attributes.extended_attributes), "All keys in extended attributes should be strings."
        assert all(isinstance(value, bytes) for value in file_info.extended_attributes.extended_attributes.values()), "All values in extended attributes should be bytes."
        assert len(file_info.extended_attributes.extended_attributes) >= 0, "Extended attributes dictionary should be initialized."
        if file_info.extended_attributes.extended_attributes:
            assert len(file_info.extended_attributes.extended_attributes) == len(file_info.extended_attributes.extended_attributes), "Extended attributes length mismatch."
            assert isinstance(next(iter(file_info.extended_attributes.extended_attributes)), str), "First key in extended attributes should be a string."
            assert isinstance(next(iter(file_info.extended_attributes.extended_attributes.values())), bytes), "First value in extended attributes should be bytes."

    def test_sparse_regions(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.sparse_regions, WindowsSparseFileRegions), "Failed to retrieve sparse regions."
        assert isinstance(file_info.sparse_regions.regions, list), "Sparse regions should be a list."
        assert all(isinstance(region, tuple) for region in file_info.sparse_regions.regions), "All sparse regions should be tuples."
        assert all(isinstance(region[0], int) for region in file_info.sparse_regions.regions), "Sparse region offsets should be integers."
        assert all(isinstance(region[1], int) for region in file_info.sparse_regions.regions), "Sparse region lengths should be integers."
        assert len(file_info.sparse_regions.regions) >= 0, "Sparse regions list should be initialized."
        if file_info.sparse_regions.regions:
            assert len(file_info.sparse_regions.regions) == len(file_info.sparse_regions.regions), "Sparse regions length mismatch."
            assert file_info.sparse_regions.regions[0][0] >= 0, "Sparse region offset should be non-negative."
            assert file_info.sparse_regions.regions[0][1] >= 0, "Sparse region length should be non-negative."

    def test_file_locks(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.locks, WindowsFileLocks), "Failed to retrieve file locks."
        assert isinstance(file_info.locks.locks, list), "File locks should be a list."
        assert all(isinstance(lock, dict) for lock in file_info.locks.locks), "All file locks should be dictionaries."
        assert all("offset" in lock for lock in file_info.locks.locks), "Each file lock should have an 'offset' key."
        assert all("length" in lock for lock in file_info.locks.locks), "Each file lock should have a 'length' key."
        assert all("process_id" in lock for lock in file_info.locks.locks), "Each file lock should have a 'process_id' key."
        assert all("flags" in lock for lock in file_info.locks.locks), "Each file lock should have a 'flags' key."
        assert len(file_info.locks.locks) >= 0, "File locks list should be initialized."
        if file_info.locks.locks:
            assert file_info.locks.locks[0]["offset"] >= 0, "File lock offset should be non-negative."
            assert file_info.locks.locks[0]["length"] >= 0, "File lock length should be non-negative."
            assert file_info.locks.locks[0]["process_id"] >= 0, "File lock process_id should be non-negative."
            assert file_info.locks.locks[0]["flags"] >= 0, "File lock flags should be non-negative."

    def test_integrity_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.integrity, WindowsFileIntegrity), "Failed to retrieve integrity information."
        assert isinstance(file_info.integrity.integrity_status, bytes), "Integrity status should be bytes."
        assert len(file_info.integrity.integrity_status) >= 0, "Integrity status should have non-negative length."
        if file_info.integrity.integrity_status:
            assert len(file_info.integrity.integrity_status) == len(file_info.integrity.integrity_status), "Integrity status length mismatch."
            assert file_info.integrity.integrity_status[:2] != b"", "Integrity status should not be empty."
            assert isinstance(file_info.integrity.integrity_status[:2], bytes), "Integrity status prefix should be bytes."

    def test_version_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.version, WindowsFileVersion), "Failed to retrieve file version."
        assert isinstance(file_info.version.file_version, (str, type(None))), "File version should be a string or None."
        assert isinstance(file_info.version.product_name, (str, type(None))), "Product name should be a string or None."
        assert isinstance(file_info.version.product_version, (str, type(None))), "Product version should be a string or None."
        assert isinstance(file_info.version.company_name, (str, type(None))), "Company name should be a string or None."
        assert isinstance(file_info.version.file_description, (str, type(None))), "File description should be a string or None."
        if file_info.version.file_version:
            assert len(file_info.version.file_version) > 0, "File version should not be empty."
        if file_info.version.product_name:
            assert len(file_info.version.product_name) > 0, "Product name should not be empty."
        if file_info.version.product_version:
            assert len(file_info.version.product_version) > 0, "Product version should not be empty."
        if file_info.version.company_name:
            assert len(file_info.version.company_name) > 0, "Company name should not be empty."
        if file_info.version.file_description:
            assert len(file_info.version.file_description) > 0, "File description should not be empty."

    def test_security_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.security_info, WindowsFileSecurityInfo), "Failed to retrieve security information."
        assert isinstance(file_info.security_info.owner, str), "Owner should be a string."
        assert isinstance(file_info.security_info.dacl, list), "DACL should be a list."
        assert len(file_info.security_info.dacl) >= 0, "DACL list should be initialized."
        if file_info.security_info.dacl:
            assert len(file_info.security_info.dacl) == len(file_info.security_info.dacl), "DACL length mismatch."
            assert isinstance(file_info.security_info.dacl[0], str), "First DACL entry should be a string."

    def test_reparse_point_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.reparse_point_info, ReparsePointInformation), "Failed to retrieve reparse point information."
        assert isinstance(file_info.reparse_point_info.tag, int), "Reparse point tag should be an integer."
        assert isinstance(file_info.reparse_point_info.data, (ReparseData, type(None))), "Reparse point data should be ReparseData or None."
        assert file_info.reparse_point_info.tag == ReparsePointInformation.IO_REPARSE_TAG_RESERVED_ZERO, "Expected reparse point tag to be zero."
        if file_info.reparse_point_info.data:
            assert isinstance(file_info.reparse_point_info.data, ReparseData), "Reparse point data should be ReparseData if not None."
        else:
            assert file_info.reparse_point_info.data is None, "Reparse point data should be None."

    def test_object_id_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.object_id_info, WindowsObjectIDInfo), "Failed to retrieve object ID information."
        assert isinstance(file_info.object_id_info.object_id, (bytes, type(None))), "Object ID should be bytes or None."
        if file_info.object_id_info.object_id:
            assert len(file_info.object_id_info.object_id) > 0, "Object ID should not be empty."
            assert isinstance(file_info.object_id_info.object_id, bytes), "Object ID should be bytes."

    def test_alternate_data_streams(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.ads_info, WindowsAlternateDataStreams), "Failed to retrieve alternate data streams."
        assert isinstance(file_info.ads_info.alternate_data_streams, list), "Alternate data streams should be a list."
        assert len(file_info.ads_info.alternate_data_streams) >= 0, "Alternate data streams list should be initialized."
        if file_info.ads_info.alternate_data_streams:
            assert isinstance(file_info.ads_info.alternate_data_streams[0], str), "First alternate data stream should be a string."

    def test_volume_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.volume_info, WindowsVolumeInformation), "Failed to retrieve volume information."
        assert isinstance(file_info.volume_info.volume_serial_number, int), "Volume serial number should be an integer."
        assert isinstance(file_info.volume_info.file_system_type, str), "File system type should be a string."
        assert isinstance(file_info.volume_info.maximum_component_length, int), "Maximum component length should be an integer."
        assert isinstance(file_info.volume_info.file_system_flags, int), "File system flags should be an integer."
        assert file_info.volume_info.volume_serial_number > 0, "Volume serial number should be positive."
        assert len(file_info.volume_info.file_system_type) > 0, "File system type should not be empty."
        assert file_info.volume_info.maximum_component_length > 0, "Maximum component length should be positive."
        assert file_info.volume_info.file_system_flags > 0, "File system flags should be positive."

    def test_compression_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.compression_info, WindowsFileCompression), "Failed to retrieve compression information."
        assert isinstance(file_info.compression_info.compression_format, bytes), "Compression format should be bytes."
        assert len(file_info.compression_info.compression_format) > 0, "Compression format should not be empty."

    def test_encryption_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.encryption_info, WindowsFileEncryption), "Failed to retrieve encryption information."
        assert isinstance(file_info.encryption_info.encryption_status, bytes), "Encryption status should be bytes."
        assert len(file_info.encryption_info.encryption_status) > 0, "Encryption status should not be empty."

    def test_sparsity_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.sparsity_info, WindowsFileSparsity), "Failed to retrieve sparsity information."
        assert isinstance(file_info.sparsity_info.sparse_status, bytes), "Sparsity status should be bytes."
        assert len(file_info.sparsity_info.sparse_status) > 0, "Sparsity status should not be empty."

    def test_quota_info(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.quotas_info, WindowsFileQuotas), "Failed to retrieve quota information."
        assert isinstance(file_info.quotas_info.quota_information, bytes), "Quota information should be bytes."
        assert len(file_info.quotas_info.quota_information) > 0, "Quota information should not be empty."

    def test_usn_journal(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.usn_journal, WindowsUsnJournal), "Failed to retrieve USN journal."
        assert isinstance(file_info.usn_journal.usn_journal_data, bytes), "USN journal data should be bytes."
        assert len(file_info.usn_journal.usn_journal_data) > 0, "USN journal data should not be empty."

    def test_resources(self):
        file_info = CompleteFileInfo.from_path(self.test_file_path)
        assert isinstance(file_info.resources, WindowsFileResources), "Failed to retrieve file resources."
        assert isinstance(file_info.resources.resources, list), "Resources should be a list."
        assert len(file_info.resources.resources) >= 0, "Resources list should be initialized."
        if file_info.resources.resources:
            assert isinstance(file_info.resources.resources[0], dict), "First resource should be a dictionary."
            assert "type" in file_info.resources.resources[0], "Resource should have a 'type' key."
            assert "name" in file_info.resources.resources[0], "Resource should have a 'name' key."
            assert "data" in file_info.resources.resources[0], "Resource should have a 'data' key."
            assert isinstance(file_info.resources.resources[0]["type"], int), "Resource 'type' should be an integer."
            assert isinstance(file_info.resources.resources[0]["name"], str), "Resource 'name' should be a string."
            assert isinstance(file_info.resources.resources[0]["data"], bytes), "Resource 'data' should be bytes."


    def test_windows_fsctl_result(self):
        # Test the complete WindowsFSCTLResult creation
        fsctl_result = WindowsFSCTLResult.from_path(self.test_file_path)

        # Assert that the result is an instance of WindowsFSCTLResult
        assert isinstance(fsctl_result, WindowsFSCTLResult)

        # Assert expected default results for a freshly created file
        assert fsctl_result.object_id is None, f"Expected no object ID on a standard file, got '{fsctl_result.object_id}' of type '{fsctl_result.object_id.__class__.__name__}'"
        assert isinstance(fsctl_result.reparse_point_information, ReparsePointInformation), (
            f"Assertion failed: isinstance(fsctl_result.reparse_point_information, ReparsePointInformation)\n"
            f"repr: {fsctl_result.reparse_point_information!r}\n"
            f"str: {fsctl_result.reparse_point_information!s}\n"
            f"class: {fsctl_result.reparse_point_information.__class__.__name__}"
        )

        assert isinstance(fsctl_result.reparse_point_information.data, NoReparseData), (
            "Expected no reparse data on a standard file\n"
            f"Assertion failed: isinstance(fsctl_result.reparse_point_information.data, (type(None), NoReparseData))\n"
            f"repr: {fsctl_result.reparse_point_information.data!r}\n"
            f"str: {fsctl_result.reparse_point_information.data!s}\n"
            f"class: {fsctl_result.reparse_point_information.data.__class__.__name__}"
        )

        assert isinstance(fsctl_result.usn_journal_data, Exception), (
            f"Assertion failed: isinstance(fsctl_result.usn_journal_data, UsnJournalData)\n"
            f"repr: {fsctl_result.usn_journal_data!r}\n"
            f"str: {fsctl_result.usn_journal_data!s}\n"
            f"class: {fsctl_result.usn_journal_data.__class__.__name__}"
        )

        assert isinstance(fsctl_result.quota_information, list), (
            f"Assertion failed: isinstance(fsctl_result.quota_information, list)\n"
            f"repr: {fsctl_result.quota_information!r}\n"
            f"str: {fsctl_result.quota_information!s}\n"
            f"class: {fsctl_result.quota_information.__class__.__name__}"
        )

        assert isinstance(fsctl_result.sparse_status, list), (
            f"Assertion failed: isinstance(fsctl_result.sparse_status, list)\n"
            f"repr: {fsctl_result.sparse_status!r}\n"
            f"str: {fsctl_result.sparse_status!s}\n"
            f"class: {fsctl_result.sparse_status.__class__.__name__}"
        )

        assert isinstance(fsctl_result.encryption_status, bool), (
            f"Assertion failed: isinstance(fsctl_result.encryption_status, bool)\n"
            f"repr: {fsctl_result.encryption_status!r}\n"
            f"str: {fsctl_result.encryption_status!s}\n"
            f"class: {fsctl_result.encryption_status.__class__.__name__}"
        )

        assert isinstance(fsctl_result.compression_format, CompressionFormat), (
            f"Assertion failed: isinstance(fsctl_result.compression_format, CompressionFormat)\n"
            f"repr: {fsctl_result.compression_format!r}\n"
            f"str: {fsctl_result.compression_format!s}\n"
            f"class: {fsctl_result.compression_format.__class__.__name__}"
        )

        assert isinstance(fsctl_result.integrity_status, IntegrityInformation), (
            f"Assertion failed: isinstance(fsctl_result.integrity_status, IntegrityInformation)\n"
            f"repr: {fsctl_result.integrity_status!r}\n"
            f"str: {fsctl_result.integrity_status!s}\n"
            f"class: {fsctl_result.integrity_status.__class__.__name__}"
        )

        # Further checks can be added based on the environment setup or expected specific values

if __name__ == "__main__":
    # Ensure the test is run only when the script is executed directly
    unittest.main()
