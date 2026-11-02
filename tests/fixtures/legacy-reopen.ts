// Executes trusted, owner-selected historical CoreLab source against a temp DB.
import { pathToFileURL } from "node:url";
import path from "node:path";
if (!process.argv[2] || !process.argv[3])
  throw new Error(
    "Explicit trusted baseline source and temporary database required",
  );
const { Store } = await import(
  pathToFileURL(path.join(process.argv[2], "lib/storage.ts")).href
);
const store = new Store(process.argv[3]);
try {
  const before = store.export();
  store.update((p: { focusReason: string }) => {
    p.focusReason = "edited by original V1 source";
  });
  store.restore(before, true);
  console.log(
    JSON.stringify({
      restored:
        JSON.stringify(store.read()) === JSON.stringify(before.progress),
      sidecarRows: store.db.prepare("SELECT count(*) n FROM v2_attempts").get()
        .n,
      version: store.db.prepare("PRAGMA user_version").get().user_version,
    }),
  );
} finally {
  store.close();
}
