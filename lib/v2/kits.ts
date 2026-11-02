import { readFileSync } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import type { Store } from "../storage";
import { canonical, digest, hash, strictJSON, V2Error } from "./contracts";
import { insert, meta, nextSequence, write, type DB } from "./db";
import { attemptById, expose } from "./records";
import type { Attempt } from "./state";
import { fingerprintCandidates } from "./assessments";
import type { Item } from "./content";

const definitions = [
  {
    id: "L01-SE2",
    title: "Frames self-check kit",
    topic: "R03",
    objectives: [
      "M12.frame-labels",
      "M12.point-vs-direction",
      "R03.compose-invert-se2",
      "R03.rotation-validity",
    ],
    description:
      "Implement six SE(2) operations with noncommuting, inverse, shape, proper-rotation and nonmutation fixtures.",
  },
  {
    id: "L02-planar",
    title: "Planar FK self-check kit",
    topic: "R04",
    objectives: ["R04.planar-fk"],
    description:
      "Implement a planar two-link pose, including unequal links, folded and stretched configurations, orientation and invalid inputs.",
  },
  {
    id: "L03-odometry",
    title: "Odometry self-check kit",
    topic: "R02",
    objectives: ["R02.exact-arc"],
    description:
      "Implement wheel/body velocity conversion and exact planar odometry. Check nonzero initial headings, reverse motion, pure spin, small arcs, units and invalid inputs. No calibration or physical-position claim.",
  },
] as const;
// Keep the original shared sample bytes unchanged: they are part of both old
// kit hashes. New kits use separate immutable manifests.
const sampleFiles: Record<string, string> = {
  "L03-odometry": "L03-odometry.samples.v1.json",
};
export function kitFiles() {
  return definitions.map((d) => ({
    code: "content/labs/" + d.id + ".v1.py",
    samples: "content/labs/" + (sampleFiles[d.id] ?? "samples.v1.json"),
  }));
}
export function kits() {
  return definitions.map((d) => ({
    ...d,
    version: 1,
    status: "manual-unverified" as const,
    review:
      "Author-tested draft; independent technical/adversarial review pending",
    verifiedI: "unavailable" as const,
  }));
}
function source(id: string) {
  const d = definitions.find((d) => d.id === id);
  if (!d)
    throw new V2Error(
      "not_found",
      "No authored self-check kit exists with this ID",
      404,
    );
  const filename = d.id + ".v1.py";
  const content = readFileSync(
    path.join(process.cwd(), "content/labs", filename),
    "utf8",
  );
  const sampleBytes = readFileSync(
    path.join(
      process.cwd(),
      "content/labs",
      sampleFiles[id] ?? "samples.v1.json",
    ),
    "utf8",
  );
  const samples = z
    .object({
      schema: z.literal("corelab-kit-samples/1"),
      kits: z.record(
        z.string(),
        z
          .array(
            z
              .object({
                structure: z.string(),
                inputs: z.record(z.string(), z.unknown()),
              })
              .strict(),
          )
          .max(50),
      ),
    })
    .strict()
    .parse(strictJSON(sampleBytes));
  return {
    ...d,
    filename,
    content,
    samples: samples.kits[id] ?? [],
    hash: hash(content + "\n" + sampleBytes),
  };
}
export function kitFingerprints(id: string) {
  const kit = source(id);
  const sampleFps = kit.samples.flatMap((sample) =>
    fingerprintCandidates({
      ...sample,
      id: "kit-sample",
      route: "sample",
      difficulty: 1,
      objectiveId: kit.objectives[0],
      prompt: "Manual kit sample",
      fields: [],
      hints: [],
      solution: "",
      remediation: "",
    } as Item),
  );
  return [
    ...new Set([
      digest({
        structure: "corelab-kit-download/1",
        source: kit.id,
        hash: kit.hash,
      }),
      ...sampleFps,
    ]),
  ];
}
const frozenSchema = z
  .object({
    kit: z.enum(definitions.map((d) => d.id)),
    version: z.literal(1),
    title: z.string().max(100),
    description: z.string().max(1000),
    fileHash: z.string().length(64),
  })
  .strict();
export function publicKitAttempt(db: DB, a: Attempt) {
  const frozen = frozenSchema.parse(strictJSON(a.instance_json));
  return {
    id: a.id,
    purpose: a.purpose,
    status: a.status,
    source: a.source_id,
    sourceVersion: a.source_version,
    observedAssistance: a.observed_level,
    issuedAt: a.issued_at,
    submittedAt: a.submitted_at,
    repeat: true,
    item: {
      id: a.id,
      route: "manual-self-check",
      difficulty: 2,
      objectiveId: "Manual kit: no implementation evidence",
      prompt: frozen.description,
      fields: [] as {
        id: string;
        label: string;
        kind: "number" | "angle" | "choice";
        options?: string[];
        tolerance: number;
      }[],
    },
    result:
      a.status === "submitted"
        ? {
            unverifiable: true as const,
            claim:
              "Manual self-report recorded. No result was verified or signed.",
          }
        : null,
    reviewStatus:
      "Manual self-check only; use the lab card to record that you ran your tests",
    verifiedI: "unavailable",
  };
}
export function downloadKit(store: Store, id: string) {
  const kit = source(id);
  return write(store.db, () => {
    const at = new Date().toISOString();
    const frozen = {
      kit: kit.id,
      version: 1 as const,
      title: kit.title,
      description: kit.description,
      fileHash: kit.hash,
    };
    // Resource identity plus authored sample exposure relations. Formula study
    // does not expose every future procedure check; identical samples do count.
    const fps = kitFingerprints(id);
    const a: Attempt = {
      id: randomUUID(),
      purpose: "practice",
      source_kind: "kit",
      source_id: kit.id,
      source_version: 1,
      source_hash: kit.hash,
      route: "manual-self-check",
      policy_version: 1,
      objective_refs: canonical(
        kit.objectives.map((id) => ({ id, version: 1 })),
      ),
      instance_json: canonical(frozen),
      fingerprints: canonical(fps),
      status: "issued",
      issued_at: at,
      issued_seq: nextSequence(store.db),
      submitted_at: null,
      closed_seq: null,
      observed_level: 0,
      declared_level: null,
      submission_json: null,
      submission_hash: null,
      grade_json: null,
      history_epoch: Number(meta(store.db, "current_history_epoch")),
    };
    insert(store.db, "v2_attempts", a);
    expose(store.db, a, "issued", at);
    expose(store.db, a, "kit_download", at);
    return { ...kit, attemptId: a.id };
  });
}
export function selfReportKit(store: Store, id: string, input: unknown) {
  const req = z
    .object({
      attemptId: z.uuid(),
      ran: z.boolean(),
      declaredAssistance: z.number().int().min(0).max(3),
    })
    .strict()
    .parse(input);
  return write(store.db, () => {
    const a = attemptById(store.db, req.attemptId);
    if (
      a.source_kind !== "kit" ||
      a.source_id !== id ||
      a.purpose !== "practice"
    )
      throw new V2Error(
        "wrong_purpose",
        "This is not a matching manual-kit practice attempt",
      );
    const kit = source(id),
      frozen = frozenSchema.parse(strictJSON(a.instance_json));
    if (kit.hash !== a.source_hash || kit.hash !== frozen.fileHash)
      throw new V2Error(
        "source_unavailable",
        "The original kit version is unavailable; its history is preserved",
        503,
      );
    const submission = {
        ran: req.ran,
        declaredAssistance: req.declaredAssistance,
      },
      submissionHash = digest(submission);
    if (a.status === "submitted") {
      if (a.submission_hash !== submissionHash)
        throw new V2Error(
          "attempt_closed",
          "This self-report is already closed",
          409,
        );
    } else {
      const at = new Date().toISOString();
      if (Date.parse(at) < Date.parse(a.issued_at))
        throw new V2Error(
          "clock_regression",
          "Clock moved backwards; no self-report saved",
          409,
        );
      store.db
        .prepare(
          "UPDATE v2_attempts SET status='submitted',submitted_at=?,closed_seq=?,declared_level=?,submission_json=?,submission_hash=?,grade_json=? WHERE id=?",
        )
        .run(
          at,
          nextSequence(store.db),
          req.declaredAssistance,
          canonical(submission),
          submissionHash,
          canonical({ claim: "manual_self_report_only", ran: req.ran }),
          a.id,
        );
    }
    return {
      recorded: true,
      ran: req.ran,
      claim:
        "Manual self-report only. No verification, signature or mastery evidence.",
      verifiedI: "unavailable",
    };
  });
}
