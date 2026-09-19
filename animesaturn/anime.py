"""
Module containing the Anime class representing an entire anime series or movie.
"""
from typing import List, Optional, Dict, Any
import re
import json
from bs4 import BeautifulSoup
import httpx

from .utility import SES, HealthCheck
from .exceptions import Error404, AnimeNotAvailable
from .episodio import Episodio


class Anime:
    """
    Represents an anime series, movie, or OVA on AnimeSaturn.

    Attributes:
        link: URL path or full link to the anime page.
        slug: Normalized anime slug.
        name: Primary title of the anime.
        title: Alias for `name`.
        jtitle: Alternate / Romaji / Japanese title.
        alternate_name: Alias for `jtitle`.
        story: Full plot / synopsis in Italian.
        synopsis: Alias for `story`.
        locandina: Direct URL to the vertical anime poster image (locandina).
        poster: Alias for `locandina`.
        copertina: Direct URL to the horizontal anime cover/banner image.
        cover: Alias for `copertina`.
        background: Direct URL to the backdrop hero background image.
        backdrop: Alias for `background`.
        category: Anime release category (e.g. 'TV', 'Movie', 'OVA', 'ONA').
        season: Release season (e.g. 'Estate 2026', 'Autunno 2022').
        language: Language format ('Giapponese', 'Italiano').
        release: Release year.
        release_date: Release date string (e.g. '11 Ottobre 2022').
        studio: Animation studio (e.g. 'MAPPA', 'Toei Animation').
        duration: Episode duration (e.g. '25 min').
        views: Total view count string (e.g. '5,501,538').
        episodes_num: Total number of released episodes.
        status: Anime status ('In corso', 'Finito').
        genres: List of genre / category names.
        rating: Community rating score out of 10.
        mal_url: Link to MyAnimeList entry.
        anilist_url: Link to AniList entry.
    """

    def __init__(self, link: str):
        """
        Initialize Anime from URL or slug.

        Args:
            link: Full URL (e.g. 'https://www.animesaturn.net/anime/one-piece-PmTvj')
                  or relative path (e.g. '/anime/one-piece-PmTvj') or slug ('one-piece-PmTvj').

        Raises:
            Error404: If anime page does not exist.
        """
        clean_link = str(link).strip()
        if clean_link.startswith("http://") or clean_link.startswith("https://"):
            parsed = httpx.URL(clean_link)
            clean_link = parsed.path

        if not clean_link.startswith("/"):
            clean_link = "/" + clean_link
        if not clean_link.startswith("/anime/"):
            clean_link = "/anime" + clean_link

        self.link: str = clean_link
        self.slug: str = self.link.replace("/anime/", "").strip("/")

        # Initialize attributes
        self.name: str = ""
        self.title: str = ""
        self.jtitle: str = ""
        self.alternate_name: str = ""
        self.story: str = ""
        self.synopsis: str = ""
        self.locandina: str = ""
        self.poster: str = ""
        self.copertina: str = ""
        self.cover: str = ""
        self.background: str = ""
        self.backdrop: str = ""
        self.category: str = "TV"
        self.season: str = ""
        self.language: str = ""
        self.release: str = ""
        self.release_date: str = ""
        self.studio: str = ""
        self.duration: str = ""
        self.views: str = ""
        self.episodes_num: int = 0
        self.status: str = ""
        self.genres: List[str] = []
        self.rating: str = ""
        self.mal_url: Optional[str] = None
        self.anilist_url: Optional[str] = None
        self.html: str = ""

        self._episodes_cache: Optional[List[Episodio]] = None
        self._load_page()

    def _load_page(self) -> None:
        """Fetch HTML and parse anime details."""
        resp = SES.get(self.link)
        self.html = resp.text
        self._parse()

    @HealthCheck
    def _parse(self) -> None:
        """Parse anime metadata, locandina, and details from fetched HTML."""
        soup = BeautifulSoup(self.html, "html.parser")

        # 1. Check for 404 message
        if "Errore 404" in self.html or "Non trovato" in self.html:
            raise Error404(self.link)

        # 2. Extract JSON-LD schema for defaults (copertina, title, description)
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(s.string)
                if data.get("@type") in ("TVSeries", "Movie", "CreativeWork"):
                    self.name = data.get("name", "")
                    self.jtitle = data.get("alternateName", "")
                    self.copertina = data.get("image", "")
                    self.story = data.get("description", "")
                    break
            except Exception:
                continue

        # 3. Main Title from <h1>
        h1 = soup.find("h1")
        if h1:
            self.name = h1.text.strip()
        self.title = self.name

        # 4. Alternate Title from .ag-head p
        head = soup.find(class_=lambda c: c and "ag-head" in c)
        if head and head.find("p"):
            p_text = head.find("p").text.strip()
            if p_text and p_text != self.name:
                self.jtitle = p_text
        self.alternate_name = self.jtitle

        # 5. Locandina (Vertical Poster)
        locandina_url = ""
        poster_box = soup.find(class_=lambda c: c and any(k in c for k in ["ag-poster", "anime-poster-card"]))
        if poster_box and poster_box.find("img"):
            locandina_url = poster_box.find("img").get("src", "")

        if not locandina_url:
            # Fallback to any image containing locandine
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if "locandine" in src:
                    locandina_url = src
                    break

        self.locandina = locandina_url
        self.poster = locandina_url or self.copertina
        self.cover = self.copertina

        # 6. Background (Backdrop Hero Image)
        bg_el = soup.find(class_=lambda c: c and "anime-hero__bg" in c)
        if bg_el and bg_el.get("src"):
            self.background = bg_el["src"]
        else:
            self.background = self.copertina
        self.backdrop = self.background

        # 7. Full synopsis from .ag-story or #trama
        story_el = soup.find(class_=lambda c: c and "ag-story" in c) or soup.find(id="trama")
        if story_el:
            clean_story = story_el.text.replace("Trama", "").strip()
            if len(clean_story) > len(self.story):
                self.story = clean_story
        self.synopsis = self.story

        # 8. Genres from filter chips / links
        genres = []
        for a in soup.find_all("a", href=True):
            if "/filter?categories=" in a["href"]:
                g_text = a.text.strip()
                if g_text and g_text not in genres:
                    genres.append(g_text)
        self.genres = genres

        # 9. External database links (MyAnimeList & AniList)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "myanimelist.net/anime/" in href:
                self.mal_url = href
            elif "anilist.co/anime/" in href:
                self.anilist_url = href

        # 10. Parse detailed metadata rows from .ag-meta
        meta_box = soup.find(class_=lambda c: c and "ag-meta" in c)
        if meta_box:
            for row in meta_box.find_all(["a", "div"], recursive=False):
                raw_text = " ".join(row.text.strip().split())
                for key in ["Tipo", "Stagione", "Lingua", "Stato", "Studio", "Data di uscita", "Episodi", "Durata", "Visualizzazioni", "Voto"]:
                    if raw_text.startswith(key):
                        val = raw_text[len(key):].strip()
                        if key == "Tipo":
                            self.category = val
                        elif key == "Stagione":
                            self.season = val
                            # Extract year from season
                            y_m = re.search(r'\b(19\d\d|20\d\d)\b', val)
                            if y_m:
                                self.release = y_m.group(1)
                        elif key == "Lingua":
                            self.language = val
                        elif key == "Stato":
                            self.status = val
                        elif key == "Studio":
                            self.studio = val
                        elif key == "Data di uscita":
                            self.release_date = val
                        elif key == "Durata":
                            self.duration = val
                        elif key == "Visualizzazioni":
                            self.views = val
                        elif key == "Voto":
                            self.rating = val.split()[0] if val else ""
                        break

        # Fallback for rating from .ag-vote if not in .ag-meta
        if not self.rating:
            vote_box = soup.find(class_=lambda c: c and "ag-vote" in c)
            if vote_box:
                m_v = re.search(r'([\d\.]+)\s*/\s*10', vote_box.text)
                if m_v:
                    self.rating = m_v.group(1)

        # 11. Parse available episode links
        episodes: List[Episodio] = []
        seen_ep_numbers = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/episode/" in href or (f"/anime/{self.slug}/ep-" in href):
                ep_match = re.search(r'/ep-([a-zA-Z0-9\._\-]+)', href)
                if ep_match:
                    num_str = ep_match.group(1)
                    if num_str not in seen_ep_numbers:
                        seen_ep_numbers.add(num_str)
                        ep_obj = Episodio(
                            number=num_str,
                            anime_slug=self.slug,
                            link=href,
                            title=f"Episodio {num_str}"
                        )
                        episodes.append(ep_obj)

        def ep_sort_key(ep: Episodio):
            try:
                return float(ep.number)
            except ValueError:
                return 999999.0

        episodes.sort(key=ep_sort_key)
        self._episodes_cache = episodes
        self.episodes_num = len(episodes)

    def getEpisodes(self) -> List[Episodio]:
        """
        Get the list of all released episodes for this anime.

        Returns:
            List of Episodio objects.

        Raises:
            AnimeNotAvailable: If no episodes were found.
        """
        if self._episodes_cache is None:
            self._parse()

        if not self._episodes_cache:
            raise AnimeNotAvailable(self.name or self.slug)

        return self._episodes_cache

    @property
    def episodes(self) -> List[Episodio]:
        """Convenience property returning all episodes."""
        return self.getEpisodes()

    def __repr__(self) -> str:
        return f"<Anime title='{self.name}' locandina='{self.locandina}' episodes={self.episodes_num}>"
