/**
 * Single-origin deployment server for sing-me-a-song.
 *
 * Serves the compiled front-end (front-end/build) and reverse-proxies the
 * API routes (/recommendations, /tests) to the back-end, so the whole app
 * is reachable through one origin — no CORS configuration and no absolute
 * API URL baked into the front-end bundle (build the front-end with
 * REACT_APP_API_BASE_URL= empty so axios uses same-origin relative URLs).
 *
 * Usage:
 *   node scripts/deploy-server.mjs
 *
 * Environment variables:
 *   DEPLOY_PORT  port to listen on            (default 8080)
 *   API_TARGET   back-end base URL to proxy   (default http://localhost:5000)
 *
 * Uses only the Node standard library — no dependencies to install.
 */
import http from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILD_DIR = path.join(__dirname, "..", "front-end", "build");
const PORT = Number(process.env.DEPLOY_PORT) || 8080;
const API_TARGET = new URL(process.env.API_TARGET || "http://localhost:5000");
const API_PREFIXES = ["/recommendations", "/tests", "/health"];

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".svg": "image/svg+xml",
  ".map": "application/json",
  ".txt": "text/plain; charset=utf-8",
};

function proxy(req, res) {
  const options = {
    hostname: API_TARGET.hostname,
    port: API_TARGET.port,
    path: req.url,
    method: req.method,
    headers: { ...req.headers, host: API_TARGET.host },
  };
  const upstream = http.request(options, (upstreamRes) => {
    res.writeHead(upstreamRes.statusCode, upstreamRes.headers);
    upstreamRes.pipe(res);
  });
  upstream.on("error", (err) => {
    console.error(`[proxy] ${req.method} ${req.url} -> ${err.message}`);
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "API upstream unavailable" }));
  });
  req.pipe(upstream);
}

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);
  let filePath = path.normalize(path.join(BUILD_DIR, urlPath));
  if (!filePath.startsWith(BUILD_DIR)) {
    res.writeHead(403);
    return res.end("Forbidden");
  }
  // SPA fallback: client-side routes (/top, /random) resolve to index.html
  if (!existsSync(filePath) || statSync(filePath).isDirectory()) {
    filePath = path.join(BUILD_DIR, "index.html");
  }
  res.writeHead(200, {
    "content-type": MIME[path.extname(filePath)] || "application/octet-stream",
  });
  createReadStream(filePath).pipe(res);
}

const server = http.createServer((req, res) => {
  if (API_PREFIXES.some((p) => req.url === p || req.url.startsWith(p + "/"))) {
    return proxy(req, res);
  }
  return serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(
    `deploy-server: serving ${BUILD_DIR} on http://localhost:${PORT}, proxying ${API_PREFIXES.join(", ")} -> ${API_TARGET.href}`
  );
});
