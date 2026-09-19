// GET /api/latest?page=[page]
const BASE_DOMAIN = "https://www.animesaturn.net";
const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const page = parseInt(url.searchParams.get("page") || "1", 10);

  try {
    const res = await fetch(`${BASE_DOMAIN}/`, {
      headers: {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      },
    });

    if (!res.ok) {
      return Response.json(
        { ok: false, error: `Failed to fetch latest releases (status ${res.status})` },
        { status: res.status }
      );
    }

    const html = await res.text();
    const items = [];
    const cardRegex = /<div class="col-6 col-sm-4 col-md-3 col-lg-2 mb-3">([\s\S]*?)<\/div>\s*<\/div>/g;
    let match;
    while ((match = cardRegex.exec(html)) !== null && items.length < 24) {
      const block = match[1];
      const linkMatch = block.match(/href="([^"]+)"/);
      const titleMatch = block.match(/title="([^"]+)"/) || block.match(/alt="([^"]+)"/);
      const imgMatch = block.match(/src="([^"]+)"/);
      const epMatch = block.match(/<span[^>]*class="[^"]*badge[^"]*"[^>]*>([\s\S]*?)<\/span>/);

      if (linkMatch && titleMatch) {
        items.push({
          title: titleMatch[1].trim(),
          url: linkMatch[1].startsWith("http") ? linkMatch[1] : `${BASE_DOMAIN}${linkMatch[1]}`,
          link: linkMatch[1],
          poster: imgMatch ? imgMatch[1] : "",
          episode: epMatch ? epMatch[1].replace(/<[^>]+>/g, "").trim() : ""
        });
      }
    }

    return Response.json({
      ok: true,
      page,
      count: items.length,
      releases: items
    });
  } catch (err) {
    return Response.json(
      { ok: false, error: `Error fetching latest releases: ${err.message}` },
      { status: 500 }
    );
  }
}
