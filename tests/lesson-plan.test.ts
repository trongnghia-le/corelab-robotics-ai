import { describe, expect, it } from "vitest";
import { lessonIds, getLesson } from "../lib/content";
import {
  lessonMinutes,
  lessonSessions,
  splitSections,
} from "../lib/lesson-plan";

describe("lesson plan", () => {
  it("keeps fenced code containing ## lines inside its section", () => {
    const body =
      "## Intuition\ntext\n```python\n## not a heading\n```\n## Exercises\n1. **(Easy)** a\n";
    const { sections } = splitSections(body);
    expect(sections.map((s) => s.heading)).toEqual(["Intuition", "Exercises"]);
  });
  it("groups sections into learn/practice/build/review and maps translations by index", () => {
    const en = [
      "Intuition",
      "Exercises",
      "Reference implementation",
      "Verification",
    ];
    const body =
      "## Trực giác\na\n## Bài tập\n1. **(Hard)** x\n## Cài đặt tham khảo\ncode\n## Kiểm chứng\nb\n";
    expect(lessonSessions(body, en).map((s) => s.key)).toEqual([
      "learn",
      "practice",
      "build",
      "review",
    ]);
  });
  it("gives every authored lesson a session plan with realistic minutes", () => {
    for (const id of lessonIds()) {
      const lesson = getLesson(id)!;
      const sessions = lessonSessions(lesson.body);
      expect(sessions[0].key, id).toBe("learn");
      expect(
        sessions.some((s) => s.key === "build"),
        id,
      ).toBe(true);
      const total = lessonMinutes(lesson.body);
      expect(total, id).toBeGreaterThanOrEqual(60);
      expect(total, id).toBeLessThanOrEqual(900);
    }
  });
});

describe("project lessons", () => {
  it("tops up the build session to the declared project effort", async () => {
    const { projectSessionMinutes, getLocalizedLesson } =
      await import("../lib/content");
    const base = { learn: 60, practice: 120, build: 200, review: 20 };
    expect(projectSessionMinutes(base, 1000).build).toBe(800);
    expect(projectSessionMinutes(base, 300)).toEqual(base);
    expect(projectSessionMinutes(base)).toEqual(base);
    for (const lang of ["en", "vi"] as const) {
      const cap = getLocalizedLesson("CAP02", lang)!;
      const total = Object.values(cap.sessionMinutes!).reduce(
        (n, m) => n + m,
        0,
      );
      expect(total).toBe(cap.meta.project_minutes);
    }
  });
});
