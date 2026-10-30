// Invoke Next through Node directly: no POSIX environment syntax or .cmd shell shims.
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { nextArguments } from "./runtime.mjs";
const require = createRequire(import.meta.url);
try {
  const args = nextArguments(process.argv[2], process.argv.slice(3));
  const child = spawn(
    process.execPath,
    [require.resolve("next/dist/bin/next"), ...args],
    {
      stdio: "inherit",
      env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
      shell: false,
    },
  );
  child.on("error", (error) => {
    console.error(`Unable to start Next.js: ${error.message}`);
    process.exitCode = 1;
  });
  for (const signal of ["SIGINT", "SIGTERM"])
    process.on(signal, () => {
      if (child.exitCode === null) child.kill(signal);
    });
  child.on("exit", (code, signal) => {
    process.exitCode = code ?? (signal === "SIGINT" ? 130 : 1);
  });
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
