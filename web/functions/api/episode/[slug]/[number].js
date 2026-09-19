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

  const cleanSlug = slug.replace(/^anime\
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
        { ok: false, error: `Episode not found (status ${res.status})` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return Response.json({
      ok: true,
      slug: cleanSlug,
      episode: cleanNum,
      title: data.title || `Episodio ${cleanNum}`,
      watch_url: `${BASE_DOMAIN}/anime/${cleanSlug}/ep-${cleanNum}`,
      servers: (data.servers || []).map(s => ({
        name: s.name,
        link: s.link,
        id: s.id,
        slug: s.slug
      }))
    });
  } catch (err) {
    return Response.json(
      { ok: false, error: `Failed to fetch episode: ${err.message}` },
      { status: 500 }
    );
  }
}
