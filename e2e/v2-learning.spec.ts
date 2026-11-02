import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
test("objective choice → help → independent declaration → practice → reload → recovery", async ({
  page,
}) => {
  await page.goto("/objectives");
  await expect(
    page.getByRole("heading", { name: "Your next independent step." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Explore", exact: true }).click();
  const family = page.locator(".v2-family").filter({
    has: page.getByRole("heading", {
      name: "Project onto an allowed direction",
    }),
  });
  await family.getByRole("button", { name: "Practice", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Work the problem." }),
  ).toBeVisible();
  const events = await (
    await page.request.get("/api/v2/history?limit=1")
  ).json();
  const detail = await (
    await page.request.get("/api/v2/attempts/" + events.items[0].id)
  ).json();
  const itemId = detail.item.id;
  const source = JSON.parse(
    readFileSync(
      "content/exercises/X01.v" + detail.sourceVersion + ".json",
      "utf8",
    ),
  );
  const item = source.items.find((i: { id: string }) => i.id === itemId);
  await page
    .getByRole("button", { name: "A1 · Concept hint", exact: true })
    .click();
  await expect(
    page.getByText("Highest observed assistance: A1.", { exact: false }),
  ).toBeVisible();
  for (const field of item.fields)
    await page
      .getByRole("textbox", { name: field.label, exact: true })
      .fill(Number(field.answer).toFixed(8));
  await page
    .getByLabel("Implementation scratchpad (optional, never executed)")
    .fill('print("This is saved text, not a grading protocol")');
  await page
    .getByRole("button", { name: "Check practice answer", exact: false })
    .click();
  await expect(
    page.getByRole("heading", { name: "Correct practice answer" }),
  ).toBeVisible();
  await expect(
    page.getByText("effective assistance A1", { exact: false }),
  ).toBeVisible();
  const before = await (await page.request.get("/api/state")).json();
  expect(before.progress.attempts).toHaveLength(0);
  await page.reload();
  await expect(
    page.getByRole("button", { name: /X01 .* View saved practice/ }).first(),
  ).toBeVisible();
  const backup = await (await page.request.get("/api/v2/backup/export")).json();
  expect(backup.schema).toBe("corelab-backup/3");
  expect(backup.v2.evidence).toHaveLength(0);
  await page.goto("/settings");
  await page.getByLabel("Choose full V2 backup").setInputFiles({
    name: "backup.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(backup)),
  });
  await page
    .getByRole("button", { name: "Preview backup replacement" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Full learning replacement" }),
  ).toBeVisible();
  await page
    .getByRole("checkbox", {
      name: "I confirm replacing the stated learning history.",
      exact: false,
    })
    .check();
  await page
    .getByRole("button", { name: "Confirm learning replacement" })
    .click();
  await expect(
    page.getByText("Learning history restored.", { exact: false }),
  ).toBeVisible();
  const after = await (await page.request.get("/api/state")).json();
  expect(after.progress).toEqual(before.progress);
});
test("valid non-ASCII backup above 8 MB restores through V2 while the legacy route keeps its limit", async ({
  page,
}) => {
  const legacy = await (await page.request.get("/api/export")).json();
  legacy.progress.sessions = Array.from({ length: 450 }, (_, i) => ({
    id: "byte-boundary-" + i,
    topicId: "M01",
    at: new Date().toISOString(),
    kind: "note",
    text: "é".repeat(9000),
    minutes: 1,
  }));
  const raw = JSON.stringify(legacy);
  expect(Buffer.byteLength(raw)).toBeGreaterThan(8000000);
  const refused = await page.request.post("/api/validate", { data: legacy });
  expect(refused.status()).toBe(400);
  const p = await page.request.post("/api/v2/backup/preview", { data: legacy });
  expect(p.status(), await p.text()).toBe(200);
  const preview = await p.json();
  const restored = await page.request.post("/api/v2/backup/restore", {
    data: legacy,
    headers: {
      "X-CoreLab-Confirm": "true",
      "X-CoreLab-BackupHash": preview.digest,
      "X-CoreLab-ExpectedRevision": preview.token,
    },
  });
  expect(restored.status(), await restored.text()).toBe(200);
  const full = await (await page.request.get("/api/v2/backup/export")).json();
  expect(full.legacy.progress.sessions).toHaveLength(450);
  expect(full.legacy.progress.sessions[0].text).toBe("é".repeat(9000));
});
test("optional bridge, manual kit download and practice-only self-report", async ({
  page,
}) => {
  await page.goto("/objectives/M01.radians-trig");
  await expect(
    page
      .getByRole("heading", {
        name: "Radians, trigonometry and coordinates",
        exact: true,
      })
      .first(),
  ).toBeVisible();
  await expect(
    page.getByText("A full turn is 2π radians", { exact: false }),
  ).toBeVisible();
  await page.goto("/objectives/R04.planar-fk");
  await expect(
    page.getByText("Optional readiness suggestions", { exact: false }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download Planar FK self-check kit" })
    .click();
  expect((await download).suggestedFilename()).toBe("L02-planar.v1.py");
  await page
    .getByRole("button", { name: "Record that I ran my own tests" })
    .click();
  await expect(
    page.getByText(
      "Manual self-report only. No verification, signature or mastery evidence.",
      { exact: true },
    ),
  ).toBeVisible();
  const backup = await (await page.request.get("/api/v2/backup/export")).json();
  expect(
    backup.v2.attempts.some(
      (a: { source_kind: string; status: string }) =>
        a.source_kind === "kit" && a.status === "submitted",
    ),
  ).toBe(true);
  expect(backup.v2.evidence).toHaveLength(0);
  await page.goto("/objectives/R02.exact-arc");
  const odometryDownload = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download Odometry self-check kit" })
    .click();
  expect((await odometryDownload).suggestedFilename()).toBe(
    "L03-odometry.v1.py",
  );
});
test("mobile keyboard, source redaction and gated verification", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/objectives/R04.planar-fk");
  await expect(
    page.getByRole("heading", { name: "Build this objective" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Practice", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("textbox", { name: "x (m)", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByRole("textbox", { name: "x (m)", exact: true }),
  ).toBeEnabled();
  await page.getByRole("textbox", { name: "x (m)", exact: true }).focus();
  await page.keyboard.type("1/2");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("textbox", { name: "y (m)", exact: true }),
  ).toBeFocused();
  const denied = await page.request.post("/api/v2/attempts", {
    data: { purpose: "verify", source: "X11" },
  });
  expect(denied.status()).toBe(503);
  const verify = await page.request.post("/api/v2/attempts", {
    data: { purpose: "verify", source: "F-R04" },
  });
  expect(verify.status()).toBe(201);
  const form = await verify.json();
  expect(form.purpose).toBe("verify");
  expect(JSON.stringify(form)).not.toContain('"answer"');
  const forged = await page.request.post("/api/v2/reports/import", {
    data: { passed: true, path: "do-not-open" },
  });
  expect(forged.status()).toBe(503);
  await page.screenshot({
    path: info.outputPath("v2-mobile.png"),
    fullPage: true,
  });
});
