// Owner-operated local maintenance; never import into an HTTP route.
import { parseArgs } from "node:util";
import { DatabaseSync } from "node:sqlite";
import { existsSync } from "node:fs";
import path from "node:path";
import { copyDatabase } from "../lib/v2/db";
try {
  const { values } = parseArgs({
    options: { db: { type: "string" }, "server-stopped": { type: "boolean" } },
  });
  if (!values.db || !values["server-stopped"])
    throw new Error(
      "Stop CoreLab, then run: npm run recovery:v2 -- --db /absolute/path/corelab.sqlite --server-stopped",
    );
  const file = path.resolve(values.db);
  if (!existsSync(file))
    throw new Error("Database does not exist; no empty database was created");
  const db = new DatabaseSync(file, { readOnly: true });
  try {
    const target = copyDatabase(db);
    console.log("Verified current SQLite recovery copy:", target);
    console.log(
      "Keep the original file and its -wal/-shm siblings. To inspect recovery, set CORELAB_DB_PATH to this copy and start CoreLab locally. Do not overwrite the original. Export a validated learning backup after reopening.",
    );
  } finally {
    db.close();
  }
} catch (e) {
  console.error(e instanceof Error ? e.message : "Recovery copy failed");
  process.exitCode = 1;
}
