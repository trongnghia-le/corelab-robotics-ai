import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { getLesson, getLocalizedLesson } from "../lib/content";
import { deskExercises, labCode, labFiles } from "../lib/desk-parse";
import { checkDeskRequest } from "../lib/http";

describe("desk lesson parsing", () => {
  it("pairs every numbered exercise with its answer", () => {
    for (const id of ["M02", "HW05", "CAP02"]) {
      const items = deskExercises(getLesson(id)!.body);
      expect(items.length, id).toBeGreaterThanOrEqual(8);
      expect(
        items.every((e) => e.answer),
        id,
      ).toBe(true);
      expect(items.map((e) => e.n)).toEqual(items.map((_, i) => i + 1));
    }
  });
  it("finds exercises in a translated body through the English headings", () => {
    const vi = getLocalizedLesson("M02", "vi")!;
    const en = deskExercises(getLesson("M02")!.body);
    const items = deskExercises(vi.body, vi.englishHeadings);
    expect(items.length).toBe(en.length);
    expect(items[0].text).not.toBe(en[0].text);
  });
  it("extracts the lab starter and tests", () => {
    const body = getLesson("M02")!.body;
    expect(labCode(body, "Starter code")[0].lang).toBe("python");
    expect(labCode(body, "Tests").length).toBeGreaterThan(0);
    const [lab] = labFiles(body);
    expect(lab.name).toBe("lab.py");
    expect(lab.content.indexOf("# --- Starter code")).toBeLessThan(
      lab.content.indexOf("# --- Tests"),
    );
    expect(labFiles(getLesson("CPP01")!.body).map((f) => f.name)).toContain(
      "lab.cpp",
    );
  });
});

describe("desk storage and runner", () => {
  let dir = "";
  let desk: typeof import("../lib/desk");
  beforeAll(async () => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "corelab-desk-test-"));
    process.env.CORELAB_DESK_DIR = dir;
    desk = await import("../lib/desk");
  });
  afterAll(() => {
    delete process.env.CORELAB_DESK_DIR;
    fs.rmSync(dir, { recursive: true, force: true });
  });
  it("stores files per topic and rejects unsafe names", () => {
    desk.writeDeskFile("M02", "notes.md", "# hi");
    expect(fs.readFileSync(path.join(dir, "M02", "notes.md"), "utf8")).toBe(
      "# hi",
    );
    expect(desk.readDesk("M02").files.map((f) => f.name)).toEqual(["notes.md"]);
    for (const bad of ["../x.py", "a/b.py", ".env", "x.sh", "x.py.exe"])
      expect(() => desk.writeDeskFile("M02", bad, "")).toThrow(
        "Invalid file name",
      );
    expect(() => desk.writeDeskFile("ZZ1", "a.py", "")).toThrow(
      "Unknown topic",
    );
    expect(() => desk.deleteDeskFile("M02", "notes.md")).toThrow();
  });
  it("runs Python in the topic folder", async () => {
    desk.writeDeskFile("M02", "helper.py", "def f():\n    return 41 + 1\n");
    desk.writeDeskFile(
      "M02",
      "main.py",
      "from helper import f\nimport sys\nprint(f())\nprint('warn', file=sys.stderr)\n",
    );
    const r = await desk.runDeskFile("M02", "main.py");
    expect(r.exitCode).toBe(0);
    expect(r.stdout.trim()).toBe("42");
    expect(r.stderr).toContain("warn");
    expect(fs.existsSync(path.join(dir, "M02", "__pycache__"))).toBe(false);
  });
  it("stops code that runs past the time limit", async () => {
    desk.writeDeskFile("M02", "loop.py", "while True:\n    pass\n");
    const r = await desk.runDeskFile("M02", "loop.py", 1000);
    expect(r.timedOut).toBe(true);
    expect(r.ms).toBeLessThan(5000);
  });
  it.skipIf(spawnSync("c++", ["--version"]).status !== 0)(
    "compiles and runs C++",
    async () => {
      desk.writeDeskFile(
        "CPP01",
        "main.cpp",
        "#include <iostream>\nint main(){ std::cout << 6*7 << '\\n'; }\n",
      );
      const r = await desk.runDeskFile("CPP01", "main.cpp");
      expect(r.exitCode).toBe(0);
      expect(r.stdout.trim()).toBe("42");
      desk.writeDeskFile("CPP01", "bad.cpp", "int main( {");
      desk.writeDeskFile(
        "CPP01",
        "abort.cpp",
        '#include <stdexcept>\nint main(){ throw std::logic_error("todo"); }\n',
      );
      const abort = await desk.runDeskFile("CPP01", "abort.cpp");
      expect(abort.signal).toBe("SIGABRT");
      const bad = await desk.runDeskFile("CPP01", "bad.cpp");
      expect(bad.exitCode).not.toBe(0);
      expect(bad.stderr).toMatch(/error/);
    },
  );
});

describe("desk request guard", () => {
  const post = (headers: Record<string, string>) =>
    new Request("http://127.0.0.1:3210/api/desk", {
      method: "POST",
      headers: { host: "127.0.0.1:3210", ...headers },
    });
  const same = { origin: "http://127.0.0.1:3210" };
  it("accepts the desk page itself", () =>
    expect(() =>
      checkDeskRequest(
        post({
          ...same,
          "x-corelab-desk": "1",
          "sec-fetch-site": "same-origin",
        }),
      ),
    ).not.toThrow());
  it("rejects requests without the desk header or origin", () => {
    expect(() => checkDeskRequest(post(same))).toThrow("desk header");
    expect(() => checkDeskRequest(post({ "x-corelab-desk": "1" }))).toThrow(
      "Origin",
    );
  });
  it("rejects cross-site and rebinding attempts", () => {
    expect(() =>
      checkDeskRequest(
        post({ origin: "https://evil.example", "x-corelab-desk": "1" }),
      ),
    ).toThrow("Cross-origin");
    expect(() =>
      checkDeskRequest(
        post({
          ...same,
          "x-corelab-desk": "1",
          "sec-fetch-site": "cross-site",
        }),
      ),
    ).toThrow("Cross-site");
    expect(() =>
      checkDeskRequest(
        new Request("http://evil.example/api/desk", {
          method: "POST",
          headers: {
            host: "evil.example",
            origin: "http://evil.example",
            "x-corelab-desk": "1",
          },
        }),
      ),
    ).toThrow("localhost");
  });
});
