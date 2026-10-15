"""Native Windows private-directory ACLs, using only ctypes.

Only the current user, SYSTEM and local administrators may have allow entries.
Existing ACLs are inspected, never repaired. New directories receive a protected
inheritable DACL at creation. Unsupported ACL forms/filesystems fail closed.
"""
import ctypes
from ctypes import wintypes
from functools import lru_cache
import re

PVOID = ctypes.c_void_p
PPVOID = ctypes.POINTER(PVOID)


@lru_cache(maxsize=1)
def api():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    signatures = [
        (kernel, 'GetCurrentProcess', [], wintypes.HANDLE),
        (kernel, 'CloseHandle', [wintypes.HANDLE], wintypes.BOOL),
        (kernel, 'LocalFree', [PVOID], PVOID),
        (kernel, 'CreateDirectoryW', [wintypes.LPCWSTR, PVOID], wintypes.BOOL),
        (advapi, 'OpenProcessToken', [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)], wintypes.BOOL),
        (advapi, 'GetTokenInformation', [wintypes.HANDLE, ctypes.c_int, PVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        (advapi, 'ConvertSidToStringSidW', [PVOID, PPVOID], wintypes.BOOL),
        (advapi, 'ConvertStringSecurityDescriptorToSecurityDescriptorW', [wintypes.LPCWSTR, wintypes.DWORD, PPVOID, PVOID], wintypes.BOOL),
        (advapi, 'GetNamedSecurityInfoW', [wintypes.LPCWSTR, ctypes.c_int, wintypes.DWORD, PPVOID, PPVOID, PPVOID, PPVOID, PPVOID], wintypes.DWORD),
        (advapi, 'GetSecurityInfo', [wintypes.HANDLE, ctypes.c_int, wintypes.DWORD, PPVOID, PPVOID, PPVOID, PPVOID, PPVOID], wintypes.DWORD),
        (advapi, 'ConvertSecurityDescriptorToStringSecurityDescriptorW', [PVOID, wintypes.DWORD, wintypes.DWORD, PPVOID, PVOID], wintypes.BOOL),
    ]
    for library, name, arguments, result in signatures:
        function = getattr(library, name)
        function.argtypes, function.restype = arguments, result
    return kernel, advapi


def require(value):
    if not value:
        raise OSError('Windows security operation failed')


@lru_cache(maxsize=1)
def current_sid():
    kernel, advapi = api()
    token = wintypes.HANDLE()
    require(advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)))
    try:
        length = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(length))
        if not 0 < length.value <= 65536:
            raise OSError('Windows user identity unavailable')
        buffer = ctypes.create_string_buffer(length.value)
        require(advapi.GetTokenInformation(token, 1, buffer, length, ctypes.byref(length)))
        sid = ctypes.cast(buffer, ctypes.POINTER(PVOID))[0]
        text = PVOID()
        require(advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)))
        try:
            return ctypes.wstring_at(text)
        finally:
            kernel.LocalFree(text)
    finally:
        kernel.CloseHandle(token)


def private_sddl(value, sid):
    """Conservative SDDL policy, separate from WinAPI for regression coverage."""
    owner = re.search(r'(?:^|(?<=\)))O:([^:()]+?)(?=[GDS]:|$)', value)
    # SDDL owner normally precedes G:/D:; no ACE is allowed in the owner field.
    if not owner or owner.group(1) != sid:
        return False
    dacl = re.search(r'D:([^:]*)(?=S:|$)', value)
    if not dacl or 'NO_ACCESS_CONTROL' in dacl.group(1):
        return False
    entries = re.findall(r'\(([^()]*)\)', dacl.group(1))
    if not entries:
        return False
    allowed = {sid, 'SY', 'BA', 'S-1-5-18', 'S-1-5-32-544'}
    for entry in entries:
        fields = entry.split(';')
        if len(fields) != 6 or fields[0] not in {'A', 'D'} or fields[3] or fields[4]:
            return False
        if fields[0] == 'A' and fields[5] not in allowed:
            return False
    return True


def validate_private(path=None, handle=None):
    kernel, advapi = api()
    descriptor, text = PVOID(), PVOID()
    if handle is None:
        code = advapi.GetNamedSecurityInfoW(str(path), 1, 5, None, None, None, None, ctypes.byref(descriptor))
    else:
        code = advapi.GetSecurityInfo(handle, 1, 5, None, None, None, None, ctypes.byref(descriptor))
    if code:
        raise OSError('Windows file security unavailable')
    try:
        require(advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW(descriptor, 1, 5, ctypes.byref(text), None))
        if not private_sddl(ctypes.wstring_at(text), current_sid()):
            raise ValueError('State ACL must restrict access to this user, SYSTEM and administrators')
    finally:
        if text:
            kernel.LocalFree(text)
        kernel.LocalFree(descriptor)


def create_private_directory(path):
    kernel, advapi = api()
    descriptor = PVOID()
    sid = current_sid()
    value = f'O:{sid}D:P(A;OICI;FA;;;{sid})(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)'
    require(advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(value, 1, ctypes.byref(descriptor), None))
    class SecurityAttributes(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('descriptor', PVOID), ('inherit', wintypes.BOOL)]
    attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
    try:
        if not kernel.CreateDirectoryW(str(path), ctypes.byref(attributes)):
            if ctypes.get_last_error() != 183:  # An existing directory is validated by the caller.
                raise OSError('Private state directory could not be created')
    finally:
        kernel.LocalFree(descriptor)
