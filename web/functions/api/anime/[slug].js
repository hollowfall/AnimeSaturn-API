const BASE_DOMAIN = "https://www.animesaturn.net";
const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

export async function onRequestGet(context) {
  const slug = context.params.slug;
  if (!slug) {
    return Response.json({ ok: false, error: "Missing anime slug" }, { status: 400 });
  }

  const cleanSlug = slug.replace(/^anime\//, "").replace(/\/$/, "");
  const targetUrl = `${BASE_DOMAIN}/anime/${cleanSlug}`;

  try {
    const res = await fetch(targetUrl, {
      headers: {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": `${BASE_DOMAIN}/`,
      },
    });

    if (!res.ok) {
      return Response.json(
        { ok: false, error: `Anime '${cleanSlug}' not found (status ${res.status})` },
        { status: res.status }
      );
    }

    const html = await res.text();

    const titleMatch = html.match(/<b[^>]*class="[^"]*box-anime-title[^"]*"[^>]*>([\s\S]*?)<\/b>/i) ||
                       html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
    const title = titleMatch ? titleMatch[1].replace(/<[^>]+>/g, "").trim() : cleanSlug;

    const posterMatch = html.match(/<img[^>]*class="[^"]*img-fluid[^"]*"[^>]*src="([^"]+)"/i);
    const poster = posterMatch ? posterMatch[1] : "";

    const storyMatch = html.match(/id="trama-anime"[^>]*>([\s\S]*?)<\/div>/i) ||
                       html.match(/<div[^>]*class="[^"]*card-body[^"]*"[^>]*>([\s\S]*?)<\/div>/i);
    const story = storyMatch ? storyMatch[1].replace(/<[^>]+>/g, "").trim() : "";

    const episodes = [];
    const epRegex = /href="(\/ep\/[^"]+|\/anime\/[^"]+\/ep-[^"]+)"[^>]*>([\s\S]*?)<\/a>/g;
    let match;
    while ((match = epRegex.exec(html)) !== null) {
      const epLink = match[1];
      const epText = match[2].replace(/<[^>]+>/g, "").trim();
      const numMatch = epLink.match(/ep-([0-9.]+)/i) || epText.match(/([0-9.]+)/);
      const num = numMatch ? numMatch[1] : String(episodes.length + 1);

      episodes.push({
        number: num,
        title: epText || `Episodio ${num}`,
        url: `${BASE_DOMAIN}${epLink.startsWith('/') ? epLink : '/' + epLink}`,
        link: epLink,
      });
    }

    return Response.json({
      ok: true,
      id: cleanSlug,
      title: title,
      poster: poster,
      locandina: poster,
      story: story,
      url: targetUrl,
      episodes_count: episodes.length,
      episodes: episodes,
    });
  } catch (err) {
    return Response.json(
      { ok: false, error: `Failed to fetch anime: ${err.message}` },
      { status: 500 }
    );
  }
}
