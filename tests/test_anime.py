import pytest
import animesaturn as saturn


def test_anime_metadata():
    anime = saturn.Anime("dara-san-of-reiwa-764Qf")
    assert "Dara-san" in anime.name
    assert anime.link.startswith("/anime/")
    assert anime.poster.startswith("http")
    assert anime.locandina.startswith("http")
    assert "locandine" in anime.locandina
    assert len(anime.genres) > 0
    assert anime.episodes_num > 0

    episodes = anime.getEpisodes()
    assert len(episodes) == anime.episodes_num
    assert episodes[0].number == "1"


def test_anime_404():
    with pytest.raises(saturn.Error404):
        saturn.Anime("non-existent-anime-slug-xyz-999999999")
