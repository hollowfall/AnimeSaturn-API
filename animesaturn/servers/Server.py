"""
Base Server module for AnimeSaturn video hosting providers.
"""
import os
import time
import re
import urllib.parse
import shutil
import subprocess
from typing import Callable, Dict, Optional, Any, List
from concurrent.futures import ThreadPoolExecutor
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

        # Route HLS (.m3u8) video playlists to dedicated concurrent HLS downloader
        if ".m3u8" in direct_url.lower():
            return self._download_hls(
                destination_path=destination_path,
                part_path=part_path,
                playlist_url=direct_url,
                request_headers=request_headers,
                safe_filename=safe_filename,
                hook=hook,
                resume=resume,
            )

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

        except (KeyboardInterrupt, HardStoppedDownload):
            if pbar:
                try:
                    pbar.close()
                except Exception:
                    pass
            raise HardStoppedDownload("Download stopped.")
        except Exception as exc:
            if pbar:
                try:
                    pbar.close()
                except Exception:
                    pass
            raise DownloadError(f"Failed to download episode from {self.name}: {exc}") from exc

    def _download_hls(
        self,
        destination_path: str,
        part_path: str,
        playlist_url: str,
        request_headers: Dict[str, str],
        safe_filename: str,
        hook: Optional[Callable[[int, int, float], bool]] = None,
        resume: bool = True,
        max_workers: int = 6,
        batch_size: int = 16,
    ) -> bool:
        """
        Download an HLS (.m3u8) video stream by resolving quality and fetching .ts chunks.
        """
        pbar = None
        executor = None
        try:
            with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(25.0, connect=10.0), headers=request_headers) as client:
                r = client.get(playlist_url)
                if r.status_code != 200:
                    raise DownloadError(f"HTTP {r.status_code} fetching master playlist: {playlist_url}")

                lines = [l.strip() for l in r.text.splitlines() if l.strip()]
                media_url = playlist_url

                # 1. If master playlist, select highest quality variant
                if any("#EXT-X-STREAM-INF" in l for l in lines):
                    variants = []
                    for i, l in enumerate(lines):
                        if l.startswith("#EXT-X-STREAM-INF"):
                            bw = 0
                            m_bw = re.search(r'BANDWIDTH=(\d+)', l)
                            if m_bw:
                                bw = int(m_bw.group(1))
                            if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                                variants.append((bw, lines[i + 1]))
                    if variants:
                        variants.sort(key=lambda x: x[0], reverse=True)
                        best_sub = variants[0][1]
                        media_url = urllib.parse.urljoin(playlist_url, best_sub)
                        r_sub = client.get(media_url)
                        if r_sub.status_code != 200:
                            raise DownloadError(f"HTTP {r_sub.status_code} fetching variant playlist: {media_url}")
                        lines = [l.strip() for l in r_sub.text.splitlines() if l.strip()]

                # 2. Extract all .ts segment URLs
                segment_lines = [l for l in lines if not l.startswith("#") and l.strip()]
                if not segment_lines:
                    raise DownloadError(f"No video segments found in playlist: {media_url}")

                segment_urls = [urllib.parse.urljoin(media_url, s) for s in segment_lines]
                total_segments = len(segment_urls)

            if hook is None and tqdm is not None:
                pbar = tqdm(
                    total=total_segments,
                    unit="seg",
                    desc=safe_filename,
                    leave=True
                )

            downloaded_bytes = 0
            total_estimated_bytes = total_segments * 250 * 1024

            def fetch_segment(item):
                idx, seg_url = item
                last_err = None
                for _ in range(3):
                    try:
                        with httpx.Client(timeout=httpx.Timeout(20.0, connect=10.0), headers=request_headers) as c:
                            resp = c.get(seg_url)
                            resp.raise_for_status()
                            return idx, resp.content
                    except Exception as e:
                        last_err = e
                        time.sleep(0.5)
                raise DownloadError(f"Failed to fetch segment {idx}: {last_err}")

            executor = ThreadPoolExecutor(max_workers=max_workers)
            with open(part_path, "wb") as f:
                for b_start in range(0, total_segments, batch_size):
                    batch_items = list(enumerate(segment_urls[b_start:b_start + batch_size], start=b_start))
                    results = list(executor.map(fetch_segment, batch_items))
                    results.sort(key=lambda x: x[0])
                    for _, chunk_data in results:
                        f.write(chunk_data)
                        downloaded_bytes += len(chunk_data)
                        if pbar:
                            pbar.update(1)

                    if hook is not None:
                        pct = ((b_start + len(batch_items)) / total_segments) * 100.0
                        should_continue = hook(downloaded_bytes, total_estimated_bytes, pct)
                        if should_continue is False:
                            raise HardStoppedDownload("Download stopped.")

            if pbar:
                pbar.close()
                pbar = None

            # Optional remux with ffmpeg if available on system
            ffmpeg_bin = shutil.which("ffmpeg")
            if ffmpeg_bin:
                try:
                    subprocess.run(
                        [ffmpeg_bin, "-y", "-i", part_path, "-c", "copy", destination_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True
                    )
                    if os.path.exists(part_path):
                        os.remove(part_path)
                    return True
                except Exception:
                    pass

            if os.path.exists(destination_path):
                os.remove(destination_path)
            os.replace(part_path, destination_path)
            return True

        except (KeyboardInterrupt, HardStoppedDownload):
            if pbar:
                try:
                    pbar.close()
                except Exception:
                    pass
                pbar = None
            if executor:
                try:
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except Exception:
                    pass
            raise HardStoppedDownload("Download stopped.")
        except Exception as exc:
            if pbar:
                try:
                    pbar.close()
                except Exception:
                    pass
                pbar = None
            raise DownloadError(f"HLS download error from {self.name}: {exc}") from exc
        finally:
            if pbar:
                try:
                    pbar.close()
                except Exception:
                    pass
            if executor:
                try:
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass

    def __repr__(self) -> str:
        return f"<Server name='{self.name}' id={self.id} ep='{self.number}'>"

