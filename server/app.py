import os
import sys

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SERVER_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List, Dict, Any
import uvicorn

import animesaturn

app = FastAPI(
    title="AnimeSaturn Live Machine API",
    description="Real-time AnimeSaturn REST API service running on VPS machine.",
    version=animesaturn.__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response

app.add_middleware(NoCacheMiddleware)

@app.get("/")
def root():
    return {
        "service": "AnimeSaturn Live Machine API",
        "version": animesaturn.__version__,
        "status": "online",
        "docs": "/docs",
        "active_domain": animesaturn.get_domain(),
        "endpoints": [
            "/api/search?q={query}",
            "/api/anime/{slug}",
            "/api/episode/{slug}/{number}",
            "/api/stream/{slug}/{number}",
            "/api/latest?page={page}",
            "/api/domains",
            "/api/health"
        ]
    }

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "status": "healthy",
        "version": animesaturn.__version__,
        "domain": animesaturn.get_domain()
    }

@app.get("/api/search")
def search_anime(q: str = Query(..., description="Anime title to search (e.g. Solo Leveling, Naruto)")):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Missing required query parameter 'q'")
    try:
        results = animesaturn.find(q.strip())
        return {
            "ok": True,
            "query": q.strip(),
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/anime/{slug:path}")
def get_anime_details(slug: str):
    clean_slug = slug.strip("/").replace("anime/", "")
    try:
        anime = animesaturn.Anime(clean_slug)
        episodes_list = []
        for ep in anime:
            episodes_list.append({
                "number": ep.number,
                "url": ep.url,
                "is_full": ep.is_full,
                "range": ep.range
            })

        return {
            "ok": True,
            "slug": clean_slug,
            "title": anime.title,
            "jtitle": getattr(anime, "jtitle", ""),
            "url": anime.url,
            "poster": getattr(anime, "poster", ""),
            "locandina": getattr(anime, "poster", ""),
            "story": getattr(anime, "story", ""),
            "category": getattr(anime, "category", ""),
            "status": getattr(anime, "status", ""),
            "studio": getattr(anime, "studio", ""),
            "year": getattr(anime, "year", ""),
            "episodes_count": len(anime),
            "episodes": episodes_list
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Anime '{clean_slug}' not found or failed to parse: {str(e)}")

@app.get("/api/episode/{slug:path}/{number}")
def get_episode_servers(slug: str, number: int):
    clean_slug = slug.strip("/").replace("anime/", "")
    try:
        anime = animesaturn.Anime(clean_slug)
        ep = anime[number]
        servers = ep.getServer()
        server_list = []
        for s in servers:
            server_list.append({
                "name": s.name,
                "url": s.url
            })

        return {
            "ok": True,
            "anime": clean_slug,
            "episode": number,
            "episode_url": ep.url,
            "servers": server_list
        }
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Episode {number} does not exist for '{clean_slug}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch servers: {str(e)}")

@app.get("/api/stream/{slug:path}/{number}")
def get_episode_stream(slug: str, number: int):
    clean_slug = slug.strip("/").replace("anime/", "")
    try:
        anime = animesaturn.Anime(clean_slug)
        ep = anime[number]
        servers = ep.getServer()
        stream_results = []
        for s in servers:
            try:
                stream_url = s.fileLink()
                stream_results.append({
                    "server_name": s.name,
                    "server_url": s.url,
                    "stream_url": stream_url
                })
            except Exception as stream_err:
                stream_results.append({
                    "server_name": s.name,
                    "server_url": s.url,
                    "stream_url": None,
                    "error": str(stream_err)
                })

        return {
            "ok": True,
            "anime": clean_slug,
            "episode": number,
            "streams": stream_results
        }
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Episode {number} not found for '{clean_slug}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream resolution failed: {str(e)}")

@app.get("/api/latest")
def get_latest(page: int = Query(1, ge=1)):
    try:
        latest = animesaturn.latest_episodes(page=page)
        return {
            "ok": True,
            "page": page,
            "data": latest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest releases: {str(e)}")

@app.get("/api/domains")
def get_domains():
    try:
        mirrors = animesaturn.fetch_official_domains()
        active = animesaturn.discover_active_domain()
        return {
            "ok": True,
            "active_domain": active,
            "mirrors": mirrors
        }
    except Exception as e:
        return {
            "ok": False,
            "active_domain": animesaturn.get_domain(),
            "mirrors": [animesaturn.get_domain()],
            "error": str(e)
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting AnimeSaturn Machine API on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
