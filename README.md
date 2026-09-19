<div align="center">

[![AnimeSaturn](https://github.com/hollowfall/AnimeSaturn-API/blob/master/docs/static/img/banner.png)](https://hollowfall.github.io/AnimeSaturn-API/)

# AnimeSaturn-API

[![PyPI](https://img.shields.io/pypi/v/animesaturn?color=blue)](https://pypi.org/project/animesaturn/)
[![Python](https://img.shields.io/pypi/pyversions/animesaturn)](https://pypi.org/project/animesaturn/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/hollowfall/AnimeSaturn-API/blob/master/LICENSE)
[![Deploy MkDocs](https://github.com/hollowfall/AnimeSaturn-API/actions/workflows/deploy-mkdocs.yml/badge.svg)](https://hollowfall.github.io/AnimeSaturn-API/)

</div>

**AnimeSaturn-API** is an unofficial, modern, and high-performance Python package for searching, extracting metadata, and downloading anime from [AnimeSaturn](https://www.animesaturn.net) and all its official mirrors.

Built to provide the same ease of use and clean architecture as [AnimeWorld-API](https://github.com/MainKronos/AnimeWorld-API).

Read this in:
- [English](README.md)
- [Italiano](README.it.md)

---

## Features

- 🔍 **Instant Search**: Direct query through AnimeSaturn's fast JSON search endpoint.
- 🌐 **Multi-Domain & Official Mirrors**: Auto-discovers and resolves working mirrors via `https://www.animesaturn.me/` (`animesaturn.net`, `animesaturn.tv`, `animesaturn.in`, etc.).
- 📑 **Comprehensive Metadata**: Title, Romaji/alternate name, plot, genres, season, language, rating, MAL/AniList links, cover image.
- 🔓 **SaturnCDN Video Decryption**: Built-in pure Python XOR decryption for SaturnCDN video streams—no browser automation needed.
- 📥 **Built-in Downloader**: High-performance chunked file downloads with auto-resume, progress bar support (`tqdm`), and custom progress hooks.
- ⌨️ **CLI Utility**: Built-in `animesaturn` command line interface for direct searching, info inspection, and downloading.

---

## Installation

```bash
pip install animesaturn
```

To install with MkDocs documentation dependencies:

```bash
pip install "animesaturn[docs]"
```

---

## Quick Usage

### Search Anime

```python
import animesaturn as asaturn

# Search for anime by keyword
results = asaturn.find("One Piece")
for item in results[:5]:
    print(f"{item['name']} ({item['year']}) -> {item['link']}")
```

### Anime Details & Metadata

```python
import animesaturn as asaturn

# Initialize anime from link or slug
anime = asaturn.Anime("one-piece-PmTvj")

print(f"Title:       {anime.name}")
print(f"Alt Title:   {anime.jtitle}")
print(f"Category:    {anime.category}")
print(f"Season/Year: {anime.season} ({anime.release})")
print(f"Status:      {anime.status}")
print(f"Rating:      {anime.rating}/10")
print(f"Genres:      {', '.join(anime.genres)}")
print(f"MAL Link:    {anime.mal_url}")
print(f"Synopsis:    {anime.story}")
```

### Episode Listing & Direct Stream Link

```python
# Get list of episodes
episodes = anime.getEpisodes()
print(f"Total episodes: {len(episodes)}")

first_ep = episodes[0]
print(f"Episode: {first_ep.number}")

# Retrieve server providers
servers = first_ep.getServer()
server = servers[0] # Server principale (SaturnStream)

# Get direct .mp4 streaming link
stream_url = server.fileLink()
print(f"Direct stream URL: {stream_url}")

# File info
info = server.fileInfo()
print(f"File size: {info['total_bytes'] / (1024*1024):.2f} MB")
```

### Downloading Episodes

```python
# Simple download with terminal progress bar
first_ep.download(folder="./downloads")

# Custom progress hook callback
def my_hook(current, total, percentage):
    print(f"Progress: {percentage:.1f}% ({current}/{total} bytes)", end="\r")
    return True # Return False to abort download

first_ep.download(folder="./downloads", hook=my_hook)
```

---

## Multi-Domain Management

```python
import animesaturn as asaturn

# View current active domain
print("Active domain:", asaturn.get_domain())

# Fetch all official mirrors from animesaturn.me
domains = asaturn.fetch_official_domains()
print("Official mirrors:", domains)

# Automatically find and switch to the fastest active domain
active = asaturn.discover_active_domain()
print("Fastest active domain set to:", active)

# Manually pin a custom domain
asaturn.set_domain("https://www.animesaturn.tv")
```

---

## CLI Usage

```bash
# Search anime
animesaturn search "Naruto"

# Show anime info
animesaturn info "naruto-shippuden-ita-PjvU1"

# Show latest released episodes
animesaturn latest --page 1

# Download episode 1
animesaturn download "naruto-shippuden-ita-PjvU1" --ep 1 --folder ./downloads

# Check official domains and mirrors
animesaturn domains
```

---

## Documentation

Full documentation is available at [https://mainkronos.github.io/AnimeSaturn-API/](https://mainkronos.github.io/AnimeSaturn-API/) or locally with:

```bash
mkdocs serve
```

---

## Disclaimer

This is an unofficial library. It is not affiliated with, endorsed by, or connected to AnimeSaturn.

## License

Released under the [MIT License](LICENSE).
