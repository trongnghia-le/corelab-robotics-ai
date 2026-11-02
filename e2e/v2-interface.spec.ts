import { test, expect } from "@playwright/test";

test("exercise discovery and activity navigation do not create learning records", async ({
  page,
}) => {
  await page.goto("/objectives");
  const before = await (
    await page.request.get("/api/v2/history?limit=50")
  ).json();
  const activities = page.getByRole("navigation", {
    name: "Learning activities",
  });
  await expect(activities).toBeVisible();
  await expect(page.locator('.sidebar a[href="/objectives"]')).toHaveAttribute(
    "aria-current",
    "page",
  );
  // Practice discovery should appear near the top, before the long kit catalog.
  const modes = page.getByRole("navigation", {
    name: "Objective practice mode",
  });
  await expect(modes).toBeVisible();
  expect((await modes.boundingBox())!.y).toBeLessThan(1100);
  await page.getByRole("button", { name: "Explore", exact: true }).click();
  const search = page.getByRole("searchbox", { name: "Search exercises" });
  await search.fill("X11");
  await expect(page.locator(".v2-family")).toHaveCount(1);
  await search.fill("no-such-exercise-xyz");
  await expect(
    page.getByText("No matching exercises in this view."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Explore all exercises" }).click();
  await expect(search).toHaveValue("");
  expect(await page.locator(".v2-family").count()).toBeGreaterThan(20);
  await activities.getByRole("link", { name: /Learn/ }).click();
  await expect(
    page.getByRole("heading", { name: "Choose an optional learning path" }),
  ).toBeVisible();
  await activities.getByRole("link", { name: /Apply/ }).click();
  await expect(
    page.getByRole("heading", { name: "Build it locally." }),
  ).toBeInViewport();
  await activities.getByRole("link", { name: /Verify/ }).click();
  await expect(
    page.getByRole("heading", { name: "Verify independently · C and M" }),
  ).toBeInViewport();
  const after = await (
    await page.request.get("/api/v2/history?limit=50")
  ).json();
  expect(after).toEqual(before);
});

test("practice stays prominent, keyboard focused and resumable with recorded assistance", async ({
  page,
}) => {
  await page.goto("/objectives");
  await page.getByRole("button", { name: "Explore", exact: true }).click();
  await page.getByRole("searchbox", { name: "Search exercises" }).fill("X11");
  await page
    .locator(".v2-family")
    .getByRole("button", { name: "Practice", exact: true })
    .click();
  const panel = page.locator(".v2-attempt");
  await expect(panel).toBeFocused();
  expect(
    await page.evaluate(
      () =>
        !!(
          document
            .querySelector(".v2-attempt")!
            .compareDocumentPosition(document.querySelector(".v2-family")!) &
          Node.DOCUMENT_POSITION_FOLLOWING
        ),
    ),
  ).toBe(true);
  await page
    .getByRole("button", { name: "A1 · Concept hint", exact: true })
    .click();
  await expect(
    page.getByText("Highest observed assistance: A1.", { exact: false }),
  ).toBeVisible();
  const history = await (
    await page.request.get("/api/v2/history?limit=1")
  ).json();
  const id = history.items[0].id;
  await page.reload();
  await page.getByRole("button", { name: "Resume recent practice" }).click();
  await expect(panel).toBeFocused();
  await expect(
    page.getByText("Highest observed assistance: A1.", { exact: false }),
  ).toBeVisible();
  const resumed = await (
    await page.request.get("/api/v2/history?limit=1")
  ).json();
  expect(resumed.items[0].id).toBe(id);
  await page.screenshot({
    path: "test-results/ui-desktop-practice.png",
    fullPage: true,
  });
});

test("small screens keep readable inputs, visible evidence limits and no page overflow", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/objectives/M01.radians-trig");
    await expect(
      page.getByRole("heading", { name: "Build this objective" }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "No independent C/M form is available for this objective yet.",
        { exact: false },
      ),
    ).toBeVisible();
    await expect(
      page.getByText("A full turn is 2π radians", { exact: false }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    const search = page.getByRole("searchbox", { name: "Search exercises" });
    expect(
      await search.evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
    ).toBeGreaterThanOrEqual(16);
    expect((await search.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await page.screenshot({
      path: `test-results/ui-mobile-${width}.png`,
      fullPage: true,
    });
  }
  expect(errors).toEqual([]);
});

test("independent checks use clear labels and record help only after consent", async ({
  page,
}) => {
  await page.goto("/objectives/M12.frame-labels");
  await page
    .getByRole("button", {
      name: "Fresh check: Frames and planar transforms check",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", { name: "Submit independent check" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Check practice answer" }),
  ).toHaveCount(0);
  const history = await (
    await page.request.get("/api/v2/history?limit=1")
  ).json();
  const id = history.items[0].id;
  await page
    .getByRole("button", { name: "A1 · Concept hint", exact: true })
    .click();
  await expect(
    page.getByText("Opening help makes this verification attempt assisted", {
      exact: false,
    }),
  ).toBeVisible();
  const before = await (
    await page.request.get("/api/v2/attempts/" + id)
  ).json();
  expect(before.observedAssistance).toBe(0);
  await page
    .getByRole("button", { name: "Keep working independently" })
    .click();
  await expect(
    page.getByRole("button", { name: "Continue with assisted attempt" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "A1 · Concept hint", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Continue with assisted attempt" })
    .click();
  await expect(
    page.getByText("Highest observed assistance: A1.", { exact: false }),
  ).toBeVisible();
  const after = await (await page.request.get("/api/v2/attempts/" + id)).json();
  expect(after.purpose).toBe("verify");
  expect(after.observedAssistance).toBe(1);
});

test("Robotics and AI identity leads to real authored learning activities", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/objectives");
  await expect(page).toHaveTitle("CoreLab · Learn Robotics & AI");
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Learn Robotics & AI. From first principles.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: "Robotics and AI concept sketch" }),
  ).toBeVisible();
  const entries = page.getByRole("navigation", {
    name: "Robotics and AI starting points",
  });
  await expect(entries.getByRole("link")).toHaveCount(4);
  for (const link of await entries.getByRole("link").all()) {
    const href = await link.getAttribute("href");
    const response = await page.request.get("/api/v2" + href);
    expect(response.status()).toBe(200);
    const detail = await response.json();
    expect(
      detail.objectives.some((o: { id: string }) => href!.endsWith(o.id)),
    ).toBe(true);
  }
  await page.screenshot({ path: "test-results/robotics-ai-desktop.png" });
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `test-results/robotics-ai-mobile-${width}.png`,
      fullPage: false,
    });
  }
  await entries.getByRole("link", { name: /Computer vision/ }).click();
  await expect(page).toHaveURL(/objectives\/V03.pinhole$/);
  await expect(
    page.getByRole("heading", { name: "Project a camera-frame point" }),
  ).toBeVisible();
});
