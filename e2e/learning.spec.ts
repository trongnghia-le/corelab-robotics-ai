import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync } from "node:fs";
import type { Assessment } from "../lib/types";
const getAssessment = (id: string): Assessment =>
  JSON.parse(readFileSync(`content/assessments/${id}.v1.json`, "utf8"));
test("empty workspace → lesson → assessment → reload → evidence → handoff → backup → restore → graph", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Xây nền tảng. Đi xa hơn." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Mathematical Basics", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Chưa đánh giá là một điểm bắt đầu"),
  ).toBeVisible();
  const initial = await (await page.request.get("/api/state")).json();
  expect(initial.progress.attempts).toHaveLength(0);
  expect(
    Object.values(initial.mastery).every(
      (v) => !!v && typeof v === "object" && "level" in v && v.level === 0,
    ),
  ).toBe(true);
  await page.getByRole("link", { name: "Tiếp tục học", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Notation, functions, and units",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".katex").first()).toBeVisible();
  await expect(page.locator(".lesson-toc a").first()).toBeVisible();
  await page
    .getByRole("button", { name: "Đánh dấu đã đọc", exact: true })
    .click();
  await expect(
    page
      .getByRole("status")
      .getByText("Đã lưu hoạt động đọc. Mastery không thay đổi."),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Kiểm tra năng lực", exact: true })
    .click();
  const contract = getAssessment("M01")!;
  await page
    .getByRole("radio", { name: "Yes, provided each input has one output." })
    .check();
  for (const q of contract.questions.filter((q) => q.kind === "number"))
    await page
      .getByRole("textbox", { name: `Đáp án ${q.id}`, exact: true })
      .fill(q.answer!);
  await page
    .getByRole("textbox", { name: "Câu trả lời theo rubric" })
    .fill(
      "I state assumptions, check units, and verify on a held-out calibration point.",
    );
  await page.getByRole("button", { name: "Nộp và lưu diagnostic" }).click();
  await expect(
    page.getByRole("heading", { name: "Kết quả · 100%" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.locator(".topic-meta").getByText("Đã kiểm chứng L1"),
  ).toBeVisible();
  await expect(page.getByText("100% · A0", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Copy Learning Context", exact: true })
    .click();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  const handoff = JSON.parse(copied);
  expect(handoff.topic.id).toBe("M01");
  expect(handoff.verifiedEvidence.level).toBe(1);
  expect(copied).not.toContain('"answer"');
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Vectors", exact: true }),
  ).toBeVisible();
  await page.goto("/tutor");
  await page.getByRole("textbox", { name: "Phản hồi AI dạng JSON" }).fill(
    JSON.stringify({
      schema: "corelab-feedback/1",
      topicId: "M01",
      summary: "AI note",
      difficulties: ["Inverse versus reciprocal"],
      nextSteps: ["Try a new example"],
    }),
  );
  await page.getByRole("button", { name: "Lưu phản hồi" }).click();
  await expect(
    page.getByText("Đã lưu phản hồi AI như ghi chú chưa kiểm chứng."),
  ).toBeVisible();
  const before = await (await page.request.get("/api/state")).json();
  expect(before.mastery.M01.level).toBe(1);
  await page.goto("/settings");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Xuất backup JSON" }).click();
  const download = await downloadPromise;
  const filepath = await download.path();
  expect(filepath).toBeTruthy();
  const backup = JSON.parse(readFileSync(filepath!, "utf8"));
  expect(backup.progress.attempts).toHaveLength(1);
  await page.request.post("/api/action", {
    data: {
      type: "session",
      topicId: "M02",
      kind: "note",
      text: "Temporary record after backup",
      minutes: 1,
    },
  });
  await page.getByLabel("Chọn backup để khôi phục").setInputFiles({
    name: "backup.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(backup)),
  });
  await expect(page.getByText("Schema hợp lệ", { exact: true })).toBeVisible();
  const restore = page.getByRole("button", { name: "Khôi phục và thay thế" });
  await expect(restore).toBeDisabled();
  await page.getByRole("checkbox").check();
  await restore.click();
  await expect(page.getByText("Đã khôi phục tiến độ từ backup.")).toBeVisible();
  const restored = await (await page.request.get("/api/state")).json();
  expect(restored.progress).toEqual(backup.progress);
  await page.goto("/roadmap");
  await page.getByRole("textbox", { name: "Tìm chủ đề" }).fill("M02");
  await expect(page.locator(".topic-list-row")).toHaveCount(1);
  await page.getByRole("textbox", { name: "Tìm chủ đề" }).fill("");
  await page.getByRole("button", { name: "Đồ thị", exact: true }).click();
  await expect(page.locator(".react-flow__node").first()).toBeVisible();
  await page.locator(".react-flow__node").filter({ hasText: "M02" }).click();
  await expect(
    page
      .locator(".graph-detail")
      .getByRole("heading", { name: "M02 · Vectors" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Mở chi tiết chủ đề" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Vectors: displacement, dot products, and geometry",
    }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test("remaining pages, honest overview, keyboard/mobile layout, invalid import and local security", async ({
  page,
}) => {
  for (const [route, heading] of [
    ["/paths", "Một lộ trình, nhiều nhánh mở."],
    ["/practice", "Tự triển khai. Tự kiểm chứng."],
    ["/lessons", "Không chỉ đọc. Hiểu sâu."],
    ["/assessments", "Kiểm chứng điều bạn hiểu."],
    ["/sources", "Tài liệu tham khảo"],
  ]) {
    await page.goto(route);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
  }
  await page.goto("/lessons/E15");
  await expect(
    page.getByText("Overview · Chủ đề này chưa có bài học"),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Advanced Embodied Intelligence",
      exact: true,
    }),
  ).toBeVisible();
  await page.goto("/settings");
  await page.getByLabel("Chọn backup để khôi phục").setInputFiles({
    name: "invalid.json",
    mimeType: "application/json",
    buffer: Buffer.from('{"schema":"unknown"}'),
  });
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Khôi phục và thay thế" }),
  ).toHaveCount(0);
  const forbidden = await page.request.post("/api/action", {
    headers: { origin: "https://untrusted.example" },
    data: { type: "goal", goal: "Robotics", focusTopic: null, focusReason: "" },
  });
  expect(forbidden.status()).toBe(400);
  const contract = await (await page.request.get("/api/topics/M01")).json();
  expect(
    contract.assessment.questions.every(
      (q: Record<string, unknown>) => !("answer" in q),
    ),
  ).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/lessons/M02");
  await expect(
    page.getByRole("heading", {
      name: "Vectors: displacement, dot products, and geometry",
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Mở menu" }).click();
  await expect(
    page.getByRole("button", { name: "Đóng menu", exact: true }).last(),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Mở menu" })).toBeFocused();
  mkdirSync(".local/screenshots", { recursive: true });
  await page.screenshot({
    path: ".local/screenshots/mobile-lesson.png",
    fullPage: false,
  });
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Xây nền tảng. Đi xa hơn." }),
  ).toBeVisible();
  await page.screenshot({
    path: ".local/screenshots/dashboard.png",
    fullPage: true,
  });
  await page.goto("/not-a-route");
  await expect(
    page.getByText("Chủ đề này chưa có trong workspace."),
  ).toBeVisible();
});

test("local fixed verifier → A3 practice → A0 signed evidence → L2, and interactive geometry", async ({
  page,
}) => {
  const { writeFileSync } = await import("node:fs");
  const { execFileSync } = await import("node:child_process");
  mkdirSync(".local/e2e-labs", { recursive: true });
  const solution = ".local/e2e-labs/dot.py";
  writeFileSync(
    solution,
    'def dot(u,v):\n    if len(u)!=len(v): raise ValueError("shape")\n    return sum(a*b for a,b in zip(u,v))\n',
  );
  const contract = getAssessment("M02");
  const answers = Object.fromEntries(
    contract.questions
      .filter((q) => q.kind !== "short")
      .map((q) => [q.id, q.answer]),
  );
  const assessment = await page.request.post("/api/action", {
    data: { type: "attempt", topicId: "M02", answers, assistance: "A0" },
  });
  expect(assessment.ok()).toBe(true);
  for (const assistance of ["A3", "A0"]) {
    const out = `.local/e2e-labs/${assistance}-report.json`;
    execFileSync(process.execPath, [
      "scripts/verify-lab.mjs",
      "--topic",
      "M02",
      "--file",
      solution,
      "--assistance",
      assistance,
      "--out",
      out,
    ]);
    await page.goto("/practice?topic=M02");
    await page.getByLabel("Chọn báo cáo lab").setInputFiles(out);
    await page
      .getByRole("button", { name: "Nhập báo cáo", exact: true })
      .click();
    await expect(
      page.getByText(
        "Đã nhập báo cáo kiểm thử. Xem bằng chứng trong Assessments.",
      ),
    ).toBeVisible();
    const current = await (await page.request.get("/api/state")).json();
    expect(current.mastery.M02.level).toBe(assistance === "A0" ? 2 : 1);
  }
  await page.reload();
  await page
    .getByLabel("Chọn báo cáo lab")
    .setInputFiles(".local/e2e-labs/A0-report.json");
  await page.getByRole("button", { name: "Nhập báo cáo", exact: true }).click();
  await expect(
    page.getByText("This report has already been imported"),
  ).toBeVisible();
  await page.goto("/lessons/M02");
  const slider = page.getByRole("slider", { name: "Tọa độ x của vector" });
  await slider.fill("4");
  await expect(
    page.getByText("projᵥ u = (3.00, 3.00)", { exact: true }),
  ).toBeVisible();
  await page.goto("/lessons/R04");
  await page.getByRole("slider", { name: "Góc khớp 1" }).fill("90");
  await page.getByRole("slider", { name: "Góc khớp 2" }).fill("0");
  await expect(
    page.getByText("p = (0.00, 3.50) m", { exact: true }),
  ).toBeVisible();
});
