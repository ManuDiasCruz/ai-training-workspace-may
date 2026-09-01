import assert from 'node:assert/strict';

const origin = process.env.SMOKE_BASE_URL || 'http://localhost:5000';
const name = `Smoke test ${Date.now()}`;
let id;
const request = (path, options) => fetch(new URL(path, origin), { signal: AbortSignal.timeout(30000), ...options });
try {
  assert.equal((await request('/health')).status, 200);
  for (const path of ['/', '/top', '/random']) {
    const page = await request(path);
    assert.equal(page.status, 200, path);
    assert.match(await page.text(), /<div id="root"><\/div>/, path);
  }
  assert.equal((await request('/tests/reset', { method: 'DELETE' })).status, 404);
  const create = await request('/recommendations', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, youtubeLink: 'https://youtu.be/qmUQr3zrqXM' }),
  });
  assert.equal(create.status, 201);
  id = (await create.json()).id;
  assert.equal((await request(`/recommendations/${id}/upvote`, { method: 'POST' })).status, 200);
  assert.equal((await (await request(`/recommendations/${id}`)).json()).score, 1);
  const list = await (await request('/recommendations')).json();
  assert.ok(list.some(song => song.id === id));
  assert.equal((await request('/recommendations/random')).status, 200);
  const top = await (await request('/recommendations/top/10')).json();
  assert.ok(top.every((song, i) => i === 0 || top[i - 1].score >= song.score));
  console.log('PASS: production routes, database health, create, list, vote, top, random, and reset-route protection.');
} finally {
  // Delete only this script's uniquely named record using the public voting rule.
  if (id) {
    for (let count = 0; count < 10; count++) {
      const current = await request(`/recommendations/${id}`);
      if (current.status === 404) break;
      assert.equal(current.status, 200);
      assert.equal((await current.json()).name, name);
      assert.equal((await request(`/recommendations/${id}/downvote`, { method: 'POST' })).status, 200);
    }
    assert.equal((await request(`/recommendations/${id}`)).status, 404);
    console.log('PASS: downvote removal; smoke record cleaned up.');
  }
}
