"""
MixDrop server extractor for AnimeSaturn episodes.
"""
import re
from typing import Optional
import httpx

from .Server import Server
from ..utility import SES
from ..exceptions import DecryptionError


class MixDrop(Server):
    """
    Handler for MixDrop video hosting links.
    """

    def __init__(
        self,
        link: str,
        name: str = "MixDrop",
        number: str = "1",
        id: int = 3,
        slug: str = "mixdrop",
        episode_id: Optional[int] = None
    ):
        super().__init__(name=name, link=link, number=number, id=id, slug=slug, episode_id=episode_id)
        self._cached_direct_url: Optional[str] = None

    def fileLink(self) -> str:
        """
        Extract direct video link from MixDrop player page.
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

            # Mixdrop uses MDCore.wurl or eval(function(p,a,c,k,e,d)...)
            m = re.search(r'(?:wurl|furl)\s*=\s*["\']([^"\']+)["\']', html_text)
            if not m:
                m = re.search(r'//([a-zA-Z0-9_\-\.\/]+(?:delivery|video|v)\.mp4[^\s"\'<>]*)', html_text)

            if not m:
                raise DecryptionError(f"Unable to extract MixDrop video URL from {self.link}")

            url = m.group(1)
            if not url.startswith("http"):
                url = "https:" + url

            self._cached_direct_url = url
            return url
        except Exception as e:
            raise DecryptionError(f"MixDrop extraction failed: {e}") from e
