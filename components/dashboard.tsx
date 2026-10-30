"use client";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Target,
  ShieldCheck,
  GitBranch,
  Clock3,
  FlaskConical,
  BookOpen,
  ChevronRight,
} from "lucide-react";
import { useCore, Loading } from "./provider";
import { PageHeading, Status, dateText, TopicChips } from "./ui";
import { weaknessUrl } from "@/lib/weaknesses";
import { WeaknessStatus } from "./weakness-practice";
import { domains, topics, topicMap } from "@/lib/curriculum";
export function Dashboard() {
  const { state } = useCore();
  if (!state) return <Loading />;
  const { progress, mastery, recommendations } = state;
  const rec = recommendations[0];
  const topic = rec ? topicMap[rec.topicId] : null;
  const verified = topics.filter((t) => mastery[t.id].level > 0),
    attempted = new Set(progress.attempts.map((a) => a.topicId));
  const weaknesses = state.weaknesses.filter(
    (w) => w.status !== "independently_corrected",
  );
  const due = progress.reviews.filter((r) => mastery[r.topicId].reviewDue);
  const recent = [
    ...progress.attempts.map((a) => ({
      id: a.id,
      topicId: a.topicId,
      at: a.at,
      text: `${a.purpose === "targeted" ? "Focused practice" : "Diagnostic"} · ${a.grade.items.some((i) => i.correct !== null) ? `${a.grade.score}%` : "Rubric only"} · ${a.assistance}`,
      kind: "assessment",
    })),
    ...progress.sessions.map((s) => ({
      id: s.id,
      topicId: s.topicId,
      at: s.at,
      text: {
        reading: "Lesson read",
        practice: "Practice",
        note: "Note",
        difficulty: "Difficulty recorded",
        self_assessment: "Self-assessed",
        ai_feedback: "AI feedback · unverified",
      }[s.kind],
      kind: s.kind,
    })),
  ]
    .sort((a, b) => b.at.localeCompare(a.at))
    .slice(0, 5);
  const last = progress.sessions.filter((s) => s.kind === "reading").at(-1);
  return (
    <div className="page dashboard">
      <PageHeading
        eyebrow="YOUR RESEARCH WORKSPACE"
        title="Build foundations. Go further."
        description="Every step forward starts with something you truly understand."
      >
        <Link className="button" href="/paths">
          <GitBranch size={16} />
          My learning path
        </Link>
      </PageHeading>
      <div className="dashboard-grid">
        <section className="focus-card">
          <div className="section-kicker">
            <span className="accent-dot" />
            NEXT ACTION <span className="priority-pill">FOUNDATION FIRST</span>
          </div>
          {topic && rec ? (
            <>
              <div className="focus-title">
                <span className="topic-code">{topic.id}</span>
                <h2>{topic.title}</h2>
              </div>
              <p className="focus-description">{rec.reason}</p>
              <div className="reason-box">
                <Target size={17} />
                <div>
                  <strong>Why this lesson?</strong>
                  <p>{rec.exercise}</p>
                </div>
              </div>
              <div className="focus-bottom">
                <Link
                  className="button primary"
                  href={
                    rec.weaknessKey
                      ? weaknessUrl(
                          rec.topicId,
                          rec.weaknessKey.split(":")[1],
                        ) + "#targeted-practice"
                      : rec.kind === "assess" || rec.kind === "review"
                        ? `/assessments/${topic.id}`
                        : rec.kind === "practice"
                          ? `/practice?topic=${topic.id}`
                          : `/lessons/${topic.id}`
                  }
                >
                  {rec.weaknessKey
                    ? "Practice weak skill"
                    : rec.kind === "review"
                      ? "Review now"
                      : rec.kind === "assess"
                        ? "Start diagnostic"
                        : "Continue learning"}
                  <ArrowRight size={17} />
                </Link>
                <span className="muted small">
                  <Clock3 size={14} />
                  Progress by competence, at your own pace
                </span>
              </div>
            </>
          ) : (
            <>
              <h2>Your next foundation</h2>
              <p>
                No authored lesson currently matches your verified
                prerequisites. Open the Roadmap to choose a foundation to work
                on.
              </p>
              <Link className="button primary" href="/roadmap">
                Open Roadmap
                <ArrowRight size={16} />
              </Link>
            </>
          )}
        </section>
        <section className="panel focus-aside">
          <div className="panel-heading">
            <h2>Your starting point</h2>
            <ShieldCheck size={18} />
          </div>
          <p className="muted small">
            Competence is recorded through evidence.
          </p>
          <div className="evidence-stat">
            <strong>{verified.length}</strong>
            <span>
              {verified.length === 1
                ? "topic with evidence"
                : "topics with evidence"}
              <br />
              <small>across {topics.length} topics</small>
            </span>
          </div>
          <div className="aside-stat">
            <span>Topics attempted</span>
            <strong>
              {attempted.size} {attempted.size === 1 ? "topic" : "topics"}
            </strong>
          </div>
          <div className="aside-stat">
            <span>Reviews due</span>
            <strong>
              {due.length} {due.length === 1 ? "topic" : "topics"}
            </strong>
          </div>
          <div className="quiet-note">
            {verified.length
              ? "Check C/M/I/T to see exactly which evidence you have."
              : "Unassessed is a starting point, not a score of zero."}
          </div>
        </section>
      </div>
      <div className="section-title">
        <h2>Competency map</h2>
        <Link href="/roadmap">
          View full Roadmap
          <ArrowUpRight size={15} />
        </Link>
      </div>
      <section className="panel domain-table">
        <div className="table-head">
          <span>DOMAIN</span>
          <span>EVIDENCE</span>
          <span>STATUS</span>
        </div>
        {domains.map((d, i) => {
          const ts = topics.filter((t) => t.domain === d),
            vs = ts.filter((t) => mastery[t.id].level > 0);
          return (
            <Link
              className="domain-row"
              href={`/roadmap?domain=${encodeURIComponent(d)}`}
              key={d}
            >
              <span>
                <span className="domain-index">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <strong>{d}</strong>
              </span>
              <span className="muted small">
                {vs.length
                  ? `${vs.length} verified ${vs.length === 1 ? "topic" : "topics"}`
                  : "No evidence yet"}
              </span>
              <span className={vs.length ? "verified-text small" : "status"}>
                {vs.length ? "Evidence available" : "Unassessed"}
                <ChevronRight size={14} />
              </span>
            </Link>
          );
        })}
      </section>
      <div className="two-columns">
        <section className="panel">
          <div className="panel-heading">
            <h2>Weaknesses to Review</h2>
            <GitBranch size={18} />
          </div>
          {weaknesses.length ? (
            <div className="stack">
              {weaknesses.slice(0, 3).map((w) => (
                <div className="dashboard-weakness" key={w.key}>
                  <strong>
                    {w.topicId} · {w.skillLabel}
                  </strong>
                  <span className="small muted">
                    {w.failureCount} mistakes · {w.failedAttempts} failed
                    attempts
                  </span>
                  <WeaknessStatus weakness={w} />
                </div>
              ))}
            </div>
          ) : (
            <p className="small muted">
              {progress.attempts.length
                ? "No active objective weaknesses. Historical mistakes remain available in Practice."
                : "Not enough evidence yet. Objective assessment mistakes will appear here; ungraded responses never count as errors."}
            </p>
          )}
          <Link
            className="text-link weakness-dashboard-action"
            href={weaknessUrl(weaknesses[0]?.topicId, weaknesses[0]?.skillTag)}
          >
            Practice Weaknesses
            <ArrowRight size={14} />
          </Link>
          {due.length > 0 && (
            <div className="review-block">
              <strong className="warning-text">Review due</strong>
              {due.slice(0, 3).map((r) => (
                <Link href={`/assessments/${r.topicId}`} key={r.topicId}>
                  {r.topicId} · {topicMap[r.topicId].title}
                  <ArrowRight size={14} />
                </Link>
              ))}
            </div>
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Recent activity</h2>
            <Clock3 size={18} />
          </div>
          {recent.length ? (
            <div className="activity-list">
              {recent.map((item) => (
                <Link href={`/assessments/${item.topicId}`} key={item.id}>
                  <span className="activity-dot" />
                  <div>
                    <strong>
                      {item.topicId} · {item.text}
                    </strong>
                    <small>{dateText(item.at)}</small>
                  </div>
                  <ChevronRight size={14} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-inline">
              <BookOpen size={23} />
              <p>
                Your workspace is ready.
                <br />
                Start with one small question.
              </p>
              <Link href="/lessons/M01">
                Open your first lesson
                <ArrowRight size={14} />
              </Link>
            </div>
          )}
        </section>
      </div>
      {last && (
        <section className="resume-line">
          <BookOpen size={18} />
          <div>
            <strong>
              Return to {last.topicId} · {topicMap[last.topicId].title}
            </strong>
            <span>
              Read · {dateText(last.at)} · reading does not increase mastery
            </span>
          </div>
          <Link className="button" href={`/lessons/${last.topicId}`}>
            Continue
            <ArrowRight size={15} />
          </Link>
        </section>
      )}
      {verified.length > 0 && (
        <section className="panel">
          <h2>Evidence-backed strengths</h2>
          <div className="stack">
            {verified.slice(0, 4).map((t) => (
              <div className="between" key={t.id}>
                <Link href={`/assessments/${t.id}`}>
                  {t.id} · {t.title}
                </Link>
                <Status mastery={mastery[t.id]} />
              </div>
            ))}
          </div>
        </section>
      )}
      <div className="quick-actions">
        <Link href="/practice">
          <FlaskConical size={20} />
          <div>
            <strong>Implement & test independently</strong>
            <span>Practice outside the browser, at your own pace.</span>
          </div>
          <ArrowUpRight size={18} />
        </Link>
        <Link href="/tutor">
          <Target size={20} />
          <div>
            <strong>Take your questions to AI Tutor</strong>
            <span>Copy the context; keep the evidence in CoreLab.</span>
          </div>
          <ArrowUpRight size={18} />
        </Link>
      </div>
      {recommendations.length > 1 && (
        <details className="secondary-recs">
          <summary>
            Suitable parallel learning branches ({recommendations.length - 1})
          </summary>
          {recommendations.slice(1).map((r) => (
            <div key={r.topicId}>
              <Link href={`/lessons/${r.topicId}`}>
                {r.topicId} · {topicMap[r.topicId].title}
              </Link>
              <p>{r.reason}</p>
              <TopicChips ids={r.prerequisites} />
            </div>
          ))}
        </details>
      )}
    </div>
  );
}
