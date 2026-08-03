const recommendationTable = `
  CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    youtubeLink TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0
  )
`;

const youtubeLinkPattern = /^(https?:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;

function json(value, status = 200) {
  return Response.json(value, {
    status,
    headers: { "access-control-allow-origin": "*" }
  });
}

function error(message, status) {
  return new Response(message, {
    status,
    headers: { "access-control-allow-origin": "*" }
  });
}

function positiveInteger(value) {
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : null;
}

async function ensureSchema(database) {
  await database.prepare(recommendationTable).run();
}

async function list(database, statement, ...parameters) {
  const result = await database.prepare(statement).bind(...parameters).all();
  return result.results;
}

async function recommendationById(database, id) {
  return database
    .prepare("SELECT id, name, youtubeLink, score FROM recommendations WHERE id = ?")
    .bind(id)
    .first();
}

async function handleRecommendationRequest(request, database, pathname) {
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 1 && request.method === "GET") {
    return json(
      await list(
        database,
        "SELECT id, name, youtubeLink, score FROM recommendations ORDER BY id DESC LIMIT 10"
      )
    );
  }

  if (segments.length === 1 && request.method === "POST") {
    let body;

    try {
      body = await request.json();
    } catch {
      return error("Invalid request body", 422);
    }

    const name = typeof body.name === "string" ? body.name.trim() : "";

    if (
      !name ||
      name.length > 255 ||
      typeof body.youtubeLink !== "string" ||
      !youtubeLinkPattern.test(body.youtubeLink)
    ) {
      return error("Invalid recommendation", 422);
    }

    try {
      const result = await database
        .prepare(
          "INSERT INTO recommendations (name, youtubeLink, score) VALUES (?, ?, 0) RETURNING id, name, youtubeLink, score"
        )
        .bind(name, body.youtubeLink)
        .first();

      return json(result, 201);
    } catch (requestError) {
      if (String(requestError.message).includes("UNIQUE")) {
        return error("Recommendations names must be unique", 409);
      }

      throw requestError;
    }
  }

  if (segments[1] === "random" && request.method === "GET") {
    const comparison = Math.random() < 0.7 ? ">" : "<=";
    let choices = await list(
      database,
      `SELECT id, name, youtubeLink, score FROM recommendations WHERE score ${comparison} ? ORDER BY id DESC LIMIT 10`,
      10
    );

    if (choices.length === 0) {
      choices = await list(
        database,
        "SELECT id, name, youtubeLink, score FROM recommendations ORDER BY id DESC LIMIT 10"
      );
    }

    if (choices.length === 0) {
      return error("Recommendation not found", 404);
    }

    return json(choices[Math.floor(Math.random() * choices.length)]);
  }

  if (segments[1] === "top" && segments.length === 3 && request.method === "GET") {
    const amount = positiveInteger(segments[2]);

    if (!amount) {
      return error("amount must be a positive integer", 422);
    }

    return json(
      await list(
        database,
        "SELECT id, name, youtubeLink, score FROM recommendations ORDER BY score DESC, id DESC LIMIT ?",
        amount
      )
    );
  }

  const id = positiveInteger(segments[1]);

  if (!id) {
    return error("id must be a positive integer", 422);
  }

  if (segments.length === 2 && request.method === "GET") {
    const recommendation = await recommendationById(database, id);
    return recommendation ? json(recommendation) : error("Recommendation not found", 404);
  }

  if (
    segments.length === 3 &&
    request.method === "POST" &&
    (segments[2] === "upvote" || segments[2] === "downvote")
  ) {
    const delta = segments[2] === "upvote" ? 1 : -1;
    const recommendation = await database
      .prepare(
        "UPDATE recommendations SET score = score + ? WHERE id = ? RETURNING id, name, youtubeLink, score"
      )
      .bind(delta, id)
      .first();

    if (!recommendation) {
      return error("Recommendation not found", 404);
    }

    if (recommendation.score < -5) {
      await database.prepare("DELETE FROM recommendations WHERE id = ?").bind(id).run();
    }

    return new Response(null, {
      status: 200,
      headers: { "access-control-allow-origin": "*" }
    });
  }

  return error("Route not found", 404);
}

export default {
  async fetch(request, environment) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-methods": "GET, POST, OPTIONS",
          "access-control-allow-headers": "content-type"
        }
      });
    }

    if (url.pathname === "/health" || url.pathname.startsWith("/recommendations")) {
      try {
        await ensureSchema(environment.DB);

        if (url.pathname === "/health") {
          return json({ status: "ok" });
        }

        return await handleRecommendationRequest(request, environment.DB, url.pathname);
      } catch (requestError) {
        console.error("Recommendation API request failed", requestError);
        return error("Internal server error", 500);
      }
    }

    const asset = await environment.ASSETS.fetch(request);

    if (asset.status !== 404 || url.pathname.includes(".")) {
      return asset;
    }

    return environment.ASSETS.fetch(new Request(new URL("/index.html", request.url)));
  }
};
