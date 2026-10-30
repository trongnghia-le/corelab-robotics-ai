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
