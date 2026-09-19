import os
import sys
import time
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List, Dict, Any

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SERVER_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

import animesaturn

try:
    from server import domain
    from server.rate_limiter import IPRateLimiter, RateLimitMiddleware
except ImportError:
    import domain
    from rate_limiter import IPRateLimiter, RateLimitMiddleware

app = FastAPI(
    title="AnimeSaturn Live Machine API",
    description="Real-time AnimeSaturn REST API service.",
    version=animesaturn.__version__,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limit_rpm = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
limiter = IPRateLimiter(limit=rate_limit_rpm, window_seconds=60)
app.add_middleware(RateLimitMiddleware, limiter=limiter, exempt_paths=["/api/health", "/api/domain"])

class SecurityAndTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response

app.add_middleware(SecurityAndTimingMiddleware)

@app.get("/")
def root(request: Request):
    sub = domain.get_or_create_subdomain()
    url = domain.get_public_url()
    client_ip = limiter.get_client_ip(request)
    return {
        "service": "saturn_api",
        "status": "online",
        "version": animesaturn.__version__,
        "client_ip": client_ip,
        "rate_limit_per_minute": rate_limit_rpm,
        "domain": url,
        "subdomain": sub,
        "persistent": True,
        "active_source_domain": animesaturn.get_domain(),
        "endpoints": [
            "/api/health",
            "/api/domain",
            "/api/search?q={query}",
            "/api/anime/{slug}",
            "/api/episode/{slug}/{number}",
            "/api/stream/{slug}/{number}",
            "/api/latest?page={page}",
            "/api/domains"
        ]
    }

@app.get("/api/health")
def health(request: Request):
    return {
        "ok": True,
        "status": "healthy",
        "version": animesaturn.__version__,
        "client_ip": limiter.get_client_ip(request),
        "domain": animesaturn.get_domain()
    }

@app.get("/api/domain")
def get_machine_domain():
    sub = domain.get_or_create_subdomain()
    url = domain.get_public_url()
    return {
        "ok": True,
        "subdomain": sub,
        "public_url": url,
        "persistent": True,
        "storage": "saturn_api/.domain"
    }

@app.get("/api/search")
def search_anime(q: str = Query(..., description="Anime title to search")):
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
    port = int(os.getenv("PORT", "9483"))
    host = os.getenv("HOST", "0.0.0.0")
    subdomain = domain.get_or_create_subdomain()
    public_url = domain.get_public_url()

    provider = os.getenv("TUNNEL_PROVIDER", "serveo")
    enable_tunnel = os.getenv("ENABLE_TUNNEL", "0").lower() in ("1", "true", "yes") or "--tunnel" in sys.argv

    if enable_tunnel:
        domain.start_tunnel_process(port=port, provider=provider)

    uvicorn.run("app:app", host=host, port=port, reload=False)
