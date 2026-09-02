import { setTimeout } from 'node:timers/promises';
for (const url of process.argv.slice(2)) {
  let ready = false;
  const deadline = Date.now() + 120000;
  while (Date.now() < deadline) {
    try { if ((await fetch(url, { signal: AbortSignal.timeout(5000) })).ok) { ready = true; break; } } catch {}
    await setTimeout(1000);
  }
  if (!ready) throw new Error(`Service did not become ready: ${url}`);
}
