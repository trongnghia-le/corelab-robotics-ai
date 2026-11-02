import { test, expect } from "@playwright/test";

test("Python and C++ use Dark+ syntax colors and copy the exact original source", async ({
  page,
}) => {
  const before = await (await page.request.get("/api/state")).json();
  for (const [topic, lang] of [
    ["M01", "python"],
    ["CPP01", "cpp"],
  ]) {
    const payload = await (
      await page.request.get("/api/topics/" + topic)
    ).json();
    const expected = payload.lesson.body.match(
      new RegExp("```" + lang + "\\n([\\s\\S]*?)```"),
    )[1];
    await page.goto("/lessons/" + topic);
    const block = page.locator(`.code-block[data-language="${lang}"]`).first();
    await expect(block).toHaveAttribute("data-highlighted", "true", {
      timeout: 20000,
    });
    expect(await block.locator("pre code").textContent()).toBe(expected);
    await expect(block.locator("pre")).toHaveCSS(
      "background-color",
      "rgb(30, 30, 30)",
    );
    const keyword = lang === "python" ? "def" : "double";
    await expect(
      block
        .locator("span[style]")
        .filter({ hasText: new RegExp("^" + keyword + "$") })
        .first(),
    ).toHaveCSS("color", "rgb(86, 156, 214)");
    await expect(
      block
        .locator("span[style]")
        .filter({
          hasText: lang === "python" ? /time must be nonnegative/ : /^"empty"$/,
        })
        .first(),
    ).toHaveCSS("color", "rgb(206, 145, 120)");
    await block.getByRole("button", { name: "Copy code", exact: true }).click();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(
      expected,
    );
    await expect(
      block.getByRole("button", { name: "Code copied", exact: true }),
    ).toBeVisible();
    await block.screenshot({ path: `test-results/code-${lang}-dark-plus.png` });
  }
  expect(
    (await (await page.request.get("/api/state")).json()).progress,
  ).toEqual(before.progress);
});

test("reading sections preserve anchors, mathematics and usable phone-width code", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/lessons/M01");
  const heading = page.getByRole("heading", {
    name: "Worked example",
    exact: true,
  });
  await expect(heading).toHaveAttribute("id", "worked-example");
  await expect(page.locator(".lesson-section-example")).toHaveAccessibleName(
    "Worked example",
  );
  await expect(page.locator(".katex").first()).toBeVisible();
  await page.locator('.lesson-toc a[href="#reference-implementation"]').click();
  const block = page.locator('.code-block[data-language="python"]');
  await expect(block).toHaveAttribute("data-highlighted", "true");
  await page.locator(".lesson-section-example").scrollIntoViewIfNeeded();
  await page.screenshot({ path: "test-results/lesson-reading-desktop.png" });
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await block.scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(
      await block
        .locator("pre")
        .evaluate((el) => parseFloat(getComputedStyle(el).fontSize)),
    ).toBeGreaterThanOrEqual(16);
    await block.locator("pre").focus();
    await expect(block.locator("pre")).toBeFocused();
    await page.screenshot({
      path: `test-results/lesson-reading-mobile-${width}.png`,
    });
  }
  expect(errors).toEqual([]);
});

test("markup-shaped code and unknown languages stay inert and retain their text", async ({
  page,
}) => {
  const before = await (await page.request.get("/api/state")).json();
  const code = 'payload = "<img src=x onerror=alert(1)>"\nprint(payload)\n';
  const plain =
    '## This belongs inside code\n<script>document.documentElement.dataset.executed="yes"</script>\n';
  await page.route("**/api/topics/M01", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    payload.lesson.body =
      "## Worked example\n\n```python\n" +
      code +
      "```\n\n```unknown-language\n" +
      plain +
      "```\n\n<img src=x onerror=\"document.documentElement.dataset.executed='yes'\">\n\n## Failure modes\n\nKeep code as data.\n";
    await route.fulfill({ json: payload });
  });
  await page.goto("/lessons/M01");
  const block = page.locator('.code-block[data-language="python"]');
  await expect(block).toHaveAttribute("data-highlighted", "true");
  expect(await block.locator("pre code").textContent()).toBe(code);
  const unknown = page.locator('.code-block[data-language="text"]');
  await expect(unknown).toHaveAttribute("data-highlighted", "false");
  expect(await unknown.locator("pre code").textContent()).toBe(plain);
  await expect(
    page.getByRole("heading", { name: "This belongs inside code" }),
  ).toHaveCount(0);
  await expect(page.locator(".prose img")).toHaveCount(0);
  expect(
    await page.evaluate(() => document.documentElement.dataset.executed),
  ).toBeUndefined();
  expect(
    (await (await page.request.get("/api/state")).json()).progress,
  ).toEqual(before.progress);
});
