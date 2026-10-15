"""Native Windows private-directory ACLs, using only ctypes.

Only the current user, SYSTEM and local administrators may have allow entries.
Existing ACLs are inspected, never repaired. New directories receive a protected
inheritable DACL at creation. Unsupported ACL forms/filesystems fail closed.
"""
import ctypes
from ctypes import wintypes
from functools import lru_cache

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
        (advapi, 'GetSecurityDescriptorOwner', [PVOID, PPVOID, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
        (advapi, 'GetSecurityDescriptorDacl', [PVOID, ctypes.POINTER(wintypes.BOOL), PPVOID, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
        (advapi, 'GetAce', [PVOID, wintypes.DWORD, PPVOID], wintypes.BOOL),
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


def private_acl(owner, entries, sid):
    """Compare canonical SIDs, avoiding SDDL aliases and string parsing."""
    allowed = {sid, 'S-1-5-18', 'S-1-5-32-544'}
    return (owner == sid and bool(entries)
            and all(kind in (0, 1) and (kind == 1 or trustee in allowed)
                    for kind, trustee in entries))


def sid_text(pointer):
    kernel, advapi = api()
    text = PVOID()
    require(advapi.ConvertSidToStringSidW(pointer, ctypes.byref(text)))
    try:
        return ctypes.wstring_at(text)
    finally:
        kernel.LocalFree(text)


def validate_private(path=None, handle=None):
    kernel, advapi = api()
    descriptor = PVOID()
    if handle is None:
        code = advapi.GetNamedSecurityInfoW(str(path), 1, 5, None, None, None, None, ctypes.byref(descriptor))
    else:
        code = advapi.GetSecurityInfo(handle, 1, 5, None, None, None, None, ctypes.byref(descriptor))
    if code:
        raise OSError('Windows file security unavailable')
    try:
        owner, dacl = PVOID(), PVOID()
        defaulted, present = wintypes.BOOL(), wintypes.BOOL()
        require(advapi.GetSecurityDescriptorOwner(descriptor, ctypes.byref(owner), ctypes.byref(defaulted)))
        require(advapi.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)))
        if not present.value or not dacl:
            raise ValueError('Missing or unrestricted Windows DACL')
        class AclHeader(ctypes.Structure):
            _fields_ = [('revision', wintypes.BYTE), ('reserved', wintypes.BYTE),
                        ('size', wintypes.WORD), ('count', wintypes.WORD), ('reserved2', wintypes.WORD)]
        header = ctypes.cast(dacl, ctypes.POINTER(AclHeader)).contents
        if not 0 < header.count <= 64:
            raise ValueError('Unsupported Windows DACL')
        entries = []
        for index in range(header.count):
            ace = PVOID()
            require(advapi.GetAce(dacl, index, ctypes.byref(ace)))
            kind = ctypes.cast(ace, ctypes.POINTER(wintypes.BYTE))[0]
            if kind not in (0, 1):
                raise ValueError('Unsupported Windows ACE')
            # ACCESS_ALLOWED_ACE / ACCESS_DENIED_ACE: header(4), mask(4), SID.
            entries.append((kind, sid_text(PVOID(ace.value + 8))))
        if not private_acl(sid_text(owner), entries, current_sid()):
            raise ValueError('State ACL must restrict access to this user, SYSTEM and administrators')
    finally:
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
