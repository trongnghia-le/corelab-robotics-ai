import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const curriculum = JSON.parse(
  readFileSync("corelab/curriculum_graph_v1.json", "utf8"),
).modules as { id: string; domain: string }[];

test("dashboard presents actual topic evidence and opens the selected curriculum domain", async ({
  page,
}) => {
  const before = await (await page.request.get("/api/state")).json();
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Your Robotics & AI journey." }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: "CoreLab subjects connected as a constellation that converges on a robot",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open Extra practice lab" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Explore Robotics & AI curriculum" }),
  ).toHaveAttribute("href", "/roadmap");
  const verified = Object.values(before.mastery).filter(
    (m) => (m as { level: number }).level > 0,
  ).length;
  const attempted = new Set(
    before.progress.attempts.map((a: { topicId: string }) => a.topicId),
  ).size;
  await expect(page.getByTestId("dashboard-evidence-count")).toHaveText(
    new RegExp(`^${verified}\\s*of ${curriculum.length} curriculum topics$`),
  );
  await expect(page.getByTestId("dashboard-attempted-count")).toHaveText(
    new RegExp(`^${attempted}\\s*through topic checks$`),
  );
  await expect(page.locator(".dashboard-domain-card")).toHaveCount(
    new Set(curriculum.map((t) => t.domain)).size,
  );
  const robotics = page.locator(".dashboard-domain-card").filter({
    has: page.getByRole("heading", { name: "Robotics", exact: true }),
  });
  await expect(robotics).toContainText(
    `${curriculum.filter((t) => t.domain === "Robotics").length} curriculum topics`,
  );
  await expect(robotics).toContainText(
    `${before.lessonIds.filter((id: string) => curriculum.some((t) => t.id === id && t.domain === "Robotics")).length} authored lessons`,
  );
  await robotics.click();
  await expect(page).toHaveURL(/roadmap\?domain=Robotics$/);
  await expect(page.getByLabel("Filter by domain")).toHaveValue("Robotics");
  const after = await (await page.request.get("/api/state")).json();
  expect(after.progress).toEqual(before.progress);
});

test("dashboard stays keyboard accessible and readable on desktop and small screens", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await expect(page.locator(".focus-card h2")).toBeVisible();
  const action = page.locator(".focus-card a.button.primary");
  await expect(action).toHaveAttribute("href", "/lessons/M01");
  await action.focus();
  await expect(action).toBeFocused();
  expect((await action.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  await page.screenshot({ path: "test-results/dashboard-desktop.png" });
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(
      await page
        .locator(".focus-description")
        .evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
    ).toBeGreaterThanOrEqual(16);
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({
      path: `test-results/dashboard-mobile-${width}.png`,
    });
  }
  expect(errors).toEqual([]);
});

test("subject colors remain readable and consistent from dashboard to lesson", async ({
  page,
}) => {
  const before = await (await page.request.get("/api/state")).json();
  await page.goto("/");
  await expect(page.locator(".dashboard-domain-card")).toHaveCount(10);
  const palette = await page
    .locator(".dashboard-domain-card")
    .evaluateAll((cards) =>
      cards.map((card) => {
        const style = getComputedStyle(card);
        const icon = getComputedStyle(
          card.querySelector(".dashboard-domain-icon")!,
        );
        return {
          name: card.querySelector("h3")!.textContent,
          accent: icon.color,
          iconBackground: icon.backgroundColor,
          text: getComputedStyle(card.querySelector("p")!).color,
          heading: getComputedStyle(card.querySelector("h3")!).color,
          surface: style.getPropertyValue("--domain-surface").trim(),
          base: style.getPropertyValue("--surface-1").trim(),
        };
      }),
    );
  const luminance = (color: string) => {
    const rgb = color.startsWith("#")
      ? [1, 3, 5].map((i) => parseInt(color.slice(i, i + 2), 16))
      : color
          .match(/[\d.]+/g)!
          .slice(0, 3)
          .map(Number);
    const values = rgb.map((v) => {
      const c = v / 255;
      return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
  };
  const contrast = (a: string, b: string) => {
    const x = luminance(a),
      y = luminance(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  };
  expect(new Set(palette.map((p) => p.accent)).size).toBe(10);
  for (const p of palette) {
    expect(
      contrast(p.accent, p.iconBackground),
      p.name + " accent",
    ).toBeGreaterThanOrEqual(4.5);
    for (const background of [p.surface, p.base]) {
      expect(
        contrast(p.text, background),
        p.name + " description",
      ).toBeGreaterThanOrEqual(4.5);
      expect(
        contrast(p.heading, background),
        p.name + " heading",
      ).toBeGreaterThanOrEqual(4.5);
    }
  }
  const math = page.locator(".dashboard-domain-card").filter({
    has: page.getByRole("heading", { name: "Mathematics", exact: true }),
  });
  const mathAccent = palette.find((p) => p.name === "Mathematics")!.accent;
  await math.focus();
  await expect(math).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Filter by domain")).toHaveValue("Mathematics");
  await page.goto("/lessons/M01");
  await expect(page.locator(".topic-meta .topic-code")).toHaveText("M01");
  expect(
    await page
      .locator(".topic-meta .topic-code")
      .evaluate((el) => getComputedStyle(el).color),
  ).toBe(mathAccent);
  expect(
    (await (await page.request.get("/api/state")).json()).progress,
  ).toEqual(before.progress);
});

test("sidebar folds into an icon rail and remembers it", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/lessons/M02");
  const sidebar = page.locator(".sidebar");
  expect((await sidebar.boundingBox())!.width).toBeGreaterThan(200);
  await page.getByRole("button", { name: "Collapse the sidebar" }).click();
  expect((await sidebar.boundingBox())!.width).toBeLessThan(80);
  // Links keep their accessible names and a hover title.
  const lessons = sidebar.getByRole("link", { name: "Lessons" });
  await expect(lessons).toHaveAttribute("title", "Lessons");
  expect((await page.locator(".main-shell").boundingBox())!.x).toBeLessThan(80);
  await page.reload();
  expect((await sidebar.boundingBox())!.width).toBeLessThan(80);
  // The old per-topic notebook is gone; notes live in the study desk.
  await expect(page.getByText("Research notebook")).toHaveCount(0);
  await page.getByRole("button", { name: "Expand the sidebar" }).click();
  expect((await sidebar.boundingBox())!.width).toBeGreaterThan(200);
});
