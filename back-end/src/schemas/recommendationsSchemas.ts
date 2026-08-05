import joi from "joi";
import { CreateRecommendationData } from "../services/recommendationsService.js";

const youtubeHosts = new Set([
  "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"
]);

function isPlayableYoutubeUrl(value: string, helpers: joi.CustomHelpers) {
  try {
    const url = new URL(value);
    const hostname = url.hostname.toLowerCase();
    if (url.protocol !== "https:" || !youtubeHosts.has(hostname)) {
      return helpers.error("string.uri");
    }
    if (hostname.endsWith("youtu.be")) {
      if (url.pathname.length <= 1) return helpers.error("string.uri");
    } else if (
      !(url.pathname === "/watch" && url.searchParams.get("v")) &&
      !url.pathname.startsWith("/embed/") &&
      !url.pathname.startsWith("/shorts/")
    ) {
      return helpers.error("string.uri");
    }
    return value;
  } catch {
    return helpers.error("string.uri");
  }
}

export const recommendationSchema = joi.object<CreateRecommendationData>({
  name: joi.string().trim().min(1).max(255).required(),
  youtubeLink: joi.string().trim().max(2048).custom(isPlayableYoutubeUrl).required(),
});
