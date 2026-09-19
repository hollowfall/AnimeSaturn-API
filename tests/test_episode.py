import pytest
import animesaturn as saturn


def test_episode_servers_and_decryption():
    # Test episode 1 of a known available anime
    ep = saturn.Episodio(number="1", anime_slug="dara-san-of-reiwa-764Qf")
    assert ep.number == "1"

    servers = ep.getServer()
    assert len(servers) > 0

    primary = servers[0]
    assert primary.name is not None
    assert primary.link.startswith("http")

    # Decrypt direct stream link
    direct_url = primary.fileLink()
    assert direct_url.startswith("http")
    assert ".mp4" in direct_url or "stream" in direct_url

    # Check fileInfo
    info = primary.fileInfo()
    assert info["content_type"] == "video/mp4"
    assert info["total_bytes"] > 0
