import { jest } from "@jest/globals";

import { recommendationService } from "../../src/services/recommendationsService.js";
import { recommendationRepository } from "../../src/repositories/recommendationRepository.js";

const recommendation = {
  id: 1,
  name: "Example song",
  youtubeLink: "https://www.youtube.com/watch?v=ABCDEFGHIJK",
  score: 2,
};

describe("recommendationService", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("creates a recommendation when the name is unique", async () => {
    jest.spyOn(recommendationRepository, "findByName").mockResolvedValueOnce(null);
    jest.spyOn(recommendationRepository, "create").mockResolvedValueOnce(recommendation);

    await expect(
      recommendationService.insert({ name: recommendation.name, youtubeLink: recommendation.youtubeLink })
    ).resolves.toEqual(recommendation);
  });

  it("rejects duplicate names", async () => {
    jest.spyOn(recommendationRepository, "findByName").mockResolvedValueOnce(recommendation);

    await expect(
      recommendationService.insert({ name: recommendation.name, youtubeLink: recommendation.youtubeLink })
    ).rejects.toEqual({ message: "Recommendations names must be unique", type: "conflict" });
  });

  it("upvotes an existing recommendation", async () => {
    jest.spyOn(recommendationRepository, "find").mockResolvedValueOnce(recommendation);
    jest.spyOn(recommendationRepository, "updateScore").mockResolvedValueOnce({ ...recommendation, score: 3 });

    await recommendationService.upvote(recommendation.id);

    expect(recommendationRepository.updateScore).toHaveBeenCalledWith(recommendation.id, "increment");
  });

  it("removes a recommendation once its score drops below -5", async () => {
    jest.spyOn(recommendationRepository, "find").mockResolvedValueOnce({ ...recommendation, score: -5 });
    jest.spyOn(recommendationRepository, "updateScore").mockResolvedValueOnce({ ...recommendation, score: -6 });
    jest.spyOn(recommendationRepository, "remove").mockResolvedValueOnce(undefined);

    await recommendationService.downvote(recommendation.id);

    expect(recommendationRepository.remove).toHaveBeenCalledWith(recommendation.id);
  });

  it("returns not_found for a random recommendation when the table is empty", async () => {
    jest.spyOn(recommendationRepository, "findAll")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);

    await expect(recommendationService.getRandom()).rejects.toEqual({ message: "", type: "not_found" });
  });
});
