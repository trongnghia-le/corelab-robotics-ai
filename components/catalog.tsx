"use client";
import { useState } from "react";
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
import { topics, domains } from "@/lib/curriculum";
import { useCore, Loading } from "./provider";
import { PageHeading, Status } from "./ui";
const Graph = dynamic(() => import("./graph").then((m) => m.Graph), {
  ssr: false,
  loading: () => <div className="graph-loading">Loading graph…</div>,
});
export function Catalog({
  mode,
}: {
  mode: "roadmap" | "lessons" | "assessments";
}) {
  const { state } = useCore();
  const params = useSearchParams();
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
      `${t.id} ${t.title} ${t.domain}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <div className="page">
      <PageHeading
        eyebrow={
          isRoad
            ? "THE LONG-TERM MAP"
            : mode === "lessons"
              ? "LEARN FROM FIRST PRINCIPLES"
              : "EVIDENCE, NOT CHECKBOXES"
        }
        title={
          isRoad
            ? "Knowledge roadmap"
            : mode === "lessons"
              ? "Go beyond reading. Understand deeply."
              : "Verify what you understand."
        }
        description={
          isRoad
            ? `${topics.length} topics connected by prerequisites. A long-term map, not a mandatory checklist.`
            : mode === "lessons"
              ? `${state.lessonIds.length} authored lessons. Start with foundations and progress through evidence.`
              : "Short diagnostics, clear feedback, and traceable evidence."
        }
      />
      {mode === "assessments" && (
        <div className="info-banner">
          <BookOpen size={18} />
          <span>
            An A0 quiz verifies evidence only with a score of at least 80% and
            no failed critical items. Open responses use a rubric and never
            automatically increase mastery.
          </span>
        </div>
      )}
      <div className="catalog-toolbar">
        <label className="search-field">
          <Search size={17} />
          <input
            aria-label="Search topics"
            placeholder="Search by topic name or ID…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd>/</kbd>
        </label>
        {isRoad && (
          <div className="segmented" aria-label="View mode">
            <button
              aria-pressed={view === "list"}
              className={view === "list" ? "selected" : ""}
              onClick={() => setView("list")}
            >
              <List size={16} />
              List
            </button>
            <button
              aria-pressed={view === "graph"}
              className={view === "graph" ? "selected" : ""}
              onClick={() => setView("graph")}
            >
              <Network size={16} />
              Graph
            </button>
          </div>
        )}
      </div>
      <div className="filters">
        <select
          aria-label="Filter by domain"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        >
          <option value="">All domains</option>
          {domains.map((d) => (
            <option key={d}>{d}</option>
          ))}
        </select>
        <select
          aria-label="Filter by priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="">All priorities</option>
          <option value="P0">P0 · Core</option>
          <option value="P1">P1 · Applied</option>
          <option value="P2">P2 · Extension</option>
        </select>
        <select
          aria-label="Filter by status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="unassessed">Unassessed</option>
          <option value="in_progress">In progress</option>
          <option value="provisional">Self-assessed</option>
          <option value="verified">Verified</option>
        </select>
        <span className="result-count">
          {visible.length} {visible.length === 1 ? "topic" : "topics"}
        </span>
      </div>
      {view === "graph" && isRoad ? (
        <Graph
          domain={domain || domains[0]}
          query={query}
          priority={priority}
          status={status}
          mastery={state.mastery}
        />
      ) : visible.length === 0 ? (
        <div className="empty-state">
          <Search size={25} />
          <h2>No topics found</h2>
          <p>Try a shorter search or remove a filter.</p>
          <button
            onClick={() => {
              setQuery("");
              setDomain("");
              setPriority("");
              setStatus("");
            }}
          >
            Clear filters
          </button>
        </div>
      ) : isRoad ? (
        <div className="roadmap-groups">
          {domains
            .filter((d) => visible.some((t) => t.domain === d))
            .map((d) => (
              <section key={d}>
                <div className="domain-heading">
                  <h2>{d}</h2>
                  <span>
                    {visible.filter((t) => t.domain === d).length} topics
                  </span>
                </div>
                <div className="panel topic-list">
                  {visible
                    .filter((t) => t.domain === d)
                    .map((t) => (
                      <div className="topic-list-row" key={t.id}>
                        <Link className="topic-main" href={`/lessons/${t.id}`}>
                          <span className="topic-id">{t.id}</span>
                          <div>
                            <strong>{t.title}</strong>
                            <small>
                              {state.lessonIds.includes(t.id)
                                ? "Complete lesson + diagnostic"
                                : "Overview · full lesson not yet available"}
                            </small>
                          </div>
                        </Link>
                        <span className={`priority ${t.priority}`}>
                          {t.priority}
                        </span>
                        <span className="prereq-count">
                          {t.prerequisites.length
                            ? `${t.prerequisites.length} prerequisites`
                            : "Foundation"}
                        </span>
                        <Status mastery={state.mastery[t.id]} />
                        <Link
                          className="icon-button"
                          href={`/lessons/${t.id}`}
                          aria-label={`Open ${t.id}`}
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
          {visible.map((t) => (
            <Link href={`/${mode}/${t.id}`} className="lesson-card" key={t.id}>
              <div className="between">
                <span className="topic-code">{t.id}</span>
                <span className={`priority ${t.priority}`}>{t.priority}</span>
              </div>
              <span className="small muted">{t.domain}</span>
              <h2>{t.title}</h2>
              <Status mastery={state.mastery[t.id]} />
              <div className="lesson-card-bottom">
                <span>
                  {mode === "lessons"
                    ? "Theory · Examples · Practice"
                    : "Concept · Math · Rubric"}
                </span>
                <ArrowUpRight size={17} />
              </div>
            </Link>
          ))}
        </div>
      )}
      <div className="catalog-note">
        <strong>P0</strong> Core foundations <span>·</span>
        <strong>P1</strong> Application <span>·</span>
        <strong>P2</strong> Research extensions. Every topic is accessible;
        prerequisites guide learning without locking pages.
      </div>
    </div>
  );
}
