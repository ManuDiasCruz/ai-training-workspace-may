import { afterEach, describe, expect, jest, test } from "@jest/globals";

import { recommendationRepository } from "../../src/repositories/recommendationRepository.js";
import { recommendationService } from "../../src/services/recommendationsService.js";

const recommendation = {
  id: 1,
  name: "Unit test song",
  youtubeLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  score: 2,
};

const recommendationInput = {
  name: recommendation.name,
  youtubeLink: recommendation.youtubeLink,
};

afterEach(() => {
  jest.restoreAllMocks();
});

describe("recommendationService", () => {
  test("creates a unique recommendation", async () => {
    jest.spyOn(recommendationRepository, "findByName").mockResolvedValue(null);
    jest.spyOn(recommendationRepository, "create").mockResolvedValue(recommendation);

    await expect(recommendationService.insert(recommendationInput)).resolves.toEqual(
      recommendation
    );
  });

  test("rejects duplicate recommendation names", async () => {
    jest
      .spyOn(recommendationRepository, "findByName")
      .mockResolvedValue(recommendation);

    await expect(recommendationService.insert(recommendationInput)).rejects.toEqual({
      message: "Recommendations names must be unique",
      type: "conflict",
    });
  });

  test("upvotes an existing recommendation", async () => {
    jest.spyOn(recommendationRepository, "find").mockResolvedValue(recommendation);
    const updateScore = jest
      .spyOn(recommendationRepository, "updateScore")
      .mockResolvedValue({ ...recommendation, score: 3 });

    await recommendationService.upvote(recommendation.id);

    expect(updateScore).toHaveBeenCalledWith(recommendation.id, "increment");
  });

  test("rejects votes for missing recommendations", async () => {
    jest.spyOn(recommendationRepository, "find").mockResolvedValue(null);

    await expect(recommendationService.upvote(999)).rejects.toEqual({
      message: "",
      type: "not_found",
    });
  });

  test("removes recommendations whose score drops below minus five", async () => {
    jest.spyOn(recommendationRepository, "find").mockResolvedValue(recommendation);
    jest
      .spyOn(recommendationRepository, "updateScore")
      .mockResolvedValue({ ...recommendation, score: -6 });
    const remove = jest
      .spyOn(recommendationRepository, "remove")
      .mockResolvedValue(undefined);

    await recommendationService.downvote(recommendation.id);

    expect(remove).toHaveBeenCalledWith(recommendation.id);
  });

  test("lists recommendations and top recommendations", async () => {
    jest.spyOn(recommendationRepository, "findAll").mockResolvedValue([recommendation]);
    jest
      .spyOn(recommendationRepository, "getAmountByScore")
      .mockResolvedValue([recommendation]);

    await expect(recommendationService.get()).resolves.toEqual([recommendation]);
    await expect(recommendationService.getTop(1)).resolves.toEqual([recommendation]);
  });

  test("uses the weighted high-score random branch", async () => {
    jest.spyOn(Math, "random").mockReturnValueOnce(0.5).mockReturnValueOnce(0);
    const findAll = jest
      .spyOn(recommendationRepository, "findAll")
      .mockResolvedValue([recommendation]);

    await expect(recommendationService.getRandom()).resolves.toEqual(recommendation);
    expect(findAll).toHaveBeenCalledWith({ score: 10, scoreFilter: "gt" });
  });

  test("returns not found when no random recommendation exists", async () => {
    jest.spyOn(Math, "random").mockReturnValue(0.5);
    jest
      .spyOn(recommendationRepository, "findAll")
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);

    await expect(recommendationService.getRandom()).rejects.toEqual({
      message: "",
      type: "not_found",
    });
  });
});
