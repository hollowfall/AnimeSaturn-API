"""
Base Server module for AnimeSaturn video hosting providers.
"""
import os
import time
from typing import Callable, Dict, Optional, Any
import httpx

from ..utility import SES, sanitize_filename
from ..exceptions import ServerNotSupported, DownloadError, HardStoppedDownload

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class Server:
    """
    Abstract base class for all AnimeSaturn video stream servers.

    Attributes:
        name: Name of the server provider (e.g. 'Server principale', 'SaturnStream').
        id: Server provider ID.
        link: Web player/embed URL for this server.
        number: Episode number string.
        slug: Server slug identifier.
        episode_id: Optional internal episode ID.
    """

    def __init__(
        self,
        name: str,
        link: str,
        number: str = "1",
        id: int = 1,
        slug: str = "serverstock",
        episode_id: Optional[int] = None
    ):
        self.name: str = name
        self.link: str = link
        self.number: str = number
        self.id: int = id
        self.slug: str = slug
        self.episode_id: Optional[int] = episode_id
        self._default_filename: str = f"Episodio_{self.number}_{sanitize_filename(self.name)}.mp4"

    def fileLink(self) -> str:
        """
        Extract and return the direct raw video stream URL (.mp4 or .m3u8).

        Returns:
            Direct URL string.

        Raises:
            ServerNotSupported: If server is unsupported.
        """
        raise ServerNotSupported(self.name)

    def fileInfo(self) -> Dict[str, Any]:
        """
        Retrieve metadata and headers for the underlying video file (e.g. size, content-type).

        Returns:
            Dictionary containing content_type, total_bytes, url, etc.
        """
        direct_url = self.fileLink()
        headers = {
            "User-Agent": SES.headers.get("User-Agent"),
            "Referer": self.link,
        }
        try:
            with httpx.Client(follow_redirects=True, timeout=10.0, headers=headers) as client:
                res = client.head(direct_url)
                if res.status_code >= 400:
                    # Fallback to GET with 0-0 range if HEAD is blocked
                    res = client.get(direct_url, headers={"Range": "bytes=0-0"})

                total_bytes = int(res.headers.get("Content-Length", 0))
                content_range = res.headers.get("Content-Range")
                if content_range and "/" in content_range:
                    try:
                        total_bytes = int(content_range.split("/")[-1])
                    except ValueError:
                        pass

                return {
                    "content_type": res.headers.get("Content-Type", "video/mp4"),
                    "total_bytes": total_bytes,
                    "last_modified": res.headers.get("Last-Modified"),
                    "server_name": self.name,
                    "server_id": self.id,
                    "url": direct_url,
                }
        except Exception as e:
            return {
                "content_type": "video/mp4",
                "total_bytes": 0,
                "last_modified": None,
                "server_name": self.name,
                "server_id": self.id,
                "url": direct_url,
                "error": str(e),
            }

    def download(
        self,
        folder: str = ".",
        filename: Optional[str] = None,
        hook: Optional[Callable[[int, int, float], bool]] = None,
        chunk_size: int = 1024 * 1024,
        resume: bool = True,
    ) -> bool:
        """
        Download the video episode directly to the specified folder with progress reporting.

        Args:
            folder: Destination folder directory path.
            filename: Custom filename (defaults to 'Episodio_{number}_{server}.mp4').
            hook: Optional callback function receiving (current_bytes, total_bytes, percentage).
                  If hook returns False, download is safely interrupted.
            chunk_size: Streaming chunk size in bytes (default 1MB).
            resume: Whether to resume partial downloads if file exists.

        Returns:
            True if download completed successfully.

        Raises:
            DownloadError: If download fails or server error occurs.
            HardStoppedDownload: If aborted by hook callback.
        """
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        if not filename:
            filename = self._default_filename

        safe_filename = sanitize_filename(filename)
        if not safe_filename.endswith(".mp4") and not safe_filename.endswith(".mkv"):
            safe_filename += ".mp4"

        destination_path = os.path.join(folder, safe_filename)
        part_path = destination_path + ".part"

        direct_url = self.fileLink()
        request_headers = {
            "User-Agent": SES.headers.get("User-Agent"),
            "Referer": self.link,
        }

        downloaded_bytes = 0
        if resume and os.path.exists(part_path):
            downloaded_bytes = os.path.getsize(part_path)
            if downloaded_bytes > 0:
                request_headers["Range"] = f"bytes={downloaded_bytes}-"

        try:
            with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60.0, connect=10.0), headers=request_headers) as client:
                with client.stream("GET", direct_url) as response:
                    if response.status_code == 416:  # Range Not Satisfiable
                        # Part file might already be complete
                        os.replace(part_path, destination_path)
                        return True

                    if response.status_code not in (200, 206):
                        raise DownloadError(f"HTTP Error {response.status_code} while downloading stream: {direct_url}")

                    total_content_length = int(response.headers.get("Content-Length", 0))
                    total_bytes = downloaded_bytes + total_content_length if response.status_code == 206 else total_content_length

                    file_mode = "ab" if (response.status_code == 206 and downloaded_bytes > 0) else "wb"
                    if file_mode == "wb":
                        downloaded_bytes = 0

                    pbar = None
                    if hook is None and tqdm is not None and total_bytes > 0:
                        pbar = tqdm(
                            total=total_bytes,
                            initial=downloaded_bytes,
                            unit="B",
                            unit_scale=True,
                            desc=safe_filename,
                            leave=True
                        )

                    with open(part_path, file_mode) as file_handle:
                        for chunk in response.iter_bytes(chunk_size=chunk_size):
                            if not chunk:
                                continue
                            file_handle.write(chunk)
                            downloaded_bytes += len(chunk)

                            if pbar:
                                pbar.update(len(chunk))

                            if hook is not None:
                                pct = (downloaded_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0
                                should_continue = hook(downloaded_bytes, total_bytes, pct)
                                if should_continue is False:
                                    if pbar:
                                        pbar.close()
                                    raise HardStoppedDownload("Download interrupted by user hook.")

                    if pbar:
                        pbar.close()

            # Atomically rename .part file to final destination
            if os.path.exists(destination_path):
                os.remove(destination_path)
            os.replace(part_path, destination_path)
            return True

        except HardStoppedDownload:
            raise
        except Exception as exc:
            raise DownloadError(f"Failed to download episode from {self.name}: {exc}") from exc

    def __repr__(self) -> str:
        return f"<Server name='{self.name}' id={self.id} ep='{self.number}'>"
