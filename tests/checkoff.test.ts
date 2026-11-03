import { describe, expect, it } from "vitest";
import {
  checkoffKind,
  checkoffText,
  doneCount,
  parseCheckoff,
  sessionProgress,
} from "../lib/checkoff";

const rec = (topicId: string, at: string, text: string) => ({
  topicId,
  at,
  text,
});

describe("session check-off", () => {
  it("round-trips the structured text", () => {
    expect(checkoffText("M01", "learn", true)).toBe("checkoff:M01:learn:done");
    expect(parseCheckoff("checkoff:CPP01:build:undone")).toEqual({
      topicId: "CPP01",
      key: "build",
      done: false,
    });
    expect(parseCheckoff("Read lesson")).toBeNull();
    expect(parseCheckoff("checkoff:M01:nope:done")).toBeNull();
  });
  it("uses reading for learn/review and practice for practice/build", () => {
    expect(checkoffKind("learn")).toBe("reading");
    expect(checkoffKind("review")).toBe("reading");
    expect(checkoffKind("practice")).toBe("practice");
    expect(checkoffKind("build")).toBe("practice");
  });
  it("derives state from the latest record per session", () => {
    const sessions = [
      rec("M01", "2026-01-01T10:00:00Z", checkoffText("M01", "learn", true)),
      rec("M01", "2026-01-01T11:00:00Z", checkoffText("M01", "build", true)),
      rec("M01", "2026-01-02T10:00:00Z", checkoffText("M01", "learn", false)),
      rec("M01", "2026-01-03T10:00:00Z", checkoffText("M01", "learn", true)),
      rec("M02", "2026-01-03T10:00:00Z", checkoffText("M02", "review", true)),
      rec("M01", "2026-01-03T12:00:00Z", "a normal note"),
    ];
    const progress = sessionProgress(sessions, "M01");
    expect(progress).toEqual({
      learn: true,
      practice: false,
      build: true,
      review: false,
    });
    expect(doneCount(progress)).toBe(2);
  });
  it("lets a later undone record win and ignores other topics", () => {
    const sessions = [
      rec("M01", "2026-01-01T10:00:00Z", checkoffText("M01", "practice", true)),
      rec(
        "M01",
        "2026-01-01T10:00:00Z",
        checkoffText("M01", "practice", false),
      ),
      rec("M01", "2026-01-01T10:00:00Z", checkoffText("M02", "learn", true)),
    ];
    const progress = sessionProgress(sessions, "M01");
    expect(progress.practice).toBe(false);
    expect(progress.learn).toBe(false);
  });
});
