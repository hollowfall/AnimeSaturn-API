"""
Search and discovery functions for AnimeSaturn.
"""
from typing import List, Dict, Any, Optional
import urllib.parse
from bs4 import BeautifulSoup

from .utility import SES, HealthCheck
from .domains import get_domain


@HealthCheck
def find(keyword: str) -> List[Dict[str, Any]]:
    """
    Search for anime by keyword matching AnimeWorld-API's `find()` method.

    Args:
        keyword: Search query string (e.g. 'One Piece', 'Naruto').

    Returns:
        List of dictionaries with anime search results:
        [
            {
                "name": "One Piece",
                "title": "One Piece",
                "link": "/anime/one-piece-PmTvj",
                "url": "https://www.animesaturn.net/anime/one-piece-PmTvj",
                "poster": "https://...",
                "year": "1999",
                "episodes": "1000+",
                "type": "TV",
                "genres": ["Azione", "Avventura"]
            },
            ...
        ]
    """
    results: List[Dict[str, Any]] = []
    base_domain = get_domain()

    # 1. First attempt: internal JSON search API (/api/search?q=...)
    try:
        encoded_query = urllib.parse.quote(keyword.strip())
        api_url = f"/api/search?q={encoded_query}"
        resp = SES.get(api_url)
        data = resp.json()
        raw_items = data.get("results", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

        for item in raw_items:
            title = item.get("title", "")
            raw_url = item.get("url", "")
            if not raw_url.startswith("/"):
                raw_url = "/" + raw_url

            # Format genres
            raw_genres = item.get("genres", [])
            genres = [g.get("name", "") if isinstance(g, dict) else str(g) for g in raw_genres]

            full_link = f"{base_domain}{raw_url}"
            poster_img = item.get("poster", "")
            results.append({
                "name": title,
                "title": title,
                "link": raw_url,
                "url": full_link,
                "locandina": poster_img,
                "poster": poster_img,
                "year": item.get("year", ""),
                "episodes": item.get("episodes", ""),
                "type": item.get("type", "TV"),
                "genres": genres,
            })

        if results:
            return results
    except Exception:
        pass

    # 2. Fallback: HTML search via /filter?key=...
    try:
        filter_url = f"/filter?key={urllib.parse.quote(keyword.strip())}"
        resp = SES.get(filter_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        seen_links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/anime/" in href and not href.endswith("/ep-1") and href not in seen_links:
                title = a.text.strip()
                # Clean title if it contains rating or type lines
                lines = [l.strip() for l in title.splitlines() if l.strip()]
                clean_title = lines[-1] if lines else title
                if clean_title and clean_title.lower() != "dettagli":
                    seen_links.add(href)
                    results.append({
                        "name": clean_title,
                        "title": clean_title,
                        "link": href,
                        "url": f"{base_domain}{href}",
                        "poster": "",
                        "year": "",
                        "episodes": "",
                        "type": "TV",
                        "genres": [],
                    })
    except Exception:
        pass

    return results


def search(keyword: str) -> List[Any]:
    """
    Search for anime and return initialized Anime class instances.

    Args:
        keyword: Search query string.

    Returns:
        List of Anime instances.
    """
    # Import locally to avoid circular dependencies
    from .anime import Anime

    items = find(keyword)
    animes: List[Anime] = []
    for item in items:
        try:
            animes.append(Anime(item["link"]))
        except Exception:
            continue
    return animes


@HealthCheck
def latest_episodes(page: int = 1) -> Dict[str, Any]:
    """
    Get the latest released episodes across AnimeSaturn.

    Args:
        page: Page number for pagination (starts at 1).

    Returns:
        Dictionary containing:
        {
            "items": [
                {
                    "url": "/episode/slug/ep-24",
                    "title": "Anime Name",
                    "poster": "https://...",
                    "episodeLabel": "24",
                    "type": "TV"
                },
                ...
            ],
            "page": 1,
            "pages": 100,
            "total": 2400,
            "hasPrev": False,
            "hasNext": True
        }
    """
    api_url = f"/api/home/episodes?page={int(page)}"
    resp = SES.get(api_url)
    return resp.json()
