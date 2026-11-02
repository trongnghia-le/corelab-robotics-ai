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
    page.getByRole("img", { name: "Robotics and AI concept sketch" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open Robotics & AI lab" }),
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
    new RegExp(`^${attempted}\\s*through topic assessments$`),
  );
  await expect(page.locator(".dashboard-domain-card")).toHaveCount(
    new Set(curriculum.map((t) => t.domain)).size,
  );
  const robotics = page
    .locator(".dashboard-domain-card")
    .filter({
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
