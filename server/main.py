import os
import asyncio
import logging
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List, Dict, Any

import animesaturn

logger = logging.getLogger("animesaturn.server")

async def keep_alive_worker():
    await asyncio.sleep(30)
    while True:
        url = os.getenv("KEEP_ALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL")
        if url:
            target = f"{url.rstrip('/')}/api/health"
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.get(target)
                    logger.info(f"[keep-alive] Self ping {target} returned {res.status_code}")
            except Exception as e:
                logger.warning(f"[keep-alive] Self ping to {target} failed: {e}")
        await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(keep_alive_worker())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="AnimeSaturn Live API",
    description="Real-time AnimeSaturn REST API service running live on Render.",
    version=animesaturn.__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
        "service": "AnimeSaturn Live API",
        "version": animesaturn.__version__,
        "status": "running",
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
def search(q: str = Query(..., description="Anime title or keyword")):
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty")
    try:
        results = animesaturn.find(query)
        return {
            "ok": True,
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/anime/{slug}")
def get_anime(slug: str):
    clean_slug = slug.strip("/").replace("anime/", "")
    try:
        anime = animesaturn.Anime(clean_slug)
        episodes = anime.getEpisodes()
        ep_list = [
            {
                "number": ep.number,
                "title": ep.title,
                "url": ep.url,
                "link": ep.link
            }
            for ep in episodes
        ]
        return {
            "ok": True,
            "id": anime.slug,
            "title": anime.name,
            "jtitle": anime.jtitle,
            "poster": anime.poster,
            "locandina": anime.locandina,
            "copertina": anime.copertina,
            "category": anime.category,
            "studio": anime.studio,
            "season": anime.season,
            "release": anime.release,
            "status": anime.status,
            "rating": anime.rating,
            "genres": anime.genres,
            "episodes_num": anime.episodes_num,
            "story": anime.story,
            "mal_url": anime.mal_url,
            "url": anime.url,
            "episodes_count": len(ep_list),
            "episodes": ep_list
        }
    except animesaturn.exceptions.AnimeSaturnError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch anime: {str(e)}")

@app.get("/api/episode/{slug}/{number}")
def get_episode(slug: str, number: str):
    clean_slug = slug.strip("/").replace("anime/", "")
    clean_num = number.replace("ep-", "")
    try:
        ep = animesaturn.Episodio(number=clean_num, anime_slug=clean_slug)
        servers = ep.getServer()
        return {
            "ok": True,
            "slug": clean_slug,
            "episode": clean_num,
            "title": ep.title,
            "watch_url": ep.url,
            "servers": [
                {
                    "name": s.name,
                    "link": s.link,
                    "id": s.id,
                    "slug": s.slug
                }
                for s in servers
            ]
        }
    except animesaturn.exceptions.AnimeSaturnError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch episode: {str(e)}")

@app.get("/api/stream/{slug}/{number}")
def get_stream(slug: str, number: str):
    clean_slug = slug.strip("/").replace("anime/", "")
    clean_num = number.replace("ep-", "")
    try:
        ep = animesaturn.Episodio(number=clean_num, anime_slug=clean_slug)
        servers = ep.getServer()
        if not servers:
            raise HTTPException(status_code=404, detail=f"No streaming servers found for {clean_slug} ep {clean_num}")

        streams = []
        for s in servers:
            stream_item = {
                "name": s.name,
                "embed_url": s.link,
                "server_id": s.id,
                "slug": s.slug,
                "direct_stream_url": None,
                "is_hls": False
            }
            try:
                direct = s.fileLink()
                stream_item["direct_stream_url"] = direct
                stream_item["is_hls"] = ".m3u8" in direct
            except Exception as err:
                stream_item["error"] = str(err)
            streams.append(stream_item)

        return {
            "ok": True,
            "slug": clean_slug,
            "episode": clean_num,
            "title": ep.title,
            "watch_url": ep.url,
            "streams": streams
        }
    except animesaturn.exceptions.AnimeSaturnError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt stream: {str(e)}")

@app.get("/api/latest")
def latest(page: int = Query(1, ge=1)):
    try:
        data = animesaturn.latest_episodes(page)
        return {
            "ok": True,
            "page": page,
            "count": len(data.get("items", [])),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest releases: {str(e)}")

@app.get("/api/domains")
def domains():
    try:
        return {
            "ok": True,
            "active_domain": animesaturn.get_domain(),
            "mirrors": animesaturn.fetch_official_domains()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch domains: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
