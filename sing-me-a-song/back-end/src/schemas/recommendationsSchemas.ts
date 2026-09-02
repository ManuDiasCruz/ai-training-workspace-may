import joi from "joi";
import { CreateRecommendationData } from "../services/recommendationsService.js";

function isYoutubeVideo(value: string) {
  try {
    const url = new URL(value);
    if (!["https:", "http:"].includes(url.protocol) || url.username || url.password || url.port) return false;
    const youtubeHost = ["youtube.com", "www.youtube.com", "m.youtube.com"].includes(url.hostname);
    const id = url.hostname === "youtu.be" ? url.pathname.slice(1)
      : youtubeHost && url.pathname === "/watch" ? url.searchParams.get("v")
      : youtubeHost && /^\/(shorts|embed)\//.test(url.pathname) ? url.pathname.split("/")[2] : null;
    return /^[\w-]{11}$/.test(id || "");
  } catch { return false; }
}

export const recommendationSchema = joi.object<CreateRecommendationData>({
  name: joi.string().trim().min(1).max(100).required(),
  youtubeLink: joi.string().trim().max(2048).required().custom((value, helpers) =>
    isYoutubeVideo(value) ? value : helpers.error("any.invalid")),
});
