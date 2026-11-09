"use client";
import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Search,
  List,
  Network,
  BookOpen,
  ArrowUpRight,
  ChevronRight,
} from "lucide-react";
import { domainTone } from "./domain-theme";
import { topics, domains } from "@/lib/curriculum";
import { useCore, Loading } from "./provider";
import { PageHeading, Status } from "./ui";
import { useI18n } from "@/lib/i18n";
import { allSessionProgress, doneCount } from "@/lib/checkoff";
import { sessionOrder } from "@/lib/lesson-plan";
const Graph = dynamic(() => import("./graph").then((m) => m.Graph), {
  ssr: false,
  loading: () => <div className="graph-loading">…</div>,
});
export function Catalog({
  mode,
}: {
  mode: "roadmap" | "lessons" | "assessments";
}) {
  const { state, title } = useCore();
  const { t, tx } = useI18n();
  const params = useSearchParams();
  const sessionsDone = useMemo(
    () => allSessionProgress(state?.progress.sessions ?? []),
    [state?.progress.sessions],
  );
  const [query, setQuery] = useState(""),
    [domain, setDomain] = useState(params.get("domain") ?? ""),
    [priority, setPriority] = useState(""),
    [status, setStatus] = useState(""),
    [view, setView] = useState<"list" | "graph">("list");
  if (!state) return <Loading />;
  const isRoad = mode === "roadmap";
  const visible = topics.filter(
    (t) =>
      (isRoad || state.lessonIds.includes(t.id)) &&
      (!domain || t.domain === domain) &&
      (!priority || t.priority === priority) &&
      (!status || state.mastery[t.id].status === status) &&
      `${t.id} ${t.title} ${title(t.id)} ${t.domain}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const badge = (id: string) => {
    const done = sessionsDone[id] ? doneCount(sessionsDone[id]) : 0;
    return done > 0 ? (
      <span className="session-badge">
        {t("lesson.sessionsDone", { n: done, total: sessionOrder.length })}
      </span>
    ) : null;
  };
  return (
    <div className="page">
      <PageHeading
        eyebrow={
          isRoad
            ? t("cat.road.eyebrow")
            : mode === "lessons"
              ? t("cat.lessons.eyebrow")
              : t("cat.review.eyebrow")
        }
        title={
          isRoad
            ? t("cat.road.title")
            : mode === "lessons"
              ? t("cat.lessons.title")
              : t("cat.review.title")
        }
        description={
          isRoad
            ? t("cat.road.desc", { n: topics.length })
            : mode === "lessons"
              ? t("cat.lessons.desc", { n: state.lessonIds.length })
              : t("cat.review.desc")
        }
      />
      {mode === "assessments" && (
        <div className="info-banner">
          <BookOpen size={18} />
          <span>{t("cat.review.banner")}</span>
        </div>
      )}
      <div className="catalog-toolbar">
        <label className="search-field">
          <Search size={17} />
          <input
            aria-label={tx("Search topics", "Tìm chủ đề")}
            placeholder={t("cat.search")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd>/</kbd>
        </label>
        {isRoad && (
          <div className="segmented" aria-label={t("cat.viewMode")}>
            <button
              aria-pressed={view === "list"}
              className={view === "list" ? "selected" : ""}
              onClick={() => setView("list")}
            >
              <List size={16} />
              {t("cat.list")}
            </button>
            <button
              aria-pressed={view === "graph"}
              className={view === "graph" ? "selected" : ""}
              onClick={() => setView("graph")}
            >
              <Network size={16} />
              {t("cat.graph")}
            </button>
          </div>
        )}
      </div>
      <div className="filters">
        <select
          aria-label={t("cat.fDomain")}
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        >
          <option value="">{t("cat.allDomains")}</option>
          {domains.map((d) => (
            <option key={d}>{d}</option>
          ))}
        </select>
        <select
          aria-label={t("cat.fPriority")}
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="">{t("cat.allPriorities")}</option>
          <option value="P0">P0 · {t("cat.p0")}</option>
          <option value="P1">P1 · {t("cat.p1")}</option>
          <option value="P2">P2 · {t("cat.p2")}</option>
        </select>
        <select
          aria-label={t("cat.fStatus")}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">{t("cat.allStatuses")}</option>
          <option value="unassessed">{t("status.notStarted")}</option>
          <option value="in_progress">{t("status.practised")}</option>
          <option value="provisional">{t("status.selfRated")}</option>
          <option value="verified">{t("status.mastered")}</option>
        </select>
        <span className="result-count">
          {t(visible.length === 1 ? "cat.topic1" : "cat.topicN", {
            n: visible.length,
          })}
        </span>
      </div>
      {view === "graph" && isRoad ? (
        <Graph
          domain={domain}
          query={query}
          priority={priority}
          status={status}
          mastery={state.mastery}
        />
      ) : visible.length === 0 ? (
        <div className="empty-state">
          <Search size={25} />
          <h2>{t("cat.none")}</h2>
          <p>{t("cat.noneNote")}</p>
          <button
            onClick={() => {
              setQuery("");
              setDomain("");
              setPriority("");
              setStatus("");
            }}
          >
            {t("cat.clear")}
          </button>
        </div>
      ) : isRoad ? (
        <div className="roadmap-groups">
          {domains
            .filter((d) => visible.some((t) => t.domain === d))
            .map((d) => (
              <section key={d} data-domain-tone={domainTone(d)}>
                <div className="domain-heading">
                  <h2>{d}</h2>
                  <span>
                    {t("cat.topicN", {
                      n: visible.filter((x) => x.domain === d).length,
                    })}
                  </span>
                </div>
                <div className="panel topic-list">
                  {visible
                    .filter((tp) => tp.domain === d)
                    .map((tp) => (
                      <div className="topic-list-row" key={tp.id}>
                        <Link className="topic-main" href={`/lessons/${tp.id}`}>
                          <span className="topic-id">{tp.id}</span>
                          <div>
                            <strong>{title(tp.id)}</strong>
                            <small>
                              {state.lessonIds.includes(tp.id)
                                ? t("cat.complete")
                                : t("cat.overviewOnly")}
                              {badge(tp.id)}
                            </small>
                          </div>
                        </Link>
                        <span className={`priority ${tp.priority}`}>
                          {tp.priority}
                        </span>
                        <span className="prereq-count">
                          {tp.prerequisites.length
                            ? t("cat.prereqs", { n: tp.prerequisites.length })
                            : t("cat.foundation")}
                        </span>
                        <Status mastery={state.mastery[tp.id]} />
                        <Link
                          className="icon-button"
                          href={`/lessons/${tp.id}`}
                          aria-label={t("cat.open", { id: tp.id })}
                        >
                          <ChevronRight size={17} />
                        </Link>
                      </div>
                    ))}
                </div>
              </section>
            ))}
        </div>
      ) : (
        <div className="lesson-grid">
          {visible.map((tp) => (
            <Link
              href={`/${mode}/${tp.id}`}
              className="lesson-card"
              data-domain-tone={domainTone(tp.domain)}
              key={tp.id}
            >
              <div className="between">
                <span className="topic-code">{tp.id}</span>
                <span className={`priority ${tp.priority}`}>{tp.priority}</span>
              </div>
              <span className="small muted">{tp.domain}</span>
              <h2>{title(tp.id)}</h2>
              <div className="lesson-card-tags">
                <Status mastery={state.mastery[tp.id]} />
                {mode === "lessons" && badge(tp.id)}
              </div>
              <div className="lesson-card-bottom">
                <span>
                  {mode === "lessons"
                    ? t("cat.cardLesson")
                    : t("cat.cardCheck")}
                </span>
                <ArrowUpRight size={17} />
              </div>
            </Link>
          ))}
        </div>
      )}
      <div className="catalog-note">{t("cat.note")}</div>
    </div>
  );
}
