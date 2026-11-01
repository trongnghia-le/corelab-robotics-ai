// Explicit, synthetic in-memory benchmark. Never opens the configured learner DB.
import { cpus, platform, arch } from "node:os";
import { performance } from "node:perf_hooks";
import { Store } from "../lib/storage";
import { issue, attemptById, history } from "../lib/v2/attempts";
import { initialize, write, setMeta, checkCapacity } from "../lib/v2/db";
import { select } from "../lib/v2/read-model";
const store = new Store(":memory:");
try {
  initialize(store.db);
  const first = issue(store, { purpose: "practice", source: "XB1" });
  const a = attemptById(store.db, first.id);
  const e = {
    ...(store.db
      .prepare("SELECT * FROM v2_exposures WHERE attempt_id=?")
      .get(a.id) as Record<string, string | number>),
  };
  const acols = Object.keys(a),
    ecols = Object.keys(e);
  const ai = store.db.prepare(
    "INSERT INTO v2_attempts (" +
      acols.join(",") +
      ") VALUES (" +
      acols.map(() => "?").join(",") +
      ")",
  );
  const ei = store.db.prepare(
    "INSERT INTO v2_exposures (" +
      ecols.join(",") +
      ") VALUES (" +
      ecols.map(() => "?").join(",") +
      ")",
  );
  write(store.db, () => {
    for (let i = 1; i < 50000; i++) {
      const id = "synthetic-load-" + i,
        seq = i * 2 + 1;
      ai.run(...Object.values({ ...a, id, issued_seq: seq }));
      ei.run(
        ...Object.values({
          ...e,
          id: "synthetic-exposure-" + i,
          attempt_id: id,
          event_seq: seq + 1,
        }),
      );
    }
    setMeta(store.db, "next_event_seq", 100001);
  });
  const timings: number[] = [];
  let payload = 0;
  for (let i = 0; i < 10; i++) {
    const start = performance.now(),
      result = select(store, new URLSearchParams());
    timings.push(performance.now() - start);
    payload = Buffer.byteLength(JSON.stringify(result));
  }
  const historyBytes = Buffer.byteLength(JSON.stringify(history(store, 50)));
  console.log(
    JSON.stringify(
      {
        fixture:
          "50000 valid repeated issued practice attempts and issue exposures; one bridge source, no artifacts",
        node: process.version,
        os: platform(),
        arch: arch(),
        cpu: cpus()[0]?.model,
        attempts: 50000,
        selectorMilliseconds: timings.map((t) => Math.round(t * 100) / 100),
        maxMilliseconds: Math.max(...timings),
        payloadBytes: payload,
        historyPageBytes: historyBytes,
        capacity: checkCapacity(store.db),
        rssBytes: process.memoryUsage().rss,
        limit:
          "Author-side single-machine in-memory measurement; not disk/restore or general OS qualification",
      },
      null,
      2,
    ),
  );
} finally {
  store.close();
}
