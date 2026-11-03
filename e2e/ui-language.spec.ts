import { test, expect } from "@playwright/test";
import { existsSync, readdirSync } from "node:fs";

const vietnamese = /[ăâđêôơưĂÂĐÊÔƠƯẠ-ỹ]/u;

test("the EN/VI switch translates the chrome, persists, and falls back per lesson", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  expect(await page.locator("body").innerText()).not.toMatch(vietnamese);
  const switcher = page.getByRole("group", { name: "Language" });
  await expect(switcher.getByRole("button", { name: "EN" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await switcher.getByRole("button", { name: "VI" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "vi");
  await expect(
    page.getByRole("heading", { name: "Hành trình Robotics & AI của bạn." }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Lộ trình", exact: true }).first(),
  ).toBeVisible();
  const cookies = await page.context().cookies();
  expect(cookies.find((c) => c.name === "corelab-lang")?.value).toBe("vi");
  expect(await page.evaluate(() => localStorage.getItem("corelab-lang"))).toBe(
    "vi",
  );

  // Persisted across reloads and visible to the server (no flash of English).
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "vi");
  await expect(
    page.getByRole("heading", { name: "Hành trình Robotics & AI của bạn." }),
  ).toBeVisible();

  // Roadmap filters and a lesson without a translation.
  await page.goto("/roadmap");
  await expect(
    page.getByRole("combobox", { name: "Lọc theo trạng thái" }),
  ).toBeVisible();
  const ids = readdirSync("content/lessons")
    .filter((f) => f.endsWith(".md"))
    .map((f) => f.slice(0, -3));
  const untranslated = ids.find(
    (id) => !existsSync(`content/lessons/vi/${id}.md`),
  );
  if (!untranslated)
    await page.route("**/api/topics/M01?lang=vi", async (route) => {
      const response = await route.fetch();
      const payload = await response.json();
      payload.lesson.missingTranslation = true;
      await route.fulfill({ json: payload });
    });
  await page.goto(`/lessons/${untranslated ?? "M01"}`);
  await expect(
    page.getByText("Chưa có bản dịch", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Các buổi học" }),
  ).toBeVisible();

  // A translated lesson keeps English heading ids so anchors still work.
  const translated = ids.find((id) =>
    existsSync(`content/lessons/vi/${id}.md`),
  );
  if (translated) {
    await page.goto(`/lessons/${translated}#theory-and-derivation`);
    await expect(page.locator("h2#theory-and-derivation")).toBeInViewport();
    await expect(page.getByText("Chưa có bản dịch")).toHaveCount(0);
  }

  // Remaining pages are translated, and translated lesson titles show in lists.
  for (const [route, heading] of [
    ["/practice", "Tự cài đặt. Tự kiểm chứng."],
    ["/paths", "Một đường học, nhiều nhánh mở."],
    ["/tutor", "Một gia sư. Một nguồn dữ liệu duy nhất."],
    ["/settings", "Dữ liệu & cài đặt"],
    ["/assessments", "Kiểm tra kiến thức của bạn."],
  ]) {
    await page.goto(route);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
  }
  await page.goto("/practice");
  await expect(
    page.getByText("Tích vô hướng từ trang giấy trắng"),
  ).toBeVisible();
  await page.goto("/settings");
  await expect(
    page.getByRole("heading", { name: "Sao lưu tiến độ" }),
  ).toBeVisible();
  await page.goto("/lessons/M02");
  await expect(page.getByTestId("lesson-time")).toHaveText(/giờ.*· 4 buổi/);
  const en = await (await page.request.get("/api/topics/M02?lang=en")).json();
  const vi = await (await page.request.get("/api/topics/M02?lang=vi")).json();
  expect(vi.lesson.sessionMinutes).toEqual(en.lesson.sessionMinutes);
  if (translated) {
    await page.goto("/lessons");
    await expect(
      page.getByRole("heading", { name: vi.lesson.meta.title, exact: true }),
    ).toBeVisible();
  }

  // Back to English.
  await page.goto("/lessons/M02");
  await page
    .getByRole("group", { name: "Ngôn ngữ" })
    .getByRole("button", { name: "EN" })
    .click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(
    page.getByRole("navigation", { name: "Study sessions" }),
  ).toBeVisible();
});
