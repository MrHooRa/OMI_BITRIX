"""Persistent app signing and Windows-protected, profile-bound credentials."""
import base64
import ctypes
import os
import secrets
from pathlib import Path


def signing_secret(directory):
    supplied = os.environ.get("WORK_COCKPIT_SECRET")
    if supplied:
        return supplied
    path = Path(directory) / ".session-secret"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="ascii") as stream:
            stream.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    return path.read_text(encoding="ascii").strip()


class CredentialVault:
    """DPAPI ciphertext is bound to the Windows account and browser profile."""
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _crypt(value, profile, decrypt=False):
        if os.name != "nt":
            raise RuntimeError("Windows credential protection is required.")
        from ctypes import wintypes

        class Blob(ctypes.Structure):
            _fields_ = [("length", wintypes.DWORD),
                        ("data", ctypes.POINTER(ctypes.c_ubyte))]

        def blob(raw):
            buffer = ctypes.create_string_buffer(raw)
            return Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer

        source, source_buffer = blob(value)
        entropy, entropy_buffer = blob(("OMI-Diwan:" + profile).encode())
        output = Blob()
        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
        function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p,
                             ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                             wintypes.DWORD, ctypes.POINTER(Blob)]
        function.restype = wintypes.BOOL
        if not function(ctypes.byref(source), None, ctypes.byref(entropy),
                        None, None, 1, ctypes.byref(output)):
            raise RuntimeError("Credential protection failed; reconnect under this Windows account.")
        try:
            return ctypes.string_at(output.data, output.length)
        finally:
            kernel32.LocalFree(output.data)

    def save(self, profile, token):
        sealed = self._crypt(token.encode(), profile)
        self.store.set("diwan_token_protected", base64.b64encode(sealed).decode(),
                       profile_id=profile)

    def get(self, profile):
        value = self.store.get("diwan_token_protected", "", profile_id=profile)
        return self._crypt(base64.b64decode(value), profile, True).decode() if value else ""

    def present(self, profile):
        return bool(self.store.get("diwan_token_protected", "", profile_id=profile))

    def remove(self, profile):
        self.store.set("diwan_token_protected", "", profile_id=profile)
