import { expect, it } from "vitest";
import { fork, type ChildProcess } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { Store } from "../../lib/storage";
import { initialize, learningData, write } from "../../lib/v2/db";
import { exportBackup } from "../../lib/v2/backup";
import { issue } from "../../lib/v2/attempts";
import { family } from "../../lib/v2/content";
import { issueCM } from "../../lib/v2/verification";
import { cmSources, type SourceResolver } from "../../lib/v2/assessments";
type Message = { action: string; id: string; answers: Record<string, string> };
async function race(file: string, messages: Message[]) {
  const children: ChildProcess[] = [];
  try {
    const jobs = await Promise.all(
      messages.map(async (message) => {
        const child = fork("tests/fixtures/attempt-worker.ts", [file], {
          execArgv: ["--import", "tsx"],
          stdio: ["ignore", "pipe", "pipe", "ipc"],
        });
        children.push(child);
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(
            () => reject(new Error("Worker readiness timeout")),
            10000,
          );
          child.once("error", reject);
          child.once("exit", (code) => {
            if (code) reject(new Error("Worker exited " + code));
          });
          child.once("message", () => {
            clearTimeout(timeout);
            resolve();
          });
        });
        return { child, message };
      }),
    );
    const results = jobs.map(
      ({ child }) =>
        new Promise<{ ok: boolean; error?: string }>((resolve, reject) => {
          const timeout = setTimeout(
            () => reject(new Error("Concurrent write timeout")),
            15000,
          );
          child.once("message", (result) => {
            clearTimeout(timeout);
            resolve(result as { ok: boolean; error?: string });
          });
          child.once("error", reject);
        }),
    );
    jobs.forEach(({ child, message }) => child.send(message));
    return await Promise.all(results);
  } finally {
    children.forEach((c) => {
      if (c.exitCode === null) c.kill();
    });
  }
}
it("two independent processes submitting the same attempt store exactly one result and feedback exposure", async () => {
  const dir = mkdtempSync(path.join(tmpdir(), "corelab-race-")),
    file = path.join(dir, "test.sqlite"),
    s = new Store(file);
  try {
    initialize(s.db);
    const a = issue(s, { purpose: "practice", source: "X01" }),
      item = family("X01")!.items.find((i) => i.id === a.item.id)!;
    const answers = Object.fromEntries(
      item.fields.map((f, i) => [String(i), Number(f.answer).toFixed(9)]),
    );
    const results = await race(file, [
      { action: "submit", id: a.id, answers },
      { action: "submit", id: a.id, answers },
    ]);
    expect(
      results.every((r) => r.ok),
      JSON.stringify(results),
    ).toBe(true);
    const data = learningData(s.db);
    expect(data.v2_attempts).toHaveLength(1);
    expect(data.v2_attempts[0].status).toBe("submitted");
    expect(data.v2_exposures.filter((e) => e.kind === "feedback")).toHaveLength(
      1,
    );
  } finally {
    s.close();
    rmSync(dir, { recursive: true, force: true });
  }
}, 25000);
it("exports one consistent legacy/sidecar snapshot while another process commits paired updates", async () => {
  const dir = mkdtempSync(path.join(tmpdir(), "corelab-export-race-")),
    file = path.join(dir, "test.sqlite"),
    s = new Store(file);
  let child: ChildProcess | undefined;
  try {
    initialize(s.db);
    write(s.db, () => {
      const p = s.read();
      p.focusReason = "0";
      s.db.prepare("UPDATE state SET json=? WHERE id=1").run(JSON.stringify(p));
      s.db.prepare("INSERT INTO v2_prefs VALUES ('goal','\"0\"')").run();
    });
    child = fork("tests/fixtures/attempt-worker.ts", [file], {
      execArgv: ["--import", "tsx"],
      stdio: ["ignore", "pipe", "pipe", "ipc"],
    });
    await new Promise<void>((resolve, reject) => {
      child!.once("message", () => resolve());
      child!.once("error", reject);
    });
    const done = new Promise<{ ok: boolean }>((resolve, reject) => {
      child!.once("message", (r) => resolve(r as { ok: boolean }));
      child!.once("error", reject);
    });
    child.send({ action: "profileWrites", id: "unused", answers: {} });
    const seen = new Set<string>();
    for (let i = 0; i < 150; i++) {
      const backup = exportBackup(s);
      const legacy = backup.legacy as { progress: { focusReason: string } };
      const paired = JSON.parse(
        backup.v2.prefs.find((p) => p.key === "goal")!.value_json,
      );
      expect(legacy.progress.focusReason).toBe(paired);
      seen.add(paired);
      // Yield CPU without allowing any unrelated write on this connection.
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 2);
    }
    expect((await done).ok).toBe(true);
    expect(seen.size).toBeGreaterThan(1);
    expect(s.read().focusReason).toBe("100");
  } finally {
    if (child?.exitCode === null) child.kill();
    s.close();
    rmSync(dir, { recursive: true, force: true });
  }
}, 25000);
it("cross-process help/close ordering cannot grant independent C/M after committed help", async () => {
  const dir = mkdtempSync(path.join(tmpdir(), "corelab-cm-race-")),
    file = path.join(dir, "test.sqlite"),
    s = new Store(file);
  const resolve: SourceResolver = (id, v) => {
    const source = cmSources().find((s) => s.id === id && s.version === v);
    return source
      ? {
          ...source,
          review: {
            status: "approved",
            reviewer: "Synthetic test fixture, NOT review",
            date: "2020-01-01",
          },
        }
      : undefined;
  };
  try {
    initialize(s.db);
    const a = issueCM(s, { purpose: "verify", source: "F-R04" }, resolve),
      variant = resolve("F-R04", 1)!.variants.find(
        (v) => v.id === a.item.route,
      )!;
    const answers = Object.fromEntries(
      variant.items.flatMap((c, i) =>
        c.task.fields.map((f, j) => [
          i + "." + j,
          f.kind === "choice" ? f.answer : Number(f.answer).toFixed(9),
        ]),
      ),
    );
    const results = await race(file, [
      { action: "submitCM", id: a.id, answers },
      { action: "assistCM", id: a.id, answers: {} },
    ]);
    expect(results[0].ok, JSON.stringify(results)).toBe(true);
    const data = learningData(s.db),
      observed = data.v2_attempts[0].observed_level;
    if (results[1].ok) {
      expect(observed).toBe(3);
      expect(data.v2_evidence.every((e) => e.outcome === "not_admitted")).toBe(
        true,
      );
    } else {
      expect(results[1].error).toContain("closed");
      expect(observed).toBe(0);
      expect(data.v2_evidence.every((e) => e.outcome === "admitted")).toBe(
        true,
      );
    }
  } finally {
    s.close();
    rmSync(dir, { recursive: true, force: true });
  }
}, 25000);
