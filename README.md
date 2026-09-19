<div align="center">

[![AnimeSaturn](https://animesaturn.lawliet.lol/static/img/banner.png)](https://animesaturn.lawliet.lol/)

# AnimeSaturn-API

[![PyPI - Version](https://img.shields.io/pypi/v/animesaturn?logo=pypi&logoColor=white&color=blue)](https://pypi.org/project/animesaturn/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/animesaturn?logo=python&logoColor=white)](https://pypi.org/project/animesaturn/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/animesaturn?color=orange&logo=pypi&logoColor=white)](https://pypi.org/project/animesaturn/)
[![PyPI - Format](https://img.shields.io/pypi/format/animesaturn?logo=pypi&logoColor=white)](https://pypi.org/project/animesaturn/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/LICENSE)
[![Publish to PyPI](https://github.com/hollowfall/AnimeSaturn-API/actions/workflows/publish-pypi.yml/badge.svg)](https://pypi.org/project/animesaturn/)
[![Deploy MkDocs](https://github.com/hollowfall/AnimeSaturn-API/actions/workflows/deploy-mkdocs.yml/badge.svg)](https://animesaturn.lawliet.lol/)

[![Language - English](https://img.shields.io/badge/lang-english-%239FA8DA)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/README.md)
[![Language - Italiano](https://img.shields.io/badge/lang-italiano-%239FA8DA)](https://github.com/hollowfall/AnimeSaturn-API/blob/Main/README.it.md)

</div>

**AnimeSaturn-API** is an unofficial, high-performance Python library and CLI tool for scraping, querying metadata, and downloading anime from [AnimeSaturn](https://www.animesaturn.net) and all its official mirrors.

Designed with clean architecture and familiar patterns inspired by [AnimeWorld-API](https://github.com/MainKronos/AnimeWorld-API).

Read this documentation in:
- [English](README.md)
- [Italiano](README.it.md)

---

## Features

- **Instant Search**: Query titles through AnimeSaturn's fast internal JSON search endpoint with automatic filter fallback.
- **Smart Slug Resolution**: Look up anime by slug hash (`solo-leveling-6iHEN`), simple title (`solo-leveling`), or full URL.
- **Multi-Domain & Official Mirrors**: Auto-discovers and resolves active mirrors via `https://www.animesaturn.me/` (`animesaturn.net`, `animesaturn.tv`, `animesaturn.in`, etc.).
- **Comprehensive Metadata**: Extracts title, Romaji alternate name, synopsis, genres, release season, year, studio, language, score, MAL/AniList links, and high-resolution posters.
- **SaturnCDN Video Decryption**: Pure Python stream decryption without headless browsers or Node.js dependencies.
- **Concurrent HLS Downloader**: Multi-threaded downloader for `.m3u8` playlists and `.ts` video chunks with automatic highest-quality selection, retries, and clean progress reporting.
- **Graceful Interruption**: Safe cancellation on `Ctrl+C` or user callback hooks without terminal corruption or hanging processes.
- **Full CLI Suite**: Built-in `animesaturn` command-line utility for searching, inspecting metadata, viewing stream links, and downloading episodes.

---

## Installation

Install the stable release from PyPI:

```bash
pip install animesaturn
```

To include documentation building dependencies:

```bash
pip install "animesaturn[docs]"
```

---

## Quick Usage

### Search Anime

```python
import animesaturn

# Search anime titles
results = animesaturn.find("One Piece")
for item in results[:5]:
    print(f"{item['name']} ({item['year']}) -> {item['url']}")
```

### Anime Details & Metadata

```python
import animesaturn

# Initialize anime via slug, name, or URL
anime = animesaturn.Anime("solo-leveling")

print(f"Title:       {anime.name}")
print(f"Alt Title:   {anime.jtitle}")
print(f"Category:    {anime.category}")
print(f"Studio:      {anime.studio}")
print(f"Season/Year: {anime.season} ({anime.release})")
print(f"Status:      {anime.status}")
print(f"Rating:      {anime.rating}/10")
print(f"Genres:      {', '.join(anime.genres)}")
print(f"Episodes:    {anime.episodes_num}")
print(f"Poster:      {anime.poster}")
print(f"MAL Link:    {anime.mal_url}")
```

### Episode Access & Stream Extraction

```python
# Access episodes via indexing or method
first_ep = anime[1]  # or anime.get_episode(1)

print(f"Episode:   {first_ep.number} - {first_ep.title}")
print(f"Watch URL: {first_ep.url}")

# Retrieve available streaming servers
servers = first_ep.servers
server = servers[0]  # Server principale (SaturnStream)

print(f"Server:     {server.name}")
print(f"Player:     {server.link}")
print(f"Stream URL: {server.fileLink()}")
```

### Downloading Episodes

```python
# Download with built-in progress bar
first_ep.download(folder="./downloads")

# Custom progress hook callback
def on_progress(current_bytes, total_bytes, percentage):
    print(f"Progress: {percentage:.1f}% ({current_bytes}/{total_bytes} bytes)", end="\r")
    return True  # Return False to cleanly abort download

first_ep.download(folder="./downloads", hook=on_progress)
```

---

## Multi-Domain Management

```python
import animesaturn

# Current active base domain
print("Active domain:", animesaturn.get_domain())

# Discover all registered official mirrors
mirrors = animesaturn.fetch_official_domains()
print("Mirrors:", mirrors)

# Test and switch to the fastest active mirror
fastest = animesaturn.discover_active_domain()
print("Fastest mirror set to:", fastest)

# Or manually set a custom mirror
animesaturn.set_domain("https://www.animesaturn.tv")
```

---

## Command Line Interface (CLI)

The package provides a built-in CLI executable (`animesaturn` or `python animesaturn`):

| Command | Description | Example |
| :--- | :--- | :--- |
| `search` | Search anime by keyword | `animesaturn search "Naruto"` |
| `info` | View anime metadata and episode numbers | `animesaturn info "solo-leveling"` |
| `episode` / `ep` | Display episode details and stream URLs | `animesaturn ep "solo-leveling" 1` |
| `download` | Download episode video with progress bar | `animesaturn download "solo-leveling" -e 1 -o ./downloads` |
| `latest` | Show latest released anime episodes | `animesaturn latest --page 1` |
| `domains` | Discover and test official mirrors | `animesaturn domains` |

### CLI Examples

```bash
# Search anime
animesaturn search "Bleach"

# Inspect anime details
animesaturn info "bleach-sennen-kessen-hen-52Qxu"

# Display episode stream links
animesaturn ep "solo-leveling" 1

# Download episode
animesaturn download "solo-leveling" -e 1 -s 0 -o ./downloads

# List latest releases
animesaturn latest -p 1
```

---

## Documentation

Full documentation with guides and API references is available at [https://animesaturn.lawliet.lol/](https://animesaturn.lawliet.lol/).

To run documentation locally:

```bash
mkdocs serve
```

---

## Disclaimer

This is an unofficial, community-driven project. It is not affiliated with, endorsed by, or connected to AnimeSaturn.

## License

Distributed under the [MIT License](LICENSE).

---

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=hollowfall/animesaturn-api&type=Date&legend=bottom-right)](https://star-history.com/#hollowfall/animesaturn-api&Date)

</div>