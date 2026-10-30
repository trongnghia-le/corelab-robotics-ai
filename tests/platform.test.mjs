import { describe, it, expect } from "vitest";
import { execFileSync } from "node:child_process";
import {
  mkdtempSync,
  readFileSync,
  writeFileSync,
  rmSync,
  existsSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { findPython, nextArguments } from "../scripts/runtime.mjs";
import { validateLab } from "../lib/labs.ts";
import { Store } from "../lib/storage.ts";
const identified = (executable) => ({
  status: 0,
  stdout: JSON.stringify({ major: 3, version: "3.12.1", executable }),
});
describe("portable process launching", () => {
  it("keeps dev/start on loopback and the webpack build portable", () => {
    expect(nextArguments("dev", ["--port", "3001"])).toEqual([
      "dev",
      "--hostname",
      "127.0.0.1",
      "--port",
      "3001",
    ]);
    expect(nextArguments("start")).toEqual([
      "start",
      "--hostname",
      "127.0.0.1",
    ]);
    expect(nextArguments("build")).toEqual(["build", "--webpack"]);
    for (const flag of ["--hostname", "--hostname=0.0.0.0", "-H", "-H0.0.0.0"])
      expect(() => nextArguments("dev", [flag])).toThrow("hostname override");
    expect(() => nextArguments("shell")).toThrow("Usage");
  });
  it("uses python3 without invoking a shell", () => {
    const calls = [];
    const result = findPython({
      platform: "linux",
      run: (command, args, options) => {
        calls.push({ command, args, options });
        return identified("/opt/Python 3/python3");
      },
    });
    expect(result.executable).toBe("/opt/Python 3/python3");
    expect(calls).toHaveLength(1);
    expect(calls[0].command).toBe("python3");
    expect(calls[0].args.slice(0, 2)).toEqual(["-I", "-c"]);
    expect(calls[0].options).toMatchObject({
      shell: false,
      timeout: 3000,
      windowsHide: true,
    });
  });
  it("falls back to python after an unavailable or invalid interpreter", () => {
    for (const failure of [
      { status: null, error: { code: "ENOENT" } },
      { status: 1, stdout: "Microsoft Store alias" },
      { status: 0, stdout: "not JSON" },
      {
        status: 0,
        stdout: JSON.stringify({
          major: 2,
          version: "2.7",
          executable: "/usr/bin/python",
        }),
      },
      {
        status: 0,
        stdout: JSON.stringify({
          major: 3,
          version: "3.12",
          executable: "relative/python",
        }),
      },
    ]) {
      const calls = [];
      const result = findPython({
        platform: "darwin",
        run: (command) => {
          calls.push(command);
          return command === "python3"
            ? failure
            : identified("/usr/local/bin/python");
        },
      });
      expect(calls).toEqual(["python3", "python"]);
      expect(result.launcher).toBe("python");
    }
  });
  it("supports the Windows py -3 launcher and safely retains a spaced Unicode executable path", () => {
    const calls = [];
    const executable = "C:\\Users\\Learner\\Python 安装\\python.exe";
    const result = findPython({
      platform: "win32",
      run: (command, args) => {
        calls.push({ command, args });
        return identified(executable);
      },
    });
    expect(calls[0].command).toBe("py");
    expect(calls[0].args.slice(0, 3)).toEqual(["-3", "-I", "-c"]);
    expect(result.executable).toBe(executable);
  });
  it("skips a missing/timed-out Windows launcher and fails with useful install guidance", () => {
    const calls = [];
    expect(() =>
      findPython({
        platform: "win32",
        run: (command) => {
          calls.push(command);
          return { status: null, error: { code: "ETIMEDOUT" } };
        },
      }),
    ).toThrow("py -3 --version or python --version");
    expect(calls).toEqual(["py", "python3", "python"]);
  });
});

describe("real local files and evidence on the current operating system", () => {
  it("verifies both labs from a spaced Unicode working directory, reuses signing keys, and creates no evidence on failure", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "CoreLab labs "));
    const verifier = fileURLToPath(
      new URL("../scripts/verify-lab.mjs", import.meta.url),
    );
    try {
      const source = path.join(dir, "solution 数学 with spaces.py");
      const code =
        'def dot(u,v):\n    if len(u)!=len(v): raise ValueError("shape")\n    return sum(a*b for a,b in zip(u,v))\ndef mean(values):\n    if not values: raise ValueError("empty")\n    return sum(values)/len(values)\n';
      writeFileSync(source, code);
      let key;
      for (const topic of ["M02", "PY01"]) {
        const out = path.join(dir, `report ${topic}.json`);
        const stdout = execFileSync(
          process.execPath,
          [verifier, "--topic", topic, "--file", source, "--out", out],
          { cwd: dir, encoding: "utf8", timeout: 30000 },
        );
        expect(stdout).toContain("Passed");
        const report = validateLab(JSON.parse(readFileSync(out, "utf8")));
        expect(report.topicId).toBe(topic);
        expect(report.sourceHash).toBe(
          createHash("sha256").update(code).digest("hex"),
        );
        if (key) expect(report.publicKey).toBe(key);
        key = report.publicKey;
      }
      const privateKey = readFileSync(
        path.join(dir, ".local", "lab-private.pem"),
        "utf8",
      );
      writeFileSync(source, "def dot(u,v): return 123\n");
      const failed = path.join(dir, "failed report.json");
      expect(() =>
        execFileSync(
          process.execPath,
          [verifier, "--topic", "M02", "--file", source, "--out", failed],
          { cwd: dir, stdio: "pipe", timeout: 30000 },
        ),
      ).toThrow();
      expect(existsSync(failed)).toBe(false);
      expect(
        readFileSync(path.join(dir, ".local", "lab-private.pem"), "utf8"),
      ).toBe(privateKey);
    } finally {
      rmSync(dir, {
        recursive: true,
        force: true,
        maxRetries: 5,
        retryDelay: 100,
      });
    }
  }, 60000);
  it("initializes nested native paths and preserves progress through restart and a file-based backup restore", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "CoreLab storage "));
    let store;
    try {
      const db = path.join(dir, "data 数学", "nested dir", "progress.sqlite");
      store = new Store(db);
      store.update((p) => {
        p.sessions.push({
          id: "portable-note",
          topicId: "M01",
          at: new Date().toISOString(),
          kind: "note",
          text: "Units and notation — 单位",
          minutes: 5,
        });
      });
      const backup = store.export();
      store.close();
      store = new Store(db);
      expect(store.read()).toEqual(backup.progress);
      store.close();
      store = undefined;
      const filename = path.join(dir, "backup 学习.json");
      writeFileSync(filename, JSON.stringify(backup));
      store = new Store(path.join(dir, "restored data", "progress.sqlite"));
      store.restore(JSON.parse(readFileSync(filename, "utf8")), true);
      expect(store.read()).toEqual(backup.progress);
    } finally {
      store?.close();
      rmSync(dir, {
        recursive: true,
        force: true,
        maxRetries: 5,
        retryDelay: 100,
      });
    }
  });
});
