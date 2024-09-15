from __future__ import annotations

import ctypes
import ctypes.wintypes

from enum import IntEnum, IntFlag
from typing import Sequence


class JOBOBJECTINFOCLASS(IntEnum):
    """https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-jobobject_limit_information_class."""

    JobObjectBasicAccountingInformation = 1
    JobObjectBasicLimitInformation = 2
    JobObjectBasicProcessIdList = 3
    JobObjectBasicUIRestrictions = 4
    JobObjectSecurityLimitInformation = 5
    JobObjectEndOfJobTimeInformation = 6
    JobObjectAssociateCompletionPortInformation = 7
    JobObjectBasicAndIoAccountingInformation = 8
    JobObjectExtendedLimitInformation = 9
    JobObjectJobSetInformation = 10
    JobObjectGroupInformation = 11
    JobObjectNotificationLimitInformation = 12
    JobObjectLimitViolationInformation = 13
    JobObjectGroupInformationEx = 14
    JobObjectCpuRateControlInformation = 15
    JobObjectCompletionFilter = 16
    JobObjectCompletionCounter = 17
    JobObjectReserved1Information = 18
    JobObjectReserved2Information = 19
    JobObjectReserved3Information = 20
    JobObjectReserved4Information = 21
    JobObjectReserved5Information = 22
    JobObjectReserved6Information = 23
    JobObjectReserved7Information = 24
    JobObjectReserved8Information = 25
    MaxJobObjectInfoClass = 26


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[ctypes._CData]] | tuple[str, type[ctypes._CData], int]] = [
        ("PerProcessUserTimeLimit", ctypes.wintypes.LARGE_INTEGER),
        ("PerJobUserTimeLimit", ctypes.wintypes.LARGE_INTEGER),
        ("LimitFlags", ctypes.wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.wintypes.DWORD),
        ("Affinity", ctypes.POINTER(ctypes.c_ulonglong)),
        ("PriorityClass", ctypes.wintypes.DWORD),
        ("SchedulingClass", ctypes.wintypes.DWORD),
    ]
    PerProcessUserTimeLimit: ctypes.wintypes.LARGE_INTEGER  # The time limit for the user time of a process in the job.
    PerJobUserTimeLimit: ctypes.wintypes.LARGE_INTEGER  # The time limit for the user time of the job.
    LimitFlags: ctypes.wintypes.DWORD  # The limit flags for the job object.
    MinimumWorkingSetSize: ctypes.wintypes.LPVOID  # The minimum working set size for the job object.
    MaximumWorkingSetSize: ctypes.wintypes.LPVOID  # The maximum working set size for the job object.
    ActiveProcessLimit: ctypes.wintypes.DWORD  # The maximum number of processes that can be active in the job object.
    Affinity: ctypes._Pointer[ctypes.wintypes.LPVOID]  # The affinity mask for the job object.
    PriorityClass: ctypes.wintypes.DWORD  # The priority class for the job object.
    SchedulingClass: ctypes.wintypes.DWORD  # The scheduling class for the job object.


class IO_COUNTERS(ctypes.Structure):  # noqa: N801
    """https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_io_counters."""

    _fields_: Sequence[tuple[str, type[ctypes._CData]] | tuple[str, type[ctypes._CData], int]] = [
        ("ReadOperationCount", ctypes.wintypes.ULARGE_INTEGER),
        ("WriteOperationCount", ctypes.wintypes.ULARGE_INTEGER),
        ("OtherOperationCount", ctypes.wintypes.ULARGE_INTEGER),
        ("ReadTransferCount", ctypes.wintypes.ULARGE_INTEGER),
        ("WriteTransferCount", ctypes.wintypes.ULARGE_INTEGER),
        ("OtherTransferCount", ctypes.wintypes.ULARGE_INTEGER),
    ]
    ReadOperationCount: ctypes.wintypes.ULARGE_INTEGER  # The number of read operations performed by the job object.
    WriteOperationCount: ctypes.wintypes.ULARGE_INTEGER  # The number of write operations performed by the job object.
    OtherOperationCount: ctypes.wintypes.ULARGE_INTEGER  # The number of other operations performed by the job object.
    ReadTransferCount: ctypes.wintypes.ULARGE_INTEGER  # The number of bytes read from the job object.
    WriteTransferCount: ctypes.wintypes.ULARGE_INTEGER  # The number of bytes written to the job object.
    OtherTransferCount: ctypes.wintypes.ULARGE_INTEGER  # The number of bytes transferred to the job object.


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
    """https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information."""

    _fields_: Sequence[tuple[str, type[ctypes._CData]] | tuple[str, type[ctypes._CData], int]] = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]
    BasicLimitInformation: JOBOBJECT_BASIC_LIMIT_INFORMATION  # The basic limit information for the job object.
    IoInfo: IO_COUNTERS  # The I/O counters for the job object.
    ProcessMemoryLimit: ctypes.wintypes.LPVOID  # The memory limit for the job object.
    JobMemoryLimit: ctypes.wintypes.LPVOID  # The memory limit for the job object.
    PeakProcessMemoryUsed: ctypes.wintypes.LPVOID  # The peak memory used by the job object.
    PeakJobMemoryUsed: ctypes.wintypes.LPVOID  # The peak memory used by the job object.


class JOBOBJECT_BASIC_PROCESS_ID_LIST(ctypes.Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[ctypes._CData]] | tuple[str, type[ctypes._CData], int]] = [
        ("NumberOfAssignedProcesses", ctypes.wintypes.DWORD),
        ("NumberOfProcessIdsInList", ctypes.wintypes.DWORD),
        ("ProcessIdList", ctypes.POINTER(ctypes.wintypes.DWORD)),
    ]
    NumberOfAssignedProcesses: ctypes.wintypes.DWORD  # The number of processes assigned to the job object.
    NumberOfProcessIdsInList: ctypes.wintypes.DWORD  # The number of process IDs in the list.
    ProcessIdList: ctypes._Pointer[ctypes.wintypes.DWORD]  # The list of process IDs assigned to the job object.


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[ctypes._CData]] | tuple[str, type[ctypes._CData], int]] = [
        ("TotalUserTime", ctypes.wintypes.LARGE_INTEGER),
        ("TotalKernelTime", ctypes.wintypes.LARGE_INTEGER),
        ("ThisPeriodTotalUserTime", ctypes.wintypes.LARGE_INTEGER),
        ("ThisPeriodTotalKernelTime", ctypes.wintypes.LARGE_INTEGER),
        ("TotalPageFaultCount", ctypes.wintypes.DWORD),
        ("TotalProcesses", ctypes.wintypes.DWORD),
        ("ActiveProcesses", ctypes.wintypes.DWORD),
        ("TotalTerminatedProcesses", ctypes.wintypes.DWORD),
    ]
    TotalUserTime: ctypes.wintypes.LARGE_INTEGER  # The total user time for the job object.
    TotalKernelTime: ctypes.wintypes.LARGE_INTEGER  # The total kernel time for the job object.
    ThisPeriodTotalUserTime: ctypes.wintypes.LARGE_INTEGER  # The total user time for the current period for the job object.
    ThisPeriodTotalKernelTime: ctypes.wintypes.LARGE_INTEGER  # The total kernel time for the current period for the job object.
    TotalPageFaultCount: ctypes.wintypes.DWORD  # The total number of page faults for the job object.
    TotalProcesses: ctypes.wintypes.DWORD  # The total number of processes for the job object.
    ActiveProcesses: ctypes.wintypes.DWORD  # The number of active processes for the job object.
    TotalTerminatedProcesses: ctypes.wintypes.DWORD  # The total number of terminated processes for the job object.


class JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION(ctypes.Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[ctypes._CData]] | tuple[str, type[ctypes._CData], int]] = [
        ("BasicInfo", JOBOBJECT_BASIC_ACCOUNTING_INFORMATION),
        ("IoInfo", IO_COUNTERS),
    ]
    BasicInfo: JOBOBJECT_BASIC_ACCOUNTING_INFORMATION  # The basic accounting information for the job object.
    IoInfo: IO_COUNTERS  # The I/O counters for the job object.


class JOBOBJECTLIMIT(IntFlag):
    """https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-jobobject_limit_information_class."""

    JOB_OBJECT_LIMIT_WORKINGSET = 0x00000001
    JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
    JOB_OBJECT_LIMIT_JOB_TIME = 0x00000004
    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
    JOB_OBJECT_LIMIT_AFFINITY = 0x00000010
    JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
    JOB_OBJECT_LIMIT_PRESERVE_JOB_TIME = 0x00000040
    JOB_OBJECT_LIMIT_SCHEDULING_CLASS = 0x00000080
    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
    JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
    JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
    JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
    JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JOB_OBJECT_LIMIT_SUBSET_AFFINITY = 0x00004000
    JOB_OBJECT_LIMIT_JOB_MEMORY_LOW = 0x00008000
    JOB_OBJECT_LIMIT_JOB_READ_BYTES = 0x00010000
    JOB_OBJECT_LIMIT_JOB_WRITE_BYTES = 0x00020000
    JOB_OBJECT_LIMIT_RATE_CONTROL = 0x00040000
    JOB_OBJECT_LIMIT_CPU_RATE_CONTROL = 0x00080000
    JOB_OBJECT_LIMIT_IO_RATE_CONTROL = 0x00100000
    JOB_OBJECT_LIMIT_NET_RATE_CONTROL = 0x00200000


def get_job_limits(job: int) -> IO_COUNTERS:
    """Retrieves the I/O counters for the specified job object.

    Further reading:
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-ntclose
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocess
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess

    Args:
        job (int): The handle to the job object.

    Returns:
        IO_COUNTERS: The I/O counters for the job object.
    """
    counters = IO_COUNTERS()
    info = JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION()
    ret_length = ctypes.wintypes.DWORD()

    if not ctypes.windll.kernel32.QueryInformationJobObject(
        job,
        JOBOBJECTINFOCLASS.JobObjectBasicAndIoAccountingInformation,
        ctypes.byref(info),
        ctypes.sizeof(info),
        ctypes.byref(ret_length),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    counters = info.IoInfo
    return counters


def close_handle(handle: int) -> None:
    """Closes the specified handle.

    Further reading:
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-ntclose
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocess
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess


    Args:
        handle (int): The handle to close.
    """
    try:
        if not ctypes.windll.kernel32.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())  # noqa: TRY301
    except Exception as e:  # noqa: BLE001
        from loggerplus import RobustLogger

        RobustLogger().warning(f"Failed to close handle {handle} using CloseHandle: {e}")

        try:
            ctypes.windll.kernel32.DuplicateHandle(
                ctypes.windll.kernel32.GetCurrentProcess(),  # source process
                handle,  # source handle
                None,  # new process
                0,  # new handle
                False,  # not inheritable  # noqa: FBT003
                2,  # DUPLICATE_CLOSE_SOURCE
            )
        except Exception as e:  # noqa: BLE001
            RobustLogger().warning(f"Failed to close handle {handle} using DuplicateHandle: {e}")

            try:
                # Use NtClose from ntdll.dll as a last resort
                ntdll = ctypes.WinDLL("ntdll.dll")
                ntdll.NtClose.argtypes = [ctypes.wintypes.HANDLE]
                ntdll.NtClose.restype = ctypes.wintypes.LONG
                status = ntdll.NtClose(handle)
                if status < 0:
                    raise ctypes.WinError(ctypes.get_last_error())  # noqa: TRY301
            except Exception as e:
                RobustLogger().error(f"Failed to close handle {handle} using all methods: {e}")
                raise


def create_job_object(
    limit_flags: JOBOBJECTLIMIT | None = JOBOBJECTLIMIT.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    extended_limit_information: JOBOBJECT_EXTENDED_LIMIT_INFORMATION | None = None,
) -> int:
    """Creates a job object with the specified limit flags and extended limit information.


    Relevant windows documentation:
    - https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
    - https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
    - https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_io_counters
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-createjobobjecta
    Further reading:
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-getinformationjobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle
    - https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle

    Args:
        limit_flags (JOBOBJECTLIMIT): The limit flags for the job object.
        extended_limit_information (int): The extended limit information for the job object.

    Returns:
        int: The handle to the job object.
    """
    job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())

    if extended_limit_information is None:
        extended_limit_information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    limit_flags_value = limit_flags.value if limit_flags is not None else JOBOBJECTLIMIT.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    extended_limit_information.BasicLimitInformation.LimitFlags = ctypes.c_ulong(limit_flags_value)
    if not ctypes.windll.kernel32.SetInformationJobObject(
        job,
        JOBOBJECTINFOCLASS.JobObjectExtendedLimitInformation,
        ctypes.byref(extended_limit_information),
        ctypes.sizeof(extended_limit_information),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return job


def assign_process_to_job_object(job: ctypes.c_int | int, process: ctypes.c_int | int) -> None:
    """Assigns a process to a job object.

    Documentation:
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
    - https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
    - https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_io_counters
    Further reading:
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-assignprocesstojobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-createjobobjecta
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocess
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa
    - https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess

    Args:
        job (int): The handle to the job object.
        process (int): The handle to the process.
    """
    if not ctypes.windll.kernel32.AssignProcessToJobObject(job, process):
        raise ctypes.WinError(ctypes.get_last_error())  # noqa: TRY301


def set_information_job_object(job: ctypes.c_int | int, info_class: JOBOBJECTINFOCLASS, data: ctypes.Structure) -> None:
    """Sets information for the specified job object.

    Documentation:
    - https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject

    Args:
        job (int): The handle to the job object.
        information (int): The information to set.
        data (bytes): The data to set.
    """
    if not ctypes.windll.kernel32.SetInformationJobObject(
        job,
        info_class,
        ctypes.byref(data),
        ctypes.sizeof(data),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    # Add support for additional information classes
    if info_class == JOBOBJECTINFOCLASS.JobObjectExtendedLimitInformation:
        extended_limit_information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        extended_limit_information.BasicLimitInformation = JOBOBJECT_BASIC_LIMIT_INFORMATION()
        extended_limit_information.BasicLimitInformation.LimitFlags = data.LimitFlags
        extended_limit_information.BasicLimitInformation.MinimumWorkingSetSize = data.MinimumWorkingSetSize
        extended_limit_information.BasicLimitInformation.MaximumWorkingSetSize = data.MaximumWorkingSetSize
        extended_limit_information.BasicLimitInformation.ActiveProcessLimit = data.ActiveProcessLimit
        extended_limit_information.BasicLimitInformation.Affinity = data.Affinity
        extended_limit_information.BasicLimitInformation.PriorityClass = data.PriorityClass
        extended_limit_information.BasicLimitInformation.SchedulingClass = data.SchedulingClass
        if not ctypes.windll.kernel32.SetInformationJobObject(
            job,
            JOBOBJECTINFOCLASS.JobObjectExtendedLimitInformation,
            ctypes.byref(extended_limit_information),
            ctypes.sizeof(extended_limit_information),
        ):
            raise ctypes.WinError(ctypes.get_last_error())


def get_information_job_object(job: ctypes.c_int | int, info_class: JOBOBJECTINFOCLASS, data: ctypes.Structure) -> None:
    ERROR_INSUFFICIENT_BUFFER = 122
    ret_length = ctypes.wintypes.DWORD()
    if not ctypes.windll.kernel32.QueryInformationJobObject(
        job,
        info_class,
        ctypes.byref(data),
        ctypes.sizeof(data),
        ctypes.byref(ret_length),
    ):
        if ctypes.get_last_error() == ERROR_INSUFFICIENT_BUFFER:
            new_data = ctypes.create_string_buffer(ret_length.value)
            if not ctypes.windll.kernel32.QueryInformationJobObject(
                job,
                info_class,
                new_data,
                ret_length.value,
                ctypes.byref(ret_length),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            ctypes.memmove(ctypes.addressof(data), new_data, ret_length.value)
        else:
            raise ctypes.WinError(ctypes.get_last_error())
