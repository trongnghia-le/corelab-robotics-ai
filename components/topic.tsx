"use client";
import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowRight,
  ArrowLeft,
  BookOpen,
  Check,
  Copy,
  ClipboardCheck,
  Pin,
  FileText,
} from "lucide-react";
import { topicMap, topics } from "@/lib/curriculum";
import { contextFor } from "@/lib/engine";
import type { TopicPayload, Attempt, Assistance, Answers } from "@/lib/types";
import { useCore, Loading, copyText } from "./provider";
import { TopicChips, Status, Matrix, Time, dateText } from "./ui";
import { headingId } from "./markdown";
import { LearningVisual } from "./learning-visual";
import { AssessmentQuestion, AssistanceSelect } from "./assessment-question";
import { AssessmentMethods } from "./assessment-methods";
import { weaknessUrl } from "@/lib/weaknesses";
const LessonMarkdown = dynamic(
  () => import("./markdown").then((m) => m.LessonMarkdown),
  { loading: () => <p>Rendering lesson…</p> },
);
export function useTopic(id: string) {
  const [data, setData] = useState<TopicPayload | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    fetch(`/api/topics/${id}`, { signal: controller.signal })
      .then(async (r) => {
        const payload = await r.json();
        if (!r.ok) throw new Error(payload.error);
        setData(payload);
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Unable to open topic.");
      });
    return () => controller.abort();
  }, [id]);
  return { data, error };
}
export function TopicPage({
  id,
  assessment = false,
}: {
  id: string;
  assessment?: boolean;
}) {
  const { state, act, busy, notify } = useCore();
  const { data, error } = useTopic(id);
  const [context, setContext] = useState("");
  if (error)
    return (
      <div className="page empty-state" role="alert">
        <h1>Unable to open topic</h1>
        <p>{error}</p>
        <Link href="/roadmap">Back to Roadmap</Link>
      </div>
    );
  if (!state || !data) return <Loading />;
  const topic = topicMap[id],
    m = state.mastery[id],
    lesson = data.lesson,
    overview = data.overview;
  const objectives =
    lesson?.meta.objectives ??
    overview.concepts.map((c) => `Explain and verify: ${c}.`);
  const successors = topics.filter((t) => t.prerequisites.includes(id));
  const authored = topics.filter((t) => state.lessonIds.includes(t.id));
  const pos = authored.findIndex((t) => t.id === id);
  const prev = authored[pos - 1],
    next = authored[pos + 1];
  async function copyContext() {
    const text = contextFor(id, state!.progress, objectives, "learning");
    setContext(text);
    try {
      await copyText(text);
      notify("Learning Context copied.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Unable to copy.");
    }
  }
  return (
    <div className={`page topic-page ${assessment ? "assessment-page" : ""}`}>
      <div className="topic-breadcrumb">
        <Link href={assessment ? "/assessments" : "/lessons"}>
          {assessment ? "Assessments" : "Lessons"}
        </Link>
        <span>/</span>
        <Link href={`/roadmap?domain=${encodeURIComponent(topic.domain)}`}>
          {topic.domain}
        </Link>
        <span>/</span>
        <span className="mono">{id}</span>
      </div>
      <div className="topic-heading">
        <div className="topic-meta">
          <span className="topic-code">{id}</span>
          <span className={`priority ${topic.priority}`}>{topic.priority}</span>
          <Status mastery={m} />
          {lesson && <Time minutes={lesson.meta.estimated_minutes} />}
        </div>
        <h1>
          {assessment
            ? `Diagnostic · ${topic.title}`
            : (lesson?.meta.title ?? topic.title)}
        </h1>
        <p>{lesson?.meta.summary ?? overview.overview}</p>
        <div className="topic-actions">
          <Link
            className={assessment ? "button" : "button primary"}
            href={`/assessments/${id}`}
          >
            <ClipboardCheck size={16} />
            Assess competence
          </Link>
          <button className="button" onClick={() => void copyContext()}>
            <Copy size={15} />
            Copy Learning Context
          </button>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              void act({
                type: "goal",
                goal: state.progress.goal,
                focusTopic: id,
                focusReason: "Topic pinned from the workspace.",
              })
                .then(() => notify(`Pinned ${id} as the current focus.`))
                .catch(() => {})
            }
          >
            <Pin size={15} />
            {state.progress.focusTopic === id ? "Focus pinned" : "Pin focus"}
          </button>
          {assessment && (
            <Link className="button" href={`/lessons/${id}`}>
              <BookOpen size={15} />
              Read lesson
            </Link>
          )}
        </div>
      </div>
      {context && (
        <details className="context-preview">
          <summary>View generated Learning Context</summary>
          <textarea
            aria-label="Learning Context"
            readOnly
            value={context}
            rows={9}
          />
        </details>
      )}
      <section className="topic-prereqs">
        <h2>Suggested prerequisites</h2>
        <TopicChips ids={topic.prerequisites} />
        {topic.prerequisites.some((p) => state.mastery[p].level < 1) && (
          <p className="small warning-text">
            Some prerequisites are not verified yet. You can still study this
            topic; consider checking the foundations first.
          </p>
        )}
      </section>
      <Matrix mastery={m} />
      {assessment ? (
        <AssessmentWorkspace id={id} data={data} />
      ) : (
        <div className="reading-layout">
          <article className="lesson-article">
            <div className="objectives-box">
              <div className="eyebrow">AFTER THIS LESSON</div>
              <ul>
                {objectives.map((o) => (
                  <li key={o}>
                    <Check size={15} />
                    {o}
                  </li>
                ))}
              </ul>
            </div>
            {lesson ? (
              <>
                <LearningVisual topicId={id} />
                <LessonMarkdown body={lesson.body} />
                <div className="reading-complete">
                  <div>
                    <strong>
                      Finished reading? Move from understanding to verification.
                    </strong>
                    <p>
                      Recording a read only saves an activity; it does not
                      increase mastery.
                    </p>
                  </div>
                  <button
                    disabled={busy}
                    onClick={() =>
                      void act({
                        type: "session",
                        topicId: id,
                        kind: "reading",
                        text: `Read ${lesson.meta.title}`,
                        minutes: 0,
                      })
                        .then(() =>
                          notify(
                            "Reading activity saved. Mastery is unchanged.",
                          ),
                        )
                        .catch(() => {})
                    }
                  >
                    Mark as read
                  </button>
                </div>
                <Link className="button primary" href={`/assessments/${id}`}>
                  Start diagnostic
                  <ArrowRight size={16} />
                </Link>
              </>
            ) : (
              <OverviewBody data={data} domain={topic.domain} />
            )}
            <Notebook id={id} />
            <div className="lesson-nav">
              {prev ? (
                <Link href={`/lessons/${prev.id}`}>
                  <ArrowLeft size={16} />
                  <span>
                    <small>Previous lesson in the library</small>
                    {prev.id} · {prev.title}
                  </span>
                </Link>
              ) : (
                <span />
              )}
              {next && (
                <Link href={`/lessons/${next.id}`}>
                  <span>
                    <small>Next lesson in the library</small>
                    {next.id} · {next.title}
                  </span>
                  <ArrowRight size={16} />
                </Link>
              )}
            </div>
            <section className="related-topics">
              <h2>Topics that build on this foundation</h2>
              <TopicChips ids={successors.map((t) => t.id)} />
            </section>
          </article>
          <aside className="lesson-toc">
            <div className="eyebrow">IN THIS LESSON</div>
            {lesson ? (
              lesson.body
                .split("\n")
                .filter((l) => l.startsWith("## "))
                .map((l) => (
                  <a href={`#${headingId(l.slice(3))}`} key={l}>
                    {l.slice(3).split(" · ")[0]}
                  </a>
                ))
            ) : (
              <>
                <a href="#overview">Overview</a>
                <a href="#application">Application</a>
                <a href="#practice">Practice</a>
              </>
            )}
            <div className="toc-note">
              <FileText size={18} />
              <p>Diagnostic → Learn → Derive → Implement → Verify → Transfer</p>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
const resourceMap: Record<string, { title: string; url: string }[]> = {
  Mathematics: [
    {
      title: "MIT OCW · Linear Algebra",
      url: "https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/",
    },
  ],
  Programming: [
    { title: "Python Tutorial", url: "https://docs.python.org/3/tutorial/" },
    { title: "LearnCpp", url: "https://www.learncpp.com/" },
  ],
  "Machine Learning": [
    { title: "Dive into Deep Learning", url: "https://d2l.ai/" },
  ],
  Robotics: [
    {
      title: "Modern Robotics",
      url: "https://modernrobotics.northwestern.edu/",
    },
  ],
  "Simulation & Systems": [
    { title: "MuJoCo documentation", url: "https://mujoco.readthedocs.io/" },
  ],
  "Computer Vision": [
    { title: "Stanford CS231n", url: "https://cs231n.stanford.edu/" },
  ],
  "Reinforcement & Robot Learning": [
    {
      title: "David Silver lectures",
      url: "https://www.davidsilver.uk/teaching/",
    },
  ],
  "Embodied & Cognitive Robotics": [
    { title: "LeRobot", url: "https://github.com/huggingface/lerobot" },
  ],
  "Scientific Research": [
    { title: "CLVR publications", url: "https://clvrai.com/publications/" },
  ],
};
function OverviewBody({
  data,
  domain,
}: {
  data: TopicPayload;
  domain: string;
}) {
  return (
    <div className="prose">
      <div className="info-banner">
        Overview · This topic does not yet have a complete lesson or diagnostic.
        No progress is assumed.
      </div>
      <h2 id="overview">Overview</h2>
      <p>{data.overview.overview}</p>
      <h2 id="application">Practical application</h2>
      <p>{data.overview.application}</p>
      <h2 id="practice">Self-study guidance</h2>
      <p>{data.overview.task}</p>
      <p>
        Study the sources below and write your own reasoning and tests. Notes
        and self-assessments remain unverified evidence.
      </p>
      <h2>Related resources</h2>
      <ul>
        {(resourceMap[domain] ?? resourceMap.Robotics).map((s) => (
          <li key={s.url}>
            <a href={s.url} rel="noreferrer">
              {s.title}
            </a>{" "}
            · a domain-level resource; choose a chapter that matches your
            objectives, rather than treating it as an equivalent lesson.
          </li>
        ))}
      </ul>
    </div>
  );
}
export function Notebook({ id }: { id: string }) {
  const { state, act, busy, notify } = useCore();
  const [text, setText] = useState(""),
    [kind, setKind] = useState("note"),
    [minutes, setMinutes] = useState(15),
    [level, setLevel] = useState(1);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    try {
      await act({
        type: "session",
        topicId: id,
        kind,
        text,
        minutes,
        provisionalLevel: kind === "self_assessment" ? level : undefined,
      });
      setText("");
      notify("Notebook entry saved locally.");
    } catch {}
  }
  const notes =
    state?.progress.sessions
      .filter((s) => s.topicId === id && s.kind !== "reading")
      .slice(-5)
      .reverse() ?? [];
  return (
    <section className="notebook panel">
      <div className="panel-heading">
        <h2>Research notebook</h2>
        <FileText size={18} />
      </div>
      <p className="small muted">
        Record reasoning, experimental results, and open questions.
        Self-assessments remain separate from verified competence.
      </p>
      <form onSubmit={submit}>
        <div className="form-row">
          <label>
            Entry type
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="note">Note</option>
              <option value="difficulty">Knowledge debt · difficulty</option>
              <option value="practice">Practice results</option>
              <option value="self_assessment">
                Self-assessment · provisional
              </option>
            </select>
          </label>
          <label>
            Time (minutes)
            <input
              type="number"
              min="0"
              max="1440"
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            />
          </label>
          {kind === "self_assessment" && (
            <label>
              Self-assessed level
              <select
                value={level}
                onChange={(e) => setLevel(Number(e.target.value))}
              >
                {[1, 2, 3, 4].map((l) => (
                  <option key={l} value={l}>
                    Provisional L{l}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <label className="sr-only" htmlFor={`note-${id}`}>
          Notebook entry
        </label>
        <textarea
          id={`note-${id}`}
          required
          maxLength={20000}
          rows={4}
          placeholder="What did I try? Which results can I not explain yet?"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          className="button"
          disabled={busy || !text.trim()}
          type="submit"
        >
          Save entry
        </button>
      </form>
      {notes.length > 0 && (
        <div className="note-list">
          {notes.map((n) => (
            <div key={n.id}>
              <div className="between">
                <span className="status">
                  {n.kind}
                  {n.provisionalLevel
                    ? ` · Provisional L${n.provisionalLevel}`
                    : ""}
                </span>
                <small className="muted">{dateText(n.at)}</small>
              </div>
              <p>{n.text}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
function AssessmentWorkspace({ id, data }: { id: string; data: TopicPayload }) {
  const { state, act, busy } = useCore();
  const [answers, setAnswers] = useState<Answers>({}),
    [assistance, setAssistance] = useState<Assistance>("A0"),
    [result, setResult] = useState<Attempt | null>(null),
    [submitError, setSubmitError] = useState("");
  const assessment = data.assessment;
  if (!state) return null;
  const attempts = state.progress.attempts
    .filter((a) => a.topicId === id)
    .slice()
    .reverse();
  const m = state.mastery[id];
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitError("");
    try {
      const attempt = (await act({
        type: "attempt",
        topicId: id,
        answers,
        assistance,
      })) as Attempt;
      setResult(attempt);
    } catch (e) {
      setSubmitError(
        e instanceof Error ? e.message : "Unable to save attempt.",
      );
    }
  }
  return (
    <div className="assessment-layout">
      <section>
        <AssessmentMethods id={id} data={data} />
        <div className="panel gates">
          <h2>Required evidence</h2>
          <ul>
            <li className={m.dimensions.C ? "verified-text" : ""}>
              {m.dimensions.C ? "✓" : "○"} L1 · A0 diagnostic ≥80%, with no
              failed critical items.
            </li>
            <li className={m.dimensions.M ? "verified-text" : ""}>
              {m.dimensions.M ? "✓" : "○"} M · Numerical answers meet the
              assessment criteria.
            </li>
            <li className={m.dimensions.I ? "verified-text" : ""}>
              {m.dimensions.I ? "✓" : "○"} I · Independently implement and
              import a valid local test report.
            </li>
            <li className={m.dimensions.T ? "verified-text" : ""}>
              {m.dimensions.T ? "✓" : "○"} Retention · Repeat A0 after at least
              7 days.
            </li>
          </ul>
          <p className="small muted">
            L2 requires conceptual, numerical, and implementation evidence.
            L3/L4 require unfamiliar transfer tasks or independently reviewed
            research contributions; this quiz does not certify those levels.
          </p>
          <Link href={`/practice?topic=${id}`} className="text-link">
            Open practice instructions
            <ArrowRight size={14} />
          </Link>
        </div>
        {assessment ? (
          <form className="assessment-form" onSubmit={submit}>
            <div className="panel">
              <div className="between">
                <h2>Diagnostic</h2>
                <span className="mono small muted">
                  CONTRACT v{assessment.version}
                </span>
              </div>
              <p className="muted small">
                Try before viewing solutions. Short responses are saved with a
                rubric and are not automatically graded.
              </p>
              <AssistanceSelect value={assistance} onChange={setAssistance} />
            </div>
            {assessment.questions.map((q, i) => (
              <AssessmentQuestion
                key={q.id}
                question={q}
                index={i}
                answers={answers}
                onAnswer={(id, value) =>
                  setAnswers((a) => ({ ...a, [id]: value }))
                }
              />
            ))}
            <button className="button primary" type="submit" disabled={busy}>
              {busy ? "Saving…" : "Submit and save diagnostic"}
              <ArrowRight size={16} />
            </button>
            {submitError && (
              <p role="alert" className="error-text">
                {submitError}
              </p>
            )}
          </form>
        ) : (
          <div className="panel empty-state">
            <h2>No diagnostic available for this topic yet</h2>
            <p>
              Record notes and self-study results in the notebook. They remain
              unverified.
            </p>
          </div>
        )}
        {result && (
          <div className="panel assessment-result" role="status">
            <div className="between">
              <h2>Result · {result.grade.score}%</h2>
              <span
                className={`status ${result.grade.passed && result.assistance === "A0" ? "verified" : ""}`}
              >
                {result.grade.passed
                  ? result.assistance === "A0"
                    ? "A0 diagnostic passed"
                    : "Passed with assistance · unverified"
                  : "Study and try again"}
              </span>
            </div>
            <p className="muted small">
              {dateText(result.at)} · {result.assistance} · Saved in SQLite
            </p>
            {result.grade.items.map((item) => (
              <div className="feedback-item" key={item.id}>
                <strong
                  className={
                    item.correct === true
                      ? "verified-text"
                      : item.correct === false
                        ? "error-text"
                        : "muted"
                  }
                >
                  {item.id} ·{" "}
                  {item.correct === null
                    ? "Review against rubric"
                    : item.correct
                      ? "Correct"
                      : "Not yet correct"}
                </strong>
                <p>{item.feedback}</p>
              </div>
            ))}
            <Link className="button" href={`/lessons/${id}`}>
              Revisit the theory
              <BookOpen size={15} />
            </Link>
            {result.grade.items.some((i) => i.correct === false) && (
              <Link className="button" href={weaknessUrl(id)}>
                Practice Weaknesses
                <ArrowRight size={15} />
              </Link>
            )}
          </div>
        )}
        <Notebook id={id} />
      </section>
      <aside className="evidence-history">
        <div className="panel">
          <h2>Evidence history</h2>
          {attempts.length ? (
            attempts.map((a) => (
              <details key={a.id}>
                <summary>
                  <strong>
                    {a.grade.items.some((i) => i.correct !== null)
                      ? `${a.grade.score}%`
                      : "Rubric only"}{" "}
                    · {a.assistance}
                  </strong>
                  <small>{dateText(a.at)}</small>
                </summary>
                <p className="small muted">
                  {a.purpose === "targeted" ? "Focused practice" : "Assessment"}{" "}
                  v{a.assessmentVersion} · {a.id}
                </p>
                {a.grade.items.map((i) => (
                  <p className="small" key={i.id}>
                    {i.id}:{" "}
                    {i.correct === null
                      ? "Rubric"
                      : i.correct
                        ? "Correct"
                        : "Not yet correct"}{" "}
                    · {i.feedback}
                  </p>
                ))}
              </details>
            ))
          ) : (
            <p className="muted small">
              No attempts yet. Missing evidence does not mean missing ability.
            </p>
          )}
          {state.progress.labs
            .filter((l) => l.topicId === id)
            .map((l) => (
              <div className="lab-evidence" key={l.id}>
                <strong className="verified-text">
                  Fixed-test report · {l.assistance}
                </strong>
                <small>{dateText(l.at)}</small>
                <code>SHA256 {l.sourceHash.slice(0, 16)}…</code>
                <p className="small">
                  {l.assistance === "A0"
                    ? "Independent implementation evidence with self-declared assistance."
                    : "Assisted · practice only."}
                </p>
              </div>
            ))}
        </div>
        <div className="quiet-note">
          Evidence is historical and remains after an unsuccessful review. A
          failed attempt creates a review gap.
        </div>
      </aside>
    </div>
  );
}
