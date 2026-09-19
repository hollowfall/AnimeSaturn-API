"""
Module containing custom exceptions for AnimeSaturn library.
"""
from typing import Optional


class AnimeSaturnError(Exception):
    """Base exception for all AnimeSaturn library errors."""
    pass


class Error404(AnimeSaturnError):
    """Raised when an AnimeSaturn page or resource returns a 404 error."""
    def __init__(self, url: str):
        super().__init__(f"Page not found (404): '{url}'")
        self.url = url


class AnimeNotAvailable(AnimeSaturnError):
    """Raised when the requested anime is not available or has no episodes."""
    def __init__(self, anime_name: str):
        super().__init__(f"The anime '{anime_name}' is currently not available or has no episodes.")
        self.anime_name = anime_name


class EpisodeNotFound(AnimeSaturnError):
    """Raised when a specific episode is not found for an anime."""
    def __init__(self, episode_number: str, anime_name: str):
        super().__init__(f"Episode '{episode_number}' was not found for anime '{anime_name}'.")
        self.episode_number = episode_number
        self.anime_name = anime_name


class ServerNotSupported(AnimeSaturnError):
    """Raised when an episode server provider is unsupported or unrecognized."""
    def __init__(self, server_name: str):
        super().__init__(f"Server '{server_name}' is not currently supported.")
        self.server_name = server_name


class DecryptionError(AnimeSaturnError):
    """Raised when video stream decryption fails."""
    def __init__(self, message: str = "Failed to decrypt video stream URL"):
        super().__init__(message)


class DownloadError(AnimeSaturnError):
    """Raised when video downloading encounters an error."""
    pass


class HardStoppedDownload(AnimeSaturnError):
    """Raised when a download is prematurely stopped by a user or hook."""
    def __init__(self, message: str = "Download aborted."):
        super().__init__(message)


class DeprecatedLibrary(AnimeSaturnError):
    """Raised when changes to AnimeSaturn website structure break parsing."""
    def __init__(self, file: Optional[str] = None, function: Optional[str] = None, line: Optional[int] = None):
        msg = "The AnimeSaturn website structure has changed and broken this operation."
        if file or function:
            msg += f" (Location: {file} in {function}() line {line})"
        super().__init__(msg)
        self.file = file
        self.function = function
        self.line = line
