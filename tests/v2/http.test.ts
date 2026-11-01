import { afterEach, expect, it, vi } from "vitest";
import { dispatch } from "../../lib/v2/api";
import { Store } from "../../lib/storage";
import { status } from "../../lib/v2/db";
import { BACKUP_LIMIT } from "../../lib/v2/contracts";
const stores: Store[] = [];
afterEach(() => {
  stores.splice(0).forEach((s) => s.close());
  vi.unstubAllEnvs();
});
it("cancels an actual streamed overflow before opening a database, without trusting Content-Length", async () => {
  vi.stubEnv("CORELAB_V2", "1");
  let cancelled = false,
    opened = false,
    pulls = 0;
  const chunk = new Uint8Array(1024 * 1024).fill(32);
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      pulls++;
      controller.enqueue(chunk);
    },
    cancel() {
      cancelled = true;
    },
  });
  const r = new Request("http://127.0.0.1:3000/api/v2/backup/preview", {
    method: "POST",
    headers: {
      host: "127.0.0.1:3000",
      origin: "http://127.0.0.1:3000",
      "content-type": "application/json",
    },
    body,
    duplex: "half",
  } as RequestInit);
  const response = await dispatch(r, ["backup", "preview"], () => {
    opened = true;
    throw new Error("must not open");
  });
  expect(response.status).toBe(413);
  expect(cancelled).toBe(true);
  expect(opened).toBe(false);
  expect(pulls * chunk.byteLength).toBeGreaterThan(BACKUP_LIMIT);
});
function request(
  path: string,
  method = "GET",
  body?: unknown,
  host = "127.0.0.1:3000",
) {
  return new Request("http://127.0.0.1:3000/api/v2/" + path, {
    method,
    headers: {
      host,
      origin: "http://127.0.0.1:3000",
      "content-type": "application/json",
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
}
it("off and nonlocal requests cannot open or migrate a database", async () => {
  const store = new Store(":memory:");
  stores.push(store);
  vi.stubEnv("CORELAB_V2", "0");
  expect(
    (await dispatch(request("objectives"), ["objectives"], () => store)).status,
  ).toBe(404);
  expect(status(store.db)).toBe("absent");
  vi.stubEnv("CORELAB_V2", "1");
  expect(
    (
      await dispatch(
        request("objectives", "GET", undefined, "attacker.example"),
        ["objectives"],
        () => store,
      )
    ).status,
  ).toBe(400);
  expect(status(store.db)).toBe("absent");
});
it("serves redacted content, strict actions and inert import", async () => {
  const store = new Store(":memory:");
  stores.push(store);
  vi.stubEnv("CORELAB_V2", "1");
  const r = await dispatch(
    request("attempts", "POST", { purpose: "practice", source: "X01" }),
    ["attempts"],
    () => store,
  );
  expect(r.status).toBe(201);
  const a = await r.json();
  expect(a.item.fields[0].answer).toBeUndefined();
  expect(
    (
      await dispatch(
        request("reports/import", "POST", { command: "do not execute" }),
        ["reports", "import"],
        () => store,
      )
    ).status,
  ).toBe(503);
  const fake = await dispatch(
    request("attempts", "POST", {
      purpose: "practice",
      source: "X01",
      passed: true,
    }),
    ["attempts"],
    () => store,
  );
  expect(fake.status).toBe(400);
});
it("delivers a manual kit only after durable exposure and rejects forged self-report fields", async () => {
  const store = new Store(":memory:");
  stores.push(store);
  vi.stubEnv("CORELAB_V2", "1");
  const r = await dispatch(
    request("kits/L01-SE2/download", "POST", {}),
    ["kits", "L01-SE2", "download"],
    () => store,
  );
  expect(r.status).toBe(200);
  expect(r.headers.get("Content-Disposition")).toContain("attachment");
  const id = r.headers.get("X-CoreLab-Attempt");
  expect(id).toBeTruthy();
  expect(await r.text()).toContain("NotImplementedError");
  const forged = await dispatch(
    request("kits/L01-SE2/self-report", "POST", {
      attemptId: id,
      ran: true,
      declaredAssistance: 0,
      passed: true,
    }),
    ["kits", "L01-SE2", "self-report"],
    () => store,
  );
  expect(forged.status).toBe(400);
  const h = await dispatch(request("history"), ["history"], () => store);
  const summary = await h.json();
  expect(summary.items[0].id).toBe(id);
  expect(summary.items[0].item).toBeUndefined();
});
