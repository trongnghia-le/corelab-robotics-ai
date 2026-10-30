"use client";
import { useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  Download,
  Upload,
  Copy,
  ShieldCheck,
  FileJson,
  Check,
  Route,
  ExternalLink,
} from "lucide-react";
import { topics, topicMap, domains } from "@/lib/curriculum";
import { contextFor } from "@/lib/engine";
import { practices } from "@/lib/practice";
import { sources } from "@/lib/resources";
import { useCore, Loading, copyText } from "./provider";
import { useTopic, Notebook } from "./topic";
import { PageHeading, Status, TopicChips, dateText } from "./ui";
import { PracticeTabs, WeaknessPractice } from "./weakness-practice";
export function Practice() {
  const { state, act, busy, notify } = useCore();
  const params = useSearchParams();
  const [topic, setTopic] = useState(params.get("topic") ?? ""),
    [report, setReport] = useState("");
  if (!state) return <Loading />;
  if (params.get("tab") === "weaknesses") return <WeaknessPractice />;
  const shown = practices.filter((p) => !topic || p.topicId === topic);
  const exact = topic && topicMap[topic];
  async function importReport(e: FormEvent) {
    e.preventDefault();
    try {
      await act({ type: "lab", report: JSON.parse(report) });
      setReport("");
      notify("Test report imported. View the evidence in Assessments.");
    } catch (e) {
      if (e instanceof SyntaxError)
        notify("The report must contain valid JSON.");
    }
  }
  return (
    <div className="page">
      <PageHeading
        eyebrow="IMPLEMENT → VERIFY → TRANSFER"
        title="Implement independently. Verify your work."
        description="Write code in VS Code and run tests in your own terminal. CoreLab does not execute code submitted through the browser."
      />
      <PracticeTabs />
      <div className="info-banner">
        <ShieldCheck size={19} />
        <span>
          Fixed tests currently support M02 and PY01. Other assignments include
          instructions and a notebook; self-reported results do not increase
          verified competence.
        </span>
      </div>
      <div className="filters">
        <select
          aria-label="Choose practice topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        >
          <option value="">All assignments</option>
          {topics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.id} · {t.title}
            </option>
          ))}
        </select>
        {topic && <button onClick={() => setTopic("")}>View all</button>}
      </div>
      <div className="practice-list">
        {shown.map((p, i) => (
          <section className="panel practice-card" key={p.id}>
            <div className="practice-number">
              {String(i + 1).padStart(2, "0")}
            </div>
            <div>
              <div className="between">
                <div className="chips">
                  <Link className="topic-code" href={`/lessons/${p.topicId}`}>
                    {p.topicId}
                  </Link>
                  <span className="muted small">{p.kind}</span>
                </div>
                <span className={`status ${p.verified ? "verified" : ""}`}>
                  {p.verified
                    ? "Fixed verifier available"
                    : "Practice · self-reported"}
                </span>
              </div>
              <h2>{p.title}</h2>
              <p>{p.task}</p>
              <TopicChips ids={topicMap[p.topicId].prerequisites} />
              <div className="command-block">
                <code>{p.command}</code>
              </div>
              <div className="topic-actions">
                <a className="button" download href={p.starter}>
                  <Download size={15} />
                  Download starter
                </a>
                <Link className="button" href={`/lessons/${p.topicId}`}>
                  Theory
                  <ArrowRight size={15} />
                </Link>
                <Link className="button" href={`/assessments/${p.topicId}`}>
                  View evidence
                  <ArrowRight size={15} />
                </Link>
              </div>
            </div>
          </section>
        ))}
      </div>
      {shown.length === 0 && exact && (
        <div className="panel">
          <h2>Practice the objectives for {exact.title}</h2>
          <p>
            This topic has no fixed verifier yet. Follow the independent
            practice section or overview guidance, then record your assumptions,
            reasoning, and results in the notebook.
          </p>
          <Link className="button" href={`/lessons/${topic}`}>
            Open topic
            <ArrowRight size={16} />
          </Link>
        </div>
      )}
      <section className="panel import-report">
        <h2>Import a local test report</h2>
        <p className="muted small">
          The runner records the source hash, timestamp, v1 contract,
          assistance, and local signature. A3 records practice only; a fresh A0
          run can establish I evidence. This is personal study evidence, not
          proctored certification.
        </p>
        <label className="file-label">
          <Upload size={16} />
          Choose report JSON
          <input
            aria-label="Choose lab report"
            type="file"
            accept="application/json,.json"
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (f) {
                if (f.size > 10000) {
                  notify("The report is too large.");
                  return;
                }
                setReport(await f.text());
              }
            }}
          />
        </label>
        <form onSubmit={importReport}>
          <textarea
            aria-label="Test report JSON"
            placeholder="Paste the contents of .local/M02-report.json…"
            value={report}
            onChange={(e) => setReport(e.target.value)}
            rows={6}
            required
            maxLength={10000}
          />
          <button
            className="button primary"
            type="submit"
            disabled={busy || !report}
          >
            Import report
            <Upload size={16} />
          </button>
        </form>
        <p className="small muted">
          Only the CLI in your terminal executes Python files. This button only
          validates and saves a report.
        </p>
      </section>
      {topic && <Notebook key={topic} id={topic} />}
    </div>
  );
}
const milestones = [
  {
    name: "01 · Mathematics & programming foundations",
    description: "Notation → vectors → matrices, alongside Python and C++.",
    ids: ["M01", "PY01", "CPP01", "M02", "M03", "PY07", "CPP02", "T04"],
  },
  {
    name: "02 · Reasoning and computation",
    description: "Derivatives, probability, linear algebra, and NumPy.",
    ids: ["M04", "M05", "M06", "M07", "M08", "PY04", "M10"],
  },
  {
    name: "03 · Machine Learning from first principles",
    description:
      "Problem formulation, baselines, gradients, neural networks, and backpropagation.",
    ids: ["ML01", "ML02", "ML04", "ML05"],
  },
  {
    name: "04 · Robot geometry & control",
    description:
      "Mechanics, mechanisms, frames, kinematics, dynamics, and feedback.",
    ids: ["R01", "R02", "M12", "R03", "R04", "R06", "R07", "C01"],
  },
  {
    name: "05 · Vision & sequential decisions",
    description:
      "Digital images and MDPs; open later branches through their prerequisites.",
    ids: ["V01", "RL01", "RL02", "V02", "V03", "RL03"],
  },
  {
    name: "06 · Robot Learning & Cognitive Robotics",
    description:
      "The long-term map: interaction, representations, planning, and research.",
    ids: ["RL17", "E01", "E02", "E07", "E08", "E10", "E12", "RS01", "RS02"],
  },
];
export function Paths() {
  const { state, act, busy, notify } = useCore();
  const [goal, setGoal] = useState(""),
    [focus, setFocus] = useState<string | undefined>(undefined),
    [reason, setReason] = useState<string | undefined>(undefined);
  if (!state) return <Loading />;
  const selectedGoal = goal || state.progress.goal;
  const selectedFocus = focus ?? state.progress.focusTopic ?? "";
  const selectedReason = reason ?? state.progress.focusReason;
  const debt = state.progress.sessions
    .filter((s) => s.kind === "difficulty")
    .slice()
    .reverse();
  return (
    <div className="page">
      <PageHeading
        eyebrow="ZERO VERIFIED KNOWLEDGE → INDEPENDENT RESEARCH"
        title="One path, many open branches."
        description="Follow prerequisites and evidence. You do not need to finish an entire domain to start a suitable branch."
      />
      <section className="panel goal-panel">
        <h2>Current learning focus</h2>
        <p className="muted small">
          Begin with foundations by default. Pin a project topic for parallel,
          just-in-time learning; recommendations prioritize its missing
          prerequisites.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void act({
              type: "goal",
              goal: selectedGoal,
              focusTopic: selectedFocus || null,
              focusReason: selectedReason,
            })
              .then(() => notify("Goal and recommendations updated."))
              .catch(() => {});
          }}
        >
          <div className="form-row">
            <label>
              Direction
              <select
                aria-label="Learning direction"
                value={selectedGoal}
                onChange={(e) => setGoal(e.target.value)}
              >
                <option>Foundations</option>
                {domains.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </label>
            <label>
              Project topic / focus
              <select
                aria-label="Project topic"
                value={selectedFocus}
                onChange={(e) => setFocus(e.target.value)}
              >
                <option value="">No pinned topic</option>
                {topics.map((t) => (
                  <option value={t.id} key={t.id}>
                    {t.id} · {t.title}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Why choose this goal?
            <input
              value={selectedReason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={1000}
              placeholder="For example: understand coordinate frames for a camera project…"
            />
          </label>
          <button disabled={busy} className="button" type="submit">
            Save goal
            <Route size={16} />
          </button>
        </form>
        {state.progress.focusTopic && (
          <p className="small">
            Pinned:{" "}
            <Link href={`/lessons/${state.progress.focusTopic}`}>
              {state.progress.focusTopic} ·{" "}
              {topicMap[state.progress.focusTopic].title}
            </Link>{" "}
            · {state.progress.focusReason}
          </p>
        )}
      </section>
      <div className="path-timeline">
        {milestones.map((stage) => (
          <section className="path-stage" key={stage.name}>
            <span className="path-dot" />
            <div>
              <h2>{stage.name}</h2>
              <p className="muted">{stage.description}</p>
              <div className="panel path-topics">
                {stage.ids.map((id) => {
                  const t = topicMap[id],
                    missing = t.prerequisites.filter(
                      (p) => state.mastery[p].level < 1,
                    );
                  return (
                    <Link key={id} href={`/lessons/${id}`}>
                      <span className="topic-id">{id}</span>
                      <div>
                        <strong>{t.title}</strong>
                        <small>
                          {missing.length
                            ? `Prerequisites needing evidence: ${missing.join(", ")}`
                            : "Ready to start a diagnostic"}
                          {!state.lessonIds.includes(id) ? " · Overview" : ""}
                        </small>
                      </div>
                      <Status mastery={state.mastery[id]} />
                    </Link>
                  );
                })}
              </div>
            </div>
          </section>
        ))}
      </div>
      <section className="panel">
        <h2>Knowledge debt</h2>
        <p className="muted small">
          Difficulties you recorded, separate from gaps detected by assessments.
        </p>
        {debt.length ? (
          debt.slice(0, 12).map((d) => (
            <div className="debt-row" key={d.id}>
              <Link href={`/lessons/${d.topicId}`}>{d.topicId}</Link>
              <p>{d.text}</p>
              <small>{dateText(d.at)}</small>
            </div>
          ))
        ) : (
          <p className="muted">
            No difficulties recorded yet. Use the notebook for each topic to
            capture open questions.
          </p>
        )}
      </section>
    </div>
  );
}
export function Tutor() {
  const { state, act, busy, notify } = useCore();
  const params = useSearchParams();
  const [topic, setTopic] = useState(
      params.get("topic") && topicMap[params.get("topic")!]
        ? params.get("topic")!
        : "M01",
    ),
    [kind, setKind] = useState("learning"),
    [question, setQuestion] = useState(""),
    [feedback, setFeedback] = useState("");
  const { data } = useTopic(topic);
  if (!state) return <Loading />;
  const objectives =
    data?.lesson?.meta.objectives ?? data?.overview.concepts ?? [];
  const context = contextFor(topic, state.progress, objectives, kind, question);
  const ex = practices
    .filter((p) => p.topicId === topic)
    .map((p) => p.task)
    .join("\n");
  const fullContext =
    context +
    (kind === "exercise"
      ? `\nExercise:\n${ex || data?.lesson?.meta.labs.join("\n") || data?.overview.task || "Choose an exercise that matches the objectives."}`
      : "");
  async function copy() {
    try {
      await copyText(fullContext);
      notify("Context copied. Paste it into your ChatGPT Project yourself.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Unable to copy.");
    }
  }
  return (
    <div className="page">
      <PageHeading
        eyebrow="CHATGPT PROJECT · MANUAL HANDOFF"
        title="One tutor. One source of truth."
        description="Bring the right context into your conversation. CoreLab keeps your progress and evidence on your machine."
      />
      <div className="two-columns tutor-columns">
        <section className="panel">
          <h2>Prepare context</h2>
          <label>
            Topic
            <select
              aria-label="Handoff topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            >
              {topics.map((t) => (
                <option value={t.id} key={t.id}>
                  {t.id} · {t.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Context type
            <select
              aria-label="Handoff type"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="learning">Copy Learning Context</option>
              <option value="exercise">Copy Exercise for AI Tutor</option>
              <option value="debugging">Copy Debugging Context</option>
              <option value="summary">Copy Session Summary</option>
            </select>
          </label>
          <label>
            Question / failing code / observed result
            <textarea
              aria-label="Question for AI Tutor"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={5}
              maxLength={20000}
              placeholder="I tried…, expected…, but observed…"
            />
          </label>
          <button
            disabled={!data}
            onClick={() => void copy()}
            className="button primary"
          >
            <Copy size={16} />
            Copy context
          </button>
          <p className="small muted">
            No data is sent through an API. Preview the content and choose what
            to copy.
          </p>
        </section>
        <section className="panel">
          <h2>Content preview</h2>
          <textarea
            className="context-output"
            aria-label="Handoff context"
            value={fullContext}
            readOnly
            rows={20}
          />
        </section>
      </div>
      <section className="panel">
        <h2>Paste study feedback</h2>
        <p className="muted">
          ChatGPT feedback is stored as AI-reported notes. It does not change
          verified mastery.
        </p>
        <details>
          <summary>Required JSON format</summary>
          <pre>
            {JSON.stringify(
              {
                schema: "corelab-feedback/1",
                topicId: topic,
                summary: "Session summary",
                difficulties: ["Remaining difficulty"],
                nextSteps: ["Next step"],
              },
              null,
              2,
            )}
          </pre>
        </details>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            try {
              const parsed = JSON.parse(feedback);
              void act({ type: "feedback", feedback: parsed })
                .then(() => {
                  setFeedback("");
                  notify("AI feedback saved as unverified notes.");
                })
                .catch(() => {});
            } catch {
              notify("Invalid JSON. Check the example format.");
            }
          }}
        >
          <textarea
            aria-label="AI feedback JSON"
            rows={6}
            required
            maxLength={50000}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
          <button className="button" disabled={busy || !feedback} type="submit">
            Save feedback
            <Upload size={15} />
          </button>
        </form>
      </section>
    </div>
  );
}
export function Settings() {
  const { state, act, busy, notify } = useCore();
  const [backup, setBackup] = useState<unknown>(null),
    [preview, setPreview] = useState<{
      attempts: number;
      sessions: number;
      labs: number;
    } | null>(null),
    [confirm, setConfirm] = useState(false),
    [error, setError] = useState(""),
    [validating, setValidating] = useState(false);
  if (!state) return <Loading />;
  async function choose(file: File | undefined) {
    setPreview(null);
    setBackup(null);
    setConfirm(false);
    setError("");
    if (!file) return;
    if (file.size > 8_000_000) {
      setError("Backup limit: 8 MB.");
      return;
    }
    setValidating(true);
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const res = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: text,
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error);
      setBackup(parsed);
      setPreview(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invalid backup.");
    } finally {
      setValidating(false);
    }
  }
  return (
    <div className="page settings-page">
      <PageHeading
        eyebrow="YOUR DATA, ON YOUR MACHINE"
        title="Data & settings"
        description="Back up progress, preserve evidence history, and control your personal data."
      />
      <section className="panel">
        <div className="panel-heading">
          <h2>Local workspace</h2>
          <ShieldCheck size={19} />
        </div>
        <div className="settings-stats">
          <div>
            <strong>{state.progress.attempts.length}</strong>
            <span>Assessment attempts</span>
          </div>
          <div>
            <strong>{state.progress.sessions.length}</strong>
            <span>Sessions / notes</span>
          </div>
          <div>
            <strong>{state.progress.labs.length}</strong>
            <span>Practice reports</span>
          </div>
        </div>
        <p className="muted small">
          SQLite at <code>.local/corelab.sqlite</code>, created automatically
          when you open the app. Personal data and local keys are excluded from
          Git. The app uses no analytics or AI services.
        </p>
      </section>
      <div className="two-columns">
        <section className="panel">
          <div className="tool-icon">
            <Download size={23} />
          </div>
          <h2>Back up progress</h2>
          <p>
            Export attempts, rubric versions, learning sessions, notes,
            knowledge debt, review schedules, and lab evidence as
            schema-versioned JSON.
          </p>
          <a
            className="button primary"
            href="/api/export"
            download="corelab-backup.json"
          >
            Export backup JSON
            <Download size={16} />
          </a>
          <p className="small muted">
            Backups contain personal learning data. Store them outside the
            repository; do not upload them to GitHub.
          </p>
        </section>
        <section className="panel">
          <div className="tool-icon">
            <Upload size={23} />
          </div>
          <h2>Restore from backup</h2>
          <p>
            Validate the schema and evidence before replacement. A pre-restore
            snapshot is retained in SQLite to support recovery.
          </p>
          <label className="file-label">
            <FileJson size={17} />
            Choose backup JSON
            <input
              aria-label="Choose backup to restore"
              type="file"
              accept=".json,application/json"
              onChange={(e) => void choose(e.target.files?.[0])}
            />
          </label>
          {validating && <p role="status">Validating…</p>}
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          {preview && (
            <div className="restore-preview">
              <p className="verified-text">
                <Check size={15} />
                Valid schema
              </p>
              <p>
                {preview.attempts} attempts · {preview.sessions} sessions ·{" "}
                {preview.labs} labs
              </p>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={confirm}
                  onChange={(e) => setConfirm(e.target.checked)}
                />
                I confirm replacing all current progress with the selected
                backup.
              </label>
              <button
                className="button danger"
                disabled={!confirm || busy}
                onClick={() =>
                  void act({ type: "restore", backup, confirm: true })
                    .then(() => {
                      setBackup(null);
                      setPreview(null);
                      setConfirm(false);
                      notify("Progress restored from backup.");
                    })
                    .catch(() => {})
                }
              >
                Restore and replace
              </button>
            </div>
          )}
        </section>
      </div>
      <section className="panel">
        <h2>Mastery rules</h2>
        <div className="level-table">
          {[
            ["L0", "No verified evidence."],
            ["L1", "An independent diagnostic meets the conceptual criteria."],
            [
              "L2",
              "Conceptual, numerical, and independent implementation evidence through fixed tests.",
            ],
            [
              "L3",
              "Apply skills to unfamiliar problems and demonstrate retention; independent review required.",
            ],
            [
              "L4",
              "Critically evaluate or extend methods with reviewed research evidence.",
            ],
          ].map(([level, text]) => (
            <div key={level}>
              <span className="mono">{level}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>
        <p className="small muted">
          The current workflow verifies L1, and L2 for M02/PY01 when all gates
          are met. Retention retests are recorded separately; repeated quizzes
          do not establish novel transfer. L3/L4 can be provisionally
          self-assessed, but the initial content has no certification contracts
          for them.
        </p>
      </section>
    </div>
  );
}
export function Sources() {
  return (
    <div className="page">
      <PageHeading
        eyebrow="STUDY THE ORIGINALS"
        title="References"
        description="Study original courses, texts, and official documentation. External links require Internet; lessons and progress work locally."
      />
      <div className="panel source-list">
        {sources.map((s) => (
          <a href={s.url} rel="noreferrer" key={s.url}>
            <div>
              <span className="small muted">{s.domain}</span>
              <h2>{s.title}</h2>
              <span className="small muted">{new URL(s.url).hostname}</span>
            </div>
            <ExternalLink size={18} />
          </a>
        ))}
      </div>
      <p className="catalog-note">
        CoreLab content is independently authored. Copyrighted books, PDFs, and
        datasets are not redistributed. The source collection is maintained at
        reference/LEARNING_SOURCES.md.
      </p>
    </div>
  );
}
