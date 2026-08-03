import joi from "joi";
import { CreateRecommendationData } from "../services/recommendationsService.js";

const youtubeLinkRegex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;

export const recommendationSchema = joi.object<CreateRecommendationData>({
  name: joi.string().required(),
  youtubeLink: joi.string().required().pattern(youtubeLinkRegex),
});

// Body of POST /tests/seed, which only exists while MODE=TEST.
export const seedSchema = joi.object({
  amount: joi.number().integer().min(1).max(500).required(),
  highScorePercentage: joi.number().min(0).max(100).default(0),
});
