import { embedUrl } from "../lib/video-player";
import { describe, it, expect } from "vitest";
import {
  videoRegistry,
  lessonMediaRegistry,
  mediaFor,
  videoSchema,
} from "../lib/media";
import { getLesson } from "../lib/content";
import { topicMap } from "../lib/curriculum";
describe("curated media sidecars", () => {
  it("keeps IDs unique and maps only known resources and topics", () => {
    const ids = videoRegistry.videos.map((v) => v.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const [topic, meta] of Object.entries(lessonMediaRegistry.lessons)) {
      expect(topicMap[topic]).toBeTruthy();
      for (const id of meta.videos) expect(ids).toContain(id);
      for (const illustration of meta.illustrations) {
        const lesson = getLesson(topic);
        if (lesson)
          expect(lesson.body.toLowerCase().replaceAll(" ", "-")).toContain(
            `##-${illustration.heading}`,
          );
      }
    }
    expect(mediaFor("M01")).toEqual({
      videos: [],
      visualizations: [],
      illustrations: [],
    });
  });
  it("records source evidence without inventing timing or captions", () => {
    for (const v of videoRegistry.videos) {
      expect(v.verifiedChannel.length).toBeGreaterThan(2);
      expect(v.verifiedTitle.length).toBeGreaterThan(5);
      expect(v.sourceUrl.startsWith("https://")).toBe(true);
      expect(v.startSeconds).toBeUndefined();
      expect(v.captions).toBeUndefined();
    }
  });
  it("creates privacy-domain embeds with autoplay disabled and external-page fallback", () => {
    const v = mediaFor("M02").videos[0];
    expect(embedUrl(v)).toBe(
      "https://www.youtube-nocookie.com/embed/fNk_zzaMoSs?autoplay=0&rel=0",
    );
    expect(embedUrl({ ...v, startSeconds: 90 })).toContain("start=90");
    expect(
      embedUrl(videoRegistry.videos.find((v) => v.provider === "external")!),
    ).toBeNull();
    expect(videoSchema.safeParse({ ...v, youtubeId: "invented" }).success).toBe(
      false,
    );
  });
  it("enriches lesson metadata without requiring changes to original markdown", () => {
    const lesson = getLesson("M02")!;
    expect(lesson.meta.videos).toContain("3b-vectors");
    expect(lesson.meta.visualizations).toContain("vectors");
    expect(getLesson("M01")!.body).toContain("## Worked example");
  });
});
