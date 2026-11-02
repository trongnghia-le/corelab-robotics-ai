// Production-build restart qualification. Every server uses a new temporary DB,
// localhost binding and its own child process; no signing CLI is invoked.
import assert from "node:assert/strict";
import { spawn, type ChildProcess } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir, platform } from "node:os";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";
import { setTimeout as delay } from "node:timers/promises";
import { chromium, expect } from "@playwright/test";
import { status, rows } from "../lib/v2/db";

const directory = mkdtempSync(path.join(tmpdir(), "corelab-toggle-")),
  file = path.join(directory, "history.sqlite"),
  browser = await chromium.launch();
let child: ChildProcess | undefined;
async function stop() {
  const process = child;
  child = undefined;
  if (!process || process.exitCode !== null) return;
  const closed = new Promise<void>((resolve) =>
    process.once("close", () => resolve()),
  );
  process.kill("SIGTERM");
  const timer = setTimeout(() => process.kill("SIGKILL"), 10000);
  try {
    await closed;
  } finally {
    clearTimeout(timer);
  }
}
async function start(flag: string) {
  await stop();
  const socket = createServer();
  await new Promise<void>((resolve, reject) => {
    socket.once("error", reject);
    socket.listen(0, "127.0.0.1", () => resolve());
  });
  const port = (socket.address() as { port: number }).port;
  await new Promise<void>((resolve, reject) =>
    socket.close((error) => (error ? reject(error) : resolve())),
  );
  const base = "http://127.0.0.1:" + port;
  child = spawn(
    process.execPath,
    [
      "node_modules/next/dist/bin/next",
      "start",
      "--hostname",
      "127.0.0.1",
      "--port",
      String(port),
    ],
    {
      env: {
        ...process.env,
        CORELAB_V2: flag,
        CORELAB_DB_PATH: file,
        NEXT_TELEMETRY_DISABLED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
      shell: false,
      windowsHide: true,
    },
  );
  let log = "";
  child.stdout?.on("data", (chunk) => {
    log = (log + String(chunk)).slice(-8000);
  });
  child.stderr?.on("data", (chunk) => {
    log = (log + String(chunk)).slice(-8000);
  });
  child.on("error", (error) => {
    log += error.message;
  });
  for (let i = 0; i < 300; i++) {
    if (child.exitCode !== null)
      throw new Error("Owned test server exited: " + log);
    try {
      const response = await fetch(base + "/api/state", {
        signal: AbortSignal.timeout(1000),
      });
      if (response.ok) return base;
    } catch {}
    await delay(100);
  }
  throw new Error("Owned test server did not become ready: " + log);
}
async function post(base: string, pathname: string, body: unknown) {
  return fetch(base + pathname, {
    method: "POST",
    headers: { Origin: base, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
function inspect() {
  const db = new DatabaseSync(file, { readOnly: true });
  try {
    return {
      status: status(db),
      attempts: status(db) === "supported" ? rows(db, "v2_attempts") : [],
    };
  } finally {
    db.close();
  }
}
try {
  const page = await browser.newPage();
  let base = await start("");
  assert.equal((await fetch(base + "/api/v2/objectives")).status, 404);
  await page.goto(base);
  await expect(
    page.getByRole("link", { name: "Objective learning · V2" }),
  ).toHaveCount(0);
  assert.equal((await page.goto(base + "/objectives"))?.status(), 404);
  await stop();
  assert.equal(inspect().status, "absent");

  base = await start("1");
  await page.goto(base + "/objectives");
  await expect(
    page.getByRole("heading", { name: "Your next independent step." }),
  ).toBeVisible();
  const issued = await post(base, "/api/v2/attempts", {
    purpose: "practice",
    source: "X11",
  });
  assert.equal(issued.status, 201);
  const opened = await issued.json();
  await stop();
  const initial = inspect();
  assert.equal(initial.status, "supported");
  assert.equal(initial.attempts.length, 1);

  base = await start("true"); // Only exactly "1" enables V2.
  assert.equal((await fetch(base + "/api/v2/objectives")).status, 404);
  await page.goto(base);
  await expect(
    page.getByRole("link", { name: "Objective learning · V2" }),
  ).toHaveCount(0);
  const edited = await post(base, "/api/action", {
    type: "goal",
    goal: "Foundations",
    focusTopic: null,
    focusReason: "Legacy edit while V2 was off",
  });
  assert.equal(edited.status, 200);
  await stop();
  assert.deepEqual(inspect().attempts, initial.attempts);

  base = await start("1");
  await page.goto(base + "/objectives");
  await expect(
    page.getByRole("heading", { name: "Your next independent step." }),
  ).toBeVisible();
  const summary = await (await fetch(base + "/api/v2/objectives")).json();
  assert.equal(typeof summary.historyAcknowledgement, "string");
  const blocked = await post(base, "/api/v2/attempts", {
    purpose: "practice",
    source: "X10",
  });
  assert.equal(blocked.status, 409);
  const ack = await post(base, "/api/v2/history/acknowledge", {
    token: summary.historyAcknowledgement,
  });
  assert.equal(ack.status, 200);
  const resumed = await fetch(base + "/api/v2/attempts/" + opened.id);
  assert.equal(resumed.status, 200);
  assert.equal((await resumed.json()).id, opened.id);
  assert.equal(
    (
      await post(base, "/api/v2/attempts", {
        purpose: "practice",
        source: "X10",
      })
    ).status,
    201,
  );
  const state = await (await fetch(base + "/api/state")).json();
  assert.equal(state.progress.focusReason, "Legacy edit while V2 was off");
  console.log(
    JSON.stringify({
      passed: true,
      node: process.version,
      os: platform(),
      flow: "fresh off → on/practice → off/legacy edit → on/acknowledge/resume",
      limit:
        "One Linux Chromium production-build restart check; not other-OS or screen-reader qualification",
    }),
  );
} finally {
  await browser.close();
  await stop();
  rmSync(directory, { recursive: true, force: true });
}
