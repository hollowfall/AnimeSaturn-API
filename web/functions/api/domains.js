// GET /api/domains
const OFFICIAL_DOMAINS = [
  "https://www.animesaturn.net",
  "https://www.animesaturn.cx",
  "https://www.animesaturn.tv",
  "https://www.animesaturn.in"
];

export async function onRequestGet() {
  return Response.json({
    ok: true,
    active_domain: OFFICIAL_DOMAINS[0],
    mirrors: OFFICIAL_DOMAINS
  });
}
