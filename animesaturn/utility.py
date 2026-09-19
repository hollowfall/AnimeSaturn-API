"""
Utility module containing session management, request helpers, decryption routines, and decorators.
"""
import base64
import functools
import inspect
import re
import time
from typing import Any, Callable, Dict, Optional, Union
import httpx

from .domains import get_domain
from .exceptions import DeprecatedLibrary, Error404


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}


class AnimeSaturnSession(httpx.Client):
    """
    Custom HTTP client wrapper with automatic base URL resolution and retries.
    """

    def __init__(self, *args, **kwargs):
        headers = dict(DEFAULT_HEADERS)
        if "headers" in kwargs and kwargs["headers"]:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        if "timeout" not in kwargs:
            kwargs["timeout"] = httpx.Timeout(15.0, connect=8.0)
        if "follow_redirects" not in kwargs:
            kwargs["follow_redirects"] = True
        super().__init__(*args, **kwargs)

    def build_full_url(self, url: Union[str, httpx.URL]) -> str:
        """
        Merge a relative path or absolute URL with the active base domain.
        """
        url_str = str(url)
        if url_str.startswith("http://") or url_str.startswith("https://"):
            return url_str
        base = get_domain()
        if not url_str.startswith("/"):
            url_str = "/" + url_str
        return base + url_str

    def get(self, url: Union[str, httpx.URL], *args, **kwargs) -> httpx.Response:
        """
        Execute a GET request with automatic URL building and retries on transient network errors.
        """
        full_url = self.build_full_url(url)
        # Ensure Referer is set if not present
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        if "Referer" not in kwargs["headers"]:
            kwargs["headers"]["Referer"] = get_domain() + "/"

        max_retries = kwargs.pop("retries", 2)
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                response = super().get(full_url, *args, **kwargs)
                if response.status_code == 404:
                    raise Error404(full_url)
                response.raise_for_status()
                return response
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep(1.0)
                    continue
                raise last_exc


# Global shared session instance
SES = AnimeSaturnSession()


def HealthCheck(func: Callable) -> Callable:
    """
    Decorator to catch unexpected parsing errors and raise DeprecatedLibrary
    with location details when website structure changes.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except (AttributeError, IndexError, KeyError) as e:
            trace = inspect.trace()
            if trace:
                frame = trace[-1]
                filename = frame.filename
                fun_name = frame.function
                line_no = frame.lineno
            else:
                filename, fun_name, line_no = None, func.__name__, None
            raise DeprecatedLibrary(filename, fun_name, line_no) from e

    return wrapper


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename by removing illegal filesystem characters across OS platforms.

    Args:
        name: Proposed filename.

    Returns:
        Clean, filesystem-safe filename string.
    """
    illegal = ['#', '%', '&', '{', '}', '\\', '<', '>', '*', '?', '/', '$', '!', "'", '"', ':', '@', '+', '`', '|', '=']
    for char in illegal:
        name = name.replace(char, '')
    return " ".join(name.split()).strip()


def xor_decrypt(ciphertext_b64: str, key: str) -> str:
    """
    Decrypt SaturnCDN XOR-encrypted payload strings (such as playlist direct streams and posters).

    Args:
        ciphertext_b64: Base64-encoded encrypted payload string.
        key: Encryption key string (typically token k).

    Returns:
        Decrypted UTF-8 string (e.g. direct video stream URL).
    """
    if not ciphertext_b64 or not key:
        return ""
    try:
        raw_bytes = base64.b64decode(ciphertext_b64)
        k_bytes = key.encode("utf-8")
        decrypted = bytearray()
        for i, byte in enumerate(raw_bytes):
            decrypted.append(byte ^ k_bytes[i % len(k_bytes)])
        return decrypted.decode("utf-8", errors="ignore")
    except Exception:
        return ""
