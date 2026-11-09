import { expect, test } from "@playwright/test";

const background = (page: import("@playwright/test").Page) =>
  page.evaluate(() => getComputedStyle(document.body).backgroundColor);

test("light theme switch persists, renders server-side and syncs the desk", async ({
  page,
  context,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  const dark = await background(page);
  const desk = await context.newPage();
  await desk.goto("/desk?topic=M02");
  await expect(desk.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.getByRole("button", { name: "Switch to light theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  expect(await background(page)).not.toBe(dark);
  // The other window follows through the storage event.
  await expect(desk.locator("html")).toHaveAttribute("data-theme", "light");

  // The cookie makes the server render light HTML: no flash on reload.
  const html = await (await page.request.get("/")).text();
  expect(html).toContain('data-theme="light"');
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  // Code blocks keep their dark palette in the light theme.
  await page.goto("/lessons/M02");
  await page
    .getByRole("navigation", { name: "Study sessions" })
    .getByRole("button", { name: /^Build/ })
    .click();
  const code = page.locator(".code-block pre").first();
  await expect(code).toBeVisible();
  const codeBg = await code.evaluate(
    (el) => getComputedStyle(el).backgroundColor,
  );
  const [r, g, b] = codeBg.match(/\d+/g)!.map(Number);
  expect(r + g + b).toBeLessThan(200);

  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});
