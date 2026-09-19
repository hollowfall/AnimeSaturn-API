# Advanced Usage

This guide covers advanced capabilities of **AnimeSaturn-API**, including multi-domain discovery, custom download progress callbacks, batch downloads, and the command line tool.

---

## 1. Multi-Domain & Mirror Management

AnimeSaturn maintains several mirrors to bypass geographic or provider blocks. You can manage and auto-discover them easily:

```python
import animesaturn as asaturn

# Check which domain is currently in use
print("Current domain:", asaturn.get_domain())

# Scrape the official list of mirrors from https://www.animesaturn.me/
mirrors = asaturn.fetch_official_domains()
print("Discovered official mirrors:", mirrors)

# Automatically ping candidate domains and pick the fastest active mirror
active_mirror = asaturn.discover_active_domain(timeout=4.0)
print("Switched to fastest domain:", active_mirror)

# Manually pin a specific mirror
asaturn.set_domain("https://www.animesaturn.tv")
```

---

## 2. Custom Download Progress Hooks

You can pass a custom progress hook to `download()` to integrate with GUI applications, logs, or custom terminal displays:

```python
import animesaturn as asaturn

def progress_callback(downloaded_bytes: int, total_bytes: int, percentage: float) -> bool:
    print(f"Downloaded: {downloaded_bytes} / {total_bytes} bytes ({percentage:.2f}%)")
    
    # Return False at any time to abort the download safely
    # For example, cancel if user clicked cancel button in GUI:
    # if user_cancelled:
    #     return False
    
    return True

anime = asaturn.Anime("dara-san-of-reiwa-764Qf")
episodes = anime.getEpisodes()

# Download with custom hook
episodes[0].download(
    folder="./downloads",
    title="MyEpisode.mp4",
    hook=progress_callback
)
```

---

## 3. Batch Downloading Episodes

Download a range of episodes with simple Python loops:

```python
import animesaturn as asaturn
import time

anime = asaturn.Anime("chainsaw-man-L5TgZ")
episodes = anime.getEpisodes()

# Download episodes 1 through 5
for ep in episodes[:5]:
    print(f"Downloading Episode {ep.number}...")
    try:
        ep.download(folder="./anime_library/Chainsaw_Man")
        print(f"Finished Episode {ep.number}")
    except Exception as err:
        print(f"Failed Episode {ep.number}: {err}")
    time.sleep(1.0) # Polite pacing between requests
```

---

## 4. Latest Episodes Feed

Fetch the latest released episodes across the entire AnimeSaturn site with pagination:

```python
import animesaturn as asaturn

# Get page 1 of newest episode updates
feed = asaturn.latest_episodes(page=1)

print(f"Page {feed['page']} of {feed['pages']} (Total updates: {feed['total']})")

for ep_item in feed["items"]:
    print(f"Anime:   {ep_item['title']}")
    print(f"Episode: {ep_item['episodeLabel']}")
    print(f"Type:    {ep_item['type']}")
    print(f"Link:    {ep_item['url']}")
    print("-" * 30)
```

---

## 5. Command Line Interface (CLI)

The package installs the `animesaturn` CLI executable:

```bash
# Search for anime
animesaturn search "Bleach"

# Inspect anime details
animesaturn info "bleach-ita-mp1vQ"

# Download a specific episode
animesaturn download "bleach-ita-mp1vQ" --ep 1 --folder ./downloads

# Check latest releases
animesaturn latest --page 1

# List official mirrors and check fastest domain
animesaturn domains
```
