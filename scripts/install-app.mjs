// Adds a "CoreLab" entry to the Linux app menu (GNOME, KDE, ...) that runs
// scripts/app.mjs, so studying starts with one click instead of a terminal.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
if (process.platform !== "linux") {
  console.error(
    "The menu entry is Linux-only. Elsewhere run `npm run app` and install the page from the browser (Install app).",
  );
  process.exit(1);
}
const dir = path.join(os.homedir(), ".local", "share", "applications");
const file = path.join(dir, "corelab.desktop");
// Prefer the PATH entry (stable across upgrades) over the versioned binary.
const node =
  spawnSync("which", ["node"], { encoding: "utf8" }).stdout.trim() ||
  process.execPath;
const quote = (s) => `"${s.replace(/(["`$\\])/g, "\\$1")}"`;
mkdirSync(dir, { recursive: true });
writeFileSync(
  file,
  [
    "[Desktop Entry]",
    "Type=Application",
    "Name=CoreLab",
    "Comment=Robotics & AI study app",
    `Exec=${quote(node)} ${quote(path.join(root, "scripts", "app.mjs"))}`,
    `Path=${root}`,
    `Icon=${path.join(root, "app", "icon.svg")}`,
    "Terminal=false",
    "Categories=Education;",
    "",
  ].join("\n"),
  { mode: 0o755 },
);
console.log(`Added CoreLab to the app menu (${file}).`);
