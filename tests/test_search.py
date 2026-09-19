import pytest
import animesaturn as saturn


def test_find_returns_results():
    results = saturn.find("one piece")
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "name" in first or "title" in first
    assert "link" in first
    assert first["link"].startswith("/anime/")
    assert "url" in first


def test_latest_episodes():
    data = saturn.latest_episodes(page=1)
    assert isinstance(data, dict)
    assert "items" in data
    assert "page" in data
    assert data["page"] == 1
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    assert "url" in first_item
    assert "title" in first_item
    assert "episodeLabel" in first_item
