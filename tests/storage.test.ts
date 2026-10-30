import { describe, it, expect } from "vitest";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { generateKeyPairSync, sign } from "node:crypto";
import { Store, validateBackup } from "../lib/storage";
import { applyAction } from "../lib/actions";
import { getAssessment } from "../lib/content";
import { masteryFor } from "../lib/engine";
import { validateLab } from "../lib/labs";
const answers = Object.fromEntries(
  getAssessment("M01")!
    .questions.filter((q) => q.kind !== "short")
    .map((q) => [q.id, q.answer!]),
);
describe("SQLite persistence and migrations", () => {
  it("persists assessment, notes, goal and review across restart", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "corelab-"));
    const db = path.join(dir, "progress.sqlite");
    try {
      let store = new Store(db);
      const a = store.attempt("M01", answers, "A0");
      applyAction(store, {
        type: "session",
        topicId: "M01",
        kind: "note",
        text: "My derivation",
        minutes: 15,
      });
      applyAction(store, {
        type: "goal",
        goal: "Robotics",
        focusTopic: "R04",
        focusReason: "camera project",
      });
      store.close();
      store = new Store(db);
      const p = store.read();
      expect(p.attempts[0].id).toBe(a.id);
      expect(p.sessions[0].text).toBe("My derivation");
      expect(p.focusTopic).toBe("R04");
      expect(p.reviews[0].lastAttemptId).toBe(a.id);
      expect(masteryFor("M01", p).level).toBe(1);
      store.close();
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
  it("migrates an existing v1 database without losing progress", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "corelab-migrate-"));
    const db = path.join(dir, "old.sqlite");
    try {
      let s = new Store(db);
      s.attempt("M01", answers, "A0");
      s.db.exec("DROP TABLE restore_snapshots; PRAGMA user_version=1");
      s.close();
      s = new Store(db);
      expect(s.read().attempts).toHaveLength(1);
      expect(s.db.prepare("PRAGMA user_version").get()).toMatchObject({
        user_version: 2,
      });
      expect(
        s.db.prepare("SELECT COUNT(*) AS n FROM restore_snapshots").get(),
      ).toMatchObject({ n: 0 });
      s.close();
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
  it("rolls back a failing update", () => {
    const s = new Store(":memory:");
    expect(() =>
      s.update((p) => {
        p.goal = "Robotics";
        throw new Error("abort");
      }),
    ).toThrow();
    expect(s.read().goal).toBe("Foundations");
    s.close();
  });
  it("keeps the review date when a learner repeats an early passing quiz", () => {
    const s = new Store(":memory:");
    s.attempt("M01", answers, "A0");
    const before = s.read().reviews[0].due;
    s.attempt("M01", answers, "A0");
    expect(s.read().reviews[0].due).toBe(before);
    s.close();
  });
});
describe("backup restore and integrity", () => {
  it("round-trips all progress into a fresh database", () => {
    const first = new Store(":memory:");
    first.attempt("M01", answers, "A0");
    applyAction(first, {
      type: "session",
      topicId: "M01",
      kind: "difficulty",
      text: "Inverse versus reciprocal",
      minutes: 10,
    });
    const backup = first.export();
    const next = new Store(":memory:");
    next.restore(backup, true);
    expect(next.read()).toEqual(first.read());
    first.close();
    next.close();
  });
  it("requires explicit replacement confirmation", () => {
    const s = new Store(":memory:");
    expect(() => s.restore(s.export(), false)).toThrow("confirmation");
    s.close();
  });
  it("regrades imported attempts rather than trusting supplied scores", () => {
    const s = new Store(":memory:");
    s.attempt("M01", {}, "A0");
    const b = s.export();
    b.progress.attempts[0].grade.passed = true;
    b.progress.attempts[0].grade.score = 100;
    const p = validateBackup(b);
    expect(p.attempts[0].grade.passed).toBe(false);
    expect(masteryFor("M01", p).level).toBe(0);
    s.close();
  });
  it("rejects unknown schema without losing current records", () => {
    const s = new Store(":memory:");
    s.attempt("M01", answers, "A0");
    const before = s.read();
    expect(() =>
      s.restore({ ...s.export(), schema: "corelab-backup/9" }, true),
    ).toThrow();
    expect(s.read()).toEqual(before);
    s.close();
  });
  it("rejects unknown topics, duplicate record IDs, future evidence and dangling review", () => {
    const s = new Store(":memory:");
    s.attempt("M01", answers, "A0");
    for (const mutate of [
      (b: ReturnType<Store["export"]>) => {
        b.progress.attempts[0].topicId = "UNKNOWN";
      },
      (b: ReturnType<Store["export"]>) => {
        b.progress.attempts.push({ ...b.progress.attempts[0] });
      },
      (b: ReturnType<Store["export"]>) => {
        b.progress.attempts[0].at = "2099-01-01T00:00:00.000Z";
      },
      (b: ReturnType<Store["export"]>) => {
        b.progress.reviews[0].lastAttemptId = "missing";
      },
    ]) {
      const b = structuredClone(s.export());
      mutate(b);
      expect(() => validateBackup(b)).toThrow();
    }
    s.close();
  });
  it("preserves a snapshot before a confirmed replacement", () => {
    const s = new Store(":memory:");
    const initial = s.export();
    s.attempt("M01", answers, "A0");
    s.restore(initial, true);
    expect(s.read().attempts).toHaveLength(0);
    const row = s.db.prepare("SELECT json FROM restore_snapshots").get() as {
      json: string;
    };
    expect(JSON.parse(row.json).attempts).toHaveLength(1);
    s.close();
  });
  it("rejects forged AI fields and separates AI feedback from mastery", () => {
    const s = new Store(":memory:");
    expect(() =>
      applyAction(s, {
        type: "feedback",
        feedback: {
          schema: "corelab-feedback/1",
          topicId: "M01",
          summary: "Understood",
          difficulties: [],
          nextSteps: [],
          verifiedLevel: 4,
        },
      }),
    ).toThrow();
    applyAction(s, {
      type: "feedback",
      feedback: {
        schema: "corelab-feedback/1",
        topicId: "M01",
        summary: "Understood",
        difficulties: ["Notation"],
        nextSteps: ["Try again"],
      },
    });
    expect(masteryFor("M01", s.read()).level).toBe(0);
    expect(s.read().sessions).toHaveLength(2);
    s.close();
  });
  it("rejects a provisional level attached to ordinary notes", () => {
    const s = new Store(":memory:");
    expect(() =>
      applyAction(s, {
        type: "session",
        topicId: "M01",
        kind: "note",
        text: "claim",
        minutes: 1,
        provisionalLevel: 4,
      }),
    ).toThrow();
    s.close();
  });
});
describe("signed local test reports", () => {
  function report() {
    const keys = generateKeyPairSync("ed25519");
    const payload = {
      schema: "corelab-lab/1",
      runner: "corelab-fixed-tests/1",
      topicId: "M02",
      at: new Date().toISOString(),
      assistance: "A0",
      sourceHash: "a".repeat(64),
      passed: true,
      checks: 8,
      publicKey: keys.publicKey
        .export({ type: "spki", format: "pem" })
        .toString(),
    };
    return {
      ...payload,
      signature: sign(
        null,
        Buffer.from(JSON.stringify(payload)),
        keys.privateKey,
      ).toString("base64"),
    };
  }
  it("checks signature and test-contract integrity", () => {
    const r = report();
    expect(validateLab(r).passed).toBe(true);
    expect(() => validateLab({ ...r, sourceHash: "b".repeat(64) })).toThrow(
      "signature",
    );
    expect(() => validateLab({ ...r, checks: 7 })).toThrow("contract");
  });
  it("retains signed lab provenance through backup restore", () => {
    const s = new Store(":memory:");
    const r = report();
    const b = s.export();
    b.progress.labs.push({
      id: "lab",
      topicId: r.topicId,
      at: r.at,
      assistance: "A0",
      sourceHash: r.sourceHash,
      report: JSON.stringify(r),
      signature: r.signature,
      trusted: true,
    });
    s.restore(b, true);
    expect(s.read().labs[0].signature).toBe(r.signature);
    const bad = structuredClone(b);
    bad.progress.labs[0].topicId = "PY01";
    expect(() => validateBackup(bad)).toThrow("provenance");
    s.close();
  });
  it("requires this workspace’s signing key for a new HTTP lab import", () => {
    const s = new Store(":memory:");
    expect(() => applyAction(s, { type: "lab", report: report() })).toThrow();
    s.close();
  });
});
