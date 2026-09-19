"""
Module containing the Episodio class representing single anime episodes.
"""
from typing import List, Dict, Any, Optional, Callable, Iterator
import re
import html
import json

from .utility import SES, HealthCheck, sanitize_filename
from .domains import get_domain
from .exceptions import EpisodeNotFound, ServerNotSupported, AnimeSaturnError
from .servers import Server, create_server


class Episodio:
    """
    Represents an anime episode on AnimeSaturn.

    Attributes:
        number: Episode number string (e.g. '1', '12', '5.5').
        anime_slug: Slug identifier of the parent anime.
        link: Direct streaming page URL path.
        title: Episode title / display label.
        episode_id: Internal AnimeSaturn episode ID.
    """

    def __init__(
        self,
        number: str,
        anime_slug: str,
        link: Optional[str] = None,
        title: Optional[str] = None,
        episode_id: Optional[int] = None,
        raw_servers: Optional[List[Dict[str, Any]]] = None
    ):
        self.number: str = str(number).strip()
        self.anime_slug: str = anime_slug.strip().strip("/")
        if self.anime_slug.startswith("anime/"):
            self.anime_slug = self.anime_slug[len("anime/"):]
        elif self.anime_slug.startswith("episode/"):
            self.anime_slug = self.anime_slug[len("episode/"):]

        # Clean episode number formatting for URLs
        clean_num = self.number
        if clean_num.lower().startswith("ep-"):
            clean_num = clean_num[3:]
        elif clean_num.lower().startswith("ep."):
            clean_num = clean_num[3:].strip()
        self.clean_number: str = clean_num

        if not link:
            self.link: str = f"/anime/{self.anime_slug}/ep-{self.clean_number}"
        else:
            self.link = link

        self.title: str = title or f"Episodio {self.number}"
        self.episode_id: Optional[int] = episode_id
        self._raw_servers: Optional[List[Dict[str, Any]]] = raw_servers
        self._server_cache: Optional[List[Server]] = None

    @property
    def url(self) -> str:
        """Full absolute URL to watch page on active AnimeSaturn domain."""
        if self.link.startswith("http"):
            return self.link
        return f"{get_domain()}{self.link if self.link.startswith('/') else '/' + self.link}"

    def _fetch_episode_data(self) -> Dict[str, Any]:
        """
        Fetch episode watch metadata from AnimeSaturn internal API or HTML fallback.
        """
        # 1. Try fast internal JSON API: /api/watch/{slug}/ep-{number}
        api_path = f"/api/watch/{self.anime_slug}/ep-{self.clean_number}"
        try:
            resp = SES.get(api_path)
            data = resp.json()
            if data and data.get("ok"):
                return data
        except Exception:
            pass

        # 2. Fallback: fetch player page HTML and extract watchPage(...)
        watch_path = self.link if self.link.startswith("/") else f"/{self.link}"
        resp = SES.get(watch_path)
        unescaped = html.unescape(resp.text)
        idx = unescaped.find("watchPage(")
        if idx != -1:
            sub = unescaped[idx + len("watchPage("):]
            end_idx = sub.find(")\">")
            if end_idx != -1:
                try:
                    return json.loads(sub[:end_idx])
                except Exception:
                    pass

        return {}

    @property
    def servers(self) -> List[Server]:
        """
        List of all video hosting servers available for this episode.
        """
        return self.getServer()

    @property
    def links(self) -> List[Server]:
        """
        Alias for servers property matching AnimeWorld-API naming convention.
        """
        return self.getServer()

    @HealthCheck
    def getServer(self) -> List[Server]:
        """
        Retrieve all Server instances providing streaming for this episode.

        Returns:
            List of Server objects.
        """
        if self._server_cache is not None:
            return self._server_cache

        servers_list: List[Server] = []

        if not self._raw_servers:
            data = self._fetch_episode_data()
            if data:
                if not self.episode_id and "episodeId" in data:
                    self.episode_id = data["episodeId"]
                self._raw_servers = data.get("servers", [])

        if self._raw_servers:
            for s_info in self._raw_servers:
                server_obj = create_server(
                    server_data=s_info,
                    number=self.number,
                    episode_id=self.episode_id
                )
                servers_list.append(server_obj)

        self._server_cache = servers_list
        return servers_list

    def download(
        self,
        folder: str = ".",
        title: Optional[str] = None,
        server_index: int = 0,
        hook: Optional[Callable[[int, int, float], bool]] = None
    ) -> bool:
        """
        Download the episode video to disk.

        Args:
            folder: Output directory (default current directory).
            title: Custom filename for the output video.
            server_index: Index of the server to download from (default 0 = primary).
            hook: Optional progress callback function.

        Returns:
            True if download succeeded, False otherwise.
        """
        servers = self.getServer()
        if not servers:
            raise ServerNotSupported(f"No available video servers found for episode {self.number}")

        if server_index >= len(servers):
            server_index = 0

        target_server = servers[server_index]
        return target_server.download(
            folder=folder,
            filename=title,
            hook=hook
        )

    def __repr__(self) -> str:
        return f"<Episodio num='{self.number}' anime='{self.anime_slug}'>"
