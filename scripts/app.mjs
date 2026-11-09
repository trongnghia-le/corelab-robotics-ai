// One-click launcher: keeps a production server running in the background and
// opens CoreLab in an app window. Rebuilds only when the code changes (a new
// commit, `git pull`, or uncommitted edits).
//   node scripts/app.mjs          open (build/start if needed)
//   node scripts/app.mjs stop     stop the background server
//   CORELAB_DESK=1 node scripts/app.mjs   also open the study desk as its own window
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  openSync,
  readFileSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number(process.env.CORELAB_APP_PORT ?? 3210);
const url = `http://127.0.0.1:${port}`;
const local = path.join(root, ".local");
const pidFile = path.join(local, "app.pid");
const stampFile = path.join(local, "app-build.txt");
const logFile = path.join(local, "app.log");
const next = require.resolve("next/dist/bin/next");
const env = { ...process.env, NEXT_TELEMETRY_DISABLED: "1" };

function git(args) {
  const r = spawnSync("git", args, {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 256 * 1024 * 1024,
  });
  return r.status === 0 ? r.stdout : null;
}

/** Fingerprint of the checked-out code: commit, uncommitted edits, new files. */
function version() {
  const head = git(["rev-parse", "HEAD"]);
  if (head === null) return "no-git";
  const hash = createHash("sha256").update(head);
  // next-env.d.ts flips between dev and build; it never changes the app.
  hash.update(
    git(["diff", "HEAD", "--", ".", ":(exclude)next-env.d.ts"]) ?? "",
  );
  for (const file of (
    git(["ls-files", "--others", "--exclude-standard", "-z"]) ?? ""
  )
    .split("\0")
    .filter(Boolean)) {
    const st = statSync(path.join(root, file), { throwIfNoEntry: false });
    hash.update(`${file}:${st?.size}:${st?.mtimeMs}\n`);
  }
  return hash.digest("hex");
}

function read(file) {
  return existsSync(file) ? readFileSync(file, "utf8").trim() : "";
}

async function up() {
  try {
    return (await fetch(url, { signal: AbortSignal.timeout(1500) })).ok;
  } catch {
    return false;
  }
}

function stop() {
  const pid = Number(read(pidFile));
  if (!pid) return;
  try {
    process.kill(pid, "SIGTERM");
  } catch {
    // Already gone.
  }
  writeFileSync(pidFile, "");
}

function build() {
  console.log("Building CoreLab (only after an update, about a minute)...");
  // `next build` rewrites next-env.d.ts for production; keep the dev version.
  const envFile = path.join(root, "next-env.d.ts");
  const saved = existsSync(envFile) ? readFileSync(envFile, "utf8") : null;
  const r = spawnSync(process.execPath, [next, "build", "--webpack"], {
    cwd: root,
    env,
    stdio: "inherit",
  });
  if (saved !== null) writeFileSync(envFile, saved);
  if (r.status !== 0) throw new Error("Build failed; see the output above.");
  writeFileSync(stampFile, version());
}

function start() {
  const log = openSync(logFile, "a");
  const child = spawn(
    process.execPath,
    [next, "start", "--hostname", "127.0.0.1", "--port", String(port)],
    { cwd: root, env, detached: true, stdio: ["ignore", log, log] },
  );
  child.unref();
  writeFileSync(pidFile, String(child.pid));
}

function which(command) {
  return spawnSync("which", [command], { encoding: "utf8" }).stdout.trim();
}

/** Usable screen size on Linux/X11 or XWayland, if xrandr can tell us. */
function screenSize() {
  const out = spawnSync("xrandr", ["--current"], { encoding: "utf8" }).stdout;
  const m = out?.match(/current (\d+) x (\d+)/);
  return m ? { w: Number(m[1]), h: Number(m[2]) } : null;
}

function open() {
  const desk = process.env.CORELAB_DESK === "1";
  if (process.platform === "darwin") return spawn("open", [url]).unref();
  if (process.platform === "win32")
    return spawn("cmd", ["/c", "start", "", url], { shell: false }).unref();
  // A Chromium-family browser gives a standalone app window. The study desk is
  // docked inside the page; CORELAB_DESK=1 also opens it as a second window.
  for (const b of [
    "google-chrome",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "microsoft-edge",
  ]) {
    const exe = which(b);
    if (!exe) continue;
    const size = screenSize();
    const split = size ? (desk ? Math.round(size.w * 0.58) : size.w) : 0;
    const app = (target, x, w) =>
      spawn(
        exe,
        [
          `--app=${target}`,
          ...(size
            ? [`--window-position=${x},0`, `--window-size=${w},${size.h}`]
            : []),
        ],
        { detached: true, stdio: "ignore" },
      ).unref();
    app(url, 0, split);
    if (desk)
      setTimeout(
        () => app(`${url}/desk`, split, size ? size.w - split : 0),
        600,
      );
    return;
  }
  spawn("xdg-open", [url], { detached: true, stdio: "ignore" }).unref();
}

async function main() {
  mkdirSync(local, { recursive: true, mode: 0o700 });
  if (process.argv[2] === "stop") return stop();
  const fresh =
    existsSync(path.join(root, ".next", "BUILD_ID")) &&
    read(stampFile) === version();
  if (fresh && (await up())) return open();
  stop();
  if (!fresh) build();
  start();
  for (let i = 0; i < 60; i++) {
    if (await up()) return open();
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`CoreLab did not start; see ${logFile}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
