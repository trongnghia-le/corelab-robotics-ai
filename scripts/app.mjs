// One-click launcher: keeps a production server running in the background and
// opens CoreLab in an app window. Rebuilds only when the checked-out commit changes.
//   node scripts/app.mjs          open (build/start if needed)
//   node scripts/app.mjs stop     stop the background server
import { spawn, spawnSync } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  openSync,
  readFileSync,
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

function commit() {
  const r = spawnSync("git", ["rev-parse", "HEAD"], {
    cwd: root,
    encoding: "utf8",
  });
  return r.status === 0 ? r.stdout.trim() : "no-git";
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
  writeFileSync(stampFile, commit());
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

function open() {
  if (process.platform === "darwin") return spawn("open", [url]).unref();
  if (process.platform === "win32")
    return spawn("cmd", ["/c", "start", "", url], { shell: false }).unref();
  // A Chromium-family browser gives a standalone app window.
  for (const b of [
    "google-chrome",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "microsoft-edge",
  ]) {
    const exe = which(b);
    if (exe)
      return spawn(exe, [`--app=${url}`], {
        detached: true,
        stdio: "ignore",
      }).unref();
  }
  spawn("xdg-open", [url], { detached: true, stdio: "ignore" }).unref();
}

async function main() {
  mkdirSync(local, { recursive: true, mode: 0o700 });
  if (process.argv[2] === "stop") return stop();
  const fresh =
    existsSync(path.join(root, ".next", "BUILD_ID")) &&
    read(stampFile) === commit();
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
