import joi from "joi";
import { CreateRecommendationData } from "../services/recommendationsService.js";

function isYoutubeVideo(value: string) {
  try {
    const url = new URL(value);
    if (!["https:", "http:"].includes(url.protocol) || url.username || url.password || url.port) return false;
    const host = url.hostname.toLowerCase();
    let videoId: string | null = null;
    if (host === "youtu.be") videoId = url.pathname.slice(1);
    if (["youtube.com", "www.youtube.com", "m.youtube.com"].includes(host)) {
      if (url.pathname === "/watch") videoId = url.searchParams.get("v");
      else videoId = /^\/(?:shorts|embed)\/([^/]+)\/?$/.exec(url.pathname)?.[1] ?? null;
    }
    return !!videoId && /^[A-Za-z0-9_-]{11}$/.test(videoId);
  } catch { return false; }
}
export const recommendationSchema = joi.object<CreateRecommendationData>({
  name: joi.string().trim().max(200).required(),
  youtubeLink: joi.string().trim().max(2048).required().custom((value, helpers) =>
    isYoutubeVideo(value) ? value : helpers.error("string.uri")),
});
