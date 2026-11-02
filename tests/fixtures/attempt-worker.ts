// Test-owned process for SQLite race probes. Never runs learner code.
import { Store } from "../../lib/storage";
import { submit } from "../../lib/v2/attempts";
import { assistCM, submitCM } from "../../lib/v2/verification";
import { cmSources, type SourceResolver } from "../../lib/v2/assessments";
import { write } from "../../lib/v2/db";
const resolve: SourceResolver = (id, v) => {
  const s = cmSources().find((s) => s.id === id && s.version === v);
  return s
    ? {
        ...s,
        review: {
          status: "approved",
          reviewer: "Synthetic concurrency fixture, NOT independent review",
          date: "2020-01-01",
        },
      }
    : undefined;
};
if (!process.argv[2])
  throw new Error(
    "Concurrency fixture requires an explicit temporary database",
  );
const store = new Store(process.argv[2]);
process.send?.({ ready: true });
process.once(
  "message",
  (message: {
    action: string;
    id: string;
    answers: Record<string, string>;
  }) => {
    try {
      if (message.action === "profileWrites") {
        for (let i = 1; i <= 100; i++) {
          write(store.db, () => {
            const p = store.read();
            p.focusReason = String(i);
            store.db
              .prepare("UPDATE state SET json=? WHERE id=1")
              .run(JSON.stringify(p));
            store.db
              .prepare(
                "INSERT INTO v2_prefs VALUES ('goal',?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
              )
              .run(JSON.stringify(String(i)));
          });
          Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 2);
        }
        process.send?.({ ok: true });
        return;
      }
      const result =
        message.action === "assistCM"
          ? assistCM(store, message.id, 3, resolve)
          : message.action === "submitCM"
            ? submitCM(
                store,
                message.id,
                { answers: message.answers, declaredAssistance: 0 },
                resolve,
              )
            : submit(store, message.id, {
                answers: message.answers,
                declaredAssistance: 0,
              });
      process.send?.({ ok: true, result });
    } catch (e) {
      process.send?.({
        ok: false,
        error: e instanceof Error ? e.message : "failed",
      });
    } finally {
      store.close();
      process.disconnect();
    }
  },
);
