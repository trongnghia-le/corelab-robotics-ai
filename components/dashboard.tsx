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
import { useI18n, localizeRecommendation, type Dict } from "@/lib/i18n";
import { isCheckoff, parseCheckoff } from "@/lib/checkoff";
type DomKey = Extract<keyof Dict, `dom.${string}`>;
const domainDetails: Record<
  string,
  { Icon: typeof Sigma; description: DomKey }
> = {
  Mathematics: {
    Icon: Sigma,
    description: "dom.Mathematics",
  },
  Programming: {
    Icon: Code2,
    description: "dom.Programming",
  },
  "Machine Learning": {
    Icon: BrainCircuit,
    description: "dom.Machine Learning",
  },
  "Computer Vision": {
    Icon: ScanEye,
    description: "dom.Computer Vision",
  },
  Robotics: {
    Icon: Bot,
    description: "dom.Robotics",
  },
  "Reinforcement & Robot Learning": {
    Icon: Workflow,
    description: "dom.Reinforcement & Robot Learning",
  },
  "Embodied & Cognitive Robotics": {
    Icon: Network,
    description: "dom.Embodied & Cognitive Robotics",
  },
  "Scientific Research": {
    Icon: Microscope,
    description: "dom.Scientific Research",
  },
};
export function Dashboard({ v2Enabled = false }: { v2Enabled?: boolean }) {
  const { state, title } = useCore();
  const { t, tx, lang } = useI18n();
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
      text: `${a.purpose === "targeted" ? t("dash.act.focused") : t("dash.act.check")} · ${a.grade.items.some((i) => i.correct !== null) ? `${a.grade.score}%` : t("assess.rubricOnly")} · ${a.assistance}`,
      kind: "assessment",
    })),
    ...progress.sessions.map((s) => ({
      id: s.id,
      topicId: s.topicId,
      at: s.at,
      text: isCheckoff(s)
        ? parseCheckoff(s.text)?.done
          ? t("dash.act.sessionDone", {
              name: t(`session.${parseCheckoff(s.text)!.key}`),
            })
          : t("dash.act.sessionUndone", {
              name: t(`session.${parseCheckoff(s.text)!.key}`),
            })
        : {
            reading: t("dash.act.read"),
            practice: t("dash.act.practice"),
            note: t("dash.act.note"),
            difficulty: t("dash.act.difficulty"),
            self_assessment: t("dash.act.self"),
            ai_feedback: t("dash.act.ai"),
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
        eyebrow={t("dash.eyebrow")}
        title={t("dash.title")}
        description={t("dash.desc")}
      >
        <Link className="button" href="/paths">
          <GitBranch size={16} />
          {t("dash.myPath")}
        </Link>
      </PageHeading>
      <div className="dashboard-grid dashboard-launch">
        <section
          className="focus-card"
          data-domain-tone={domainTone(topic?.domain)}
        >
          <div className="section-kicker">
            <span className="accent-dot" />
            {t("dash.next")}
            <span className="priority-pill">
              {rec
                ? {
                    learn: t("dash.kind.learn"),
                    assess: t("dash.kind.assess"),
                    practice: t("dash.kind.practice"),
                    review: t("dash.kind.review"),
                  }[rec.kind]
                : t("dash.kind.explore")}
            </span>
          </div>
          {topic && rec ? (
            <>
              <div className="focus-title">
                <span className="topic-code">{topic.id}</span>
                <h2>{title(topic.id)}</h2>
              </div>
              <p className="focus-description">
                {localizeRecommendation(rec.reason, lang)}
              </p>
              <div className="reason-box">
                <Target size={17} />
                <div>
                  <strong>{t("dash.tryNext")}</strong>
                  <p>{localizeRecommendation(rec.exercise, lang)}</p>
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
                    ? t("dash.cta.weak")
                    : rec.kind === "review"
                      ? t("dash.cta.review")
                      : rec.kind === "assess"
                        ? t("dash.cta.assess")
                        : t("dash.cta.learn")}
                  <ArrowRight size={17} />
                </Link>
                <span className="muted small">
                  <Clock3 size={14} />
                  {t("dash.pace")}
                </span>
              </div>
            </>
          ) : (
            <>
              <h2>{t("dash.noRec.title")}</h2>
              <p>{t("dash.noRec.body")}</p>
              <Link className="button primary" href="/roadmap">
                {t("dash.openRoadmap")}
                <ArrowRight size={16} />
              </Link>
            </>
          )}
        </section>
        <section
          className="dashboard-lab-card"
          aria-labelledby="dashboard-lab-title"
        >
          <div className="eyebrow">{t("dash.labEyebrow")}</div>
          <RoboticsConcept idPrefix="dashboard-concept" />
          <div className="dashboard-lab-caption">
            <h2 id="dashboard-lab-title">{t("dash.labTitle")}</h2>
            <Link
              className="button"
              href={v2Enabled ? "/objectives" : "/roadmap"}
            >
              <Compass size={18} aria-hidden="true" />
              {v2Enabled ? t("dash.openLab") : t("dash.exploreCurriculum")}
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
            {v2Enabled && <small>{t("dash.labNote")}</small>}
          </div>
        </section>
      </div>
      <section
        className="dashboard-evidence"
        aria-label={t("dash.progressLabel")}
      >
        <dl>
          <div>
            <dt>
              <ShieldCheck size={18} aria-hidden="true" /> {t("dash.mastered")}
            </dt>
            <dd data-testid="dashboard-evidence-count">
              {verified.length}
              <span>{t("dash.ofTopics", { n: topics.length })}</span>
            </dd>
          </div>
          <div>
            <dt>
              <Target size={18} aria-hidden="true" /> {t("dash.attempted")}
            </dt>
            <dd data-testid="dashboard-attempted-count">
              {attempted.size}
              <span>{t("dash.throughChecks")}</span>
            </dd>
          </div>
          <div>
            <dt>
              <RotateCcw size={18} aria-hidden="true" /> {t("dash.due")}
            </dt>
            <dd data-testid="dashboard-due-count">
              {due.length}
              <span>{t("dash.dueNote")}</span>
            </dd>
          </div>
        </dl>
        <p>{verified.length ? t("dash.evidenceNote") : t("dash.startNote")}</p>
      </section>
      <div className="section-title dashboard-directions-heading">
        <div>
          <div className="eyebrow">{t("dash.exploreEyebrow")}</div>
          <h2>{t("dash.exploreTitle")}</h2>
        </div>
        <Link href="/roadmap">
          {t("dash.fullCurriculum")} <ArrowUpRight size={16} />
        </Link>
      </div>
      <p className="dashboard-directions-note">{t("dash.exploreNote")}</p>
      <section
        className="dashboard-domains"
        aria-label={tx("Curriculum directions", "Các hướng trong chương trình")}
      >
        {domains.map((d) => {
          const ts = topics.filter((t) => t.domain === d);
          const vs = ts.filter((t) => mastery[t.id].level > 0);
          const lessons = ts.filter((t) =>
            state.lessonIds.includes(t.id),
          ).length;
          const detail = domainDetails[d];
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
              <p>{detail ? t(detail.description) : t("dash.domainDefault")}</p>
              <div className="dashboard-domain-meta">
                <span>{t("dash.curriculumTopics", { n: ts.length })}</span>
                <span>
                  {t(lessons === 1 ? "dash.lesson1" : "dash.lessonN", {
                    n: lessons,
                  })}
                </span>
              </div>
              {vs.length > 0 && (
                <span className="dashboard-domain-evidence">
                  <ShieldCheck size={14} aria-hidden="true" />{" "}
                  {t(vs.length === 1 ? "dash.masteredN1" : "dash.masteredN", {
                    n: vs.length,
                  })}
                </span>
              )}
            </Link>
          );
        })}
      </section>
      <div className="two-columns">
        <section className="panel">
          <div className="panel-heading">
            <h2>{t("dash.weak")}</h2>
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
                    {t("dash.weakCounts", {
                      m: w.failureCount,
                      a: w.failedAttempts,
                    })}
                  </span>
                  <WeaknessStatus weakness={w} />
                </div>
              ))}
            </div>
          ) : (
            <p className="small muted">
              {progress.attempts.length
                ? t("dash.noWeak")
                : t("dash.noWeakYet")}
            </p>
          )}
          <Link
            className="text-link weakness-dashboard-action"
            href={weaknessUrl(weaknesses[0]?.topicId, weaknesses[0]?.skillTag)}
          >
            {t("assess.practiceWeak")}
            <ArrowRight size={14} />
          </Link>
          {due.length > 0 && (
            <div className="review-block">
              <strong className="warning-text">{t("status.reviewDue")}</strong>
              {due.slice(0, 3).map((r) => (
                <Link href={`/assessments/${r.topicId}`} key={r.topicId}>
                  {r.topicId} · {title(r.topicId)}
                  <ArrowRight size={14} />
                </Link>
              ))}
            </div>
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>{t("dash.recent")}</h2>
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
                {t("dash.ready1")}
                <br />
                {t("dash.ready2")}
              </p>
              <Link href="/lessons/M01">
                {t("dash.firstLesson")}
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
              {t("dash.return")} {last.topicId} · {title(last.topicId)}
            </strong>
            <span>
              {t("dash.readOn")} {dateText(last.at)}
            </span>
          </div>
          <Link className="button" href={`/lessons/${last.topicId}`}>
            {t("dash.continue")}
            <ArrowRight size={15} />
          </Link>
        </section>
      )}
      {verified.length > 0 && (
        <section className="panel">
          <h2>{t("dash.strengths")}</h2>
          <div className="stack">
            {verified.slice(0, 4).map((t) => (
              <div className="between" key={t.id}>
                <Link href={`/assessments/${t.id}`}>
                  {t.id} · {title(t.id)}
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
            <strong>{t("dash.q1")}</strong>
            <span>{t("dash.q1b")}</span>
          </div>
          <ArrowUpRight size={18} />
        </Link>
        <Link href="/tutor">
          <Target size={20} />
          <div>
            <strong>{t("dash.q2")}</strong>
            <span>{t("dash.q2b")}</span>
          </div>
          <ArrowUpRight size={18} />
        </Link>
      </div>
      {recommendations.length > 1 && (
        <details className="secondary-recs">
          <summary>
            {t("dash.branches", { n: recommendations.length - 1 })}
          </summary>
          {recommendations.slice(1).map((r) => (
            <div key={r.topicId}>
              <Link href={`/lessons/${r.topicId}`}>
                {r.topicId} · {title(r.topicId)}
              </Link>
              <p>{localizeRecommendation(r.reason, lang)}</p>
              <TopicChips ids={r.prerequisites} />
            </div>
          ))}
        </details>
      )}
    </div>
  );
}
