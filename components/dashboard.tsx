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
  Sigma,
  Code2,
  BrainCircuit,
  ScanEye,
  Bot,
  Workflow,
  Network,
  Microscope,
  Compass,
  RotateCcw,
} from "lucide-react";
import { domainTone } from "./domain-theme";
import { RoboticsConcept } from "./robotics-concept";
import { useCore, Loading } from "./provider";
import { PageHeading, Status, dateText, TopicChips } from "./ui";
import { weaknessUrl } from "@/lib/weaknesses";
import { WeaknessStatus } from "./weakness-practice";
import { domains, topics, topicMap } from "@/lib/curriculum";
const domainDetails = {
  Mathematics: {
    Icon: Sigma,
    description: "The language of motion and uncertainty.",
  },
  Programming: {
    Icon: Code2,
    description: "Turn ideas into reliable algorithms.",
  },
  "Machine Learning": {
    Icon: BrainCircuit,
    description: "Patterns, losses and generalization.",
  },
  "Computer Vision": {
    Icon: ScanEye,
    description: "Connect pixels to geometry.",
  },
  Robotics: {
    Icon: Bot,
    description: "Frames, motion, estimation and control.",
  },
  "Reinforcement & Robot Learning": {
    Icon: Workflow,
    description: "Make decisions from rewards and dynamics.",
  },
  "Embodied & Cognitive Robotics": {
    Icon: Network,
    description: "Connect perception, memory and action.",
  },
  "Scientific Research": {
    Icon: Microscope,
    description: "Design experiments. Question results.",
  },
};
export function Dashboard({ v2Enabled = false }: { v2Enabled?: boolean }) {
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
        eyebrow="YOUR ROBOTICS & AI LEARNING LAB"
        title="Your Robotics & AI journey."
        description="Understand the foundations. Build the algorithms. Discover what you can do independently."
      >
        <Link className="button" href="/paths">
          <GitBranch size={16} />
          My learning path
        </Link>
      </PageHeading>
      <div className="dashboard-grid dashboard-launch">
        <section
          className="focus-card"
          data-domain-tone={domainTone(topic?.domain)}
        >
          <div className="section-kicker">
            <span className="accent-dot" />
            YOUR NEXT STEP
            <span className="priority-pill">
              {rec
                ? {
                    learn: "LEARN",
                    assess: "DIAGNOSTIC",
                    practice: "PRACTICE",
                    review: "REVIEW",
                  }[rec.kind]
                : "EXPLORE"}
            </span>
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
                  <strong>Try this next</strong>
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
        <section
          className="dashboard-lab-card"
          aria-labelledby="dashboard-lab-title"
        >
          <div className="eyebrow">FROM FIRST PRINCIPLES TO ROBOT BEHAVIOR</div>
          <RoboticsConcept idPrefix="dashboard-concept" />
          <div className="dashboard-lab-caption">
            <h2 id="dashboard-lab-title">Make the connection.</h2>
            <Link
              className="button"
              href={v2Enabled ? "/objectives" : "/roadmap"}
            >
              <Compass size={18} aria-hidden="true" />
              {v2Enabled
                ? "Open Robotics & AI lab"
                : "Explore Robotics & AI curriculum"}
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
            {v2Enabled && (
              <small>
                Objective practice and C/M checks have their own evidence
                record.
              </small>
            )}
          </div>
        </section>
      </div>
      <section
        className="dashboard-evidence"
        aria-label="Your topic learning evidence"
      >
        <dl>
          <div>
            <dt>
              <ShieldCheck size={18} aria-hidden="true" /> Topics with evidence
            </dt>
            <dd data-testid="dashboard-evidence-count">
              {verified.length}
              <span>of {topics.length} curriculum topics</span>
            </dd>
          </div>
          <div>
            <dt>
              <Target size={18} aria-hidden="true" /> Topics attempted
            </dt>
            <dd data-testid="dashboard-attempted-count">
              {attempted.size}
              <span>through topic assessments</span>
            </dd>
          </div>
          <div>
            <dt>
              <RotateCcw size={18} aria-hidden="true" /> Topic reviews due
            </dt>
            <dd data-testid="dashboard-due-count">
              {due.length}
              <span>return when it is time to retrieve</span>
            </dd>
          </div>
        </dl>
        <p>
          {verified.length
            ? "Topic evidence reflects your recorded C/M/I/T checks; reading and practice do not automatically increase mastery."
            : "Unassessed is a starting point, not a score of zero."}
        </p>
      </section>
      <div className="section-title dashboard-directions-heading">
        <div>
          <div className="eyebrow">EXPLORE YOUR INTERESTS</div>
          <h2>Where will you go next?</h2>
        </div>
        <Link href="/roadmap">
          Full curriculum <ArrowUpRight size={16} />
        </Link>
      </div>
      <p className="dashboard-directions-note">
        Start with a foundation or follow your curiosity. The roadmap includes
        future topics; authored lessons are counted separately.
      </p>
      <section className="dashboard-domains" aria-label="Curriculum directions">
        {domains.map((d) => {
          const ts = topics.filter((t) => t.domain === d);
          const vs = ts.filter((t) => mastery[t.id].level > 0);
          const lessons = ts.filter((t) =>
            state.lessonIds.includes(t.id),
          ).length;
          const detail = domainDetails[d as keyof typeof domainDetails];
          const Icon = detail?.Icon ?? Compass;
          return (
            <Link
              className="dashboard-domain-card"
              data-domain-tone={domainTone(d)}
              href={`/roadmap?domain=${encodeURIComponent(d)}`}
              key={d}
            >
              <div className="dashboard-domain-top">
                <span className="dashboard-domain-icon">
                  <Icon size={24} aria-hidden="true" />
                </span>
                <ArrowUpRight size={17} aria-hidden="true" />
              </div>
              <h3>{d}</h3>
              <p>
                {detail?.description ?? "Explore this part of the curriculum."}
              </p>
              <div className="dashboard-domain-meta">
                <span>{ts.length} curriculum topics</span>
                <span>
                  {lessons} authored {lessons === 1 ? "lesson" : "lessons"}
                </span>
              </div>
              {vs.length > 0 && (
                <span className="dashboard-domain-evidence">
                  <ShieldCheck size={14} aria-hidden="true" /> {vs.length}{" "}
                  {vs.length === 1 ? "topic has" : "topics have"} evidence
                </span>
              )}
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
                <Link
                  href={
                    item.kind === "assessment"
                      ? `/assessments/${item.topicId}`
                      : `/lessons/${item.topicId}`
                  }
                  key={item.id}
                >
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
