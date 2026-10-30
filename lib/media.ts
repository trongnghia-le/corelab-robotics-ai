import { z } from "zod";
import rawVideos from "../content/media/videos.v1.json";
import rawLessons from "../content/media/lesson-media.v1.json";
const https = z
  .url()
  .refine(
    (value) => new URL(value).protocol === "https:",
    "Media must use HTTPS",
  );
export const visualizationIds = [
  "vectors",
  "matrices",
  "gradient-descent",
  "forward-kinematics",
  "jacobian",
  "pid",
  "convolution",
  "q-learning",
] as const;
export const illustrationIds = [
  "projection",
  "frames",
  "backpropagation",
  "mdp",
  "feedback",
] as const;
export type VisualizationId = (typeof visualizationIds)[number];
export const videoSchema = z
  .object({
    id: z.string().min(1),
    title: z.string().min(1),
    creator: z.string().min(1),
    sourceUrl: https,
    watchUrl: https,
    description: z.string().min(1),
    objectives: z.array(z.string()).min(1),
    provider: z.enum(["youtube", "external"]),
    youtubeId: z
      .string()
      .regex(/^[\w-]{11}$/)
      .optional(),
    startSeconds: z.number().int().nonnegative().optional(),
    captions: z.enum(["available", "unavailable"]).optional(),
    verifiedOn: z.iso.date(),
    verification: z.string().min(1),
    verifiedTitle: z.string().min(1),
    verifiedChannel: z.string().min(1),
  })
  .superRefine((v, ctx) => {
    if (
      v.provider === "youtube" &&
      (!v.youtubeId ||
        v.watchUrl !== `https://www.youtube.com/watch?v=${v.youtubeId}`)
    )
      ctx.addIssue({
        code: "custom",
        message: "YouTube ID and original URL must agree",
      });
    if (v.provider === "external" && v.youtubeId)
      ctx.addIssue({
        code: "custom",
        message: "External lecture pages cannot claim an embedded ID",
      });
  });
export const lessonMediaSchema = z.object({
  videos: z.array(z.string()).default([]),
  visualizations: z.array(z.enum(visualizationIds)).default([]),
  illustrations: z
    .array(
      z.object({
        id: z.enum(illustrationIds),
        heading: z.string().min(1),
        description: z.string().min(1),
        attribution: z.string().min(1),
      }),
    )
    .default([]),
});
export type VideoResource = z.infer<typeof videoSchema>;
export type LessonMedia = z.infer<typeof lessonMediaSchema>;
export type ResolvedMedia = Omit<LessonMedia, "videos"> & {
  videos: VideoResource[];
};
export const videoRegistry = z
  .object({ schemaVersion: z.literal(1), videos: z.array(videoSchema) })
  .parse(rawVideos);
export const lessonMediaRegistry = z
  .object({
    schemaVersion: z.literal(1),
    lessons: z.record(z.string(), lessonMediaSchema),
  })
  .parse(rawLessons);
export function mediaFor(id: string): ResolvedMedia {
  const meta = lessonMediaRegistry.lessons[id] ?? lessonMediaSchema.parse({});
  return {
    ...meta,
    videos: meta.videos.map((ref) => {
      const video = videoRegistry.videos.find((v) => v.id === ref);
      if (!video) throw new Error(`Unknown media resource ${ref}`);
      return video;
    }),
  };
}
