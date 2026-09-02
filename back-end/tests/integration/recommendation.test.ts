import supertest from "supertest";

import app from "./../../src/app.js";
import { createRandomSong } from "../factories/recommendationFactory.js";
import { prisma } from "../../src/database.js";

const agent = supertest(app);

describe("INTEGRATION TESTS SUITE", () => {
  beforeEach(async () => {
    await prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`;
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  describe("GET /health", () => {
    it("Reports the API is up", async () => {
      const response = await agent.get("/health");
      expect(response.status).toBe(200);
      expect(response.body).toEqual({ status: "ok" });
    });
  });

  describe("POST /recommendations", () => {
    it("Create a recommendation", async () => {
      const song = createRandomSong();

      const response = await agent.post("/recommendations").send(song);
      expect(response.status).toBe(201);

      const { name, youtubeLink } = song;
      const created = await prisma.recommendation.findFirst({
        where: { name, youtubeLink },
      });

      expect(created).not.toBeNull();
    });

    it("Create a conflicting recommendation", async () => {
      const body = createRandomSong();

      const create = await agent.post("/recommendations").send(body);
      expect(create.status).toBe(201);

      const conflict = await agent.post("/recommendations").send(body);
      expect(conflict.status).toBe(409);
    });

    it("Create a 'invalid data' recommendation", async () => {
      const response = await agent.post("/recommendations").send({});
      expect(response.status).toBe(422);
    });

    it("Reject a link that is not from YouTube", async () => {
      const response = await agent
        .post("/recommendations")
        .send({ name: "Not a YouTube link", youtubeLink: "https://example.com/video" });
      expect(response.status).toBe(422);
    });
  });

  describe("GET /recommendations", () => {
    it("List recommendations (newest first)", async () => {
      const recommendation1 = createRandomSong();
      const recommendation2 = createRandomSong();
      const recommendation3 = createRandomSong();

      await agent.post("/recommendations").send(recommendation1);
      await agent.post("/recommendations").send(recommendation2);
      await agent.post("/recommendations").send(recommendation3);

      const response = await agent.get("/recommendations");
      expect(response.status).toBe(200);
      expect(response.body).toHaveLength(3);

      expect(response.body[0].name).toBe(recommendation3.name);
      expect(response.body[0].youtubeLink).toBe(recommendation3.youtubeLink);

      expect(response.body[1].name).toBe(recommendation2.name);
      expect(response.body[1].youtubeLink).toBe(recommendation2.youtubeLink);

      expect(response.body[2].name).toBe(recommendation1.name);
      expect(response.body[2].youtubeLink).toBe(recommendation1.youtubeLink);
    });

    it("Show at most 10 recommendations", async () => {
      for (let i = 0; i < 12; i++) {
        await agent.post("/recommendations").send(createRandomSong());
      }

      const response = await agent.get("/recommendations");
      expect(response.status).toBe(200);
      expect(response.body).toHaveLength(10);
    });

    it("Show empty recommendations list", async () => {
      const response = await agent.get("/recommendations");
      expect(response.status).toBe(200);
      expect(response.body).toHaveLength(0);
    });

    it("List a random recommendation", async () => {
      const recommendation1 = createRandomSong();
      const recommendation2 = createRandomSong();
      const recommendation3 = createRandomSong();

      await agent.post("/recommendations").send(recommendation1);
      await agent.post("/recommendations").send(recommendation2);
      await agent.post("/recommendations").send(recommendation3);

      const response = await agent.get("/recommendations/random");
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty("name");
      expect([recommendation1.name, recommendation2.name, recommendation3.name]).toContain(
        response.body.name
      );
    });

    it("Random recommendation on an empty database returns 404", async () => {
      const response = await agent.get("/recommendations/random");
      expect(response.status).toBe(404);
    });

    it("List top recommendations", async () => {
      const recommendation1 = createRandomSong();
      const recommendation2 = createRandomSong();
      const recommendation3 = createRandomSong();

      await agent.post("/recommendations").send(recommendation1);
      await agent.post("/recommendations").send(recommendation2);
      await agent.post("/recommendations").send(recommendation3);

      const first = await prisma.recommendation.findUnique({
        where: { name: recommendation1.name },
      });
      await agent.post(`/recommendations/${first.id}/upvote`);

      const response = await agent.get("/recommendations/top/2");

      expect(response.status).toBe(200);
      expect(response.body).toHaveLength(2);

      expect(response.body[0].name).toBe(recommendation1.name);
      expect(response.body[0].youtubeLink).toBe(recommendation1.youtubeLink);
      expect(response.body[0].score).toBe(1);
      expect(response.body[1].score).toBe(0);
    });

    it("Top with an invalid amount returns 422", async () => {
      const response = await agent.get("/recommendations/top/abc");
      expect(response.status).toBe(422);
    });

    it("Show a recommendation by id", async () => {
      const body = createRandomSong();

      await agent.post("/recommendations").send(body);

      const recommendation = await prisma.recommendation.findFirst({
        where: { name: body.name, youtubeLink: body.youtubeLink },
      });

      const response = await agent.get(`/recommendations/${recommendation.id}`);

      expect(response.status).toBe(200);
      expect(response.body.name).toBe(recommendation.name);
      expect(response.body.youtubeLink).toBe(recommendation.youtubeLink);
    });

    it("Show a non-existent recommendation returns 404", async () => {
      const response = await agent.get("/recommendations/999");
      expect(response.status).toBe(404);
    });

    it("Show a recommendation with an invalid id returns 422", async () => {
      const response = await agent.get("/recommendations/not-a-number");
      expect(response.status).toBe(422);
    });
  });

  describe("POST /upvote and /downvote", () => {
    it("Upvote a recommendation", async () => {
      const body = createRandomSong();
      await agent.post("/recommendations").send(body);

      const recommendation = await prisma.recommendation.findFirst({
        where: { name: body.name, youtubeLink: body.youtubeLink },
      });

      await agent.post(`/recommendations/${recommendation.id}/upvote`);
      await agent.post(`/recommendations/${recommendation.id}/upvote`);

      const response = await agent.get(`/recommendations/${recommendation.id}`);

      expect(response.status).toBe(200);
      expect(response.body.score).toBe(2);
    });

    it("Upvote non-existent recommendation", async () => {
      const response = await agent.post("/recommendations/1/upvote");
      expect(response.status).toBe(404);
    });

    it("Downvote a recommendation", async () => {
      const body = createRandomSong();

      await agent.post("/recommendations").send(body);

      const recommendation = await prisma.recommendation.findFirst({
        where: { name: body.name, youtubeLink: body.youtubeLink },
      });

      await agent.post(`/recommendations/${recommendation.id}/upvote`);
      await agent.post(`/recommendations/${recommendation.id}/upvote`);
      await agent.post(`/recommendations/${recommendation.id}/downvote`);

      const response = await agent.get(`/recommendations/${recommendation.id}`);

      expect(response.status).toBe(200);
      expect(response.body.score).toBe(1);
    });

    it("Downvote below -5 removes the recommendation", async () => {
      const body = createRandomSong();
      await agent.post("/recommendations").send(body);

      const recommendation = await prisma.recommendation.findFirst({
        where: { name: body.name },
      });

      for (let i = 0; i < 6; i++) {
        const response = await agent.post(`/recommendations/${recommendation.id}/downvote`);
        expect(response.status).toBe(200);
      }

      const removed = await prisma.recommendation.findUnique({
        where: { id: recommendation.id },
      });
      expect(removed).toBeNull();
    });

    it("Downvote non-existent recommendation", async () => {
      const response = await agent.post("/recommendations/1/downvote");
      expect(response.status).toBe(404);
    });
  });
});
