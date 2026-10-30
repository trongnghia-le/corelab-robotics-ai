import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import type { Assessment } from "../lib/types";
const getAssessment = (id: string): Assessment =>
  JSON.parse(readFileSync(`content/assessments/${id}.v1.json`, "utf8"));
test("empty workspace → lesson → assessment → reload → evidence → handoff → backup → restore → graph", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Build foundations. Go further." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Mathematical Basics", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Unassessed is a starting point")).toBeVisible();
  const initial = await (await page.request.get("/api/state")).json();
  expect(initial.progress.attempts).toHaveLength(0);
  expect(
    Object.values(initial.mastery).every(
      (v) => !!v && typeof v === "object" && "level" in v && v.level === 0,
    ),
  ).toBe(true);
  await page
    .getByRole("link", { name: "Continue learning", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Notation, functions, and units",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".katex").first()).toBeVisible();
  await expect(page.locator(".lesson-toc a").first()).toBeVisible();
  await page.getByRole("button", { name: "Mark as read", exact: true }).click();
  await expect(
    page
      .getByRole("status")
      .getByText("Reading activity saved. Mastery is unchanged."),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Assess competence", exact: true })
    .click();
  const contract = getAssessment("M01")!;
  await page
    .getByRole("radio", { name: "Yes, provided each input has one output." })
    .check();
  for (const q of contract.questions.filter((q) => q.kind === "number"))
    await page
      .getByRole("textbox", { name: `Answer ${q.id}`, exact: true })
      .fill(q.answer!);
  await page
    .getByRole("textbox", { name: "Rubric response" })
    .fill(
      "I state assumptions, check units, and verify on a held-out calibration point.",
    );
  await page
    .getByRole("button", { name: "Submit and save diagnostic" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Result · 100%" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.locator(".topic-meta").getByText("Verified L1"),
  ).toBeVisible();
  await expect(page.getByText("100% · A0", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Copy Learning Context", exact: true })
    .click();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  const handoff = JSON.parse(copied);
  expect(handoff.topic.id).toBe("M01");
  expect(handoff.verifiedEvidence.level).toBe(1);
  expect(copied).not.toContain('"answer"');
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Vectors", exact: true }),
  ).toBeVisible();
  await page.goto("/tutor");
  await page.getByRole("textbox", { name: "AI feedback JSON" }).fill(
    JSON.stringify({
      schema: "corelab-feedback/1",
      topicId: "M01",
      summary: "AI note",
      difficulties: ["Inverse versus reciprocal"],
      nextSteps: ["Try a new example"],
    }),
  );
  await page.getByRole("button", { name: "Save feedback" }).click();
  await expect(
    page.getByText("AI feedback saved as unverified notes."),
  ).toBeVisible();
  const before = await (await page.request.get("/api/state")).json();
  expect(before.mastery.M01.level).toBe(1);
  await page.goto("/settings");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export backup JSON" }).click();
  const download = await downloadPromise;
  const filepath = await download.path();
  expect(filepath).toBeTruthy();
  const backup = JSON.parse(readFileSync(filepath!, "utf8"));
  expect(backup.progress.attempts).toHaveLength(1);
  await page.request.post("/api/action", {
    data: {
      type: "session",
      topicId: "M02",
      kind: "note",
      text: "Temporary record after backup",
      minutes: 1,
    },
  });
  await page.getByLabel("Choose backup to restore").setInputFiles({
    name: "backup.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(backup)),
  });
  await expect(page.getByText("Valid schema", { exact: true })).toBeVisible();
  const restore = page.getByRole("button", { name: "Restore and replace" });
  await expect(restore).toBeDisabled();
  await page.getByRole("checkbox").check();
  await restore.click();
  await expect(page.getByText("Progress restored from backup.")).toBeVisible();
  const restored = await (await page.request.get("/api/state")).json();
  expect(restored.progress).toEqual(backup.progress);
  await page.goto("/roadmap");
  await page.getByRole("textbox", { name: "Search topics" }).fill("M02");
  await expect(page.locator(".topic-list-row")).toHaveCount(1);
  await page.getByRole("textbox", { name: "Search topics" }).fill("");
  await page.getByRole("button", { name: "Graph", exact: true }).click();
  await expect(page.locator(".react-flow__node").first()).toBeVisible();
  await page.locator(".react-flow__node").filter({ hasText: "M02" }).click();
  await expect(
    page
      .locator(".graph-detail")
      .getByRole("heading", { name: "M02 · Vectors" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Open topic details" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Vectors: displacement, dot products, and geometry",
    }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("remaining pages, honest overview, keyboard/mobile layout, invalid import and local security", async ({
  page,
}) => {
  for (const [route, heading] of [
    ["/paths", "One path, many open branches."],
    ["/practice", "Implement independently. Verify your work."],
    ["/lessons", "Go beyond reading. Understand deeply."],
    ["/assessments", "Verify what you understand."],
    ["/sources", "References"],
    ["/roadmap", "Knowledge roadmap"],
    ["/tutor", "One tutor. One source of truth."],
    ["/settings", "Data & settings"],
  ]) {
    await page.goto(route);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    const vietnameseText = /[ăâđêôơưĂÂĐÊÔƠƯ\u1ea0-\u1ef9]/u;
    expect(await page.locator("body").innerText()).not.toMatch(vietnameseText);
    const accessibleCopy = await page
      .locator("[aria-label], [placeholder]")
      .evaluateAll((elements) =>
        elements
          .map(
            (el) =>
              `${el.getAttribute("aria-label") ?? ""} ${el.getAttribute("placeholder") ?? ""}`,
          )
          .join("\n"),
      );
    expect(accessibleCopy).not.toMatch(vietnameseText);
  }
  await page.goto("/lessons/E15");
  await expect(
    page.getByText("Overview · This topic does not yet have a complete lesson"),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Advanced Embodied Intelligence",
      exact: true,
    }),
  ).toBeVisible();
  await page.goto("/settings");
  await page.getByLabel("Choose backup to restore").setInputFiles({
    name: "invalid.json",
    mimeType: "application/json",
    buffer: Buffer.from('{"schema":"unknown"}'),
  });
  await expect(page.locator('.error-text[role="alert"]')).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Restore and replace" }),
  ).toHaveCount(0);
  const forbidden = await page.request.post("/api/action", {
    headers: { origin: "https://untrusted.example" },
    data: { type: "goal", goal: "Robotics", focusTopic: null, focusReason: "" },
  });
  expect(forbidden.status()).toBe(400);
  const contract = await (await page.request.get("/api/topics/M01")).json();
  expect(
    contract.assessment.questions.every(
      (q: Record<string, unknown>) => !("answer" in q),
    ),
  ).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/lessons/M02");
  await expect(
    page.getByRole("heading", {
      name: "Vectors: displacement, dot products, and geometry",
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Open menu" }).click();
  await expect(
    page.getByRole("button", { name: "Close menu", exact: true }).last(),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Open menu" })).toBeFocused();
  mkdirSync(".local/screenshots", { recursive: true });
  await page.screenshot({
    path: ".local/screenshots/mobile-lesson.png",
    fullPage: false,
  });
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Build foundations. Go further." }),
  ).toBeVisible();
  await page.screenshot({
    path: ".local/screenshots/dashboard.png",
    fullPage: true,
  });
  await page.goto("/not-a-route");
  await expect(
    page.getByText("This topic is not in the workspace."),
  ).toBeVisible();
});

test("local fixed verifier → A3 practice → A0 signed evidence → L2, and interactive geometry", async ({
  page,
}) => {
  const { writeFileSync } = await import("node:fs");
  const { execFileSync } = await import("node:child_process");
  mkdirSync(".local/e2e-labs", { recursive: true });
  const solution = ".local/e2e-labs/dot.py";
  writeFileSync(
    solution,
    'def dot(u,v):\n    if len(u)!=len(v): raise ValueError("shape")\n    return sum(a*b for a,b in zip(u,v))\n',
  );
  const contract = getAssessment("M02");
  const answers = Object.fromEntries(
    contract.questions
      .filter((q) => q.kind !== "short")
      .map((q) => [q.id, q.answer]),
  );
  const assessment = await page.request.post("/api/action", {
    data: { type: "attempt", topicId: "M02", answers, assistance: "A0" },
  });
  expect(assessment.ok()).toBe(true);
  for (const assistance of ["A3", "A0"]) {
    const out = `.local/e2e-labs/${assistance}-report.json`;
    execFileSync(process.execPath, [
      "scripts/verify-lab.mjs",
      "--topic",
      "M02",
      "--file",
      solution,
      "--assistance",
      assistance,
      "--out",
      out,
    ]);
    await page.goto("/practice?topic=M02");
    await page.getByLabel("Choose lab report").setInputFiles(out);
    await page
      .getByRole("button", { name: "Import report", exact: true })
      .click();
    await expect(
      page.getByText("Test report imported. View the evidence in Assessments."),
    ).toBeVisible();
    const current = await (await page.request.get("/api/state")).json();
    expect(current.mastery.M02.level).toBe(assistance === "A0" ? 2 : 1);
  }
  await page.reload();
  await page
    .getByLabel("Choose lab report")
    .setInputFiles(".local/e2e-labs/A0-report.json");
  await page
    .getByRole("button", { name: "Import report", exact: true })
    .click();
  await expect(
    page.getByText("This report has already been imported"),
  ).toBeVisible();
  await page.goto("/lessons/M02");
  const slider = page.getByRole("slider", { name: "Vector x coordinate" });
  await slider.fill("4");
  await expect(
    page.getByText("projᵥ u = (3.00, 3.00)", { exact: true }),
  ).toBeVisible();
  await page.goto("/lessons/R04");
  await page.getByRole("slider", { name: "Joint 1 angle" }).fill("90");
  await page.getByRole("slider", { name: "Joint 2 angle" }).fill("0");
  await expect(
    page.getByText("p = (0.00, 3.50) m", { exact: true }),
  ).toBeVisible();
});

test("mistakes → type-aware remediation → assisted practice → independent repair → backup persistence", async ({
  page,
}) => {
  const bank = JSON.parse(
    readFileSync("content/practice/M05.v1.json", "utf8"),
  ) as Assessment;
  const diagnostic = getAssessment("M05");
  const correct = Object.fromEntries(
    diagnostic.questions
      .filter((q) => q.kind !== "short")
      .map((q) => [q.id, q.answer!]),
  );
  for (let n = 0; n < 3; n++) {
    const r = await page.request.post("/api/action", {
      data: {
        type: "attempt",
        topicId: "M05",
        answers: { ...correct, q3: "99" },
        assistance: "A0",
      },
    });
    expect(r.ok()).toBe(true);
  }
  await page.goto("/assessments/M05");
  await expect(
    page
      .locator(".assessment-methods")
      .getByText("CONCEPT — Understand the principle", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator(".assessment-methods")
      .getByText("PROCEDURE — Perform the calculation", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator(".assessment-methods")
      .getByText("DESIGN — Choose and justify", { exact: true }),
  ).toBeVisible();
  await expect(
    page
      .locator(".assessment-methods")
      .getByText("IMPLEMENTATION — Build and verify", { exact: true }),
  ).toBeVisible();
  await page
    .locator(".assessment-methods")
    .screenshot({ path: ".local/screenshots/type-aware-assessment.png" });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Weaknesses to Review", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".dashboard-weakness")).toHaveCount(1);
  await page
    .getByRole("link", { name: "Practice Weaknesses", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Practice the skill behind the mistake.",
    }),
  ).toBeVisible();
  await expect(page.locator(".weakness-card")).toHaveCount(1);
  await expect(
    page.getByText("3 objective mistakes across 3 failed attempts", {
      exact: false,
    }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Practice Weak Skill", exact: true })
    .click();
  // M01 was independently verified by the earlier learning-flow test.
  // Repeated mistakes must not invent an unverified prerequisite deficit.
  const foundationState = await (await page.request.get("/api/state")).json();
  expect(foundationState.mastery.M01.level).toBe(1);
  await expect(
    page.getByRole("heading", { name: "Check the foundation", exact: true }),
  ).toHaveCount(0);
  await page
    .locator(".weakness-card")
    .screenshot({ path: ".local/screenshots/weakness-card.png" });
  const response = await (
    await page.request.get("/api/practice?topic=M05&skill=chain-rule")
  ).json();
  expect(
    response.plan.assessment.questions.every(
      (q: Record<string, unknown>) => !("answer" in q) && q.explanation === "",
    ),
  ).toBe(true);
  async function fillFocused() {
    const qs = page.locator(".targeted-form fieldset");
    await expect(qs).not.toHaveCount(0);
    for (let i = 0; i < (await qs.count()); i++) {
      const fs = qs.nth(i);
      const id = await fs.getAttribute("id");
      const q = bank.questions.find((q) => `assessment-${q.id}` === id)!;
      if (q.kind === "choice")
        await fs
          .getByRole("radio", {
            name: q.options![Number(q.answer)],
            exact: true,
          })
          .check();
      else
        await fs
          .getByRole("textbox", { name: `Answer ${q.id}`, exact: true })
          .fill(q.answer!);
    }
  }
  await page.getByLabel("Assistance level", { exact: true }).selectOption("A3");
  await fillFocused();
  await page
    .getByRole("button", { name: "Save focused practice", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Focused result · 100%" }),
  ).toBeVisible();
  await expect(
    page
      .locator(".weakness-card")
      .getByText("Practiced with assistance", { exact: true }),
  ).toBeVisible();
  const assisted = await (await page.request.get("/api/state")).json();
  expect(assisted.mastery.M05.level).toBe(0);
  expect(
    assisted.weaknesses.find((w: { topicId: string }) => w.topicId === "M05")
      .status,
  ).toBe("practiced_with_assistance");
  await page.getByRole("button", { name: "Check next available set" }).click();
  await page.getByLabel("Assistance level", { exact: true }).selectOption("A0");
  await fillFocused();
  await page
    .getByRole("button", { name: "Save focused practice", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Focused result · 100%" }),
  ).toBeVisible();
  await page.locator("#weakness-status").selectOption("all");
  await expect(
    page
      .locator(".weakness-card")
      .getByText("Independently corrected", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("3 objective mistakes across 3 failed attempts", {
      exact: false,
    }),
  ).toBeVisible();
  const repaired = await (await page.request.get("/api/state")).json();
  expect(repaired.mastery.M05.level).toBe(0);
  expect(repaired.mastery.M01.level).toBe(1);
  expect(
    repaired.progress.reviews.filter(
      (r: { topicId: string }) => r.topicId === "M05",
    ),
  ).toHaveLength(1);
  await page.getByRole("button", { name: "Check next available set" }).click();
  await expect(
    page.getByText("No fresh variants remain.", { exact: false }),
  ).toBeVisible();
  await expect(page.locator(".targeted-form")).toHaveCount(0);
  await page
    .getByLabel("Focused practice skill")
    .selectOption("design-decisions");
  await expect(
    page.getByText("DESIGN — Choose and justify", { exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Rubric response", { exact: true })
    .fill(
      "Analytical derivatives, finite differences, cancellation, truncation, noise: these words alone do not verify a design. I must justify assumptions and compare results.",
    );
  await page
    .getByRole("button", { name: "Save focused practice", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Rubric response saved · unverified" }),
  ).toBeVisible();
  const afterDesign = await (await page.request.get("/api/state")).json();
  expect(afterDesign.mastery.M05.level).toBe(0);
  expect(
    afterDesign.weaknesses.filter(
      (w: { topicId: string }) => w.topicId === "M05",
    ),
  ).toHaveLength(1);
  const backup = await (await page.request.get("/api/export")).json();
  expect(backup.schema).toBe("corelab-backup/2");
  const restore = await page.request.post("/api/action", {
    data: { type: "restore", backup, confirm: true },
  });
  expect(restore.ok()).toBe(true);
  await page.reload();
  await page.locator("#weakness-status").selectOption("all");
  await expect(
    page
      .locator(".weakness-card")
      .getByText("Independently corrected", { exact: true }),
  ).toBeVisible();
  const restored = await (await page.request.get("/api/state")).json();
  expect(restored.progress).toEqual(backup.progress);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", {
      name: "Practice the skill behind the mistake.",
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.goto("/practice?tab=weaknesses&topic=E15&skill=unavailable");
  await expect(
    page.getByText("No authored variants exist for this skill yet.", {
      exact: false,
    }),
  ).toBeVisible();
});
