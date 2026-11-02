import { afterEach, expect, it, vi } from "vitest";
vi.mock("node:fs", async (importOriginal) => {
  const actual = await importOriginal<typeof import("node:fs")>();
  return { ...actual, statfsSync: vi.fn(actual.statfsSync) };
});
import * as fs from "node:fs";
import path from "node:path";
import { tmpdir } from "node:os";
import { Store } from "../../lib/storage";
import { DatabaseSync } from "node:sqlite";
import {
  initialize,
  status,
  meta,
  write,
  learningData,
  schemaSQL,
} from "../../lib/v2/db";
import { issue } from "../../lib/v2/attempts";
const stores: Store[] = [],
  dirs: string[] = [];
afterEach(() => {
  vi.restoreAllMocks();
  stores.splice(0).forEach((s) => s.close());
  dirs.splice(0).forEach((d) => fs.rmSync(d, { recursive: true, force: true }));
});
it("rolls back a real SQLite page-capacity failure across rows and event counters", () => {
  const s = fresh();
  initialize(s.db);
  const pages = (
    s.db.prepare("PRAGMA page_count").get() as { page_count: number }
  ).page_count;
  s.db.exec("PRAGMA max_page_count=" + pages);
  let failed = false;
  for (let i = 0; i < 100; i++) {
    const before = learningData(s.db),
      counter = meta(s.db, "next_event_seq"),
      revision = meta(s.db, "data_revision");
    try {
      issue(s, { purpose: "practice", source: "X11" });
    } catch (e) {
      expect((e as Error).message).toMatch(/full/i);
      expect(learningData(s.db)).toEqual(before);
      expect(meta(s.db, "next_event_seq")).toBe(counter);
      expect(meta(s.db, "data_revision")).toBe(revision);
      failed = true;
      break;
    }
  }
  expect(failed).toBe(true);
  expect(s.read().attempts).toEqual([]);
});
function fresh() {
  const dir = fs.mkdtempSync(path.join(tmpdir(), "corelab-migration-failure-"));
  dirs.push(dir);
  const s = new Store(path.join(dir, "history.sqlite"));
  stores.push(s);
  return s;
}
it("keeps the legacy database untouched when pre-migration recovery headroom is unavailable", () => {
  const s = fresh(),
    before = s.read();
  vi.mocked(fs.statfsSync).mockReturnValueOnce({
    bavail: 0n,
    bsize: 4096n,
  } as never);
  expect(() => initialize(s.db)).toThrow("Insufficient free disk");
  expect(status(s.db)).toBe("absent");
  expect(s.read()).toEqual(before);
  expect(s.db.prepare("PRAGMA user_version").get()).toEqual({
    user_version: 2,
  });
});
it("does not modify a partial sidecar or a metadata contract changed by another connection", () => {
  const s = fresh();
  s.db.exec("CREATE TABLE v2_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)");
  expect(status(s.db)).toBe("unsupported");
  expect(() => initialize(s.db)).toThrow("unsupported");
  expect(s.db.prepare("SELECT count(*) n FROM v2_meta").get()).toEqual({
    n: 0,
  });
  const valid = fresh();
  initialize(valid.db);
  const revision = meta(valid.db, "data_revision");
  valid.db
    .prepare("UPDATE v2_meta SET value='not-a-uuid' WHERE key='workspace_id'")
    .run();
  expect(status(valid.db)).toBe("unsupported");
  expect(() =>
    write(valid.db, () => {
      throw Error("must not call");
    }),
  ).toThrow("Unsupported");
  expect(meta(valid.db, "data_revision")).toBe(revision);
  expect(() =>
    valid.update((p) => {
      p.focusReason = "Legacy view remains available";
    }),
  ).not.toThrow();
});

it.each(["copy interrupted", "copy integrity failed"])(
  "discards an unusable pre-migration file after %s and never applies DDL",
  (failure) => {
    const s = fresh(),
      before = s.read(),
      prepare = DatabaseSync.prototype.prepare;
    vi.spyOn(DatabaseSync.prototype, "prepare").mockImplementation(function (
      this: DatabaseSync,
      sql: string,
    ) {
      const statement = prepare.call(this, sql);
      if (failure === "copy interrupted" && sql === "VACUUM INTO ?") {
        const run = statement.run.bind(statement);
        vi.spyOn(statement, "run").mockImplementationOnce((...args) => {
          run(...args);
          throw new Error(failure);
        });
      }
      if (
        failure === "copy integrity failed" &&
        sql === "PRAGMA integrity_check"
      )
        vi.spyOn(statement, "get").mockReturnValueOnce({
          integrity_check: "damaged test copy",
        });
      return statement;
    });
    expect(() => initialize(s.db)).toThrow(
      failure === "copy interrupted" ? failure : "integrity check failed",
    );
    expect(status(s.db)).toBe("absent");
    expect(s.read()).toEqual(before);
    const file = (
      s.db.prepare("PRAGMA database_list").get() as { file: string }
    ).file;
    expect(
      fs.readdirSync(path.join(path.dirname(file), "v2-recovery")),
    ).toEqual([]);
    expect(s.db.isTransaction).toBe(false);
  },
);

it("rolls back partially executed migration DDL and retains an openable pre-migration copy", () => {
  const store = fresh(),
    before = store.read(),
    exec = store.db.exec.bind(store.db);
  vi.spyOn(store.db, "exec").mockImplementation((sql) => {
    exec(sql);
    if (sql === schemaSQL) throw new Error("interrupted DDL");
  });
  expect(() => initialize(store.db)).toThrow("interrupted DDL");
  expect(status(store.db)).toBe("absent");
  expect(store.read()).toEqual(before);
  const file = (
      store.db.prepare("PRAGMA database_list").get() as { file: string }
    ).file,
    directory = path.join(path.dirname(file), "v2-recovery"),
    files = fs.readdirSync(directory);
  expect(files).toHaveLength(1);
  const copy = new Store(path.join(directory, files[0]));
  stores.push(copy);
  expect(copy.read()).toEqual(before);
  expect(status(copy.db)).toBe("absent");
  expect(store.db.isTransaction).toBe(false);
});
