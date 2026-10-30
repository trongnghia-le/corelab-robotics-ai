import assert from "node:assert/strict";
import fs from "node:fs";
import { topics, topicMap, validateGraph } from "../lib/curriculum";
import source from "../corelab/curriculum_graph_v1.json";
import {
  getLesson,
  getAssessment,
  getOverview,
  lessonIds,
  publicAssessment,
} from "../lib/content";
validateGraph(source);
const ids = lessonIds();
for (const topic of topics) {
  const overview = getOverview(topic.id);
  assert(
    overview &&
      overview.concepts.length >= 2 &&
      overview.overview &&
      overview.application &&
      overview.task,
    `Missing overview: ${topic.id}`,
  );
}
for (const id of ids) {
  const lesson = getLesson(id)!;
  assert.equal(lesson.meta.module_id, id);
  assert.deepEqual(lesson.meta.prerequisites, topicMap[id].prerequisites);
  assert(lesson.body.split(/\s+/).length > 350, `Lesson too shallow: ${id}`);
  assert(
    (lesson.body.match(/^## /gm) ?? []).length >= 7,
    `Missing learning structure: ${id}`,
  );
  for (const pre of topicMap[id].prerequisites)
    assert(
      ids.includes(pre),
      `Authored path hits unavailable content: ${id} needs ${pre}`,
    );
  const assessment = getAssessment(id)!;
  assert(
    assessment && assessment.topicId === id && assessment.questions.length >= 4,
  );
  assert(assessment.questions.some((q) => q.critical && q.kind === "choice"));
  for (const q of assessment.questions) {
    assert(q.kind === "short" || q.answer !== undefined);
    if (q.kind === "choice")
      assert(q.options && Number(q.answer) < q.options.length);
    if (q.kind === "number") assert(Number.isFinite(Number(q.answer)));
  }
  assert(
    publicAssessment(assessment)?.questions.every(
      (q) => q.answer === undefined && q.explanation === "",
    ),
  );
}
const csv = fs
  .readFileSync("corelab/curriculum_graph_v1.csv", "utf8")
  .replace(/^\uFEFF/, "")
  .trim()
  .split(/\r?\n/);
assert.equal(csv.length - 1, topics.length);
console.log(
  `Validated ${topics.length} topics, ${ids.length} complete lessons and assessments, all authored prerequisite chains, and public answer-key redaction.`,
);

// Metadata augments immutable contracts; it never changes an answer or dimension.
const { getAssessmentCatalog, getPracticeAssessment } =
  await import("../lib/content");
const { questionMetadataSchema, knowledgeTypeFor, skillTagsFor } =
  await import("../lib/assessment");
const { ancestors } = await import("../lib/curriculum");
const metadata = JSON.parse(
  fs.readFileSync("content/assessment-metadata.v1.json", "utf8"),
);
assert.equal(metadata.schemaVersion, 1);
for (const [key, entries] of Object.entries(
  metadata.contracts as Record<string, Record<string, unknown>>,
)) {
  const match = key.match(/^([A-Z]+\d+)\.v(\d+)$/);
  assert(match, `Invalid metadata contract ${key}`);
  const raw = JSON.parse(
    fs.readFileSync(`content/assessments/${key}.json`, "utf8"),
  );
  for (const [id, value] of Object.entries(entries)) {
    const extra = questionMetadataSchema.parse(value);
    assert(
      raw.questions.some((q: { id: string }) => q.id === id),
      `Metadata references missing question ${key}/${id}`,
    );
    assert(extra.knowledgeType);
  }
}
const catalog = getAssessmentCatalog();
let variantCount = 0;
for (const [key, a] of Object.entries(catalog)) {
  for (const q of a.questions) {
    assert(
      new Set(skillTagsFor(a.topicId, q)).size ===
        skillTagsFor(a.topicId, q).length,
    );
    for (const id of q.relatedPrerequisites ?? [])
      assert(
        ancestors(a.topicId).includes(id),
        `Metadata invents prerequisite ${id} for ${a.topicId}`,
      );
    for (const ref of q.remediationRefs ?? []) {
      if (ref.href.startsWith("/lessons/")) {
        const [route, heading] = ref.href.split("#");
        const id = route.split("/").at(-1)!;
        assert(topicMap[id], `Unknown remediation topic ${id}`);
        if (heading) {
          const body = getLesson(id)?.body ?? "";
          const headings = body
            .split("\n")
            .filter((l) => l.startsWith("## "))
            .map((l) =>
              l
                .slice(3)
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/^-|-$/g, ""),
            );
          assert(
            headings.includes(heading),
            `Missing remediation heading ${ref.href}`,
          );
        }
      }
    }
    if (q.verifiedLabTopicId) assert(q.verifiedLabTopicId === a.topicId);
  }
  if (key.startsWith("targeted:")) {
    variantCount += a.questions.length;
    for (const q of a.questions) {
      assert(q.knowledgeType && q.skillTags?.length && q.skillLabel);
      if (["design", "implementation"].includes(knowledgeTypeFor(q)))
        assert.equal(
          q.kind,
          "short",
          "Unsupported judgment/code must use an unverified rubric",
        );
      for (const originalId of q.equivalentTo ?? []) {
        const original = getAssessment(a.topicId)?.questions.find(
          (v) => v.id === originalId,
        );
        assert(original, `Missing equivalent question ${originalId}`);
        assert(
          q.skillTags!.some((tag) =>
            skillTagsFor(a.topicId, original).includes(tag),
          ),
          `Unrelated equivalent skill ${q.id}`,
        );
      }
    }
    const publicBank = publicAssessment(getPracticeAssessment(a.topicId));
    assert(
      publicBank?.questions.every(
        (q) =>
          q.answer === undefined &&
          q.tolerance === undefined &&
          q.explanation === "",
      ),
    );
  }
}
console.log(
  `Validated metadata and ${variantCount} authored targeted questions across ${Object.keys(catalog).filter((k) => k.startsWith("targeted:")).length} topic banks.`,
);
