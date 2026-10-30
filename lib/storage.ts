import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import { topics, topicMap } from "./curriculum";
import { emptyProgress, type Progress, type Attempt } from "./types";
import { gradeAssessment } from "./engine";
import { getAssessment } from "./content";
import { validateLab } from "./labs";
const id = z.string().min(1).max(100);
const topicId = z.string().refine((v) => !!topicMap[v], "Unknown topic");
const date = z.iso.datetime();
const assistance = z.enum(["A0", "A1", "A2", "A3"]);
const grade = z.object({
  score: z.number().min(0).max(100),
  passed: z.boolean(),
  dimensions: z.partialRecord(z.enum(["C", "M", "I", "T"]), z.boolean()),
  items: z.array(
    z.object({
      id,
      correct: z.boolean().nullable(),
      feedback: z.string().max(10000),
    }),
  ),
});
const attemptSchema = z.object({
  id,
  topicId,
  assessmentVersion: z.number().int().positive(),
  at: date,
  assistance,
  answers: z.record(z.string().max(100), z.string().max(10000)),
  grade,
});
const sessionSchema = z.object({
  id,
  topicId,
  at: date,
  kind: z.enum([
    "reading",
    "practice",
    "note",
    "ai_feedback",
    "self_assessment",
    "difficulty",
  ]),
  text: z.string().max(20000),
  minutes: z.number().int().min(0).max(1440),
  provisionalLevel: z.number().int().min(0).max(4).optional(),
});
const labSchema = z.object({
  id,
  topicId,
  at: date,
  assistance,
  sourceHash: z.string().length(64),
  report: z.string().max(5000),
  signature: z.string().max(500),
  trusted: z.boolean(),
});
export const progressSchema = z
  .object({
    attempts: z.array(attemptSchema).max(20000),
    sessions: z.array(sessionSchema).max(50000),
    labs: z.array(labSchema).max(20000),
    reviews: z
      .array(
        z.object({
          topicId,
          due: date,
          stage: z.number().int().min(0).max(3),
          lastAttemptId: id,
        }),
      )
      .max(topics.length),
    goal: z.string().max(100),
    focusTopic: topicId.nullable(),
    focusReason: z.string().max(1000),
  })
  .strict();
export const backupSchema = z
  .object({
    schema: z.literal("corelab-backup/1"),
    curriculumVersion: z.literal("1.0"),
    exportedAt: date,
    progress: progressSchema,
  })
  .strict();
export function validateBackup(input: unknown): Progress {
  const p = backupSchema.parse(input).progress as Progress;
  for (const collection of [p.attempts, p.sessions, p.labs]) {
    const seen = new Set<string>();
    for (const item of collection) {
      if (seen.has(item.id)) throw new Error("Duplicate record ID");
      seen.add(item.id);
      if (Date.parse(item.at) > Date.now() + 60000)
        throw new Error("Evidence date is in the future");
    }
  }
  for (const a of p.attempts) {
    const contract = getAssessment(a.topicId, a.assessmentVersion);
    if (!contract)
      throw new Error(
        `Missing assessment contract ${a.topicId} v${a.assessmentVersion}`,
      );
    a.grade = gradeAssessment(contract, a.answers);
  }
  for (const s of p.sessions)
    if (s.provisionalLevel && s.kind !== "self_assessment")
      throw new Error("Only self-assessment may hold a provisional level");
  for (const l of p.labs) {
    const report = validateLab(JSON.parse(l.report));
    if (
      report.topicId !== l.topicId ||
      report.at !== l.at ||
      report.assistance !== l.assistance ||
      report.sourceHash !== l.sourceHash ||
      report.signature !== l.signature
    )
      throw new Error("Lab provenance mismatch");
    l.trusted = true;
  }
  const seenReviews = new Set<string>();
  for (const r of p.reviews) {
    if (seenReviews.has(r.topicId)) throw new Error("Duplicate review");
    seenReviews.add(r.topicId);
    const attempt = p.attempts.find(
      (a) => a.id === r.lastAttemptId && a.topicId === r.topicId,
    );
    if (!attempt) throw new Error("Review references a missing attempt");
  }
  return p;
}
export class Store {
  db: DatabaseSync;
  constructor(
    filename = process.env.CORELAB_DB_PATH ??
      path.join(process.cwd(), ".local", "corelab.sqlite"),
  ) {
    if (filename !== ":memory:")
      mkdirSync(path.dirname(filename), { recursive: true, mode: 0o700 });
    this.db = new DatabaseSync(filename);
    this.db.exec(
      "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;",
    );
    const version = (
      this.db.prepare("PRAGMA user_version").get() as { user_version: number }
    ).user_version;
    if (version > 2)
      throw new Error(
        "Database was created by a newer CoreLab. Upgrade the app before opening it.",
      );
    this.db.exec("BEGIN IMMEDIATE");
    try {
      this.db.exec(
        "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), json TEXT NOT NULL); CREATE TABLE IF NOT EXISTS modules (id TEXT PRIMARY KEY,json TEXT NOT NULL); CREATE TABLE IF NOT EXISTS restore_snapshots (id TEXT PRIMARY KEY,at TEXT NOT NULL,json TEXT NOT NULL); PRAGMA user_version=2;",
      );
      this.db
        .prepare("INSERT OR IGNORE INTO state VALUES (1,?)")
        .run(JSON.stringify(emptyProgress()));
      const insert = this.db.prepare(
        "INSERT INTO modules VALUES (?,?) ON CONFLICT(id) DO UPDATE SET json=excluded.json",
      );
      for (const t of topics) insert.run(t.id, JSON.stringify(t));
      this.db.exec("COMMIT");
    } catch (e) {
      this.db.exec("ROLLBACK");
      throw e;
    }
  }
  read(): Progress {
    return JSON.parse(
      (
        this.db.prepare("SELECT json FROM state WHERE id=1").get() as {
          json: string;
        }
      ).json,
    );
  }
  update(fn: (p: Progress) => void) {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const p = this.read();
      fn(p);
      this.db
        .prepare("UPDATE state SET json=? WHERE id=1")
        .run(JSON.stringify(p));
      this.db.exec("COMMIT");
      return p;
    } catch (e) {
      this.db.exec("ROLLBACK");
      throw e;
    }
  }
  export() {
    return {
      schema: "corelab-backup/1" as const,
      curriculumVersion: "1.0" as const,
      exportedAt: new Date().toISOString(),
      progress: this.read(),
    };
  }
  restore(input: unknown, confirm: boolean) {
    if (!confirm) throw new Error("Explicit replacement confirmation required");
    const p = validateBackup(input);
    this.update((current) => {
      this.db
        .prepare("INSERT INTO restore_snapshots VALUES (?,?,?)")
        .run(randomUUID(), new Date().toISOString(), JSON.stringify(current));
      Object.assign(current, p);
    });
    return p;
  }
  attempt(
    topic: string,
    answers: Record<string, string>,
    help: Attempt["assistance"],
  ) {
    const contract = getAssessment(topic);
    if (!contract) throw new Error("No authored assessment for this topic");
    const attempt: Attempt = {
      id: randomUUID(),
      topicId: topic,
      assessmentVersion: contract.version,
      at: new Date().toISOString(),
      assistance: help,
      answers,
      grade: gradeAssessment(contract, answers),
    };
    this.update((p) => {
      p.attempts.push(attempt);
      const old = p.reviews.find((r) => r.topicId === topic);
      const independentPass = attempt.grade.passed && help === "A0";
      const isDue = old && Date.parse(old.due) <= Date.parse(attempt.at);
      const stage = independentPass
        ? Math.min(3, old && isDue ? old.stage + 1 : (old?.stage ?? 0))
        : 0;
      const days = independentPass ? [1, 3, 7, 21][stage] : 1;
      const due = new Date(
        Date.parse(attempt.at) + days * 86400000,
      ).toISOString();
      if (!old || !independentPass || isDue) {
        p.reviews = p.reviews.filter((r) => r.topicId !== topic);
        p.reviews.push({
          topicId: topic,
          due,
          stage,
          lastAttemptId: attempt.id,
        });
      }
    });
    return attempt;
  }
  close() {
    this.db.close();
  }
}
const globalStore = globalThis as typeof globalThis & { corelabStore?: Store };
export function getStore() {
  return (globalStore.corelabStore ??= new Store());
}
