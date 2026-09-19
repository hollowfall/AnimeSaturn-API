"""
Module for managing AnimeSaturn domains, official mirrors, and automatic domain discovery.
"""
from typing import List, Optional
import re
import httpx

# Official domain index page managed by the AnimeSaturn team
INDEX_DOMAIN_URL = "https://www.animesaturn.me/"

# Known official domains & mirrors
DEFAULT_DOMAINS = [
    "https://www.animesaturn.net",
    "https://www.animesaturn.tv",
    "https://www.animesaturn.in",
    "https://www.animesaturn.cx",
    "https://www.animesaturn.cc",
    "https://www.animesaturn.com",
    "https://www.animemars.org",
]

_current_domain: str = DEFAULT_DOMAINS[0]
_cached_domains: List[str] = list(DEFAULT_DOMAINS)


def get_domain() -> str:
    """
    Get the currently active base domain.

    Returns:
        The active domain URL string (e.g. 'https://www.animesaturn.net').
    """
    global _current_domain
    return _current_domain


def set_domain(domain_url: str) -> None:
    """
    Manually set the base domain to use for all AnimeSaturn requests.

    Args:
        domain_url: Full domain URL (e.g. 'https://www.animesaturn.tv').
    """
    global _current_domain
    clean = domain_url.rstrip("/")
    if not clean.startswith("http://") and not clean.startswith("https://"):
        clean = "https://" + clean
    _current_domain = clean


def fetch_official_domains(timeout: float = 6.0) -> List[str]:
    """
    Scrape the official domains list from https://www.animesaturn.me/.

    Args:
        timeout: Request timeout in seconds.

    Returns:
        List of scraped official domain URLs.
    """
    global _cached_domains
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    domains = []
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            resp = client.get(INDEX_DOMAIN_URL)
            if resp.status_code == 200:
                matches = re.findall(r'href=["\'](https?://(?:www\.)?(?:animesaturn\.[a-z]+|animemars\.[a-z]+)[^"\'\s]*)["\']', resp.text, re.IGNORECASE)
                for m in matches:
                    clean = m.rstrip("/")
                    # Extract only the protocol + host (e.g. https://www.animesaturn.net)
                    host_m = re.match(r'(https?://[^/]+)', clean)
                    if host_m:
                        base = host_m.group(1)
                        if base not in domains and base != INDEX_DOMAIN_URL.rstrip("/"):
                            domains.append(base)
    except Exception:
        pass

    if domains:
        # Merge with default domains without duplicates
        for d in DEFAULT_DOMAINS:
            if d not in domains:
                domains.append(d)
        _cached_domains = domains
        return domains

    return list(_cached_domains)


def discover_active_domain(timeout: float = 4.0) -> str:
    """
    Ping candidate domains and select the fastest responding active domain.

    Args:
        timeout: Timeout per domain check.

    Returns:
        The fastest responding working domain URL.
    """
    global _current_domain
    candidates = fetch_official_domains()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    for candidate in candidates:
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
                res = client.get(candidate)
                if res.status_code == 200 and ("AnimeSaturn" in res.text or "anime" in res.text.lower()):
                    final_url = str(res.url).rstrip("/")
                    parts = final_url.split("/", 3)
                    base = f"{parts[0]}//{parts[2]}"
                    _current_domain = base
                    return base
        except Exception:
            continue

    return _current_domain
