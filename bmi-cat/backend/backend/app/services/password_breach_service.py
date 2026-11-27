import hashlib
import logging
import time
from threading import Lock

import requests
from fastapi import HTTPException


PASSWORD_REJECTED_MESSAGE = (
    "To hasło pojawiło się w znanych wyciekach lub jest zbyt łatwe do odgadnięcia. "
    "Wybierz inne, unikalne hasło."
)


class PasswordBreachService:
    """Checks password candidates without ever sending them outside the backend."""

    _prefix_cache: dict[str, tuple[float, dict[str, int]]] = {}
    _cache_lock = Lock()
    _local_blocklist = frozenset({
        "123456", "123456789", "12345678", "password", "qwerty", "abc123",
        "password123", "admin", "letmein", "welcome", "iloveyou", "haslo",
        "haslo123", "kot", "bmicat",
    })

    def __init__(self, settings):
        self.settings = settings

    def validate(self, password: str) -> None:
        if password.casefold() in self._local_blocklist:
            raise HTTPException(422, PASSWORD_REJECTED_MESSAGE)
        if self.settings.password_breach_check_enabled and self._is_breached(password):
            raise HTTPException(422, PASSWORD_REJECTED_MESSAGE)

    def _is_breached(self, password: str) -> bool:
        digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        suffixes = self._get_suffixes(prefix)
        return suffixes.get(suffix, 0) >= self.settings.password_breach_minimum_count

    def _get_suffixes(self, prefix: str) -> dict[str, int]:
        now = time.monotonic()
        with self._cache_lock:
            cached = self._prefix_cache.get(prefix)
            if cached and cached[0] > now:
                return cached[1]
        try:
            response = requests.get(
                f"{self.settings.password_breach_api_url.rstrip('/')}/{prefix}",
                timeout=self.settings.password_breach_timeout_seconds,
                headers={"Add-Padding": "true"},
            )
            response.raise_for_status()
            suffixes = {
                line.partition(":")[0].strip().upper(): int(line.partition(":")[2])
                for line in response.text.splitlines()
                if len(line.partition(":")[0].strip()) == 35 and line.partition(":")[2].isdigit()
            }
            with self._cache_lock:
                self._prefix_cache[prefix] = (now + self.settings.password_breach_cache_seconds, suffixes)
            return suffixes
        except requests.RequestException:
            logging.getLogger(__name__).warning("Password breach lookup unavailable")
            return {}
