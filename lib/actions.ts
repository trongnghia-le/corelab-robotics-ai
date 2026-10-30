import { z } from "zod";
import { randomUUID } from "node:crypto";
import { domains, topicMap } from "./curriculum";
import { validateLab } from "./labs";
import type { Store } from "./storage";
const topicId = z.string().refine((v) => !!topicMap[v], "Unknown topic");
const actionSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("attempt"),
    topicId,
    answers: z.record(z.string().max(100), z.string().max(10000)),
    assistance: z.enum(["A0", "A1", "A2", "A3"]),
  }),
  z.object({
    type: z.literal("session"),
    topicId,
    kind: z.enum([
      "reading",
      "practice",
      "note",
      "difficulty",
      "self_assessment",
    ]),
    text: z.string().max(20000),
    minutes: z.number().int().min(0).max(1440),
    provisionalLevel: z.number().int().min(0).max(4).optional(),
  }),
  z.object({
    type: z.literal("feedback"),
    feedback: z
      .object({
        schema: z.literal("corelab-feedback/1"),
        topicId,
        summary: z.string().min(1).max(15000),
        difficulties: z.array(z.string().max(2000)).max(20),
        nextSteps: z.array(z.string().max(2000)).max(20),
      })
      .strict(),
  }),
  z.object({
    type: z.literal("goal"),
    goal: z.enum(["Foundations", ...domains]),
    focusTopic: topicId.nullable(),
    focusReason: z.string().max(1000),
  }),
  z.object({ type: z.literal("lab"), report: z.unknown() }),
  z.object({
    type: z.literal("restore"),
    backup: z.unknown(),
    confirm: z.literal(true),
  }),
]);
export function applyAction(store: Store, input: unknown) {
  const a = actionSchema.parse(input);
  if (a.type === "attempt")
    return store.attempt(a.topicId, a.answers, a.assistance);
  if (a.type === "restore") return store.restore(a.backup, a.confirm);
  const at = new Date().toISOString();
  if (a.type === "session") {
    if (a.provisionalLevel !== undefined && a.kind !== "self_assessment")
      throw new Error("Provisional levels require explicit self assessment");
    store.update((p) =>
      p.sessions.push({
        id: randomUUID(),
        topicId: a.topicId,
        at,
        kind: a.kind,
        text: a.text,
        minutes: a.minutes,
        provisionalLevel: a.provisionalLevel,
      }),
    );
  }
  if (a.type === "feedback") {
    store.update((p) => {
      p.sessions.push({
        id: randomUUID(),
        topicId: a.feedback.topicId,
        at,
        kind: "ai_feedback",
        text:
          a.feedback.summary +
          "\nNext steps: " +
          a.feedback.nextSteps.join("; "),
        minutes: 0,
      });
      for (const text of a.feedback.difficulties)
        p.sessions.push({
          id: randomUUID(),
          topicId: a.feedback.topicId,
          at,
          kind: "difficulty",
          text,
          minutes: 0,
        });
    });
  }
  if (a.type === "goal")
    store.update((p) => {
      p.goal = a.goal;
      p.focusTopic = a.focusTopic;
      p.focusReason = a.focusReason;
    });
  if (a.type === "lab") {
    const report = validateLab(a.report, true);
    store.update((p) => {
      if (p.labs.some((l) => l.signature === report.signature))
        throw new Error("This report has already been imported");
      p.labs.push({
        id: randomUUID(),
        topicId: report.topicId,
        at: report.at,
        assistance: report.assistance,
        sourceHash: report.sourceHash,
        report: JSON.stringify(report),
        signature: report.signature,
        trusted: true,
      });
    });
  }
  return { ok: true };
}
