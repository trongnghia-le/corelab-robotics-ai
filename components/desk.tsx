"use client";
// Study desk: a second window beside the lesson for notes, exercise answers
// and code. It follows the topic open in the lesson window.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import {
  Check,
  Code2,
  Eye,
  FilePlus2,
  FolderOpen,
  ListChecks,
  NotebookPen,
  Pin,
  PinOff,
  Play,
  Square,
  Trash2,
  Download,
} from "lucide-react";
import { topics, topicMap } from "@/lib/curriculum";
import { useI18n } from "@/lib/i18n";
import { useCore, copyText } from "./provider";
import { LessonMarkdown } from "./markdown";
import { useTopic } from "./topic";
import { lastTopic, onTopic } from "@/lib/desk-channel";
import { deskExercises, labFiles } from "@/lib/desk-parse";
import { langFor } from "./code-editor";
import type { TopicPayload } from "@/lib/types";

const CodeEditor = dynamic(
  () => import("./code-editor").then((m) => m.CodeEditor),
  { ssr: false, loading: () => <div className="code-editor is-loading" /> },
);

const NOTES = "notes.md";
const ANSWERS = "exercises.json";
type DeskFile = { name: string; content: string };
type Answers = {
  answers: Record<string, string>;
  done: Record<string, boolean>;
};
type RunResult = {
  command: string;
  exitCode: number | null;
  signal: string | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
  ms: number;
};

async function deskPost(body: object) {
  const r = await fetch("/api/desk", {
    method: "POST",
    headers: { "content-type": "application/json", "x-corelab-desk": "1" },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error ?? "Desk request failed");
  return data;
}

/** Debounced autosave of one desk file. */
function useAutosave(topic: string) {
  const timers = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const [state, setState] = useState<"saved" | "saving" | "error">("saved");
  const save = useCallback(
    (file: string, content: string, delay = 700) => {
      setState("saving");
      clearTimeout(timers.current.get(file));
      return new Promise<void>((resolve) => {
        timers.current.set(
          file,
          setTimeout(() => {
            deskPost({ op: "write", topic, file, content })
              .then(() => setState("saved"))
              .catch(() => setState("error"))
              .finally(resolve);
          }, delay),
        );
      });
    },
    [topic],
  );
  useEffect(() => {
    const pending = timers.current;
    return () => pending.forEach((t) => clearTimeout(t));
  }, [topic]);
  return { save, state };
}

export function Desk() {
  const { title } = useCore();
  const { tx, lang, setLang } = useI18n();
  const [topic, setTopic] = useState("");
  const [follow, setFollow] = useState(true);
  const [tab, setTab] = useState<"notes" | "exercises" | "code">("notes");
  useEffect(() => {
    const fromUrl = new URLSearchParams(location.search).get("topic") ?? "";
    const first = [fromUrl, lastTopic()].find((t) => topicMap[t]) ?? "M01";
    setTopic(first);
  }, []);
  useEffect(
    () =>
      onTopic((t) => {
        if (follow && topicMap[t]) setTopic(t);
      }),
    [follow],
  );
  useEffect(() => {
    if (topic) document.title = `Desk · ${topic} · CoreLab`;
  }, [topic]);
  return (
    <div className="desk">
      <header className="desk-header">
        <select
          aria-label={tx("Topic", "Chủ đề")}
          value={topic}
          onChange={(e) => {
            setTopic(e.target.value);
            setFollow(false);
          }}
        >
          {topics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.id} · {title(t.id)}
            </option>
          ))}
        </select>
        <button
          type="button"
          className={`icon-button ${follow ? "is-on" : ""}`}
          aria-pressed={follow}
          title={tx(
            "Follow the lesson window",
            "Tự đi theo bài đang mở ở cửa sổ chính",
          )}
          onClick={() => setFollow((f) => !f)}
        >
          {follow ? <Pin size={16} /> : <PinOff size={16} />}
          <span>
            {follow ? tx("Following", "Đang theo") : tx("Pinned", "Đã ghim")}
          </span>
        </button>
        <div className="lang-switch" role="group" aria-label="Language">
          {(["en", "vi"] as const).map((l) => (
            <button
              key={l}
              type="button"
              aria-pressed={lang === l}
              className={lang === l ? "selected" : ""}
              onClick={() => setLang(l)}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </header>
      <nav className="desk-tabs" role="tablist">
        {(
          [
            ["notes", NotebookPen, tx("Notes", "Ghi chú")],
            ["exercises", ListChecks, tx("Exercises", "Bài tập")],
            ["code", Code2, tx("Code", "Code")],
          ] as const
        ).map(([key, Icon, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={tab === key}
            className={tab === key ? "selected" : ""}
            onClick={() => setTab(key)}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </nav>
      {topic && <DeskTopic key={topic} topic={topic} tab={tab} />}
    </div>
  );
}

function DeskTopic({
  topic,
  tab,
}: {
  topic: string;
  tab: "notes" | "exercises" | "code";
}) {
  const { tx, lang } = useI18n();
  const { data } = useTopic(topic);
  const [english, setEnglish] = useState<TopicPayload | null>(null);
  const [files, setFiles] = useState<DeskFile[] | null>(null);
  const [dir, setDir] = useState("");
  const [error, setError] = useState("");
  const { save, state } = useAutosave(topic);
  useEffect(() => {
    fetch(`/api/desk?topic=${topic}`)
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw new Error(d.error);
        setFiles(d.files);
        setDir(d.dir);
      })
      .catch((e) => setError(String(e.message ?? e)));
  }, [topic]);
  useEffect(() => {
    // Lab code is identical in both languages; read it from the English body.
    if (lang === "en") return setEnglish(null);
    fetch(`/api/topics/${topic}`)
      .then((r) => r.json())
      .then(setEnglish)
      .catch(() => setEnglish(null));
  }, [topic, lang]);
  if (error) return <p className="desk-error">{error}</p>;
  if (!files || !data) return <p className="desk-loading">…</p>;
  const lesson = data.lesson;
  const codeBody = (english ?? data).lesson?.body ?? "";
  const read = (name: string) =>
    files.find((f) => f.name === name)?.content ?? "";
  const update = (name: string, content: string, delay?: number) => {
    setFiles((fs) => {
      const rest = (fs ?? []).filter((f) => f.name !== name);
      return [...rest, { name, content }].sort((a, b) =>
        a.name.localeCompare(b.name),
      );
    });
    return save(name, content, delay);
  };
  return (
    <section className="desk-body" aria-live="polite">
      <div className="desk-meta">
        <strong>
          {topic} · {lesson?.meta.title ?? topicMap[topic].title}
        </strong>
        <span className={`desk-save is-${state}`}>
          {state === "saving"
            ? tx("Saving…", "Đang lưu…")
            : state === "error"
              ? tx("Not saved", "Chưa lưu được")
              : tx("Saved", "Đã lưu")}
        </span>
      </div>
      {tab === "notes" && (
        <NotesTab value={read(NOTES)} onChange={(v) => update(NOTES, v)} />
      )}
      {tab === "exercises" &&
        (lesson ? (
          <ExercisesTab
            body={lesson.body}
            englishHeadings={lesson.englishHeadings}
            raw={read(ANSWERS)}
            onChange={(v) => update(ANSWERS, v)}
          />
        ) : (
          <p className="muted">
            {tx("This topic has no exercises.", "Chủ đề này chưa có bài tập.")}
          </p>
        ))}
      {tab === "code" && (
        <CodeTab
          topic={topic}
          files={files.filter((f) => f.name !== NOTES && f.name !== ANSWERS)}
          body={codeBody}
          update={update}
          remove={async (name) => {
            await deskPost({ op: "delete", topic, file: name });
            setFiles((fs) => (fs ?? []).filter((f) => f.name !== name));
          }}
        />
      )}
      <footer className="desk-footer">
        <FolderOpen size={14} />
        <code>{dir}</code>
        <button
          type="button"
          className="link-button"
          onClick={() => copyText(dir)}
        >
          {tx("Copy path", "Sao chép đường dẫn")}
        </button>
      </footer>
    </section>
  );
}

function NotesTab({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const { tx } = useI18n();
  const [preview, setPreview] = useState(false);
  return (
    <div className="desk-notes">
      <div className="desk-toolbar">
        <button
          type="button"
          className="button secondary"
          aria-pressed={preview}
          onClick={() => setPreview((p) => !p)}
        >
          <Eye size={15} />{" "}
          {preview ? tx("Edit", "Sửa") : tx("Preview", "Xem trước")}
        </button>
        <span className="muted small">
          {tx(
            "Markdown and $math$ are supported.",
            "Hỗ trợ Markdown và công thức $math$.",
          )}
        </span>
      </div>
      {preview ? (
        <div className="desk-preview">
          <LessonMarkdown body={value || "_…_"} />
        </div>
      ) : (
        <textarea
          className="desk-textarea"
          aria-label={tx("Notes", "Ghi chú")}
          value={value}
          placeholder={tx(
            "Write what you understood, questions, formulas…",
            "Ghi lại điều bạn hiểu, câu hỏi, công thức…",
          )}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}

function parseAnswers(raw: string): Answers {
  try {
    const a = JSON.parse(raw);
    return { answers: a.answers ?? {}, done: a.done ?? {} };
  } catch {
    return { answers: {}, done: {} };
  }
}

function ExercisesTab({
  body,
  englishHeadings,
  raw,
  onChange,
}: {
  body: string;
  englishHeadings?: string[];
  raw: string;
  onChange: (v: string) => void;
}) {
  const { tx } = useI18n();
  const items = useMemo(
    () => deskExercises(body, englishHeadings),
    [body, englishHeadings],
  );
  const state = parseAnswers(raw);
  const set = (next: Answers) => onChange(JSON.stringify(next, null, 2));
  const done = items.filter((e) => state.done[e.n]).length;
  if (!items.length)
    return (
      <p className="muted">
        {tx(
          "This lesson has no numbered exercises.",
          "Bài này không có bài tập đánh số.",
        )}
      </p>
    );
  return (
    <div className="desk-exercises">
      <p className="muted small">
        {tx(
          `${done}/${items.length} done. Try first, then open the answer.`,
          `Đã xong ${done}/${items.length}. Tự làm trước, rồi mới mở lời giải.`,
        )}
      </p>
      <ol>
        {items.map((e) => (
          <li key={e.n} className={state.done[e.n] ? "is-done" : ""}>
            <div className="desk-exercise-head">
              <span className="desk-exercise-n">{e.n}</span>
              <label>
                <input
                  type="checkbox"
                  checked={!!state.done[e.n]}
                  onChange={(ev) =>
                    set({
                      ...state,
                      done: { ...state.done, [e.n]: ev.target.checked },
                    })
                  }
                />
                {tx("Done", "Xong")}
              </label>
            </div>
            <LessonMarkdown body={e.text} />
            <textarea
              className="desk-answer"
              aria-label={tx(`Answer ${e.n}`, `Lời giải ${e.n}`)}
              rows={4}
              value={state.answers[e.n] ?? ""}
              placeholder={tx("Your working…", "Bài làm của bạn…")}
              onChange={(ev) =>
                set({
                  ...state,
                  answers: { ...state.answers, [e.n]: ev.target.value },
                })
              }
            />
            {e.answer && (
              <details className="desk-solution">
                <summary>{tx("Show the answer", "Xem lời giải")}</summary>
                <LessonMarkdown body={e.answer} />
              </details>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

function CodeTab({
  topic,
  files,
  body,
  update,
  remove,
}: {
  topic: string;
  files: DeskFile[];
  body: string;
  update: (name: string, content: string, delay?: number) => Promise<void>;
  remove: (name: string) => Promise<void>;
}) {
  const { tx } = useI18n();
  const [active, setActive] = useState(files[0]?.name ?? "");
  const [result, setResult] = useState<RunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");
  const current = files.find((f) => f.name === active);
  const lab = useMemo(() => labFiles(body), [body]);
  useEffect(() => {
    if (!current && files[0]) setActive(files[0].name);
  }, [current, files]);
  async function loadLab() {
    const existing = lab.filter((b) => files.some((f) => f.name === b.name));
    if (
      existing.length &&
      !confirm(
        tx(
          `Replace ${existing.map((b) => b.name).join(", ")} with the lesson's code?`,
          `Ghi đè ${existing.map((b) => b.name).join(", ")} bằng code của bài học?`,
        ),
      )
    )
      return;
    for (const b of lab) await update(b.name, b.content, 0);
    if (lab[0]) setActive(lab[0].name);
    setMessage(
      tx(
        "Loaded the starter with the tests below it. Fill in the TODOs, then Run.",
        "Đã nạp starter, phần tests nằm ngay bên dưới. Điền các chỗ TODO rồi bấm Chạy.",
      ),
    );
  }
  function newFile() {
    const name = prompt(
      tx(
        "File name (.py, .cpp, .c, .md, .txt)",
        "Tên file (.py, .cpp, .c, .md, .txt)",
      ),
      files.length ? "scratch.py" : "main.py",
    );
    if (!name) return;
    if (
      !/^[A-Za-z0-9][A-Za-z0-9_-]{0,47}\.(py|cpp|cc|c|h|hpp|md|txt)$/.test(name)
    )
      return setMessage(tx("Invalid file name.", "Tên file không hợp lệ."));
    if (!files.some((f) => f.name === name)) void update(name, "", 0);
    setActive(name);
  }
  async function run() {
    if (!current) return;
    setRunning(true);
    setResult(null);
    try {
      await update(current.name, current.content, 0);
      setResult(await deskPost({ op: "run", topic, file: current.name }));
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }
  const runnable = current && /\.(py|cpp|cc|c)$/.test(current.name);
  return (
    <div className="desk-code">
      <div className="desk-toolbar">
        <div className="desk-files" role="tablist">
          {files.map((f) => (
            <button
              key={f.name}
              type="button"
              role="tab"
              aria-selected={f.name === active}
              className={f.name === active ? "selected" : ""}
              onClick={() => setActive(f.name)}
            >
              {f.name}
            </button>
          ))}
          <button type="button" className="icon-button" onClick={newFile}>
            <FilePlus2 size={15} /> {tx("New", "Mới")}
          </button>
        </div>
        {lab.length > 0 && (
          <button type="button" className="button secondary" onClick={loadLab}>
            <Download size={15} /> {tx("Load lab code", "Nạp code của lab")}
          </button>
        )}
      </div>
      {message && <p className="muted small">{message}</p>}
      {current ? (
        <>
          <CodeEditor
            key={`${topic}/${current.name}`}
            value={current.content}
            lang={langFor(current.name)}
            label={current.name}
            onChange={(v) => void update(current.name, v)}
            onRun={runnable ? run : undefined}
          />
          <div className="desk-toolbar">
            {runnable && (
              <button
                type="button"
                className="button"
                disabled={running}
                onClick={run}
              >
                {running ? <Square size={15} /> : <Play size={15} />}
                {running ? tx("Running…", "Đang chạy…") : tx("Run", "Chạy")}
                <kbd>Ctrl+Enter</kbd>
              </button>
            )}
            <button
              type="button"
              className="icon-button"
              onClick={async () => {
                if (
                  confirm(tx(`Delete ${current.name}?`, `Xoá ${current.name}?`))
                )
                  await remove(current.name);
              }}
            >
              <Trash2 size={15} /> {tx("Delete", "Xoá")}
            </button>
          </div>
          {result && (
            <div className="desk-output" role="status">
              <div className="desk-output-head">
                {result.timedOut ? (
                  <span className="bad">
                    {tx("Timed out", "Quá thời gian")}
                  </span>
                ) : result.exitCode === 0 ? (
                  <span className="good">
                    <Check size={14} /> exit 0
                  </span>
                ) : result.signal ? (
                  <span className="bad">{result.signal}</span>
                ) : (
                  <span className="bad">exit {String(result.exitCode)}</span>
                )}
                <span>{(result.ms / 1000).toFixed(2)} s</span>
                <code>{result.command}</code>
              </div>
              {result.stdout && <pre>{result.stdout}</pre>}
              {result.stderr && <pre className="stderr">{result.stderr}</pre>}
            </div>
          )}
        </>
      ) : (
        <p className="muted">
          {tx(
            "No files yet. Load the lab code or create a new file.",
            "Chưa có file. Nạp code của lab hoặc tạo file mới.",
          )}
        </p>
      )}
    </div>
  );
}
