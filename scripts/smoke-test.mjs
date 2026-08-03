import assert from "node:assert/strict";

const baseUrl = (process.env.BASE_URL ?? "http://localhost:5000").replace(/\/$/, "");
const recommendation = {
  name: `Deployment smoke test ${Date.now()}`,
  youtubeLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
};

async function request(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, options);
  const type = response.headers.get("content-type") ?? "";
  const body = type.includes("application/json")
    ? await response.json()
    : await response.text();

  return { status: response.status, body };
}

const health = await request("/health");
assert.equal(health.status, 200, "The health endpoint must reach the database");
assert.equal(health.body.status, "ok");

const created = await request("/recommendations", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(recommendation)
});
assert.equal(created.status, 201, "The backend must create recommendations");
assert.equal(created.body.name, recommendation.name);

const duplicate = await request("/recommendations", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(recommendation)
});
assert.equal(duplicate.status, 409, "Duplicate recommendation names must conflict");

const listed = await request("/recommendations");
assert.equal(listed.status, 200);
assert.ok(listed.body.some((song) => song.id === created.body.id));

const upvote = await request(`/recommendations/${created.body.id}/upvote`, {
  method: "POST"
});
assert.equal(upvote.status, 200);

const afterUpvote = await request(`/recommendations/${created.body.id}`);
assert.equal(afterUpvote.body.score, 1);

const top = await request("/recommendations/top/10");
assert.equal(top.status, 200);
assert.ok(top.body.some((song) => song.id === created.body.id));

const random = await request("/recommendations/random");
assert.equal(random.status, 200);
assert.ok(random.body.id);

for (let count = 0; count < 7; count++) {
  const downvote = await request(`/recommendations/${created.body.id}/downvote`, {
    method: "POST"
  });
  assert.equal(downvote.status, 200);
}

const removed = await request(`/recommendations/${created.body.id}`);
assert.equal(removed.status, 404, "Scores below -5 must remove recommendations");

for (const route of ["/", "/top", "/random"]) {
  const page = await request(route);
  assert.equal(page.status, 200, `The ${route} frontend route must be reachable`);
  assert.match(page.body, /<div id="root"><\/div>/);
}

console.log(
  `Smoke test passed for ${baseUrl}: health, create, conflict, list, voting, top, random, removal, and SPA routes.`
);
