import type { VideoResource } from "./media";
export function embedUrl(video: VideoResource) {
  if (video.provider !== "youtube" || !video.youtubeId) return null;
  const params = new URLSearchParams({ autoplay: "0", rel: "0" });
  if (video.startSeconds !== undefined)
    params.set("start", String(video.startSeconds));
  return `https://www.youtube-nocookie.com/embed/${video.youtubeId}?${params}`;
}
