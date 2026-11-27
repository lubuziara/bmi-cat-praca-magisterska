import base64
import hashlib
import hmac
import secrets
import struct
import time


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def verify(secret: str, code: str, skew: int = 1) -> int | None:
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    current = int(time.time()) // 30
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    for counter in range(current - skew, current + skew + 1):
        digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
        offset = digest[-1] & 15
        value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff) % 1000000
        if hmac.compare_digest(f"{value:06d}", code):
            return counter
    return None
