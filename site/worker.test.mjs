import assert from "node:assert/strict";
import test from "node:test";
import worker from "./worker.js";

function createEnvironment() {
  const songs = [];
  let nextId = 1;

  return {
    ASSETS: {
      async fetch(request) {
        return new URL(request.url).pathname === "/index.html"
          ? new Response('<div id="root"></div>', { status: 200 })
          : new Response("Not found", { status: 404 });
      }
    },
    DB: {
      prepare(sql) {
        let bindings = [];

        return {
          bind(...values) {
            bindings = values;
            return this;
          },
          async run() {
            if (sql.startsWith("DELETE")) {
              const index = songs.findIndex((song) => song.id === bindings[0]);
              if (index >= 0) songs.splice(index, 1);
            }

            return { success: true };
          },
          async first() {
            if (sql.startsWith("INSERT")) {
              if (songs.some((song) => song.name === bindings[0])) {
                throw new Error("UNIQUE constraint failed: recommendations.name");
              }

              const song = {
                id: nextId++,
                name: bindings[0],
                youtubeLink: bindings[1],
                score: 0
              };
              songs.push(song);
              return { ...song };
            }

            if (sql.startsWith("UPDATE")) {
              const song = songs.find((item) => item.id === bindings[1]);
              if (!song) return null;
              song.score += bindings[0];
              return { ...song };
            }

            const song = songs.find((item) => item.id === bindings[0]);
            return song ? { ...song } : null;
          },
          async all() {
            let results = [...songs];

            if (sql.includes("WHERE score >")) {
              results = results.filter((song) => song.score > bindings[0]);
            } else if (sql.includes("WHERE score <=")) {
              results = results.filter((song) => song.score <= bindings[0]);
            }

            results.sort((left, right) =>
              sql.includes("ORDER BY score")
                ? right.score - left.score || right.id - left.id
                : right.id - left.id
            );

            const limit = sql.includes("LIMIT ?") ? bindings.at(-1) : 10;
            return { results: results.slice(0, limit).map((song) => ({ ...song })) };
          }
        };
      }
    }
  };
}

async function request(environment, pathname, init = {}) {
  return worker.fetch(new Request(`https://songs.example${pathname}`, init), environment);
}

test("hosted health checks and empty random recommendations", async () => {
  const environment = createEnvironment();

  assert.deepEqual(await (await request(environment, "/health")).json(), {
    status: "ok"
  });
  assert.equal((await request(environment, "/recommendations/random")).status, 404);
});

test("hosted recommendations support creation, conflicts, listing, and ranking", async () => {
  const environment = createEnvironment();
  const song = {
    name: "A hosted song",
    youtubeLink: "https://youtu.be/abcdefghijk"
  };
  const options = {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(song)
  };

  const created = await request(environment, "/recommendations", options);
  assert.equal(created.status, 201);
  const recommendation = await created.json();
  assert.equal(recommendation.score, 0);

  assert.equal((await request(environment, "/recommendations", options)).status, 409);
  assert.equal(
    (await (await request(environment, "/recommendations")).json()).length,
    1
  );
  assert.equal(
    (await (await request(environment, "/recommendations/top/10")).json())[0].id,
    recommendation.id
  );
  assert.equal((await request(environment, "/recommendations/random")).status, 200);

  assert.equal(
    (await request(environment, `/recommendations/${recommendation.id}/upvote`, {
      method: "POST"
    })).status,
    200
  );
  const upvoted = await request(environment, `/recommendations/${recommendation.id}`);
  assert.equal((await upvoted.json()).score, 1);

  for (let count = 0; count < 7; count++) {
    assert.equal(
      (await request(environment, `/recommendations/${recommendation.id}/downvote`, {
        method: "POST"
      })).status,
      200
    );
  }

  assert.equal((await request(environment, `/recommendations/${recommendation.id}`)).status, 404);
});

test("hosted recommendations reject invalid input and support SPA fallbacks", async () => {
  const environment = createEnvironment();
  const invalid = await request(environment, "/recommendations", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: "", youtubeLink: "not-a-link" })
  });

  assert.equal(invalid.status, 422);
  assert.equal((await request(environment, "/recommendations/not-a-number")).status, 422);
  assert.equal((await request(environment, "/top")).status, 200);
  assert.equal((await request(environment, "/random")).status, 200);
});
