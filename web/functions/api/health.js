export async function onRequestGet() {
  return Response.json({
    ok: true,
    service: "AnimeSaturn Real-Time Edge API",
    version: "1.0.3",
    timestamp: new Date().toISOString(),
    endpoints: [
      "/api/search?q={query}",
      "/api/anime/{slug}",
      "/api/episode/{slug}/{number}",
      "/api/stream/{slug}/{number}",
      "/api/latest?page={page}",
      "/api/domains",
      "/api/health"
    ]
  });
}
