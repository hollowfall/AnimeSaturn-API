"""
AnimeSaturn Python API
~~~~~~~~~~~~~~~~~~~~~~

An unofficial, high-performance Python package for AnimeSaturn.
Provides full programmatic access to anime search, metadata parsing,
episode lists, video stream decrypters (SaturnCDN, StreamTape, MixDrop),
multi-domain auto-discovery, and robust video downloading.

:copyright: (c) 2026 AnimeSaturn Contributors
:license: MIT, see LICENSE for more details.
"""

from .anime import Anime
from .episodio import Episodio
from .search import find, search, latest_episodes
from .domains import (
    get_domain,
    set_domain,
    discover_active_domain,
    fetch_official_domains,
)
from .servers import Server, SaturnStream, StreamTape, MixDrop
from .exceptions import (
    AnimeSaturnError,
    Error404,
    AnimeNotAvailable,
    EpisodeNotFound,
    ServerNotSupported,
    DecryptionError,
    DownloadError,
    HardStoppedDownload,
    DeprecatedLibrary,
)

__version__ = "1.0.0"
__author__ = "AnimeSaturn Contributors"
__license__ = "MIT"

__all__ = [
    # Classes
    "Anime",
    "Episodio",
    "Server",
    "SaturnStream",
    "StreamTape",
    "MixDrop",
    # Functions
    "find",
    "search",
    "latest_episodes",
    "get_domain",
    "set_domain",
    "discover_active_domain",
    "fetch_official_domains",
    # Exceptions
    "AnimeSaturnError",
    "Error404",
    "AnimeNotAvailable",
    "EpisodeNotFound",
    "ServerNotSupported",
    "DecryptionError",
    "DownloadError",
    "HardStoppedDownload",
    "DeprecatedLibrary",
]
