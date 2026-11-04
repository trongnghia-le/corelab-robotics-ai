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
