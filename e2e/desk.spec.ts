import { expect, test } from "@playwright/test";

test("study desk keeps notes, exercise answers and runs code", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));

  // The lesson window announces its topic; a desk opened later picks it up.
  await page.goto("/lessons/M02");
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  await page.goto("/desk");
  await expect(page.getByLabel("Topic")).toHaveValue("M02");
  await expect(page.locator(".sidebar")).toHaveCount(0);

  // Notes autosave and survive a reload.
  await page.getByLabel("Notes", { exact: true }).fill("dot = |u||v| cos θ");
  await expect(page.getByText("Saved", { exact: true })).toBeVisible();
  await page.waitForTimeout(1200);
  await page.reload();
  await expect(page.getByLabel("Notes", { exact: true })).toHaveValue(
    "dot = |u||v| cos θ",
  );

  // Formula palette inserts LaTeX at the cursor; the split view renders it.
  const notes = page.getByLabel("Notes", { exact: true });
  await notes.fill("Kalman: ");
  await notes.press("End");
  await page.getByRole("tab", { name: "Linear algebra" }).click();
  await page.getByRole("button", { name: "transpose", exact: true }).click();
  await expect(notes).toHaveValue("Kalman: $^{\\top}$");
  await notes.press("End");
  await page.getByRole("tab", { name: "From this lesson" }).click();
  await page.locator(".math-items.is-lesson .math-item").first().click();
  // A lesson formula is appended inline ($…$) or as a display block ($$…$$).
  await expect(notes).toHaveValue(
    /^Kalman: \$\^\{\\top\}\$(?: \$[^\n]+=[^\n]+\$|\n\n\$\$\n[^\n]+=[^\n]+\n\$\$\n?)$/,
  );
  await expect(page.locator(".desk-preview .katex").first()).toBeVisible();
  await expect(page.locator(".desk-preview .katex-error")).toHaveCount(0);

  // Exercises: answers are hidden until asked for, working is saved.
  await page.getByRole("tab", { name: "Exercises" }).click();
  await expect(page.locator(".desk-exercises li").first()).toBeVisible();
  const first = page.locator(".desk-exercises li").first();
  await expect(first.locator(".desk-solution .prose")).toBeHidden();
  await first.getByText("Show the answer").click();
  await expect(first.locator(".desk-solution .prose")).toBeVisible();
  await first.getByLabel("Answer 1", { exact: true }).fill("sqrt(17)");
  await first.getByLabel("Done").check();
  await page.waitForTimeout(1200);
  await page.reload();
  await page.getByRole("tab", { name: "Exercises" }).click();
  await expect(page.getByLabel("Answer 1", { exact: true })).toHaveValue(
    "sqrt(17)",
  );

  // Code: load the lab, write a file and run it with the local Python.
  await page.getByRole("tab", { name: "Code" }).click();
  await page.getByRole("button", { name: "Load lab code" }).click();
  await expect(page.getByRole("tab", { name: "lab.py" })).toBeVisible();
  page.once("dialog", (d) => d.accept("hello.py"));
  await page.getByRole("button", { name: "New" }).click();
  await page.locator(".cm-content").click();
  await page.keyboard.type("print(6 * 7)");
  await page.getByRole("button", { name: /^Run/ }).click();
  await expect(page.locator(".desk-output pre").first()).toHaveText("42\n");
  await expect(page.locator(".desk-output")).toContainText("exit 0");

  // The desk follows the lesson window.
  const lesson = await page.context().newPage();
  await lesson.goto("/lessons/HW05");
  await expect(page.getByLabel("Topic")).toHaveValue("HW05");
  expect(errors).toEqual([]);
});

test("desk API refuses requests that do not come from CoreLab", async ({
  request,
}) => {
  const run = await request.post("/api/desk", {
    headers: { origin: "https://evil.example", "x-corelab-desk": "1" },
    data: { op: "run", topic: "M02", file: "hello.py" },
  });
  expect(run.status()).toBe(400);
  const noHeader = await request.post("/api/desk", {
    headers: { origin: "http://127.0.0.1:3217" },
    data: { op: "write", topic: "M02", file: "x.py", content: "" },
  });
  expect(noHeader.status()).toBe(400);
});

test("desk docks beside the lesson, resizes and follows navigation", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1600, height: 900 });
  await page.goto("/lessons/M02");
  await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
  const toggle = page.locator(".topbar .desk-open");
  await toggle.click();
  const panel = page.getByRole("complementary", { name: "Study desk" });
  await expect(panel).toBeVisible();
  await expect(panel.getByLabel("Topic")).toHaveValue("M02");
  // The lesson column shrinks so nothing hides under the panel.
  const shell = await page.locator(".main-shell").boundingBox();
  const box = await panel.boundingBox();
  expect(shell!.x + shell!.width).toBeLessThanOrEqual(box!.x + 1);

  // Drag the left edge to widen the desk; the width is remembered.
  const edge = page.locator(".desk-resizer");
  const e = (await edge.boundingBox())!;
  await page.mouse.move(e.x + 4, e.y + 200);
  await page.mouse.down();
  await page.mouse.move(e.x - 196, e.y + 200, { steps: 5 });
  await page.mouse.up();
  const wider = (await panel.boundingBox())!.width;
  expect(wider).toBeGreaterThan(box!.width + 150);

  // Notes typed in the docked desk autosave.
  await panel.getByLabel("Notes", { exact: true }).fill("docked note");
  await expect(panel.getByText("Saved", { exact: true })).toBeVisible();

  // Moving to another lesson keeps the desk open and switches its topic.
  await page.goto("/lessons/HW05");
  await expect(panel).toBeVisible();
  await expect(panel.getByLabel("Topic")).toHaveValue("HW05");
  expect(Math.abs((await panel.boundingBox())!.width - wider)).toBeLessThan(2);

  // Ctrl+\ hides and shows it.
  await page.keyboard.press("Control+Backslash");
  await expect(panel).toBeHidden();
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await page.keyboard.press("Control+Backslash");
  await expect(panel).toBeVisible();
  await panel.getByRole("button", { name: "Close the desk" }).click();
  await expect(panel).toBeHidden();

  // Narrow screens: a bottom sheet instead of a column.
  await page.setViewportSize({ width: 390, height: 844 });
  await toggle.click();
  const sheet = (await panel.boundingBox())!;
  expect(sheet.width).toBeGreaterThan(380);
  expect(sheet.y).toBeGreaterThan(200);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  expect(errors).toEqual([]);
});
