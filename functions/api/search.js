const BASE_DOMAIN = "https://www.animesaturn.net";
const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const query = url.searchParams.get("q");

  if (!query || !query.trim()) {
    return Response.json(
      { ok: false, error: "Missing required query parameter 'q'" },
      { status: 400 }
    );
  }

  const upstreamUrl = `${BASE_DOMAIN}/api/search?q=${encodeURIComponent(query.trim())}`;
  try {
    const upstreamRes = await fetch(upstreamUrl, {
      headers: {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": `${BASE_DOMAIN}/`,
      },
    });

    if (!upstreamRes.ok) {
      return Response.json(
        { ok: false, error: `Upstream returned status ${upstreamRes.status}` },
        { status: upstreamRes.status }
      );
    }

    const data = await upstreamRes.json();
    const rawItems = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : []);

    const formatted = rawItems.map(item => {
      const rawUrl = item.url || "";
      const path = rawUrl.startsWith("/") ? rawUrl : "/" + rawUrl;
      const poster = item.poster || "";
      return {
        name: item.title || item.name || "",
        title: item.title || item.name || "",
        link: path,
        url: `${BASE_DOMAIN}${path}`,
        poster: poster,
        locandina: poster,
        year: item.year || "",
        episodes: item.episodes || "",
        type: item.type || "TV",
        genres: Array.isArray(item.genres)
          ? item.genres.map(g => (typeof g === "object" ? g.name : String(g)))
          : []
      };
    });

    return Response.json({
      ok: true,
      query: query.trim(),
      count: formatted.length,
      results: formatted
    });
  } catch (err) {
    return Response.json(
      { ok: false, error: `Search failed: ${err.message}` },
      { status: 500 }
    );
  }
}
