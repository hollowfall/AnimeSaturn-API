import os
import time
import threading
from typing import Dict, List, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class IPRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        self.last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()

        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip.strip()

        if request.client and request.client.host:
            return request.client.host

        return "unknown_client"

    def is_allowed(self, ip: str) -> Tuple[bool, int, int]:
        now = time.time()
        cutoff = now - self.window_seconds

        with self.lock:
            if now - self.last_cleanup > 60:
                self._cleanup(cutoff)
                self.last_cleanup = now

            timestamps = self.history.get(ip, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= self.limit:
                oldest_in_window = valid_timestamps[0]
                reset_seconds = max(1, int(oldest_in_window + self.window_seconds - now))
                self.history[ip] = valid_timestamps
                return False, 0, reset_seconds

            valid_timestamps.append(now)
            self.history[ip] = valid_timestamps
            remaining = max(0, self.limit - len(valid_timestamps))
            reset_seconds = int(self.window_seconds)
            return True, remaining, reset_seconds

    def _cleanup(self, cutoff: float):
        expired_ips = [ip for ip, timestamps in self.history.items() if not timestamps or timestamps[-1] <= cutoff]
        for ip in expired_ips:
            del self.history[ip]

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: IPRateLimiter, exempt_paths: List[str] = None):
        super().__init__(app)
        self.limiter = limiter
        self.exempt_paths = exempt_paths or ["/docs", "/openapi.json", "/redoc", "/favicon.ico"]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        ip = self.limiter.get_client_ip(request)
        allowed, remaining, reset_seconds = self.limiter.is_allowed(ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "ok": False,
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {self.limiter.limit} requests per minute.",
                    "client_ip": ip,
                    "retry_after_seconds": reset_seconds
                },
                headers={
                    "Retry-After": str(reset_seconds),
                    "X-RateLimit-Limit": str(self.limiter.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds)
                }
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)
        return response
