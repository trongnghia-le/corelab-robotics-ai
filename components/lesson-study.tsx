"use client";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowRight,
  BookOpen,
  Check,
  Circle,
  FlaskConical,
  Hammer,
  ListTree,
  RotateCcw,
  Target,
  FileText,
  Eye,
  EyeOff,
} from "lucide-react";
import type { Lesson, TopicPayload } from "@/lib/types";
import {
  lessonPlan,
  type LessonSection,
  type LessonSession,
  type SessionKey,
} from "@/lib/lesson-plan";
import {
  checkoffKind,
  checkoffText,
  doneCount,
  sessionProgress,
} from "@/lib/checkoff";
import { formatDuration, useI18n, type Dict } from "@/lib/i18n";
import { headingId } from "./lesson-sections";
import { useCore } from "./provider";
import { LessonMedia } from "./lesson-media";
import { LearningVisual } from "./learning-visual";

const LessonMarkdown = dynamic(
  () => import("./markdown").then((m) => m.LessonMarkdown),
  { loading: () => <p>…</p> },
);

const sessionIcon = {
  learn: BookOpen,
  practice: FlaskConical,
  build: Hammer,
  review: RotateCcw,
} as const;

const nameKey = {
  learn: "session.learn",
  practice: "session.practice",
  build: "session.build",
  review: "session.review",
} as const satisfies Record<SessionKey, keyof Dict>;

/** Sections whose anchors live outside the Markdown body belong to Learn. */
function sessionForId(
  sessions: LessonSession[],
  id: string,
): SessionKey | null {
  if (
    id === "lesson-media" ||
    id === "lesson-theory" ||
    id.startsWith("explore-")
  )
    return "learn";
  for (const s of sessions)
    for (const sec of s.sections)
      if (headingId(sec.englishHeading ?? sec.heading) === id) return s.key;
  return null;
}

export function SessionProgressBar({
  topicId,
  sessionCount,
}: {
  topicId: string;
  sessionCount: number;
}) {
  const { state } = useCore();
  const { t } = useI18n();
  const done = doneCount(
    sessionProgress(state?.progress.sessions ?? [], topicId),
  );
  return (
    <div className="session-progress">
      <div
        className="session-progress-bar"
        role="progressbar"
        aria-label={t("lesson.progress")}
        aria-valuemin={0}
        aria-valuemax={sessionCount}
        aria-valuenow={done}
      >
        <span style={{ width: `${(done / sessionCount) * 100}%` }} />
      </div>
      <span className="small muted">
        {t("lesson.sessionsDone", { n: done, total: sessionCount })}
      </span>
    </div>
  );
}

function AnswersGate({
  open,
  onToggle,
  section,
  ids,
  numbers,
  illustrations,
}: {
  open: boolean;
  onToggle: () => void;
  section: LessonSection;
  ids: string[];
  numbers: number[];
  illustrations: NonNullable<TopicPayload["media"]>["illustrations"];
}) {
  const { t } = useI18n();
  return (
    <div className="answers-gate">
      {open ? (
        <LessonMarkdown
          body={section.markdown}
          illustrations={illustrations}
          headingIds={ids}
          numbers={numbers}
        />
      ) : (
        <div id="exercise-answers" className="answers-gate-closed">
          <p>{t("lesson.answersHidden")}</p>
        </div>
      )}
      <button
        type="button"
        className="button"
        aria-expanded={open}
        onClick={onToggle}
      >
        {open ? <EyeOff size={15} /> : <Eye size={15} />}
        {open ? t("lesson.hideAnswers") : t("lesson.showAnswers")}
      </button>
    </div>
  );
}

/** Runs of consecutive non-answer sections render together; answers are gated. */
function SessionBody({
  session,
  illustrations,
  answersOpen,
  onToggleAnswers,
}: {
  session: LessonSession;
  illustrations: NonNullable<TopicPayload["media"]>["illustrations"];
  answersOpen: boolean;
  onToggleAnswers: () => void;
}) {
  const runs: { gated: boolean; sections: LessonSection[] }[] = [];
  for (const s of session.sections) {
    const gated =
      headingId(s.englishHeading ?? s.heading) === "exercise-answers";
    const last = runs.at(-1);
    if (last && !gated && !last.gated) last.sections.push(s);
    else runs.push({ gated, sections: [s] });
  }
  return (
    <>
      {runs.map((run) => {
        const ids = run.sections.map((s) =>
          headingId(s.englishHeading ?? s.heading),
        );
        const numbers = run.sections.map((s) => s.index + 1);
        return run.gated ? (
          <AnswersGate
            key={run.sections[0].index}
            open={answersOpen}
            onToggle={onToggleAnswers}
            section={run.sections[0]}
            ids={ids}
            numbers={numbers}
            illustrations={illustrations}
          />
        ) : (
          <LessonMarkdown
            key={run.sections[0].index}
            body={run.sections.map((s) => s.markdown).join("\n")}
            illustrations={illustrations}
            headingIds={ids}
            numbers={numbers}
          />
        );
      })}
    </>
  );
}

export function LessonReader({
  id,
  lesson,
  media,
  objectives,
  sessions: providedSessions,
  after,
}: {
  id: string;
  lesson: Lesson;
  media: TopicPayload["media"];
  objectives: string[];
  sessions?: LessonSession[];
  after?: ReactNode;
}) {
  const { state, act, busy, notify } = useCore();
  const { t, lang } = useI18n();
  const sessions = useMemo(
    () => providedSessions ?? lessonPlan(lesson).sessions,
    [providedSessions, lesson],
  );
  const [active, setActive] = useState<SessionKey>(() => {
    if (typeof window === "undefined") return sessions[0].key;
    const key = sessionForId(
      sessions,
      decodeURIComponent(location.hash.slice(1)),
    );
    return key && sessions.some((s) => s.key === key) ? key : sessions[0].key;
  });
  const [answersOpen, setAnswersOpen] = useState(
    () =>
      typeof window !== "undefined" && location.hash === "#exercise-answers",
  );
  const [tocOpen, setTocOpen] = useState(false);
  const stepperRef = useRef<HTMLElement>(null);
  const pending = useRef<string | null>(null);
  const tocButton = useRef<HTMLButtonElement>(null);
  const current = sessions.find((s) => s.key === active) ?? sessions[0];
  const progress = sessionProgress(state?.progress.sessions ?? [], id);

  const scrollWhenReady = useCallback((target: string) => {
    pending.current = target;
    let tries = 0;
    const timer = setInterval(() => {
      const el = document.getElementById(target);
      if (el || ++tries > 40) {
        clearInterval(timer);
        if (el && pending.current === target) {
          el.scrollIntoView({ block: "start" });
          pending.current = null;
        }
      }
    }, 75);
    return () => clearInterval(timer);
  }, []);

  const openAnchor = useCallback(
    (target: string) => {
      const key = sessionForId(sessions, target);
      if (!key) return false;
      if (target === "exercise-answers") setAnswersOpen(true);
      setActive(key);
      scrollWhenReady(target);
      return true;
    },
    [sessions, scrollWhenReady],
  );

  useEffect(() => {
    const onHash = () => {
      const target = decodeURIComponent(location.hash.slice(1));
      if (target) openAnchor(target);
    };
    onHash();
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [openAnchor]);

  useEffect(() => {
    if (!tocOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setTocOpen(false);
        tocButton.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [tocOpen]);

  function choose(key: SessionKey) {
    setActive(key);
    history.replaceState(null, "", location.pathname + location.search);
    stepperRef.current?.scrollIntoView({ block: "start" });
  }

  function jump(target: string, e: React.MouseEvent) {
    setTocOpen(false);
    if (openAnchor(target)) {
      e.preventDefault();
      history.replaceState(null, "", `#${target}`);
    }
  }

  async function toggle(key: SessionKey, minutes: number) {
    const done = !progress[key];
    try {
      await act({
        type: "session",
        topicId: id,
        kind: checkoffKind(key),
        text: checkoffText(id, key, done),
        minutes: done ? minutes : 0,
      });
      notify(done ? t("lesson.savedDone") : t("lesson.savedUndone"));
    } catch {}
  }

  const index = sessions.findIndex((s) => s.key === current.key);
  const next = sessions[index + 1];
  const Icon = sessionIcon[current.key];
  const tocGroups = sessions.map((s) => ({
    key: s.key,
    items: s.sections.map((sec) => ({
      id: headingId(sec.englishHeading ?? sec.heading),
      label: sec.heading.split(" · ")[0],
    })),
  }));

  return (
    <>
      <nav
        ref={stepperRef}
        className="session-stepper"
        aria-label={t("lesson.sessions")}
      >
        <ol>
          {sessions.map((s, i) => {
            const StepIcon = sessionIcon[s.key];
            return (
              <li key={s.key}>
                <button
                  type="button"
                  className={`session-step ${s.key === current.key ? "active" : ""} ${progress[s.key] ? "done" : ""}`}
                  aria-current={s.key === current.key ? "step" : undefined}
                  onClick={() => choose(s.key)}
                >
                  <span className="session-step-mark" aria-hidden="true">
                    {progress[s.key] ? <Check size={14} /> : i + 1}
                  </span>
                  <span className="session-step-text">
                    <strong>
                      <StepIcon size={14} aria-hidden="true" />{" "}
                      {t(nameKey[s.key])}
                    </strong>
                    <small>≈ {formatDuration(s.minutes, lang)}</small>
                  </span>
                  {progress[s.key] && (
                    <span className="sr-only"> ({t("lesson.done")})</span>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
        <button
          ref={tocButton}
          type="button"
          className="button toc-toggle"
          aria-expanded={tocOpen}
          aria-controls="lesson-toc"
          onClick={() => setTocOpen((o) => !o)}
        >
          <ListTree size={15} aria-hidden="true" />
          {t("lesson.contents")}
        </button>
      </nav>
      {lesson.missingTranslation && (
        <p className="info-banner" role="note">
          {t("lesson.notTranslated")}
        </p>
      )}
      <div className="reading-layout">
        <article className="lesson-article">
          {current.key === "learn" && (
            <div className="objectives-box">
              <div className="eyebrow">{t("lesson.after")}</div>
              <ul>
                {objectives.map((o) => (
                  <li key={o}>
                    <Target size={16} aria-hidden="true" />
                    {o}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <header className="session-header">
            <Icon size={20} aria-hidden="true" />
            <h2 className="session-title">
              {t("lesson.sessionOf", {
                n: index + 1,
                total: sessions.length,
                name: t(nameKey[current.key]),
              })}
            </h2>
            <span className="time">
              ≈ {formatDuration(current.minutes, lang)}
            </span>
          </header>
          {current.key === "learn" && media && (
            <LessonMedia key={id} media={media} />
          )}
          {current.key === "learn" && (
            <LearningVisual
              key={`visual-${id}`}
              topicId={id}
              ids={media?.visualizations}
            />
          )}
          <div id="lesson-theory">
            <SessionBody
              session={current}
              illustrations={media?.illustrations ?? []}
              answersOpen={answersOpen}
              onToggleAnswers={() => setAnswersOpen((o) => !o)}
            />
          </div>
          <div className="session-footer">
            <button
              type="button"
              className={`button ${progress[current.key] ? "" : "primary"}`}
              aria-pressed={progress[current.key]}
              disabled={busy}
              onClick={() => void toggle(current.key, current.minutes)}
            >
              {progress[current.key] ? (
                <Check size={16} />
              ) : (
                <Circle size={16} />
              )}
              {current.key === "build"
                ? t("lesson.labDone")
                : t("lesson.markDone")}
            </button>
            {next && (
              <button
                type="button"
                className="button"
                onClick={() => choose(next.key)}
              >
                {t("lesson.next", { name: t(nameKey[next.key]) })}
                <ArrowRight size={16} />
              </button>
            )}
            {!next && (
              <Link className="button primary" href={`/assessments/${id}`}>
                {t("lesson.testYourself")}
                <ArrowRight size={16} />
              </Link>
            )}
          </div>
          <p className="small muted">{t("lesson.readingNote")}</p>
          {after}
        </article>
        <aside
          id="lesson-toc"
          className={`lesson-toc ${tocOpen ? "is-open" : ""}`}
          aria-label={t("lesson.contents")}
        >
          <div className="eyebrow">{t("lesson.inThis")}</div>
          {media && (
            <a href="#lesson-media" onClick={(e) => jump("lesson-media", e)}>
              {t("lesson.video")}
            </a>
          )}
          {!!media?.visualizations.length && (
            <a
              href={`#explore-${media.visualizations[0]}`}
              onClick={(e) => jump(`explore-${media.visualizations[0]}`, e)}
            >
              {t("lesson.interactive")}
            </a>
          )}
          {tocGroups.map((g) => (
            <div className="toc-group" key={g.key}>
              <div className="toc-group-name">
                {progress[g.key] && <Check size={12} aria-hidden="true" />}{" "}
                {t(nameKey[g.key])}
              </div>
              {g.items.map((item) => (
                <a
                  href={`#${item.id}`}
                  key={item.id}
                  onClick={(e) => jump(item.id, e)}
                >
                  {item.label}
                </a>
              ))}
            </div>
          ))}
          <div className="toc-note">
            <FileText size={18} />
            <p>{t("lesson.flow")}</p>
          </div>
        </aside>
      </div>
    </>
  );
}
