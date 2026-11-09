// Splits a lesson body into study sessions and estimates realistic study time.
// Sessions follow the lesson's own `## ` headings, so a translated body with
// the same heading order maps onto the same sessions by index.

export type SessionKey = "learn" | "practice" | "build" | "review";

export type LessonSection = {
  heading: string;
  index: number;
  markdown: string;
  /** English heading at this index when the body is a translation. */
  englishHeading?: string;
};

export type LessonSession = {
  key: SessionKey;
  sections: LessonSection[];
  minutes: number;
};

const sessionOf: Record<string, SessionKey> = {
  "why-this-matters": "learn",
  intuition: "learn",
  "intuition-and-definitions": "learn",
  "theory-and-derivation": "learn",
  "reasoning-and-assumptions": "learn",
  "worked-example": "learn",
  exercises: "practice",
  "exercise-answers": "practice",
  "reference-implementation": "build",
  "implementation-and-verification": "build",
  "independent-practice": "build",
  "independent-practice-and-transfer": "build",
  verification: "review",
  "failure-modes": "review",
  "misconceptions-and-alternatives": "review",
  "alternatives-and-trade-offs": "review",
  "transfer-and-retention": "review",
  "further-reading": "review",
};

export const sessionOrder: SessionKey[] = [
  "learn",
  "practice",
  "build",
  "review",
];

function slug(text: string) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** Split a Markdown body into its `## ` sections (fenced code is never split). */
export function splitSections(body: string): {
  preamble: string;
  sections: LessonSection[];
} {
  const lines = body.split("\n");
  const sections: LessonSection[] = [];
  const preamble: string[] = [];
  let current: string[] | null = null;
  let heading = "";
  let fence = false;
  const flush = () => {
    if (current)
      sections.push({
        heading,
        index: sections.length,
        markdown: current.join("\n"),
      });
  };
  for (const line of lines) {
    if (/^\s*(```|~~~)/.test(line)) fence = !fence;
    if (!fence && line.startsWith("## ")) {
      flush();
      heading = line.slice(3).trim();
      current = [line];
      continue;
    }
    (current ?? preamble).push(line);
  }
  flush();
  return { preamble: preamble.join("\n"), sections };
}

function words(text: string) {
  return text.split(/\s+/).filter(Boolean).length;
}

function proseAndCode(markdown: string) {
  const code = [...markdown.matchAll(/```[\s\S]*?```/g)].map((m) => m[0]);
  const codeWords = code.reduce((n, c) => n + words(c), 0);
  return { prose: Math.max(0, words(markdown) - codeWords), code: codeWords };
}

/** Minutes for one exercise from its difficulty tag. */
function exerciseMinutes(line: string) {
  if (/mini-?project/i.test(line)) return 45;
  if (/\(challenge\)/i.test(line)) return 30;
  if (/\(hard\)/i.test(line)) return 20;
  if (/\(medium\)/i.test(line)) return 12;
  if (/\(easy\)/i.test(line)) return 6;
  return 10;
}

/** Realistic minutes for one session of focused study. */
export function sessionMinutes(key: SessionKey, sections: LessonSection[]) {
  let minutes = 0;
  for (const s of sections) {
    const { prose, code } = proseAndCode(s.markdown);
    const id = slug(s.englishHeading ?? s.heading);
    if (id === "exercises") {
      const problems = s.markdown.split("\n").filter((l) => /^\d+\. /.test(l));
      minutes += problems.reduce((n, l) => n + exerciseMinutes(l), 0);
    } else if (id === "exercise-answers") {
      minutes += prose / 200;
    } else if (id.startsWith("independent-practice")) {
      const tasks = (s.markdown.split("### Tasks")[1] ?? "")
        .split("\n### ")[0]
        .split("\n")
        .filter((l) => /^\d+\. /.test(l)).length;
      const library = /### Library track/.test(s.markdown) ? 30 : 0;
      minutes += Math.max(45, 20 + 15 * tasks) + library + prose / 120;
    } else if (key === "learn") {
      // Theory with derivations is worked through with pen and paper, not skimmed.
      minutes += prose / 40 + code / 30;
      if (id === "worked-example") minutes += 10;
    } else {
      minutes += prose / 100 + code / 40;
    }
  }
  // Learn includes the recommended video and pausing to predict; review includes recall.
  if (key === "learn") minutes += 15;
  if (key === "review") minutes += 10;
  return Math.max(10, Math.round(minutes / 5) * 5);
}

/**
 * Group sections into sessions. `englishHeadings` (optional) gives the
 * English heading at each index when `body` is a translation.
 */
export function lessonSessions(
  body: string,
  englishHeadings?: string[],
): LessonSession[] {
  const { sections } = splitSections(body);
  const groups = new Map<SessionKey, LessonSection[]>();
  let last: SessionKey = "learn";
  for (const s of sections) {
    const english = englishHeadings?.[s.index] ?? s.heading;
    const key: SessionKey = sessionOf[slug(english)] ?? last;
    last = key;
    const list = groups.get(key) ?? [];
    list.push({ ...s, englishHeading: english });
    groups.set(key, list);
  }
  return sessionOrder
    .filter((k) => groups.has(k))
    .map((k) => ({
      key: k,
      sections: groups.get(k)!,
      minutes: sessionMinutes(k, groups.get(k)!),
    }));
}

/** Total realistic study minutes for a lesson body. */
export function lessonMinutes(body: string) {
  return lessonSessions(body).reduce((n, s) => n + s.minutes, 0);
}

/**
 * Sessions for display. Minutes always come from the English body
 * (`sessionMinutes`), so translated difficulty tags never change the time.
 */
export function lessonPlan(lesson: {
  body: string;
  englishHeadings?: string[];
  sessionMinutes?: Record<string, number>;
}) {
  const sessions = lessonSessions(lesson.body, lesson.englishHeadings).map(
    (s) => ({ ...s, minutes: lesson.sessionMinutes?.[s.key] ?? s.minutes }),
  );
  return {
    sessions,
    minutes: sessions.reduce((n, s) => n + s.minutes, 0),
  };
}
