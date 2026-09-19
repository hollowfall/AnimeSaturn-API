# Developer Interface

Detailed API reference for all public functions, classes, and attributes in **AnimeSaturn-API**.

---

## Top-Level Functions

### `find(keyword: str) -> List[Dict[str, Any]]`

Searches AnimeSaturn by keyword and returns a list of matching result dictionaries.

- **Parameters**:
  - `keyword` (*str*): The search term (e.g. `"Naruto"`).
- **Returns**:
  - *List[Dict[str, Any]]*: List of result dictionaries containing `name`, `link`, `url`, `poster`, `year`, `episodes`, `type`, and `genres`.

---

### `search(keyword: str) -> List[Anime]`

Searches AnimeSaturn and returns initialized `Anime` class instances.

- **Parameters**:
  - `keyword` (*str*): The search term.
- **Returns**:
  - *List[Anime]*: List of initialized `Anime` objects.

---

### `latest_episodes(page: int = 1) -> Dict[str, Any]`

Fetches the newest released episodes on AnimeSaturn with pagination data.

- **Parameters**:
  - `page` (*int*): Page number (starts at 1).
- **Returns**:
  - *Dict[str, Any]*: Dictionary with keys `items`, `page`, `pages`, `total`, `hasPrev`, `hasNext`.

---

### Domain Helpers

- **`get_domain() -> str`**: Returns the active base domain URL.
- **`set_domain(domain_url: str) -> None`**: Manually sets the base domain.
- **`fetch_official_domains(timeout: float = 6.0) -> List[str]`**: Scrapes active official domains from `https://www.animesaturn.me/`.
- **`discover_active_domain(timeout: float = 4.0) -> str`**: Tests official candidate mirrors and sets the fastest responding domain.

---

## Class: `Anime`

Represents an anime series or film.

```python
Anime(link: str)
```

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `name` / `title` | `str` | Primary anime title. |
| `jtitle` / `alternate_name` | `str` | Japanese or Romaji alternate title. |
| `story` / `synopsis` | `str` | Plot summary in Italian. |
| `poster` | `str` | Direct URL to high-resolution poster image. |
| `category` | `str` | Release type (`TV`, `Movie`, `OVA`, `ONA`). |
| `season` | `str` | Season of release (e.g. `"Estate 2026"`). |
| `language` | `str` | Audio/sub language (`"Giapponese"`, `"Italiano"`). |
| `release` | `str` | Year of release. |
| `episodes_num` | `int` | Total count of released episodes. |
| `status` | `str` | Release status (`"In corso"`, `"Finito"`). |
| `genres` | `List[str]` | List of anime genre tags. |
| `rating` | `str` | Community rating score out of 10. |
| `mal_url` | `Optional[str]` | MyAnimeList URL if available. |
| `anilist_url` | `Optional[str]` | AniList URL if available. |
| `link` | `str` | Relative page path (e.g. `"/anime/one-piece-PmTvj"`). |
| `slug` | `str` | URL slug identifier. |

### Methods

#### `getEpisodes() -> List[Episodio]`
Fetches and returns the list of all available `Episodio` objects, sorted in numeric order.

---

## Class: `Episodio`

Represents an individual anime episode.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `number` | `str` | Episode number string (e.g. `"1"`, `"12"`, `"5.5"`). |
| `title` | `str` | Episode display label. |
| `anime_slug` | `str` | Parent anime slug identifier. |
| `link` | `str` | Relative web streaming path. |
| `servers` / `links` | `List[Server]` | Video hosting servers providing streams. |

### Methods

#### `getServer() -> List[Server]`
Retrieves the list of `Server` instances offering video playback for this episode.

#### `download(folder=".", title=None, server_index=0, hook=None) -> bool`
Downloads the episode video file directly to the specified `folder`.

---

## Class: `Server`

Base class for video hosting providers (`SaturnStream`, `StreamTape`, `MixDrop`).

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | Provider name (`"Server principale"`, `"StreamTape"`). |
| `link` | `str` | Video embed URL. |
| `id` | `int` | Server provider ID. |
| `number` | `str` | Episode number. |

### Methods

#### `fileLink() -> str`
Extracts and decrypts the direct playable video stream URL (`.mp4` / `.m3u8`).

#### `fileInfo() -> Dict[str, Any]`
Fetches file metadata including `content_type`, `total_bytes`, and `url`.

#### `download(folder=".", filename=None, hook=None, chunk_size=1048576, resume=True) -> bool`
Streams and writes the video file to disk with automatic resumption and progress reporting.
