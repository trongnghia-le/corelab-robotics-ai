#!/usr/bin/env node
// Intentionally local CLI only. Never import this module into an HTTP handler.
import { parseArgs } from "node:util";
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { fileURLToPath } from "node:url";
import { findPython } from "./runtime.mjs";
try {
  const { values } = parseArgs({
    options: {
      topic: { type: "string" },
      file: { type: "string" },
      assistance: { type: "string", default: "A0" },
      out: { type: "string" },
    },
  });
  if (
    !["M02", "PY01"].includes(values.topic) ||
    !values.file ||
    !["A0", "A1", "A2", "A3"].includes(values.assistance)
  )
    throw new Error(
      "Usage: npm run verify:lab -- --topic M02|PY01 --file /absolute/solution.py --assistance A0 --out .local/report.json",
    );
  const file = resolve(values.file);
  const source = readFileSync(file);
  const python = findPython();
  const result = spawnSync(
    python.executable,
    [
      fileURLToPath(new URL("./lab-tests.py", import.meta.url)),
      file,
      values.topic,
    ],
    {
      encoding: "utf8",
      timeout: 30000,
      maxBuffer: 1024 * 1024,
      windowsHide: true,
      shell: false,
    },
  );
  if (result.error)
    throw new Error(
      `Unable to run the local Python tests (${python.launcher}): ${result.error.message}. No evidence created.`,
    );
  if (result.status !== 0)
    throw new Error(
      `Fixed tests failed. No evidence created.\n${result.stderr || result.stdout}`,
    );
  const outcome = JSON.parse(result.stdout.trim().split("\n").at(-1));
  if (!outcome.passed) throw new Error("Tests did not pass");
  const keyPath = resolve(".local/lab-private.pem");
  mkdirSync(dirname(keyPath), { recursive: true, mode: 0o700 });
  if (!existsSync(keyPath)) {
    const keys = generateKeyPairSync("ed25519", {
      privateKeyEncoding: { type: "pkcs8", format: "pem" },
      publicKeyEncoding: { type: "spki", format: "pem" },
    });
    writeFileSync(keyPath, keys.privateKey, { mode: 0o600 });
    writeFileSync(resolve(".local/lab-public.pem"), keys.publicKey, {
      mode: 0o600,
    });
  }
  const payload = {
    schema: "corelab-lab/1",
    runner: "corelab-fixed-tests/1",
    topicId: values.topic,
    at: new Date().toISOString(),
    assistance: values.assistance,
    sourceHash: createHash("sha256").update(source).digest("hex"),
    passed: true,
    checks: outcome.checks,
    publicKey: readFileSync(resolve(".local/lab-public.pem"), "utf8"),
  };
  const report = {
    ...payload,
    signature: sign(
      null,
      Buffer.from(JSON.stringify(payload)),
      readFileSync(keyPath),
    ).toString("base64"),
  };
  const destination = resolve(
    values.out ?? `.local/${values.topic}-report.json`,
  );
  mkdirSync(dirname(destination), { recursive: true, mode: 0o700 });
  writeFileSync(destination, JSON.stringify(report, null, 2) + "\n", {
    mode: 0o600,
  });
  console.log(
    `Passed ${outcome.checks} test groups. Report: ${destination}\nImport it in CoreLab → Practice. Assistance is self-declared; this is local study evidence, not proctored certification.`,
  );
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
