![AnimeSaturn](static/img/banner.png)

# AnimeSaturn-API

[![Version](https://img.shields.io/pypi/v/animesaturn)](https://pypi.org/project/animesaturn/)
[![Python Versions](https://img.shields.io/pypi/pyversions/animesaturn)](https://pypi.org/project/animesaturn/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/hollowfall/AnimeSaturn-API/blob/master/LICENSE)

**AnimeSaturn-API** is an unofficial, high-performance, and feature-complete Python library designed for scraping, querying, and downloading anime from [AnimeSaturn](https://www.animesaturn.net) and all its official mirrors.

Modeled with the familiar syntax and architectural philosophy of [AnimeWorld-API](https://github.com/MainKronos/AnimeWorld-API).

---

## Key Features

- **Fast Search & Discovery**: Direct access to AnimeSaturn's internal JSON API endpoints (`/api/search`, `/api/home/episodes`) with automatic fallback to HTML filters.
- **Smart Slug Resolution**: Search or access anime by slug, simple title, or full URL.
- **Multi-Domain & Mirrors Support**: Automatically checks and resolves active official domains via `https://www.animesaturn.me/` (`animesaturn.net`, `animesaturn.tv`, `animesaturn.in`, etc.).
- **Rich Metadata**: Extract titles, alternate Romaji/Japanese names, full Italian synopses, genres, release seasons, ratings, MAL/AniList links, and cover images.
- **Built-In Video Decryption**: Pure Python XOR decrypter for SaturnCDN / SaturnStream player links—no Selenium, Puppeteer, or headless browsers needed.
- **Concurrent HLS Downloader**: High-speed chunked streaming downloads for `.m3u8` playlists and `.ts` video chunks with auto-resume, customizable progress bars (`tqdm`), and interruptible callbacks.
- **Full CLI Tool**: Built-in `animesaturn` command-line utility for search, inspecting anime, viewing stream URLs, and direct downloads.

---

## Installation

Install the package via `pip`:

```bash
pip install animesaturn
```

To include documentation building tools:

```bash
pip install "animesaturn[docs]"
```

---

## Quick Example

```python
import animesaturn as asaturn

# Search for an anime
results = asaturn.find("Chainsaw Man")
print("First match:", results[0]["name"], results[0]["link"])

# Load anime details
anime = asaturn.Anime(results[0]["link"])
print(f"Title: {anime.name}")
print(f"Episodes count: {anime.episodes_num}")
print(f"Synopsis: {anime.story[:150]}...")

# Get episodes & stream link
episodes = anime.getEpisodes()
first_ep = episodes[0]
servers = first_ep.getServer()

print(f"Using server: {servers[0].name}")
direct_mp4_url = servers[0].fileLink()
print(f"Direct video stream: {direct_mp4_url}")

# Download episode 1
first_ep.download(folder="./downloads")
```

---

## License

This project is licensed under the [MIT License](https://github.com/MainKronos/AnimeSaturn-API/blob/master/LICENSE).
