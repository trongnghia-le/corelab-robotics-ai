import { z } from "zod";
import { getStore } from "../storage";
import { checkLocalRequest } from "../http";
import { enabled, BACKUP_LIMIT, readJSON, V2Error } from "./contracts";
import { initialize, write } from "./db";
import {
  issue,
  assist,
  submit,
  publicAttempt,
  history,
  acknowledge,
} from "./attempts";
import {
  exportBackup,
  preview,
  restore,
  snapshots,
  snapshotBackup,
} from "./backup";
import {
  summaries,
  select,
  objectiveDetail,
  savePreference,
} from "./read-model";
const replies = (value: unknown, status = 200) =>
  Response.json(value, { status, headers: { "Cache-Control": "no-store" } });
let heavyOperation = false;
export async function dispatch(
  request: Request,
  parts: string[],
  resolveStore = getStore,
) {
  let ownsHeavyOperation = false;
  try {
    if (!enabled()) return replies({ error: "Not found" }, 404);
    const method = request.method,
      key = parts.join("/");
    const full = key === "backup/preview" || key === "backup/restore";
    checkLocalRequest(request, { maxBytes: full ? BACKUP_LIMIT : 16384 });
    if (parts.some((p) => !/^[A-Za-z0-9][A-Za-z0-9._@-]{0,119}$/.test(p)))
      return replies({ error: "Not found" }, 404);
    if (key === "reports/import")
      throw new V2Error(
        "unavailable",
        "Verified I is unavailable. No report is read or executed.",
        503,
      );
    const known =
      (method === "GET" &&
        /^(objectives(\/[^/]+)?|select|history|backup\/(export|snapshots)|attempts\/[^/]+)$/.test(
          key,
        )) ||
      (method === "POST" &&
        /^(attempts|attempts\/[^/]+\/(assist|submit)|backup\/(preview|restore)|backup\/snapshots\/[^/]+\/(preview|restore)|history\/acknowledge)$/.test(
          key,
        )) ||
      (method === "PATCH" && key === "preferences");
    if (!known) return replies({ error: "Not found" }, 404);
    if (key.startsWith("backup/")) {
      if (heavyOperation)
        throw new V2Error(
          "backup_busy",
          "Another backup operation is active. Retry after it finishes.",
          503,
        );
      heavyOperation = true;
      ownsHeavyOperation = true;
    }
    const body =
      method === "GET"
        ? null
        : await readJSON(request, full ? BACKUP_LIMIT : 16384);
    const store = resolveStore();
    initialize(store.db);
    const params = new URL(request.url).searchParams;
    if (method === "GET") {
      if (key === "objectives") return replies(summaries(store));
      if (parts[0] === "objectives")
        return replies(objectiveDetail(store, parts[1]));
      if (key === "select") return replies(select(store, params));
      if (key === "history") {
        const p = z
          .object({
            limit: z.coerce.number().int().min(1).max(50).default(25),
            cursor: z
              .string()
              .regex(/^\d{1,16}$/)
              .optional(),
          })
          .strict()
          .parse(Object.fromEntries(params));
        return replies(history(store, p.limit, p.cursor));
      }
      if (parts[0] === "attempts")
        return replies(publicAttempt(store.db, parts[1]));
      if (key === "backup/snapshots")
        return replies({ items: snapshots(store.db) });
      if (key === "backup/export")
        return new Response(JSON.stringify(exportBackup(store)), {
          headers: {
            "Content-Type": "application/json",
            "Content-Disposition":
              'attachment; filename="corelab-v2-backup.json"',
            "Cache-Control": "no-store",
          },
        });
    }
    if (key === "attempts") return replies(issue(store, body), 201);
    if (parts[0] === "attempts" && parts[2] === "assist")
      return replies(assist(store, parts[1], body));
    if (parts[0] === "attempts" && parts[2] === "submit")
      return replies(submit(store, parts[1], body));
    if (key === "history/acknowledge")
      return replies(
        acknowledge(
          store,
          z
            .object({ token: z.string().length(64) })
            .strict()
            .parse(body).token,
        ),
      );
    if (key === "preferences")
      return replies(write(store.db, () => savePreference(store, body)));
    if (key === "backup/preview") return replies(preview(store, body));
    const confirmation = () => ({
      confirm: request.headers.get("X-CoreLab-Confirm") === "true",
      digest: z
        .string()
        .regex(/^[a-f0-9]{64}$/)
        .parse(request.headers.get("X-CoreLab-BackupHash")),
      token: z
        .string()
        .regex(/^[a-f0-9]{64}$/)
        .parse(request.headers.get("X-CoreLab-ExpectedRevision")),
    });
    if (key === "backup/restore")
      return replies(restore(store, body, confirmation()));
    if (parts[0] === "backup" && parts[1] === "snapshots") {
      z.object({}).strict().parse(body);
      const backup = snapshotBackup(store.db, parts[2]);
      return replies(
        parts[3] === "preview"
          ? preview(store, backup)
          : restore(store, backup, confirmation()),
      );
    }
    return replies({ error: "Not found" }, 404);
  } catch (e) {
    if (e instanceof V2Error)
      return replies({ error: e.message, code: e.code }, e.status);
    if (e instanceof z.ZodError)
      return replies(
        {
          error: e.issues
            .map((i) => i.path.join(".") + ": " + i.message)
            .join("; "),
          code: "invalid_input",
        },
        400,
      );
    return replies(
      {
        error: e instanceof Error ? e.message : "Local operation failed",
        code: "invalid_request",
      },
      400,
    );
  } finally {
    if (ownsHeavyOperation) heavyOperation = false;
  }
}
