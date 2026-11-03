"use client";
import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowLeft,
  BookOpen,
  Copy,
  ClipboardCheck,
  Pin,
  FileText,
  Clock3,
} from "lucide-react";
import { domainTone } from "./domain-theme";
import { topicMap, topics } from "@/lib/curriculum";
import { contextFor } from "@/lib/engine";
import type { TopicPayload, Attempt, Assistance, Answers } from "@/lib/types";
import { useCore, Loading, copyText } from "./provider";
import { TopicChips, Status, Matrix, dateText } from "./ui";
import { LessonReader, SessionProgressBar } from "./lesson-study";
import { lessonPlan } from "@/lib/lesson-plan";
import { isCheckoff } from "@/lib/checkoff";
import { formatDuration, useI18n } from "@/lib/i18n";
import { AssessmentQuestion, AssistanceSelect } from "./assessment-question";
import { AssessmentMethods } from "./assessment-methods";
import { weaknessUrl } from "@/lib/weaknesses";
export function useTopic(id: string) {
  const { lang } = useI18n();
  const [data, setData] = useState<TopicPayload | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    fetch(`/api/topics/${id}${lang === "vi" ? "?lang=vi" : ""}`, {
      signal: controller.signal,
    })
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
  }, [id, lang]);
  return { data, error };
}
export function TopicPage({
  id,
  assessment = false,
}: {
  id: string;
  assessment?: boolean;
}) {
  const { state, act, busy, notify, title } = useCore();
  const { t, lang } = useI18n();
  const { data, error } = useTopic(id);
  const [context, setContext] = useState("");
  if (error)
    return (
      <div className="page empty-state" role="alert">
        <h1>{t("topic.unableTitle")}</h1>
        <p>{error}</p>
        <Link href="/roadmap">{t("topic.backRoadmap")}</Link>
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
  const plan = lesson ? lessonPlan(lesson) : null;
  const sessions = plan?.sessions ?? [];
  async function copyContext() {
    const text = contextFor(id, state!.progress, objectives, "learning");
    setContext(text);
    try {
      await copyText(text);
      notify(t("topic.contextCopied"));
    } catch (e) {
      notify(e instanceof Error ? e.message : t("topic.copyFailed"));
    }
  }
  const after = (
    <>
      <Notebook id={id} />
      <div className="lesson-nav">
        {prev ? (
          <Link href={`/lessons/${prev.id}`}>
            <ArrowLeft size={16} />
            <span>
              <small>{t("topic.prevLesson")}</small>
              {prev.id} · {title(prev.id)}
            </span>
          </Link>
        ) : (
          <span />
        )}
        {next && (
          <Link href={`/lessons/${next.id}`}>
            <span>
              <small>{t("topic.nextLesson")}</small>
              {next.id} · {title(next.id)}
            </span>
            <ArrowRight size={16} />
          </Link>
        )}
      </div>
      <section className="related-topics">
        <h2>{t("topic.buildsOn")}</h2>
        <TopicChips ids={successors.map((t) => t.id)} />
      </section>
    </>
  );
  return (
    <div
      className={`page topic-page ${assessment ? "assessment-page" : ""}`}
      data-domain-tone={domainTone(topic.domain)}
    >
      <div className="topic-breadcrumb">
        <Link href={assessment ? "/assessments" : "/lessons"}>
          {assessment ? t("nav.review") : t("nav.lessons")}
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
          {lesson && !assessment && (
            <span className="time" data-testid="lesson-time">
              <Clock3 size={14} />≈ {formatDuration(plan?.minutes ?? 0, lang)} ·{" "}
              {t("lesson.sessionCount", { n: sessions.length })}
            </span>
          )}
        </div>
        <h1>
          {assessment
            ? t("topic.checkTitle", { title: title(id) })
            : (lesson?.meta.title ?? topic.title)}
        </h1>
        <p>{lesson?.meta.summary ?? overview.overview}</p>
        {lesson && !assessment && (
          <SessionProgressBar topicId={id} sessionCount={sessions.length} />
        )}
        <div className="topic-actions">
          <Link
            className={assessment ? "button" : "button primary"}
            href={`/assessments/${id}`}
          >
            <ClipboardCheck size={16} />
            {t("topic.checkKnow")}
          </Link>
          <button className="button" onClick={() => void copyContext()}>
            <Copy size={15} />
            {t("topic.copyContext")}
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
                .then(() => notify(t("topic.pinned", { id })))
                .catch(() => {})
            }
          >
            <Pin size={15} />
            {state.progress.focusTopic === id
              ? t("topic.focusPinned")
              : t("topic.pinFocus")}
          </button>
          {assessment && (
            <Link className="button" href={`/lessons/${id}`}>
              <BookOpen size={15} />
              {t("topic.readLesson")}
            </Link>
          )}
        </div>
      </div>
      {context && (
        <details className="context-preview">
          <summary>{t("topic.viewContext")}</summary>
          <textarea
            aria-label="Learning Context"
            readOnly
            value={context}
            rows={9}
          />
        </details>
      )}
      <section className="topic-prereqs">
        <h2>{t("topic.prereqs")}</h2>
        <TopicChips ids={topic.prerequisites} />
        {topic.prerequisites.some((p) => state.mastery[p].level < 1) && (
          <p className="small warning-text">{t("topic.prereqWarn")}</p>
        )}
      </section>
      <details className="details-disclosure">
        <summary>{t("common.details")}</summary>
        <Matrix mastery={m} />
      </details>
      {assessment ? (
        <AssessmentWorkspace id={id} data={data} />
      ) : lesson ? (
        <LessonReader
          key={`${id}-${lang}`}
          id={id}
          lesson={lesson}
          media={data.media}
          objectives={objectives}
          sessions={sessions}
          after={after}
        />
      ) : (
        <div className="reading-layout">
          <article className="lesson-article">
            <div id="lesson-theory">
              <OverviewBody data={data} domain={topic.domain} />
            </div>
            {after}
          </article>
          <aside className="lesson-toc is-static">
            <div className="eyebrow">{t("lesson.inThis")}</div>
            <a href="#overview">Overview</a>
            <a href="#application">Application</a>
            <a href="#practice">Practice</a>
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
const noteKinds: Record<string, [string, string]> = {
  note: ["note", "ghi chú"],
  difficulty: ["difficulty", "khó khăn"],
  practice: ["practice", "luyện tập"],
  self_assessment: ["self_assessment", "tự đánh giá"],
  ai_feedback: ["ai_feedback", "phản hồi AI"],
};
export function Notebook({ id }: { id: string }) {
  const { state, act, busy, notify } = useCore();
  const { t, tx } = useI18n();
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
      notify(t("notebook.saved"));
    } catch {}
  }
  const notes =
    state?.progress.sessions
      .filter((s) => s.topicId === id && s.kind !== "reading" && !isCheckoff(s))
      .slice(-5)
      .reverse() ?? [];
  return (
    <section className="notebook panel">
      <div className="panel-heading">
        <h2>{t("notebook.title")}</h2>
        <FileText size={18} />
      </div>
      <p className="small muted">{t("notebook.intro")}</p>
      <form onSubmit={submit}>
        <div className="form-row">
          <label>
            {t("notebook.type")}
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="note">{t("notebook.note")}</option>
              <option value="difficulty">{t("notebook.difficulty")}</option>
              <option value="practice">{t("notebook.practice")}</option>
              <option value="self_assessment">{t("notebook.self")}</option>
            </select>
          </label>
          <label>
            {t("notebook.time")}
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
              {t("notebook.level")}
              <select
                value={level}
                onChange={(e) => setLevel(Number(e.target.value))}
              >
                {[1, 2, 3, 4].map((l) => (
                  <option key={l} value={l}>
                    {tx("Provisional", "Tạm thời")} L{l}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <label className="sr-only" htmlFor={`note-${id}`}>
          {tx("Notebook entry", "Nội dung ghi chú")}
        </label>
        <textarea
          id={`note-${id}`}
          required
          maxLength={20000}
          rows={4}
          placeholder={t("notebook.placeholder")}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          className="button"
          disabled={busy || !text.trim()}
          type="submit"
        >
          {t("notebook.save")}
        </button>
      </form>
      {notes.length > 0 && (
        <div className="note-list">
          {notes.map((n) => (
            <div key={n.id}>
              <div className="between">
                <span className="status">
                  {noteKinds[n.kind]
                    ? tx(noteKinds[n.kind][0], noteKinds[n.kind][1])
                    : n.kind}
                  {n.provisionalLevel
                    ? ` · ${tx("Provisional", "Tạm thời")} L${n.provisionalLevel}`
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
  const { t, tx, lang } = useI18n();
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
        lang,
      })) as Attempt;
      setResult(attempt);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : t("assess.saveFail"));
    }
  }
  return (
    <div className="assessment-layout">
      <section>
        <details className="details-disclosure panel">
          <summary>{t("assess.methods")}</summary>
          <AssessmentMethods id={id} data={data} />
        </details>
        <div className="panel gates">
          <h2>{t("assess.masteredTitle")}</h2>
          <ul>
            <li className={m.dimensions.C ? "verified-text" : ""}>
              {m.dimensions.C ? "✓" : "○"} {t("assess.gateC")}
            </li>
            <li className={m.dimensions.M ? "verified-text" : ""}>
              {m.dimensions.M ? "✓" : "○"} {t("assess.gateM")}
            </li>
            <li className={m.dimensions.I ? "verified-text" : ""}>
              {m.dimensions.I ? "✓" : "○"} {t("assess.gateI")}
            </li>
            <li className={m.dimensions.T ? "verified-text" : ""}>
              {m.dimensions.T ? "✓" : "○"} {t("assess.gateT")}
            </li>
          </ul>
          <details className="details-disclosure">
            <summary>{t("common.details")}</summary>
            <p className="small muted">{t("assess.levelsNote")}</p>
            <dl className="assist-legend">
              <dt>C · M · I · T</dt>
              <dd>{t("assess.cmit")}</dd>
              <dt>A0 · A1 · A2 · A3</dt>
              <dd>{t("assess.assistNote")}</dd>
            </dl>
          </details>
          <Link href={`/practice?topic=${id}`} className="text-link">
            {t("assess.practiceInstructions")}
            <ArrowRight size={14} />
          </Link>
        </div>
        {assessment ? (
          <form className="assessment-form" onSubmit={submit}>
            <div className="panel">
              <div className="between">
                <h2>{t("assess.checkTitle")}</h2>
                <span className="mono small muted">
                  {tx("VERSION", "PHIÊN BẢN")} v{assessment.version}
                </span>
              </div>
              <p className="muted small">{t("assess.tryFirst")}</p>
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
              {busy ? t("common.saving") : t("assess.submit")}
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
            <h2>{t("assess.none")}</h2>
            <p>{t("assess.noneNote")}</p>
          </div>
        )}
        {result && (
          <div className="panel assessment-result" role="status">
            <div className="between">
              <h2>{t("assess.result", { score: result.grade.score })}</h2>
              <span
                className={`status ${result.grade.passed && result.assistance === "A0" ? "verified" : ""}`}
              >
                {result.grade.passed
                  ? result.assistance === "A0"
                    ? t("assess.passed")
                    : t("assess.passedHelp")
                  : t("assess.tryAgain")}
              </span>
            </div>
            <p className="muted small">
              {dateText(result.at)} · {result.assistance} · {t("assess.saved")}
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
                    ? t("assess.rubric")
                    : item.correct
                      ? t("assess.correct")
                      : t("assess.notYet")}
                </strong>
                <p>{result.localizedFeedback?.[item.id] ?? item.feedback}</p>
              </div>
            ))}
            <Link className="button" href={`/lessons/${id}`}>
              {t("assess.revisit")}
              <BookOpen size={15} />
            </Link>
            {result.grade.items.some((i) => i.correct === false) && (
              <Link className="button" href={weaknessUrl(id)}>
                {t("assess.practiceWeak")}
                <ArrowRight size={15} />
              </Link>
            )}
          </div>
        )}
        <Notebook id={id} />
      </section>
      <aside className="evidence-history">
        <div className="panel">
          <h2>{t("assess.history")}</h2>
          {attempts.length ? (
            attempts.map((a) => (
              <details key={a.id}>
                <summary>
                  <strong>
                    {a.grade.items.some((i) => i.correct !== null)
                      ? `${a.grade.score}%`
                      : t("assess.rubricOnly")}{" "}
                    · {a.assistance}
                  </strong>
                  <small>{dateText(a.at)}</small>
                </summary>
                <p className="small muted">
                  {a.purpose === "targeted"
                    ? t("assess.focused")
                    : t("assess.check")}{" "}
                  v{a.assessmentVersion} · {a.id}
                </p>
                {a.grade.items.map((i) => (
                  <p className="small" key={i.id}>
                    {i.id}:{" "}
                    {i.correct === null
                      ? t("assess.rubricShort")
                      : i.correct
                        ? t("assess.correct")
                        : t("assess.notYet")}{" "}
                    · {i.feedback}
                  </p>
                ))}
              </details>
            ))
          ) : (
            <p className="muted small">{t("assess.noAttempts")}</p>
          )}
          {state.progress.labs
            .filter((l) => l.topicId === id)
            .map((l) => (
              <div className="lab-evidence" key={l.id}>
                <strong className="verified-text">
                  {t("assess.labReport")} · {l.assistance}
                </strong>
                <small>{dateText(l.at)}</small>
                <code>SHA256 {l.sourceHash.slice(0, 16)}…</code>
                <p className="small">
                  {l.assistance === "A0"
                    ? t("assess.labIndependent")
                    : t("assess.labAssisted")}
                </p>
              </div>
            ))}
        </div>
        <div className="quiet-note">{t("assess.historyNote")}</div>
      </aside>
    </div>
  );
}
