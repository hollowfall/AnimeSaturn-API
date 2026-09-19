const BASE_DOMAIN = "https://www.animesaturn.net";
const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

export async function onRequestGet(context) {
  const { slug, number } = context.params;
  if (!slug || !number) {
    return Response.json(
      { ok: false, error: "Missing anime slug or episode number" },
      { status: 400 }
    );
  }

  const cleanSlug = slug.replace(/^anime\//, "").replace(/\/$/, "");
  const cleanNum = number.replace(/^ep-?/i, "");

  const watchUrl = `${BASE_DOMAIN}/api/watch/${cleanSlug}/ep-${cleanNum}`;
  try {
    const res = await fetch(watchUrl, {
      headers: {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Referer": `${BASE_DOMAIN}/`,
      },
    });

    if (!res.ok) {
      return Response.json(
        { ok: false, error: `Episode watch metadata not found (status ${res.status})` },
        { status: res.status }
      );
    }

    const data = await res.json();
    const rawServers = data.servers || [];

    const resolvedStreams = [];
    for (const s of rawServers) {
      const streamInfo = {
        name: s.name,
        embed_url: s.link,
        server_id: s.id,
        slug: s.slug,
        direct_stream_url: null,
      };

      if (s.link && s.link.includes("saturncdn.net")) {
        try {
          const embedRes = await fetch(s.link, {
            headers: {
              "User-Agent": USER_AGENT,
              "Referer": `${BASE_DOMAIN}/`,
            },
          });
          if (embedRes.ok) {
            const embedHtml = await embedRes.text();
            
            const fileMatch = embedHtml.match(/file:\s*["']([^"']+)["']/i) ||
                              embedHtml.match(/(https?:\/\/[^"'\s]+\.m3u8[^"'\s]*)/i);
            if (fileMatch) {
              streamInfo.direct_stream_url = fileMatch[1];
              streamInfo.is_hls = streamInfo.direct_stream_url.includes(".m3u8");
            }
          }
        } catch (err) {
          streamInfo.error = err.message;
        }
      }

      resolvedStreams.push(streamInfo);
    }

    return Response.json({
      ok: true,
      slug: cleanSlug,
      episode: cleanNum,
      title: data.title || `Episodio ${cleanNum}`,
      watch_url: `${BASE_DOMAIN}/anime/${cleanSlug}/ep-${cleanNum}`,
      streams: resolvedStreams
    });
  } catch (err) {
    return Response.json(
      { ok: false, error: `Stream resolution failed: ${err.message}` },
      { status: 500 }
    );
  }
}
