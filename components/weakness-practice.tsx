"use client";
import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, RotateCcw } from "lucide-react";
import { topics, topicMap } from "@/lib/curriculum";
import { weaknessUrl, mistakeCategoryLabel } from "@/lib/weaknesses";
import type {
  Weakness,
  TargetedPlan,
  PracticeSkill,
  Answers,
  Assistance,
  Attempt,
} from "@/lib/types";
import { useCore, Loading } from "./provider";
import { PageHeading, dateText, TopicChips } from "./ui";
import { AssistanceSelect, AssessmentQuestion } from "./assessment-question";
const statusLabels = {
  active: "Active weakness",
  practiced_with_assistance: "Practiced with assistance",
  independently_corrected: "Independently corrected",
  due_for_retention_review: "Due for retention review",
};
export function WeaknessStatus({ weakness }: { weakness: Weakness }) {
  return (
    <span
      className={`status ${weakness.status === "independently_corrected" ? "verified" : ""}`}
    >
      {statusLabels[weakness.status]}
    </span>
  );
}
export function PracticeTabs({ weaknesses = false }: { weaknesses?: boolean }) {
  return (
    <nav className="practice-tabs segmented" aria-label="Practice sections">
      <Link
        className={weaknesses ? "" : "selected"}
        aria-current={!weaknesses ? "page" : undefined}
        href="/practice"
      >
        Assignments
      </Link>
      <Link
        className={weaknesses ? "selected" : ""}
        aria-current={weaknesses ? "page" : undefined}
        href={weaknessUrl()}
      >
        My Weaknesses
      </Link>
    </nav>
  );
}
export function WeaknessPractice() {
  const { state } = useCore();
  const params = useSearchParams();
  const router = useRouter();
  const [filter, setFilter] = useState("open");
  if (!state) return <Loading />;
  const all = state.weaknesses;
  const visible = all.filter((w) =>
    filter === "all" || filter === "open"
      ? filter === "all" || w.status !== "independently_corrected"
      : w.status === filter,
  );
  const requested = params.get("topic");
  const topic =
    requested && topicMap[requested]
      ? requested
      : (all.find((w) => w.status !== "independently_corrected")?.topicId ??
        "M05");
  const skill = params.get("skill") ?? undefined;
  return (
    <div className="page">
      <PageHeading
        eyebrow="PRACTICE → MY WEAKNESSES"
        title="Practice the skill behind the mistake."
        description="Objective errors become a focused queue. Correcting a skill preserves its history and does not certify a whole topic."
      />
      <PracticeTabs weaknesses />
      <div className="filters">
        <label className="sr-only" htmlFor="weakness-status">
          Filter weakness status
        </label>
        <select
          id="weakness-status"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="open">Needs practice or retention review</option>
          <option value="active">Active weakness</option>
          <option value="practiced_with_assistance">
            Practiced with assistance
          </option>
          <option value="independently_corrected">
            Independently corrected
          </option>
          <option value="due_for_retention_review">
            Due for retention review
          </option>
          <option value="all">All mistake history</option>
        </select>
        <span className="result-count">{visible.length} skills</span>
      </div>
      {visible.length ? (
        <div className="weakness-list">
          {visible.map((w) => (
            <section className="panel weakness-card" key={w.key}>
              <div className="between">
                <span className="topic-code">
                  {w.topicId} · {topicMap[w.topicId].title}
                </span>
                <WeaknessStatus weakness={w} />
              </div>
              <h2>{w.skillLabel}</h2>
              <p className="small">
                {w.failureCount} objective mistakes across {w.failedAttempts}{" "}
                failed {w.failedAttempts === 1 ? "attempt" : "attempts"} · Last
                activity: {dateText(w.lastAttemptAt)}
              </p>
              <div className="chips">
                {w.categories.map((c) => (
                  <span className="status" key={c}>
                    {mistakeCategoryLabel(c)}
                  </span>
                ))}
              </div>
              <p className="small muted">
                {w.status === "practiced_with_assistance"
                  ? "Assisted success is useful practice. A fresh equivalent A0 answer is still needed."
                  : w.status === "independently_corrected"
                    ? "New independent evidence corrected this skill. Its failure history remains available."
                    : w.status === "due_for_retention_review"
                      ? "The existing topic review schedule is due. Check retention without consulting the solution."
                      : "Review the specific reasoning, then try a different authored example."}
              </p>
              <div className="topic-actions">
                <Link
                  className="button"
                  href={w.remediation[0]?.href ?? `/lessons/${w.topicId}`}
                >
                  Review Concept
                </Link>
                <Link
                  className="button primary"
                  href={
                    weaknessUrl(w.topicId, w.skillTag) + "#targeted-practice"
                  }
                >
                  Practice Weak Skill
                  <ArrowRight size={15} />
                </Link>
                <Link className="button" href={`/assessments/${w.topicId}`}>
                  Retry Assessment
                </Link>
              </div>
              <details className="weakness-provenance">
                <summary>Evidence and prerequisites</summary>
                <p className="small muted">
                  Classification:{" "}
                  {w.classificationSource === "authored"
                    ? "authored skill metadata"
                    : "legacy question format; no finer skill classification is authored"}
                  . Latest result: {w.latestResult.replaceAll("_", " ")}. Topic
                  review:{" "}
                  {w.reviewDueAt ? dateText(w.reviewDueAt) : "not scheduled"}.{" "}
                  {w.lastCorrectedAt
                    ? `Independent correction: ${dateText(w.lastCorrectedAt)}.`
                    : ""}
                </p>
                <ul>
                  {w.questionRefs.map((r) => (
                    <li
                      key={`${r.purpose}-${r.version}-${r.questionId}`}
                      className="small mono"
                    >
                      {r.purpose} v{r.version} · {r.questionId}
                    </li>
                  ))}
                </ul>
                <TopicChips ids={w.prerequisites} />
                {w.remediation.slice(1).map((ref) => (
                  <Link key={ref.href} className="text-link" href={ref.href}>
                    {ref.label}
                  </Link>
                ))}
              </details>
            </section>
          ))}
        </div>
      ) : (
        <div className="panel">
          <h2>
            {all.length
              ? "No skills match this filter."
              : "No objectively graded mistakes recorded yet."}
          </h2>
          <p>
            Reading and ungraded rubric responses never count as mistakes. Try a
            diagnostic or explore an authored practice skill below.
          </p>
          <Link className="button" href="/assessments">
            Open assessments
          </Link>
        </div>
      )}
      <section id="targeted-practice" className="targeted-section">
        <div className="section-title">
          <h2>Focused practice</h2>
        </div>
        <label>
          Practice topic
          <select
            aria-label="Focused practice topic"
            value={topic}
            onChange={(e) => {
              router.push(weaknessUrl(e.target.value) + "#targeted-practice");
            }}
          >
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.id} · {t.title}
              </option>
            ))}
          </select>
        </label>
        <TargetedSet
          key={`${topic}:${skill ?? ""}`}
          topicId={topic}
          skill={skill}
          defaultSkill={
            all.find(
              (w) =>
                w.topicId === topic && w.status !== "independently_corrected",
            )?.skillTag ?? all.find((w) => w.topicId === topic)?.skillTag
          }
        />
      </section>
    </div>
  );
}
function TargetedSet({
  topicId,
  skill,
  defaultSkill,
}: {
  topicId: string;
  skill?: string;
  defaultSkill?: string;
}) {
  const { act, busy } = useCore();
  const [selectedSkill] = useState(() => skill ?? defaultSkill);
  const router = useRouter();
  const [data, setData] = useState<{
      skills: PracticeSkill[];
      plan: TargetedPlan;
    } | null>(null),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0),
    [answers, setAnswers] = useState<Answers>({}),
    [assistance, setAssistance] = useState<Assistance>("A0"),
    [result, setResult] = useState<Attempt | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    const params = new URLSearchParams({ topic: topicId });
    if (selectedSkill) params.set("skill", selectedSkill);
    fetch(`/api/practice?${params}`, { signal: controller.signal })
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.error);
        setData(body);
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Unable to load practice.");
      });
    return () => controller.abort();
  }, [topicId, selectedSkill, reload]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!data) return;
    setError("");
    try {
      const attempt = (await act({
        type: "targeted_attempt",
        topicId,
        skillTag: data.plan.skillTag,
        questionIds: data.plan.assessment.questions.map((q) => q.id),
        assessmentVersion: data.plan.assessment.version,
        answers,
        assistance,
      })) as Attempt;
      setResult(attempt);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save practice.");
    }
  }
  if (!data)
    return (
      <div className="panel" role={error ? "alert" : "status"}>
        {error || "Loading authored practice…"}
      </div>
    );
  const { plan, skills } = data;
  const objective = result?.grade.items.some((i) => i.correct !== null);
  return (
    <div>
      <label>
        Weak skill / assessment type
        <select
          aria-label="Focused practice skill"
          value={plan.skillTag}
          onChange={(e) =>
            router.push(
              weaknessUrl(topicId, e.target.value) + "#targeted-practice",
            )
          }
        >
          {!skills.some((s) => s.tag === plan.skillTag) && (
            <option value={plan.skillTag}>{plan.skillLabel}</option>
          )}
          {skills.map((s) => (
            <option value={s.tag} key={s.tag}>
              {s.label} · {s.knowledgeTypes.join(" / ")}
            </option>
          ))}
        </select>
      </label>
      <div className="info-banner">{plan.message}</div>
      {plan.prerequisiteActivities.length > 0 && (
        <section className="panel">
          <h3>Check the foundation</h3>
          {plan.prerequisiteActivities.map((a) => (
            <div key={a.topicId}>
              <p className="small">{a.reason}</p>
              <Link className="button" href={a.href}>
                Check {a.topicId} · {topicMap[a.topicId].title}
              </Link>
            </div>
          ))}
        </section>
      )}
      {plan.assessment.questions.length > 0 && !result && (
        <form className="assessment-form targeted-form" onSubmit={submit}>
          <div className="panel">
            <div className="between">
              <h2>{plan.skillLabel}</h2>
              <span className="mono small">
                PRACTICE v{plan.assessment.version}
              </span>
            </div>
            <AssistanceSelect value={assistance} onChange={setAssistance} />
          </div>
          {plan.assessment.questions.map((q, index) => (
            <AssessmentQuestion
              key={q.id}
              question={q}
              index={index}
              answers={answers}
              onAnswer={(id, value) =>
                setAnswers((a) => ({ ...a, [id]: value }))
              }
              requireShort
            />
          ))}
          <button type="submit" className="button primary" disabled={busy}>
            Save focused practice
            <ArrowRight size={16} />
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      {result && (
        <section className="panel assessment-result" role="status">
          <h2>
            {objective
              ? `Focused result · ${result.grade.score}%`
              : "Rubric response saved · unverified"}
          </h2>
          <p>
            Assistance: {result.assistance}. Focused results do not satisfy full
            diagnostic gates or automatically raise L1/L2/L3 mastery.
          </p>
          {result.grade.items.map((i) => (
            <div className="feedback-item" key={i.id}>
              <strong
                className={
                  i.correct === true
                    ? "verified-text"
                    : i.correct === false
                      ? "error-text"
                      : "muted"
                }
              >
                {i.id} ·{" "}
                {i.correct === null
                  ? "Review against rubric"
                  : i.correct
                    ? "Correct"
                    : "Not yet correct"}
              </strong>
              <p>{i.feedback}</p>
            </div>
          ))}
          <button
            className="button"
            onClick={() => {
              setData(null);
              setResult(null);
              setAnswers({});
              setReload((n) => n + 1);
            }}
          >
            <RotateCcw size={15} />
            Check next available set
          </button>
        </section>
      )}
      {!plan.assessment.questions.length && (
        <div className="topic-actions">
          <Link className="button" href={`/lessons/${topicId}`}>
            Review Concept
          </Link>
          <Link className="button" href={`/assessments/${topicId}`}>
            Retry Assessment
          </Link>
        </div>
      )}
    </div>
  );
}
