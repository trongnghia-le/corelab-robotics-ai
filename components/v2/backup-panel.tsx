"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { v2 } from "./client";
type Preview = {
  digest: string;
  token: string;
  scope: string;
  counts: Record<string, number>;
  warnings: string[];
};
type Snapshot = { id: string; at: string };
export function V2BackupPanel() {
  const [file, setFile] = useState<File | null>(null),
    [selection, setSelection] = useState<string | null>(null),
    [preview, setPreview] = useState<Preview | null>(null);
  const [confirm, setConfirm] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  useEffect(() => {
    let active = true;
    v2<{ items: Snapshot[] }>("backup/snapshots")
      .then((d) => {
        if (active) setSnapshots(d.items);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, []);
  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Recovery operation failed");
      setConfirm(false);
    } finally {
      setBusy(false);
    }
  };
  async function upload(path: string, extra: Record<string, string> = {}) {
    if (!file) throw new Error("Choose a backup file first.");
    const r = await fetch("/api/v2/" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...extra },
      body: file,
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error ?? "Backup validation failed");
    return d;
  }
  return (
    <section className="panel v2-backup" aria-labelledby="v2-backup-title">
      <div className="eyebrow">YOUR FULL LOCAL LEARNING HISTORY</div>
      <h2 id="v2-backup-title">
        Back up objectives and topic progress together.
      </h2>
      <p>
        A full backup includes attempts, recorded help, objective history and
        existing topic progress. Private keys and issuer enrollment stay on this
        machine. Imported claims are revalidated; a backup never grants trust by
        itself.
      </p>
      <div className="v2-actions">
        <a className="button primary" href="/api/v2/backup/export" download>
          Export full V2 backup
        </a>
        <a className="button" href="/api/export" download>
          Export legacy-only backup
        </a>
        <Link className="button" href="/objectives">
          Return to objective learning
        </Link>
      </div>
      <p className="muted">
        Legacy-only exports exclude objective history. The full backup transport
        limit is 128 MiB; safe export reserves recovery overhead and may stop
        earlier. Keep backups private and outside Git.
      </p>
      <label>
        Choose a backup JSON file
        <input
          type="file"
          accept=".json,application/json"
          aria-label="Choose full V2 backup"
          disabled={busy}
          onChange={(e) => {
            const next = e.target.files?.[0] ?? null;
            setPreview(null);
            setConfirm(false);
            setSelection(null);
            setError("");
            if (next && next.size > 128 * 1024 * 1024) {
              setFile(null);
              setError(
                "This file exceeds 128 MiB. Use the local recovery procedure.",
              );
            } else setFile(next);
          }}
        />
      </label>
      <button
        className="button"
        disabled={!file || busy}
        onClick={() =>
          void run(async () => {
            setConfirm(false);
            setSelection(null);
            setPreview(await upload("backup/preview"));
          })
        }
      >
        Preview backup replacement
      </button>
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      {busy && <p role="status">Checking the local recovery operation…</p>}
      {message && <p role="status">{message}</p>}
      {preview && (
        <div className="v2-feedback">
          <h3>
            {preview.scope === "full"
              ? "Full learning replacement"
              : "Legacy-only replacement · objective history retained"}
          </h3>
          <ul>
            {Object.entries(preview.counts).map(([key, n]) => (
              <li key={key}>
                {key}: {n}
              </li>
            ))}
          </ul>
          {preview.warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={confirm}
              onChange={(e) => setConfirm(e.target.checked)}
            />{" "}
            I confirm replacing the stated learning history. A full local
            snapshot will be preserved.
          </label>
          <button
            className="button danger"
            disabled={!confirm || busy}
            onClick={() =>
              void run(async () => {
                const headers = {
                  "X-CoreLab-Confirm": "true",
                  "X-CoreLab-BackupHash": preview.digest,
                  "X-CoreLab-ExpectedRevision": preview.token,
                };
                if (selection) {
                  const r = await fetch(
                    "/api/v2/backup/snapshots/" + selection + "/restore",
                    {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        ...headers,
                      },
                      body: "{}",
                    },
                  );
                  const d = await r.json();
                  if (!r.ok) throw new Error(d.error);
                } else await upload("backup/restore", headers);
                setPreview(null);
                setConfirm(false);
                setFile(null);
                setSelection(null);
                setMessage(
                  "Learning history restored. Reload any open learning pages before continuing.",
                );
                setSnapshots(
                  (await v2<{ items: Snapshot[] }>("backup/snapshots")).items,
                );
              })
            }
          >
            Confirm learning replacement
          </button>
        </div>
      )}
      <details>
        <summary>Recover a previous local snapshot</summary>
        <p>
          Snapshots preserve pre-replacement history. Recovery also requires
          preview and confirmation; installation identity and trust are never
          imported from another workspace.
        </p>
        {snapshots.length ? (
          snapshots.map((s) => (
            <div className="v2-actions" key={s.id}>
              <span>{new Date(s.at).toLocaleString("en-GB")}</span>
              <button
                className="button"
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    setConfirm(false);
                    setFile(null);
                    setSelection(s.id);
                    setPreview(
                      await v2<Preview>(
                        "backup/snapshots/" + s.id + "/preview",
                        {},
                      ),
                    );
                  })
                }
              >
                Preview snapshot recovery
              </button>
            </div>
          ))
        ) : (
          <p>No pre-restore snapshots yet.</p>
        )}
      </details>
    </section>
  );
}
