import type { Session } from "./types";
import { sessionOrder, type SessionKey } from "./lesson-plan";

export type Checkoff = { topicId: string; key: SessionKey; done: boolean };

/** Session kind used when storing a check-off record. */
export function checkoffKind(key: SessionKey): "reading" | "practice" {
  return key === "learn" || key === "review" ? "reading" : "practice";
}

export function checkoffText(topicId: string, key: SessionKey, done: boolean) {
  return `checkoff:${topicId}:${key}:${done ? "done" : "undone"}`;
}

export function parseCheckoff(text: string): Checkoff | null {
  const m =
    /^checkoff:([A-Z]+\d+):(learn|practice|build|review):(done|undone)$/.exec(
      text,
    );
  return m
    ? { topicId: m[1], key: m[2] as SessionKey, done: m[3] === "done" }
    : null;
}

export function isCheckoff(session: Pick<Session, "text">) {
  return parseCheckoff(session.text) !== null;
}

/**
 * Derive done/not-done per session from the latest check-off record
 * (by timestamp, later array position wins ties).
 */
export function sessionProgress(
  sessions: Pick<Session, "topicId" | "at" | "text">[],
  topicId: string,
): Record<SessionKey, boolean> {
  const latest = new Map<SessionKey, { at: string; done: boolean }>();
  for (const s of sessions) {
    if (s.topicId !== topicId) continue;
    const c = parseCheckoff(s.text);
    if (!c || c.topicId !== topicId) continue;
    const prev = latest.get(c.key);
    if (!prev || s.at >= prev.at) latest.set(c.key, { at: s.at, done: c.done });
  }
  return Object.fromEntries(
    sessionOrder.map((k) => [k, latest.get(k)?.done ?? false]),
  ) as Record<SessionKey, boolean>;
}

export function doneCount(progress: Record<SessionKey, boolean>) {
  return sessionOrder.filter((k) => progress[k]).length;
}

/** Per-topic progress for every topic that has any check-off record. */
export function allSessionProgress(
  sessions: Pick<Session, "topicId" | "at" | "text">[],
): Record<string, Record<SessionKey, boolean>> {
  const byTopic = new Map<string, typeof sessions>();
  for (const s of sessions) {
    if (!s.text.startsWith("checkoff:")) continue;
    const list = byTopic.get(s.topicId) ?? [];
    list.push(s);
    byTopic.set(s.topicId, list);
  }
  return Object.fromEntries(
    [...byTopic].map(([id, list]) => [id, sessionProgress(list, id)]),
  );
}
