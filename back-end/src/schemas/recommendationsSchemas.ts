import joi from "joi";
import { CreateRecommendationData } from "../services/recommendationsService.js";

const youtubeLinkRegex = /^https?:\/\/(?:(?:www|m)\.)?(?:youtube\.com|youtu\.be)\/.+$/i;

export const recommendationSchema = joi.object<CreateRecommendationData>({
  name: joi.string().trim().max(200).required(),
  youtubeLink: joi.string().trim().max(2048).required().pattern(youtubeLinkRegex),
});
