// Study desk storage and runner. Notes, exercise answers and code live as
// plain files in .local/desk/<TOPIC>/ so they can also be opened in an editor.
// Code runs with the learner's own Python 3 or C/C++ compiler, in that folder,
// with a time limit and capped output; it has the same rights as a terminal.
import { spawn } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import { topicMap } from "./curriculum";

export const NOTES = "notes.md";
export const ANSWERS = "exercises.json";
const FILE =
  /^[A-Za-z0-9][A-Za-z0-9_-]{0,47}\.(py|cpp|cc|c|h|hpp|md|txt|json)$/;
const MAX_FILE = 512 * 1024;
const MAX_FILES = 40;
const MAX_OUTPUT = 200 * 1024;

export function deskRoot() {
  return (
    process.env.CORELAB_DESK_DIR ?? path.join(process.cwd(), ".local", "desk")
  );
}

function topicDir(topic: string) {
  if (!topicMap[topic]) throw new Error("Unknown topic");
  return path.join(deskRoot(), topic);
}

export function checkFileName(name: string) {
  if (!FILE.test(name)) throw new Error("Invalid file name");
  return name;
}

export type DeskFile = { name: string; content: string; updated: number };

export function readDesk(topic: string) {
  const dir = topicDir(topic);
  const files: DeskFile[] = existsSync(dir)
    ? readdirSync(dir)
        .filter((f) => FILE.test(f))
        .sort()
        .map((name) => {
          const p = path.join(dir, name);
          return {
            name,
            content: readFileSync(p, "utf8"),
            updated: statSync(p).mtimeMs,
          };
        })
    : [];
  return { dir, files };
}

export function writeDeskFile(topic: string, name: string, content: string) {
  checkFileName(name);
  if (Buffer.byteLength(content) > MAX_FILE) throw new Error("File too large");
  const dir = topicDir(topic);
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const target = path.join(dir, name);
  if (
    !existsSync(target) &&
    readdirSync(dir).filter((f) => FILE.test(f)).length >= MAX_FILES
  )
    throw new Error("Too many files for this topic");
  writeFileSync(target, content, { mode: 0o600 });
}

export function deleteDeskFile(topic: string, name: string) {
  checkFileName(name);
  if (name === NOTES || name === ANSWERS)
    throw new Error("Notes and answers cannot be deleted");
  const target = path.join(topicDir(topic), name);
  if (existsSync(target)) unlinkSync(target);
}

export type RunResult = {
  command: string;
  exitCode: number | null;
  /** Set when the process was stopped by a signal (e.g. SIGABRT, SIGSEGV). */
  signal: string | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
  ms: number;
};

function collect(
  command: string,
  args: string[],
  cwd: string,
  timeoutMs: number,
): Promise<RunResult> {
  const started = Date.now();
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd,
      detached: process.platform !== "win32",
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        PYTHONDONTWRITEBYTECODE: "1",
        MPLBACKEND: "Agg",
      },
      windowsHide: true,
    });
    let stdout = "",
      stderr = "",
      timedOut = false;
    const take = (prev: string, chunk: Buffer) =>
      prev.length >= MAX_OUTPUT
        ? prev
        : (prev + chunk.toString("utf8")).slice(0, MAX_OUTPUT);
    child.stdout.on("data", (c: Buffer) => (stdout = take(stdout, c)));
    child.stderr.on("data", (c: Buffer) => (stderr = take(stderr, c)));
    const timer = setTimeout(() => {
      timedOut = true;
      try {
        // Kill the whole process group so child processes stop too.
        if (child.pid && process.platform !== "win32")
          process.kill(-child.pid, "SIGKILL");
        else child.kill("SIGKILL");
      } catch {
        child.kill("SIGKILL");
      }
    }, timeoutMs);
    const finish = (
      exitCode: number | null,
      error?: Error,
      signal: string | null = null,
    ) => {
      clearTimeout(timer);
      resolve({
        command: [command, ...args].join(" "),
        exitCode,
        signal: timedOut ? null : signal,
        stdout,
        stderr: error ? `${stderr}${error.message}\n` : stderr,
        timedOut,
        ms: Date.now() - started,
      });
    };
    child.on("error", (e) => finish(null, e));
    child.on("close", (code, signal) => finish(code, undefined, signal));
  });
}

function python() {
  return process.platform === "win32"
    ? { command: "py", args: ["-3"] }
    : { command: "python3", args: [] };
}

export async function runDeskFile(
  topic: string,
  name: string,
  timeoutMs = 20_000,
): Promise<RunResult> {
  checkFileName(name);
  const dir = topicDir(topic);
  const file = path.join(dir, name);
  if (!existsSync(file)) throw new Error("Save the file before running it");
  const limit = Math.min(Math.max(timeoutMs, 1000), 120_000);
  const ext = path.extname(name);
  if (ext === ".py") {
    const py = python();
    return collect(py.command, [...py.args, name], dir, limit);
  }
  if ([".cpp", ".cc", ".c"].includes(ext)) {
    const build = mkdtempSync(path.join(os.tmpdir(), "corelab-desk-"));
    try {
      const exe = path.join(
        build,
        process.platform === "win32" ? "main.exe" : "main",
      );
      const compiler = ext === ".c" ? "cc" : "c++";
      const std = ext === ".c" ? "-std=c11" : "-std=c++17";
      const compiled = await collect(
        compiler,
        [std, "-O1", "-Wall", "-Wextra", name, "-o", exe, "-lm"],
        dir,
        limit,
      );
      if (compiled.exitCode !== 0 || compiled.timedOut) return compiled;
      const ran = await collect(exe, [], dir, limit);
      return {
        ...ran,
        command: `${compiled.command} && ${exe}`,
        stderr: compiled.stderr + ran.stderr,
        ms: compiled.ms + ran.ms,
      };
    } finally {
      rmSync(build, { recursive: true, force: true });
    }
  }
  throw new Error("Only .py, .c and .cpp files can be run");
}
