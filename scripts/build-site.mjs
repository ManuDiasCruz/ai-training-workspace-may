import { spawnSync } from "node:child_process";
import { cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const frontend = path.join(root, "front-end");
const reactScripts = path.join(
  frontend,
  "node_modules",
  "react-scripts",
  "bin",
  "react-scripts.js"
);

const frontendBuild = spawnSync(process.execPath, [reactScripts, "build"], {
  cwd: frontend,
  env: { ...process.env, REACT_APP_API_BASE_URL: "" },
  stdio: "inherit"
});

if (frontendBuild.status !== 0) {
  process.exit(frontendBuild.status ?? 1);
}

const output = path.join(root, "dist");

await rm(output, { recursive: true, force: true });
await mkdir(path.join(output, "server"), { recursive: true });
await mkdir(path.join(output, ".openai"), { recursive: true });
await cp(path.join(frontend, "build"), path.join(output, "client"), {
  recursive: true
});
await cp(path.join(root, "site", "worker.js"), path.join(output, "server", "index.js"));
await cp(
  path.join(root, ".openai", "hosting.json"),
  path.join(output, ".openai", "hosting.json")
);
await cp(path.join(root, "drizzle"), path.join(output, ".openai", "drizzle"), {
  recursive: true
});

console.log("Built the frontend and durable recommendation API for Sites.");
