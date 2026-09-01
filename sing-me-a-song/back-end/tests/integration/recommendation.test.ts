import { jest } from "@jest/globals";
import supertest from "supertest";
import app from "../../src/app.js";
import { prisma } from "../../src/database.js";
import { assertTestDatabase } from "../../src/utils/testDatabase.js";
import { createRandomSong } from "../factories/recommendationFactory.js";
const agent = supertest(app);
// Runs before any TRUNCATE; a normal DATABASE_URL must fail closed.
assertTestDatabase();
beforeEach(async () => { await prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`; });
afterAll(async () => { await prisma.$disconnect(); });

it("creates, persists and rejects duplicate recommendations", async () => {
  const song = createRandomSong();
  expect((await agent.post("/api/recommendations").send(song)).status).toBe(201);
  expect((await agent.post("/recommendations").send(song)).status).toBe(409);
  expect(await prisma.recommendation.findUnique({ where: { name: song.name } })).toMatchObject(song);
});
it("handles concurrent duplicate creation without a 500", async () => {
  const song = createRandomSong();
  const responses = await Promise.all([agent.post("/recommendations").send(song), agent.post("/recommendations").send(song)]);
  expect(responses.map(r => r.status).sort()).toEqual([201, 409]);
});
it.each([{}, {name: " ", youtubeLink: "https://youtu.be/dQw4w9WgXcQ"},
  {name: "Bad host", youtubeLink: "https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ"},
  {name: "Not a video", youtubeLink: "https://www.youtube.com/channel/test"},
  {name: "No protocol", youtubeLink: "youtu.be/dQw4w9WgXcQ"}])("rejects invalid input: %j", async body => {
  expect((await agent.post("/recommendations").send(body)).status).toBe(422);
});
it.each(["https://youtu.be/dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://youtube.com/shorts/dQw4w9WgXcQ"])("accepts video URL %s and trims names", async youtubeLink => {
  expect((await agent.post("/recommendations").send({ name: "  Song  ", youtubeLink })).status).toBe(201);
  expect((await prisma.recommendation.findFirst()).name).toBe("Song");
});
it("returns the latest ten and deterministic top scores", async () => {
  for (let i = 0; i < 12; i++) await prisma.recommendation.create({ data: { ...createRandomSong(), score: i } });
  const latest = await agent.get("/recommendations");
  expect(latest.status).toBe(200);
  expect(latest.body.map(r => r.id)).toEqual([12,11,10,9,8,7,6,5,4,3]);
  const top = await agent.get("/recommendations/top/2");
  expect(top.status).toBe(200);
  expect(top.body.map(r => r.score)).toEqual([11,10]);
});
it("returns empty lists and a 404 for random on an empty database", async () => {
  expect((await agent.get("/recommendations")).body).toEqual([]);
  expect((await agent.get("/recommendations/top/10")).body).toEqual([]);
  expect((await agent.get("/recommendations/random")).status).toBe(404);
});
it.each([-1, 20])("falls back when the other random score bucket is empty (%i)", async score => {
  const song = await prisma.recommendation.create({ data: { ...createRandomSong(), score } });
  for (let i = 0; i < 10; i++) {
    const response = await agent.get("/recommendations/random");
    expect(response.status).toBe(200);
    expect(response.body.id).toBe(song.id);
  }
});
it("retrieves, votes and deletes only below -5", async () => {
  const song = await prisma.recommendation.create({ data: createRandomSong() });
  expect((await agent.get(`/recommendations/${song.id}`)).body).toMatchObject(song);
  expect((await agent.post(`/recommendations/${song.id}/upvote`)).status).toBe(200);
  expect((await agent.get(`/recommendations/${song.id}`)).body.score).toBe(1);
  for(let i=0;i<6;i++) expect((await agent.post(`/recommendations/${song.id}/downvote`)).status).toBe(200);
  expect((await agent.get(`/recommendations/${song.id}`)).body.score).toBe(-5);
  expect((await agent.post(`/recommendations/${song.id}/downvote`)).status).toBe(200);
  expect((await agent.get(`/recommendations/${song.id}`)).status).toBe(404);
});
it("does not lose concurrent upvotes", async () => {
  const song = await prisma.recommendation.create({ data: createRandomSong() });
  const votes = await Promise.all(Array.from({length: 8}, () => agent.post(`/recommendations/${song.id}/upvote`)));
  expect(votes.every(r => r.status === 200)).toBe(true);
  expect((await agent.get(`/recommendations/${song.id}`)).body.score).toBe(8);
});
it.each(["abc", "0", "-1", "1.5", "2147483648"])("rejects invalid numeric parameter %s", async id => {
  expect((await agent.get(`/recommendations/${id}`)).status).toBe(422);
  expect((await agent.post(`/recommendations/${id}/upvote`)).status).toBe(422);
  expect((await agent.get(`/recommendations/top/${id}`)).status).toBe(422);
});
it("bounds the ranking size", async () => { expect((await agent.get("/recommendations/top/101")).status).toBe(422); });
it("returns 404 for missing vote targets", async () => {
  expect((await agent.post("/recommendations/999/upvote")).status).toBe(404);
  expect((await agent.post("/recommendations/999/downvote")).status).toBe(404);
});
it("handles malformed JSON without exposing internals", async () => {
  const response = await agent.post("/recommendations").set("Content-Type", "application/json").send('{"name":');
  expect(response.status).toBe(400);
  expect(response.text).toBe("Invalid JSON");
});
it("has database-backed health and no enabled destructive reset endpoint", async () => {
  expect((await agent.get("/health")).body).toEqual({status: "ok"});
  expect((await agent.delete("/tests/reset")).status).toBe(404);
  expect((await agent.get("/api/missing")).status).toBe(404);
});
it("allows configured CORS origins but not arbitrary websites", async () => {
  const allowed = await agent.options("/api/recommendations").set("Origin", "http://localhost:3000").set("Access-Control-Request-Method", "POST");
  expect(allowed.headers["access-control-allow-origin"]).toBe("http://localhost:3000");
  const denied = await agent.get("/recommendations").set("Origin", "https://untrusted.example");
  expect(denied.headers["access-control-allow-origin"]).toBeUndefined();
});

it("random selection can reach songs older than the latest ten", async () => {
  for (let i=0;i<14;i++) await prisma.recommendation.create({data:createRandomSong()});
  jest.spyOn(Math, "random").mockReturnValue(0.99);
  const response = await agent.get("/recommendations/random");
  expect(response.status).toBe(200);
  expect(response.body.id).toBe(1);
});
it("reports database health failure without leaking details", async () => {
  jest.spyOn(prisma.recommendation, "count").mockRejectedValueOnce(new Error("private database failure"));
  const response = await agent.get("/health");
  expect(response.status).toBe(503);
  expect(response.body).toEqual({status:"unavailable"});
});
