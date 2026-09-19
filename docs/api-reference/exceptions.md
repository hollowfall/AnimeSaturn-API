# Exceptions

Overview of exceptions raised by **AnimeSaturn-API**. All library exceptions inherit from `AnimeSaturnError`.

---

## Exception Hierarchy

```text
AnimeSaturnError
├── Error404
├── AnimeNotAvailable
├── EpisodeNotFound
├── ServerNotSupported
├── DecryptionError
├── DownloadError
│   └── HardStoppedDownload
└── DeprecatedLibrary
```

---

## Reference

### `AnimeSaturnError`
Base class for all library exceptions. Catch this exception to handle any error raised by `animesaturn`.

```python
from animesaturn import AnimeSaturnError

try:
    # library calls
    pass
except AnimeSaturnError as err:
    print(f"AnimeSaturn error occurred: {err}")
```

---

### `Error404(url: str)`
Raised when an anime or episode page returns an HTTP 404 status.
- **Attributes**: `url` (*str*)

---

### `AnimeNotAvailable(anime_name: str)`
Raised when the requested anime does not contain any released episodes or has been taken down.
- **Attributes**: `anime_name` (*str*)

---

### `EpisodeNotFound(episode_number: str, anime_name: str)`
Raised when a requested episode number cannot be found within the anime's episode list.
- **Attributes**: `episode_number` (*str*), `anime_name` (*str*)

---

### `ServerNotSupported(server_name: str)`
Raised when attempting to stream or download from an unknown or unimplemented video hosting provider.
- **Attributes**: `server_name` (*str*)

---

### `DecryptionError(message: str)`
Raised when the player stream URL or token decryption fails (e.g. invalid token, expired link, or changed obfuscation routine).

---

### `DownloadError(message: str)`
Raised when an HTTP error or file writing error occurs during video streaming or saving.

---

### `HardStoppedDownload(message: str)`
Subclass of `DownloadError`. Raised when a user-supplied progress callback returns `False`, safely terminating the active download.

---

### `DeprecatedLibrary(file: str, function: str, line: int)`
Raised when structural HTML or API changes on AnimeSaturn cause parsing failures. This helps developers immediately identify broken selectors or endpoints.
- **Attributes**: `file` (*str*), `function` (*str*), `line` (*int*)
