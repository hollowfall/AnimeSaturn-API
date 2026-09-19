import pytest
import animesaturn as saturn


def test_domain_get_and_set():
    original = saturn.get_domain()
    assert original.startswith("http")

    saturn.set_domain("https://www.animesaturn.tv")
    assert saturn.get_domain() == "https://www.animesaturn.tv"

    saturn.set_domain("animesaturn.net/")
    assert saturn.get_domain() == "https://animesaturn.net"

    # Reset
    saturn.set_domain(original)


def test_fetch_official_domains():
    domains = saturn.fetch_official_domains()
    assert isinstance(domains, list)
    assert len(domains) > 0
    assert any("animesaturn" in d for d in domains)


def test_discover_active_domain():
    active = saturn.discover_active_domain(timeout=5.0)
    assert active.startswith("http")
    assert "animesaturn" in active or "animemars" in active
