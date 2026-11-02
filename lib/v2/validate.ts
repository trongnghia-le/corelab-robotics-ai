import { readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";
import { hash, strictJSON } from "./contracts";
import {
  catalog,
  gradeItem,
  itemFingerprint,
  archivedFamilies,
} from "./content";
import { objectives, curriculumPreview } from "./objectives";
import { cmSources, fingerprintCandidates } from "./assessments";
import { kitFingerprints, kitFiles, kits } from "./kits";
import { labRoadmap } from "./roadmap";
export function validateV2() {
  const c = catalog(),
    o = objectives(),
    p = curriculumPreview(),
    sources = cmSources();
  const manifest = z
    .object({
      schema: z.literal("corelab-content-manifest/1"),
      files: z.record(
        z.string().regex(/^content\/[A-Za-z0-9._/-]+$/),
        z.string().regex(/^[a-f0-9]{64}$/),
      ),
    })
    .strict()
    .parse(
      strictJSON(
        readFileSync(
          path.join(process.cwd(), "content/v2/manifest.v1.json"),
          "utf8",
        ),
      ),
    );
  for (const [file, expected] of Object.entries(manifest.files)) {
    if (
      file.includes("..") ||
      hash(readFileSync(path.join(process.cwd(), file))) !== expected
    )
      throw new Error("Immutable content manifest mismatch: " + file);
  }
  const required = [
    "content/labs/roadmap.v1.json",
    "content/v2/archive.v1.json",
    "content/v2/catalog.v1.json",
    "content/v2/objectives.v1.json",
    "content/v2/assessments.v1.json",
    "content/v2/curriculum-planning.v1.json",
    "content/v2/bridges/radians-trig.v1.md",
    "content/labs/samples.v1.json",
    ...c.families.map(
      (f) => "content/exercises/" + f.id + ".v" + f.version + ".json",
    ),
    ...sources.map(
      (s) => "content/verify/" + s.id + ".v" + s.version + ".json",
    ),
    ...kitFiles().flatMap((files) => [files.code, files.samples]),
  ];
  for (const f of archivedFamilies())
    required.push("content/exercises/" + f.id + ".v" + f.version + ".json");
  if (required.some((file) => !manifest.files[file]))
    throw new Error("Incomplete content manifest");
  const practiced = new Set(
    c.families.flatMap((f) => f.items.map(itemFingerprint)),
  );
  const samples = new Set(kits().flatMap((kit) => kitFingerprints(kit.id)));
  const seen = new Set<string>();
  for (const s of sources)
    for (const v of s.variants)
      for (const check of v.items) {
        const aliases = fingerprintCandidates(check.task);
        if (
          aliases.some(
            (fp) => practiced.has(fp) || samples.has(fp) || seen.has(fp),
          )
        )
          throw new Error(
            "Assessment/review pool overlaps exposed content: " + check.task.id,
          );
        aliases.forEach((fp) => seen.add(fp));
        if (!o.objectives.some((o) => o.id === check.task.objectiveId))
          throw new Error("Unknown assessment objective");
      }
  for (const f of c.families)
    for (const item of f.items) {
      const answers = Object.fromEntries(
        item.fields.map((q, i) => [
          String(i),
          q.kind === "choice" ? q.answer : Number(q.answer).toFixed(9),
        ]),
      );
      if (!gradeItem(item, answers).passed)
        throw new Error("Invalid stored item oracle: " + item.id);
    }
  return {
    manualKits: kits().length,
    roadmapLabs: labRoadmap().labs.length,
    objectives: o.objectives.length,
    families: c.families.filter((f) => /^X\d+$/.test(f.id)).length,
    practiceItems: c.families.reduce((n, f) => n + f.items.length, 0),
    forms: sources.filter((s) => s.kind === "form").length,
    reviewItems: sources
      .filter((s) => s.kind === "review_pool")
      .reduce((n, s) => n + s.variants.length, 0),
    advisoryTopics: p.nodes.length,
    independentReview: "pending",
    verifiedI: "unavailable",
  };
}
