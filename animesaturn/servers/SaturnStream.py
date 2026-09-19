"""
SaturnCDN (Server principale) video stream extractor and decrypter.
"""
import json
import re
from typing import Optional
import httpx

from .Server import Server
from ..utility import SES, xor_decrypt
from ..exceptions import DecryptionError


class SaturnStream(Server):
    """
    Handler for AnimeSaturn's primary SaturnCDN / SaturnStream hosting service.
    Automatically parses the embedded player script and decrypts XOR-encoded
    playlist data to obtain direct high-speed MP4/HLS streaming and download URLs.
    """

    def __init__(
        self,
        link: str,
        name: str = "Server principale",
        number: str = "1",
        id: int = 1,
        slug: str = "serverstock",
        episode_id: Optional[int] = None
    ):
        super().__init__(name=name, link=link, number=number, id=id, slug=slug, episode_id=episode_id)
        self._cached_direct_url: Optional[str] = None
        self._cached_poster: Optional[str] = None

    def fileLink(self) -> str:
        """
        Decrypt and return the direct raw .mp4 stream URL for the episode.

        Returns:
            Direct playable MP4 URL.

        Raises:
            DecryptionError: If the token, expires, or playlist response cannot be decrypted.
        """
        if self._cached_direct_url:
            return self._cached_direct_url

        headers = {
            "User-Agent": SES.headers.get("User-Agent"),
            "Referer": "https://www.animesaturn.net/",
        }

        # 1. Fetch the embed player HTML
        try:
            with httpx.Client(follow_redirects=True, timeout=12.0, headers=headers) as client:
                resp = client.get(self.link)
                resp.raise_for_status()
                embed_html = resp.text
        except Exception as e:
            raise DecryptionError(f"Failed to fetch embed page: {e}") from e

        # 2. Extract window.__E = {i: ..., k: "...", e: ...}
        m_e = re.search(r'window\.__E\s*=\s*(\{.*?\});', embed_html)
        if not m_e:
            raise DecryptionError(f"Could not locate window.__E in embed page for {self.name}")

        e_str = m_e.group(1)
        i_match = re.search(r'i:\s*(\d+)', e_str)
        k_match = re.search(r'k:\s*["\']([^"\']+)["\']', e_str)
        e_match = re.search(r'e:\s*(\d+)', e_str)

        if not (i_match and k_match and e_match):
            raise DecryptionError(f"Incomplete parameters in window.__E: {e_str}")

        episode_i = i_match.group(1)
        token_k = k_match.group(1)
        expires_e = e_match.group(1)

        # 3. Call the internal playlist endpoint
        # Base url from embed link (usually play.saturncdn.net)
        base_match = re.match(r'(https?://[^/]+)', self.link)
        base_embed = base_match.group(1) if base_match else "https://play.saturncdn.net"
        playlist_url = f"{base_embed}/embed/{episode_i}/playlist?token={token_k}&expires={expires_e}"

        playlist_headers = {
            "User-Agent": SES.headers.get("User-Agent"),
            "Referer": self.link,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

        try:
            with httpx.Client(follow_redirects=True, timeout=12.0, headers=playlist_headers) as client:
                playlist_resp = client.get(playlist_url)
                playlist_resp.raise_for_status()
                playlist_data = playlist_resp.json()
        except Exception as e:
            raise DecryptionError(f"Failed to fetch playlist endpoint {playlist_url}: {e}") from e

        encrypted_stream = playlist_data.get("d")
        if not encrypted_stream:
            raise DecryptionError("Missing encrypted payload 'd' in playlist response")

        direct_url = xor_decrypt(encrypted_stream, token_k)
        if not direct_url.startswith("http"):
            raise DecryptionError(f"Decrypted payload is not a valid URL: {direct_url}")

        if "p" in playlist_data:
            self._cached_poster = xor_decrypt(playlist_data["p"], token_k)

        self._cached_direct_url = direct_url
        return direct_url

    @property
    def poster(self) -> Optional[str]:
        """Get the episode video poster thumbnail URL if available."""
        if not self._cached_direct_url:
            try:
                self.fileLink()
            except Exception:
                pass
        return self._cached_poster
