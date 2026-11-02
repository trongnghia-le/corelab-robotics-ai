import { readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
import { catalog } from "./content";
import { id, strictJSON } from "./contracts";
import { kits } from "./kits";
const schema = z
  .object({
    schema: z.literal("corelab-lab-roadmap/1"),
    labs: z
      .array(
        z
          .object({
            id,
            title: z.string().max(200),
            outcome: z.string().max(1000),
            status: z.enum(["manual-self-check", "planned-not-implemented"]),
            kit: id.nullable(),
            practiceFamilies: z.array(id).max(10),
            scopeNote: z.string().max(1000),
            unavailable: z.array(z.string().min(1).max(300)).max(12).optional(),
          })
          .strict(),
      )
      .length(22),
    resources: z
      .array(
        z
          .object({
            id,
            title: z.string().max(200),
            url: z.url().refine((u) => new URL(u).protocol === "https:"),
            pathway: z.enum(["MuJoCo", "ROS 2", "Hardware"]),
            availability: z.literal("external-reading-only"),
            checkedOn: z.iso.date(),
            check: z.string().max(1000),
            rights: z.string().max(1000),
          })
          .strict(),
      )
      .max(20),
    rights: z
      .object({
        status: z.literal("original"),
        author: z.string(),
        license: z.literal("CC-BY-4.0"),
      })
      .strict(),
  })
  .strict();
let cached: z.infer<typeof schema> | undefined;
export function labRoadmap() {
  if (cached) return cached;
  const data = schema.parse(
    strictJSON(
      readFileSync(
        path.join(process.cwd(), "content/labs/roadmap.v1.json"),
        "utf8",
      ),
    ),
  );
  const families = new Set(catalog().families.map((f) => f.id));
  const availableKits = new Set<string>(kits().map((kit) => kit.id));
  if (new Set(data.labs.map((l) => l.id)).size !== 22)
    throw new Error("Duplicate lab roadmap identity");
  for (const lab of data.labs)
    if (
      lab.practiceFamilies.some((id) => !families.has(id)) ||
      (lab.status === "manual-self-check") !== (lab.kit !== null) ||
      (lab.kit !== null && !availableKits.has(lab.kit))
    )
      throw new Error("Invalid roadmap availability or mapping");
  return (cached = data);
}
