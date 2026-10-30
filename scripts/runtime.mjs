import { spawnSync } from "node:child_process";
import path from "node:path";

/** Resolve fixed launchers without a shell; never parse a command supplied by a file. */
export function findPython({
  platform = process.platform,
  run = spawnSync,
} = {}) {
  const candidates =
    platform === "win32"
      ? [
          { command: "py", args: ["-3"] },
          { command: "python3", args: [] },
          { command: "python", args: [] },
        ]
      : [
          { command: "python3", args: [] },
          { command: "python", args: [] },
        ];
  const probe =
    'import json, sys; print(json.dumps({"major": sys.version_info[0], "version": sys.version.split()[0], "executable": sys.executable}))';
  const failures = [];
  for (const candidate of candidates) {
    const label = [candidate.command, ...candidate.args].join(" ");
    const result = run(
      candidate.command,
      [...candidate.args, "-I", "-c", probe],
      {
        encoding: "utf8",
        timeout: 3000,
        maxBuffer: 65536,
        windowsHide: true,
        shell: false,
      },
    );
    if (result.error || result.status !== 0) {
      failures.push(
        `${label}: ${result.error?.code ?? `exit ${result.status}`}`,
      );
      continue;
    }
    try {
      const info = JSON.parse(result.stdout.trim());
      const paths = platform === "win32" ? path.win32 : path;
      if (
        info.major !== 3 ||
        typeof info.executable !== "string" ||
        !paths.isAbsolute(info.executable) ||
        info.executable.includes("\0") ||
        typeof info.version !== "string"
      )
        throw new Error("Not a usable Python 3 interpreter");
      return {
        executable: info.executable,
        version: info.version,
        launcher: label,
      };
    } catch {
      failures.push(`${label}: did not identify Python 3`);
    }
  }
  throw new Error(
    `Python 3 is required for local lab verification. Install Python 3 and reopen your terminal. Check ${platform === "win32" ? "py -3 --version or python --version" : "python3 --version or python --version"}. Tried: ${failures.join("; ")}. No evidence was created.`,
  );
}

export function nextArguments(command, args = []) {
  if (!["dev", "build", "start"].includes(command))
    throw new Error(
      "Usage: node scripts/run-next.mjs dev|build|start [Next.js options]",
    );
  if (args.some((arg) => arg.startsWith("--hostname") || arg.startsWith("-H")))
    throw new Error(
      "CoreLab binds to 127.0.0.1 for local use. Do not pass a hostname override.",
    );
  return [
    command,
    ...(command === "build" ? ["--webpack"] : ["--hostname", "127.0.0.1"]),
    ...args,
  ];
}
