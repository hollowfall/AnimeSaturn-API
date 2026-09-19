// CORS Middleware for Cloudflare Pages Functions
export async function onRequest(context) {
  const { request, next } = context;

  // Handle CORS pre-flight
  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Max-Age": "86400",
      },
    });
  }

  const response = await next();
  const newResponse = new Response(response.body, response);
  newResponse.headers.set("Access-Control-Allow-Origin", "*");
  newResponse.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  newResponse.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
  newResponse.headers.set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
  newResponse.headers.set("Pragma", "no-cache");
  return newResponse;
}
