import { test, expect } from "@playwright/test";
import { mkdirSync } from "node:fs";
test("video is click-to-load; reading bookmark and player survive mode changes without changing evidence", async ({
  page,
}) => {
  const external: string[] = [];
  await page.route("**/*", async (route) => {
    const url = route.request().url();
    if (url.startsWith("http://127.0.0.1:3217")) return route.continue();
    external.push(url);
    if (url.startsWith("https://www.youtube-nocookie.com/embed/"))
      return route.fulfill({
        contentType: "text/html",
        body: '<!doctype html><html lang="en"><body>Test lecture player</body></html>',
      });
    return route.abort();
  });
  const before = await (await page.request.get("/api/state")).json();
  await page.goto("/lessons/M02");
  await expect(
    page.getByRole("heading", { name: "Recommended video", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".katex").first()).toBeVisible();
  expect(await page.locator("iframe").count()).toBe(0);
  expect(external).toEqual([]);
  await page
    .getByRole("button", { name: "Load video player", exact: true })
    .click();
  const iframe = page.locator(".video-stage iframe");
  await expect(iframe).toHaveAttribute(
    "src",
    "https://www.youtube-nocookie.com/embed/fNk_zzaMoSs?autoplay=0&rel=0",
  );
  await expect(
    page.frameLocator(".video-stage iframe").getByText("Test lecture player"),
  ).toBeVisible();
  await iframe.evaluate((node) => node.setAttribute("data-persisted", "yes"));
  await page
    .getByRole("button", { name: "Continue theory", exact: true })
    .click();
  await page.evaluate(() => {
    const heading = document.getElementById("worked-example")!;
    window.scrollBy({
      top: heading.getBoundingClientRect().top - 125,
      behavior: "instant",
    });
  });
  const offset = await page
    .locator("#worked-example")
    .evaluate((node) => node.getBoundingClientRect().top);
  await page
    .getByRole("button", { name: "Watch & explore", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Recommended video", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Continue theory", exact: true })
    .click();
  expect(
    Math.abs(
      (await page
        .locator("#worked-example")
        .evaluate((node) => node.getBoundingClientRect().top)) - offset,
    ),
  ).toBeLessThan(4);
  await expect(iframe).toHaveAttribute("data-persisted", "yes");
  expect(external).toHaveLength(1);
  await expect(
    page.getByRole("link", { name: "Open original video", exact: true }),
  ).toHaveAttribute("href", "https://www.youtube.com/watch?v=fNk_zzaMoSs");
  const after = await (await page.request.get("/api/state")).json();
  expect(after.progress).toEqual(before.progress);
  expect(after.mastery).toEqual(before.mastery);
});

test("blocked player, offline media and external lecture pages retain local learning fallbacks", async ({
  page,
}) => {
  await page.route("https://**/*", (route) => route.abort());
  await page.goto("/lessons/M02");
  await page
    .getByRole("button", { name: "Load video player", exact: true })
    .click();
  await expect(
    page.getByText(
      "If playback is blocked or unavailable, open the original or continue below.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open original video", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Load video player", exact: true }),
  ).toBeVisible();
  await page.evaluate(() => {
    Object.defineProperty(navigator, "onLine", {
      configurable: true,
      get: () => false,
    });
    window.dispatchEvent(new Event("offline"));
  });
  await expect(
    page.getByRole("button", { name: "Load video player", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("slider", { name: "Vector x coordinate", exact: true })
    .fill("4");
  await expect(
    page.getByText("projᵥ u = (3.00, 3.00)", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".katex").first()).toBeAttached();
  await page.goto("/lessons/M04");
  await page
    .getByRole("button", {
      name: /2\. Lecture 1: The geometry of linear equations/,
    })
    .click();
  await expect(
    page.getByText("This lecture opens on its original site."),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open original video", exact: true }),
  ).toHaveAttribute("href", /ocw.mit.edu.*lecture-1-the-geometry/);
  expect(await page.locator("iframe").count()).toBe(0);
  await page.goto("/lessons/M01");
  await expect(
    page.getByText("No verified video is curated for this topic yet.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(page.locator(".katex").first()).toBeVisible();
});

test("all eight demos have working controls, reset, mobile layouts and no mastery side effects", async ({
  page,
}) => {
  const before = await (await page.request.get("/api/state")).json();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 390, height: 844 });
  const cases = [
    {
      topic: "M02",
      title: "Vectors and projections",
      run: async () => {
        await page
          .getByRole("slider", { name: "Vector x coordinate", exact: true })
          .fill("4");
        await expect(
          page.getByText("projᵥ u = (3.00, 3.00)", { exact: true }),
        ).toBeVisible();
      },
    },
    {
      topic: "M03",
      title: "Matrix transformations",
      run: async () => {
        await page
          .getByRole("button", { name: "Rotate 90°", exact: true })
          .click();
        await expect(
          page.getByText("A(1,1) = (-1.00, 1.00); det A = 1.00", {
            exact: true,
          }),
        ).toBeVisible();
      },
    },
    {
      topic: "M10",
      title: "Gradient descent",
      run: async () => {
        await page
          .getByRole("button", { name: "Step once", exact: true })
          .click();
        await expect(
          page.getByText("Step 1: x=2.40, J=2.88", { exact: true }),
        ).toBeVisible();
      },
    },
    {
      topic: "R04",
      title: "One configuration, one endpoint position",
      run: async () => {
        await page
          .getByRole("slider", { name: "Joint 1 angle", exact: true })
          .fill("90");
        await page
          .getByRole("slider", { name: "Joint 2 angle", exact: true })
          .fill("0");
        await expect(
          page.getByText("p = (0.00, 3.50) m", { exact: true }),
        ).toBeVisible();
      },
    },
    {
      topic: "R06",
      title: "Jacobian: joint motion becomes tip velocity",
      run: async () => {
        await page
          .getByRole("slider", { name: "Joint 2 angle", exact: true })
          .fill("0");
        await expect(
          page.getByText("Near singular: one direction is lost.", {
            exact: false,
          }),
        ).toBeVisible();
      },
    },
    {
      topic: "C01",
      title: "PID step response",
      run: async () => {
        await page
          .getByRole("slider", { name: "Integral gain Ki", exact: true })
          .fill("0");
        await expect(
          page.getByText(
            "Final y=0.67 · error=0.33 · peak=0.67 · final u=0.67",
            { exact: true },
          ),
        ).toBeVisible();
      },
    },
    {
      topic: "V06",
      title: "CNN convolution: a sliding kernel",
      run: async () => {
        await expect(
          page.getByRole("button", {
            name: "Output row 1 column 1: 3",
            exact: true,
          }),
        ).toBeVisible();
        await page
          .getByRole("button", { name: "Identity", exact: true })
          .click();
        await expect(
          page.getByRole("button", {
            name: "Output row 1 column 1: 0",
            exact: true,
          }),
        ).toBeVisible();
      },
    },
    {
      topic: "RL06",
      title: "Q-learning GridWorld",
      run: async () => {
        await page
          .getByRole("button", { name: "Train 50 episodes", exact: true })
          .click();
        await expect(
          page.getByText("Episodes: 50 · Goals reached:", { exact: false }),
        ).toBeVisible();
      },
    },
  ];
  for (const demo of cases) {
    await page.goto(`/lessons/${demo.topic}`);
    const region = page.getByRole("region", { name: demo.title, exact: true });
    await expect(region).toBeVisible();
    await demo.run();
    await region.getByRole("button", { name: "Reset", exact: true }).click();
    await expect(
      region.getByText("Worked example & model limits", { exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  await expect(
    page.getByText("Episodes: 0 · Goals reached: 0", { exact: true }),
  ).toBeVisible();
  mkdirSync(".local/screenshots", { recursive: true });
  await page
    .locator(".concept-demo")
    .screenshot({ path: ".local/screenshots/gridworld-mobile.png" });
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.goto("/lessons/M02");
  await expect(
    page.getByRole("heading", { name: "Vectors and projections", exact: true }),
  ).toBeVisible();
  await page
    .locator(".concept-demo")
    .screenshot({ path: ".local/screenshots/vectors-desktop.png" });
  const after = await (await page.request.get("/api/state")).json();
  expect(after.progress).toEqual(before.progress);
  expect(after.mastery).toEqual(before.mastery);
  expect(errors).toEqual([]);
});
