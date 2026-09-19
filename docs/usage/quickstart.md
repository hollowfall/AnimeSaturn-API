# QuickStart

This guide walks you through the essential operations of **AnimeSaturn-API**: searching for titles, inspecting series information, extracting episode stream URLs, and downloading videos.

---

## 1. Searching for Anime

You can search for any anime title using `animesaturn.find()`:

```python
import animesaturn as asaturn

# Search returns a list of dictionary results
results = asaturn.find("Bleach")

for anime_data in results:
    print(f"Title: {anime_data['name']}")
    print(f"Year: {anime_data['year']}")
    print(f"Type: {anime_data['type']}")
    print(f"Link: {anime_data['link']}")
    print(f"Genres: {', '.join(anime_data['genres'])}")
    print("-" * 40)
```

If you prefer `Anime` object instances directly, use `animesaturn.search()`:

```python
animes = asaturn.search("Bleach")
for anime in animes:
    print(anime.name, anime.episodes_num)
```

---

## 2. Inspecting Anime Metadata

Initialize an `Anime` object using either a relative URL path (e.g. `"/anime/one-piece-PmTvj"`), a full URL, or just the slug:

```python
import animesaturn as asaturn

anime = asaturn.Anime("one-piece-PmTvj")

print("Title:        ", anime.name)
print("Romaji Title: ", anime.jtitle)
print("Type:         ", anime.category)
print("Season:       ", anime.season)
print("Language:     ", anime.language)
print("Release Year: ", anime.release)
print("Status:       ", anime.status)
print("Rating:       ", anime.rating)
print("Total Eps:    ", anime.episodes_num)
print("MAL:          ", anime.mal_url)
print("AniList:      ", anime.anilist_url)
print("\nSynopsis:\n", anime.story)
```

---

## 3. Working with Episodes

Fetch the full list of episodes with `getEpisodes()`:

```python
episodes = anime.getEpisodes()
print(f"Retrieved {len(episodes)} episodes.")

first_episode = episodes[0]
print(f"Episode Number: {first_episode.number}")
print(f"Watch Link:     {first_episode.link}")
```

---

## 4. Extracting Video Stream Links

Each episode provides available hosting servers via `getServer()`:

```python
servers = first_episode.getServer()
server = servers[0]  # Primary SaturnCDN server

print(f"Server Name: {server.name}")

# Decrypt direct playable MP4 link
direct_url = server.fileLink()
print(f"Direct Stream URL: {direct_url}")

# Inspect file size and content type
info = server.fileInfo()
print(f"File size: {info['total_bytes'] / (1024 * 1024):.2f} MB")
print(f"MIME type: {info['content_type']}")
```

---

## 5. Downloading Episodes

Download an episode directly to any target folder:

```python
# Automatic progress bar in terminal
first_episode.download(folder="./downloads")

# Or download from a specific server
servers[0].download(folder="./downloads", filename="One_Piece_01.mp4")
```
