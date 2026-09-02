import joi from "joi";
import { CreateRecommendationData } from "../services/recommendationsService.js";

const youtubeLinkRegex = /^https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/.+$/i;

export const recommendationSchema = joi.object<CreateRecommendationData>({
  name: joi.string().trim().min(1).max(100).required(),
  youtubeLink: joi.string().required().pattern(youtubeLinkRegex),
});
