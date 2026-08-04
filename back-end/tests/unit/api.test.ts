import { jest } from "@jest/globals";
import supertest from "supertest";
import app from "../../src/app.js";
import { recommendationRepository } from "../../src/repositories/recommendationRepository.js";

const agent = supertest(app);

describe("API contract without a database", () => {
  afterEach(() => jest.restoreAllMocks());

  it("exposes a process health check", async () => {
    const response = await agent.get("/health");
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ status: "ok" });
  });

  it.each(["abc", "0", "-1", "1.5", "9007199254740992"])(
    "rejects invalid recommendation id %s before querying Prisma",
    async (id) => {
      const find = jest.spyOn(recommendationRepository, "find");
      const response = await agent.get(`/recommendations/${id}`);
      expect(response.status).toBe(422);
      expect(find).not.toHaveBeenCalled();
    }
  );

  it("bounds top-list requests", async () => {
    const getTop = jest.spyOn(recommendationRepository, "getAmountByScore");
    const response = await agent.get("/recommendations/top/101");
    expect(response.status).toBe(422);
    expect(getTop).not.toHaveBeenCalled();
  });

  it("rejects a non-YouTube URL", async () => {
    const response = await agent.post("/recommendations").send({
      name: "Not a video",
      youtubeLink: "https://youtube.com.evil.example/watch?v=abc",
    });
    expect(response.status).toBe(422);
  });

  it("returns the created recommendation", async () => {
    const created = { id: 1, name: "Song", youtubeLink: "https://youtu.be/abcdefghijk", score: 0 };
    jest.spyOn(recommendationRepository, "findByName").mockResolvedValueOnce(null);
    jest.spyOn(recommendationRepository, "create").mockResolvedValueOnce(created);
    const response = await agent.post("/recommendations").send({
      name: created.name,
      youtubeLink: created.youtubeLink,
    });
    expect(response.status).toBe(201);
    expect(response.body).toEqual(created);
  });
});
