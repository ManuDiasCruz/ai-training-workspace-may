import supertest from "supertest";

import app from "../../src/app.js";
import { prisma } from "../../src/database.js";
import { createRandomSong } from "../factories/recommendationFactory.js";

const agent = supertest(app);

describe("recommendation routes", () => {
  beforeEach(async () => {
    await prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`;
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  it("creates and lists a recommendation", async () => {
    const song = createRandomSong();

    const createResponse = await agent.post("/recommendations").send(song);
    const listResponse = await agent.get("/recommendations");

    expect(createResponse.status).toBe(201);
    expect(createResponse.body).toMatchObject(song);
    expect(listResponse.status).toBe(200);
    expect(listResponse.body).toHaveLength(1);
    expect(listResponse.body[0]).toMatchObject(song);
  });

  it("rejects invalid payloads and duplicate names", async () => {
    const song = createRandomSong();
    await agent.post("/recommendations").send(song);

    expect((await agent.post("/recommendations").send({})).status).toBe(422);
    expect((await agent.post("/recommendations").send(song)).status).toBe(409);
  });

  it("supports voting and top listing", async () => {
    const song = createRandomSong();
    const createResponse = await agent.post("/recommendations").send(song);
    const id = createResponse.body.id;

    await agent.post(`/recommendations/${id}/upvote`);
    await agent.post(`/recommendations/${id}/upvote`);

    const topResponse = await agent.get("/recommendations/top/1");
    const byIdResponse = await agent.get(`/recommendations/${id}`);

    expect(topResponse.status).toBe(200);
    expect(topResponse.body).toHaveLength(1);
    expect(topResponse.body[0].id).toBe(id);
    expect(byIdResponse.body.score).toBe(2);
  });

  it("returns 404 for random when no recommendations exist", async () => {
    expect((await agent.get("/recommendations/random")).status).toBe(404);
  });

  it("returns 422 for invalid route params", async () => {
    expect((await agent.get("/recommendations/top/nope")).status).toBe(422);
    expect((await agent.get("/recommendations/nope")).status).toBe(422);
  });
});
