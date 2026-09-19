"""
Servers package containing extractors for different video hosting providers.
"""
from typing import Dict, Any, Optional

from .Server import Server
from .SaturnStream import SaturnStream
from .StreamTape import StreamTape
from .MixDrop import MixDrop


def create_server(
    server_data: Dict[str, Any],
    number: str = "1",
    episode_id: Optional[int] = None
) -> Server:
    """
    Instantiate the appropriate Server subclass based on server metadata.

    Args:
        server_data: Dictionary containing server metadata (name, slug, link, id).
        number: Episode number string.
        episode_id: Optional internal episode ID.

    Returns:
        Instance of Server subclass (SaturnStream, StreamTape, MixDrop, or generic Server).
    """
    name = server_data.get("name", "Server principale")
    link = server_data.get("link", "")
    slug = server_data.get("slug", "")
    server_id = server_data.get("id", 1)

    lower_name = name.lower()
    lower_slug = slug.lower()
    lower_link = link.lower()

    if "streamtape" in lower_name or "streamtape" in lower_slug or "streamtape" in lower_link:
        return StreamTape(name=name, link=link, number=number, id=server_id, slug=slug, episode_id=episode_id)
    elif "mixdrop" in lower_name or "mixdrop" in lower_slug or "mixdrop" in lower_link:
        return MixDrop(name=name, link=link, number=number, id=server_id, slug=slug, episode_id=episode_id)
    else:
        # Default & primary AnimeSaturn host is SaturnStream / saturncdn
        return SaturnStream(name=name, link=link, number=number, id=server_id, slug=slug, episode_id=episode_id)


__all__ = [
    "Server",
    "SaturnStream",
    "StreamTape",
    "MixDrop",
    "create_server",
]
