import { test, expect } from "@playwright/test";

// A topic no other flow depends on, so its check-off records stay isolated.
const topic = "RS08";

test("lessons are split into four sessions with deep links, gated answers and tick-off progress", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`/lessons/${topic}`);
  const stepper = page.getByRole("navigation", { name: "Study sessions" });
  await expect(stepper.locator("ol button")).toHaveCount(4);
  await expect(page.getByTestId("lesson-time")).toHaveText(
    /≈ \d+ h( \d+ min)? · 4 sessions/,
  );
  await expect(stepper.getByRole("button", { name: /^Learn/ })).toHaveAttribute(
    "aria-current",
    "step",
  );
  await expect(page.locator("h2#theory-and-derivation")).toBeVisible();
  await expect(page.locator("h2#exercises")).toHaveCount(0);

  // Practice: exercises shown, answers behind a keyboard-accessible button.
  await stepper.getByRole("button", { name: /^Practice/ }).click();
  await expect(page.locator("h2#exercises")).toBeVisible();
  await expect(page.locator("h2#exercise-answers")).toHaveCount(0);
  const show = page.getByRole("button", { name: "Show answers" });
  await show.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("h2#exercise-answers")).toBeVisible();
  await page.getByRole("button", { name: "Hide answers" }).click();
  await expect(page.locator("h2#exercise-answers")).toHaveCount(0);

  // Deep links open the session that contains the anchor.
  await page.goto(`/lessons/${topic}#failure-modes`);
  await expect(page.locator("h2#failure-modes")).toBeVisible();
  await expect(
    stepper.getByRole("button", { name: /^Review/ }),
  ).toHaveAttribute("aria-current", "step");
  await page.goto(`/lessons/${topic}#exercise-answers`);
  await expect(page.locator("h2#exercise-answers")).toBeVisible();
  await page.goto(`/lessons/${topic}#reference-implementation`);
  await expect(page.locator("h2#reference-implementation")).toBeInViewport();

  // The contents drawer switches sessions too.
  await page.getByRole("button", { name: "Contents", exact: true }).click();
  await page.locator('.lesson-toc a[href="#worked-example"]').click();
  await expect(page.locator("h2#worked-example")).toBeInViewport();

  // Tick-off: structured records, derived state, survives a reload.
  await stepper.getByRole("button", { name: /^Build/ }).click();
  await page.getByRole("button", { name: "Lab done", exact: true }).click();
  await stepper.getByRole("button", { name: /^Practice/ }).click();
  await page
    .getByRole("button", { name: "Mark session done", exact: true })
    .click();
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "2",
  );
  let state = await (await page.request.get("/api/state")).json();
  const records = state.progress.sessions.filter((s: { text: string }) =>
    s.text.startsWith(`checkoff:${topic}:`),
  );
  expect(records.map((s: { text: string }) => s.text)).toEqual([
    `checkoff:${topic}:build:done`,
    `checkoff:${topic}:practice:done`,
  ]);
  expect(records.map((s: { kind: string }) => s.kind)).toEqual([
    "practice",
    "practice",
  ]);
  expect(records[0].minutes).toBeGreaterThan(0);
  await page.reload();
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "2",
  );
  await expect(
    page.getByText("2/4 sessions", { exact: true }).first(),
  ).toBeVisible();
  await page.goto("/lessons");
  await expect(page.getByText("2/4 sessions").first()).toBeVisible();

  // Undo is another record; the latest one wins.
  await page.goto(`/lessons/${topic}#exercises`);
  await page
    .getByRole("button", { name: "Mark session done", exact: true })
    .click();
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "1",
  );
  state = await (await page.request.get("/api/state")).json();
  expect(state.progress.sessions.at(-1).text).toBe(
    `checkoff:${topic}:practice:undone`,
  );
  await page.goto(`/lessons/${topic}#reference-implementation`);
  await page.getByRole("button", { name: "Lab done", exact: true }).click();
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "0",
  );
  expect(errors).toEqual([]);
});

test("sessions fit phones without horizontal scrolling and the sticky bar never covers anchors", async ({
  page,
}) => {
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(`/lessons/${topic}`);
    for (const name of [/^Learn/, /^Practice/, /^Build/, /^Review/]) {
      await page
        .getByRole("navigation", { name: "Study sessions" })
        .getByRole("button", { name })
        .click();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`/lessons/${topic}#worked-example`);
  const heading = page.locator("h2#worked-example");
  await expect(heading).toBeInViewport();
  await page.waitForTimeout(300);
  const bar = await page.locator(".media-navigation").boundingBox();
  const top = (await heading.boundingBox())!.y;
  if (bar) expect(top).toBeGreaterThanOrEqual(bar.y + bar.height - 1);
});
