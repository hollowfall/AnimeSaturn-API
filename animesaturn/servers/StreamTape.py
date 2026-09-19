"""
StreamTape server extractor for AnimeSaturn episodes.
"""
import re
from typing import Optional
import httpx

from .Server import Server
from ..utility import SES
from ..exceptions import DecryptionError


class StreamTape(Server):
    """
    Handler for StreamTape video hosting links.
    """

    def __init__(
        self,
        link: str,
        name: str = "StreamTape",
        number: str = "1",
        id: int = 2,
        slug: str = "streamtape",
        episode_id: Optional[int] = None
    ):
        super().__init__(name=name, link=link, number=number, id=id, slug=slug, episode_id=episode_id)
        self._cached_direct_url: Optional[str] = None

    def fileLink(self) -> str:
        """
        Extract direct video link from StreamTape player page.
        """
        if self._cached_direct_url:
            return self._cached_direct_url

        headers = {
            "User-Agent": SES.headers.get("User-Agent"),
        }

        try:
            with httpx.Client(follow_redirects=True, timeout=12.0, headers=headers) as client:
                resp = client.get(self.link)
                resp.raise_for_status()
                html_text = resp.text

            # StreamTape embeds video link in robotlink script:
            # document.getElementById('robotlink').innerHTML = '//...&token=...';
            m = re.search(r"document\.getElementById\('robotlink'\)\.innerHTML\s*=\s*['\"]([^'\"]+)['\"]", html_text)
            if not m:
                # Alternative pattern: substring concatenation
                m = re.search(r"&token=([a-zA-Z0-9_\-]+)", html_text)
                if not m:
                    raise DecryptionError(f"Unable to extract StreamTape token from {self.link}")

            # Extract base stream url pattern
            token = m.group(1)
            # Find base link
            base_m = re.search(r"//([a-zA-Z0-9\.\-]+/get_video\?[^'\"]+)", html_text)
            if base_m:
                full_stream = "https://" + base_m.group(1) + token
            else:
                full_stream = ("https:" if not token.startswith("http") else "") + token

            self._cached_direct_url = full_stream
            return full_stream
        except Exception as e:
            raise DecryptionError(f"StreamTape extraction failed: {e}") from e
