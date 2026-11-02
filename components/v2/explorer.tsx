"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Compass,
  FlaskConical,
  RotateCcw,
} from "lucide-react";
import { PageHeading } from "../ui";
import type { objectiveDetail } from "@/lib/v2/read-model";
import type {
  publicAttempt,
  history as learningHistory,
} from "@/lib/v2/attempts";
import { readableAnswer, v2 } from "./client";
import { LearningPanel } from "./learning-panel";
type Data = ReturnType<typeof objectiveDetail>;
type Attempt = ReturnType<typeof publicAttempt>;
type History = ReturnType<typeof learningHistory>["items"];
type Mode = "recommended" | "explore" | "more";
export function V2Explorer({ objective }: { objective?: string }) {
  const [data, setData] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<Mode>("recommended"),
    [domain, setDomain] = useState(""),
    [source, setSource] = useState(""),
    [route, setRoute] = useState(""),
    [difficulty, setDifficulty] = useState("");
  const [attempt, setAttempt] = useState<Attempt | null>(null),
    [answers, setAnswers] = useState<Record<string, string>>({}),
    [declared, setDeclared] = useState(0),
    [hint, setHint] = useState(""),
    [artifact, setArtifact] = useState("");
  const [history, setHistory] = useState<History>([]),
    [cursor, setCursor] = useState<string | null>(null);
  const [goal, setGoal] = useState(""),
    [recommendations, setRecommendations] = useState<
      { id: string; reason: string }[]
    >([]);
  const [pendingHelp, setPendingHelp] = useState<number | null>(null);
  const refresh = useCallback(async () => {
    const value = await v2<Data>(
      objective ? "objectives/" + encodeURIComponent(objective) : "objectives",
    );
    setData(value);
    return value;
  }, [objective]);
  const loadHistory = useCallback(async (next?: string) => {
    const value = await v2<{ items: History; nextCursor: string | null }>(
      "history?limit=10" + (next ? "&cursor=" + next : ""),
    );
    setHistory((old) => (next ? [...old, ...value.items] : value.items));
    setCursor(value.nextCursor);
  }, []);
  useEffect(() => {
    let active = true;
    Promise.all([
      v2<Data>(
        objective
          ? "objectives/" + encodeURIComponent(objective)
          : "objectives",
      ),
      v2<{ items: History; nextCursor: string | null }>("history?limit=10"),
    ])
      .then(([value, events]) => {
        if (active) {
          setData(value);
          setHistory(events.items);
          setCursor(events.nextCursor);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [objective]);
  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save");
    } finally {
      setBusy(false);
    }
  };
  function open(a: Attempt) {
    setAttempt(a);
    setAnswers(a.result && "answers" in a.result ? a.result.answers : {});
    setDeclared(0);
    setHint("");
    setPendingHelp(null);
    setArtifact(a.result && "artifact" in a.result ? a.result.artifact : "");
  }
  async function issue(familyId: string, chosenRoute?: string) {
    const a = await v2<Attempt>("attempts", {
      purpose: "practice",
      source: familyId,
      ...(objective ? { objectiveId: objective } : {}),
      ...(chosenRoute ? { route: chosenRoute } : {}),
      ...(difficulty ? { difficulty: Number(difficulty) } : {}),
    });
    await Promise.all([refresh(), loadHistory()]);
    open(a);
    setSource(familyId);
    setRoute(a.item.route);
  }
  const selected = data?.families.find((f) => f.id === source);
  let families =
    data?.families.filter((f) => !domain || f.domain === domain) ?? [];
  if (mode === "recommended") {
    const byId = new Map(families.map((f) => [f.id, f]));
    families = recommendations
      .map((r) => byId.get(r.id))
      .filter((f): f is Data["families"][number] => !!f);
  }
  if (mode === "more" && source)
    families = families.filter((f) => f.id === source);
  const domains = [...new Set(data?.families.map((f) => f.domain) ?? [])];
  const attemptPanel = useRef<HTMLElement>(null);
  useEffect(() => {
    if (attempt?.id) attemptPanel.current?.focus();
  }, [attempt?.id]);
  const revision = data?.workspace.revision;
  useEffect(() => {
    if (mode !== "recommended") return;
    let active = true;
    const p = new URLSearchParams({ mode: "recommended", limit: "5" });
    if (objective) p.set("objective", objective);
    if (domain) p.set("domain", domain);
    if (goal) p.set("goal", goal);
    v2<{ items: { id: string; reason: string }[] }>("select?" + p)
      .then((r) => {
        if (active) setRecommendations(r.items);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [mode, objective, domain, goal, revision]);
  async function loadHelp(level: number) {
    if (!attempt) return;
    const h = await v2<{ level: number; content: string }>(
      "attempts/" + attempt.id + "/assist",
      { level },
    );
    setHint(h.content);
    setAttempt({ ...attempt, observedAssistance: h.level });
    setPendingHelp(null);
  }
  return (
    <div className="page v2-page">
      <PageHeading
        eyebrow="LEARN · BUILD · PROVE"
        title={
          objective ? "Build this objective" : "Your next independent step."
        }
        description="Choose a skill, work through a meaningful problem, and keep the evidence honest. Your learning path is yours to choose."
      >
        <Link className="button" href="/settings">
          Back up your learning
        </Link>
      </PageHeading>
      <div className="v2-notice">
        <strong>CoreLab V2</strong>
        <p>
          Original exercises are author-tested and checked by an owner-assigned
          AI review, not a human expert review. Practice, code notes and watched
          solutions do not grant verified mastery; only scoped C/M checks with
          approved review records can. Verified I and human-reviewed transfer
          are unavailable.
        </p>
      </div>
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      {!data && !error && (
        <p role="status">Opening your local learning workspace…</p>
      )}
      {data?.historyAcknowledgement && (
        <section className="panel">
          <h2>Your topic history changed outside V2</h2>
          <p>
            Both histories have been preserved. Acknowledge the change before
            saving more objective practice.
          </p>
          <button
            className="button primary"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                await v2("history/acknowledge", {
                  token: data.historyAcknowledgement,
                });
                await refresh();
              })
            }
          >
            Acknowledge preserved histories
          </button>
        </section>
      )}
      {data && (
        <>
          <div className="v2-stat-grid">
            <div className="panel">
              <strong>{data.totals.families}</strong>
              <span>Original exercise families</span>
            </div>
            <div className="panel">
              <strong>{data.totals.items}</strong>
              <span>Authored practice instances</span>
            </div>
            <div className="panel">
              <strong>{data.totals.attempts}</strong>
              <span>Durable practice attempts</span>
            </div>
          </div>
          <LearningPanel
            data={data}
            objective={objective}
            busy={busy}
            onGoal={setGoal}
            onCheck={(source, scope) =>
              void run(async () => {
                const a = await v2<Attempt>("attempts", {
                  purpose: scope ? "review" : "verify",
                  source,
                  ...(scope
                    ? {
                        objectiveId: scope.objective,
                        dimension: scope.dimension,
                      }
                    : {}),
                });
                open(a);
                await Promise.all([refresh(), loadHistory()]);
              })
            }
          />
          <nav className="v2-modes" aria-label="Objective practice mode">
            {(
              [
                ["recommended", "Recommended"],
                ["explore", "Explore"],
                ["more", "More Practice"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                className={"button " + (mode === id ? "primary" : "")}
                aria-pressed={mode === id}
                onClick={() => setMode(id)}
              >
                {label}
              </button>
            ))}
          </nav>
          <div className="v2-filters">
            <label>
              Domain
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              >
                <option value="">All domains</option>
                {domains.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </label>
            <label>
              Difficulty
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="">All authored levels</option>
                <option value="1">1 · Start with the model</option>
                <option value="2">2 · Apply the method</option>
                <option value="3">3 · Change a condition</option>
              </select>
            </label>
          </div>
          <div className="v2-card-grid">
            {families.map((f) => (
              <article className="panel v2-family" key={f.id}>
                <div className="eyebrow">
                  {f.domain} · {f.id}
                </div>
                <h2>{f.title}</h2>
                <p>{f.scope}</p>
                <div className="v2-meta">
                  <span>{f.itemCount} authored tasks</span>
                  <span>{f.completed} completed practice</span>
                </div>
                <p className="muted">
                  {mode === "recommended"
                    ? recommendations.find((r) => r.id === f.id)?.reason
                    : f.attempts === 0
                      ? "Not practiced yet. Choose any route to begin."
                      : "Try another route or revisit a specific mistake."}
                </p>
                <label>
                  Application choice
                  <select
                    value={source === f.id ? route : ""}
                    onChange={(e) => {
                      setSource(f.id);
                      setRoute(e.target.value);
                    }}
                  >
                    <option value="">Any available route</option>
                    {f.routes.map((r) => (
                      <option key={r} value={r}>
                        {r.replaceAll("-", " ")}
                      </option>
                    ))}
                  </select>
                </label>
                {f.routeNotes && source === f.id && route && (
                  <p className="muted">{f.routeNotes[route]}</p>
                )}
                <div className="v2-actions">
                  <button
                    className="button primary"
                    disabled={busy}
                    onClick={() =>
                      void run(() =>
                        issue(f.id, source === f.id ? route : undefined),
                      )
                    }
                  >
                    <FlaskConical size={17} /> Practice
                  </button>
                  <Link className="button" href={"/lessons/" + f.topicId}>
                    <BookOpen size={17} /> Learn
                  </Link>
                  {!objective && (
                    <Link
                      className="button"
                      href={"/objectives/" + f.objectiveId}
                    >
                      <Compass size={17} /> Objective
                    </Link>
                  )}
                </div>
              </article>
            ))}
          </div>
          {!families.length && (
            <p className="panel">
              No authored family matches these filters. Change a filter; nothing
              is locked.
            </p>
          )}
          {attempt && (
            <section
              ref={attemptPanel}
              tabIndex={-1}
              className="panel v2-attempt"
              aria-labelledby="v2-task-title"
            >
              <div className="eyebrow">
                {attempt.source} · Difficulty {attempt.item.difficulty} ·{" "}
                {attempt.repeat
                  ? "Repeated instance · practice only"
                  : "Unseen in your recorded history"}
              </div>
              <h2 id="v2-task-title">Work the problem.</h2>
              <p className="v2-prompt">{attempt.item.prompt}</p>
              <p>
                Scope: <strong>{attempt.item.objectiveId}</strong>.{" "}
                {selected?.scope}
              </p>
              {attempt.item.fields.length > 0 && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void run(async () => {
                      const result = await v2<Attempt>(
                        "attempts/" + attempt.id + "/submit",
                        { answers, declaredAssistance: declared, artifact },
                      );
                      setAttempt(result);
                      await Promise.all([refresh(), loadHistory()]);
                    });
                  }}
                >
                  <fieldset disabled={busy || attempt.status === "submitted"}>
                    <legend>
                      Your answer · precision and units are part of the task
                    </legend>
                    <div className="v2-input-grid">
                      {attempt.item.fields.map((field) => (
                        <label key={field.id}>
                          {field.label}
                          {field.kind === "choice" ? (
                            <select
                              required
                              aria-label={field.label}
                              value={answers[field.id] ?? ""}
                              onChange={(e) =>
                                setAnswers((a) => ({
                                  ...a,
                                  [field.id]: e.target.value,
                                }))
                              }
                            >
                              <option value="">Choose an option</option>
                              {field.options?.map((o) => (
                                <option key={o}>{o}</option>
                              ))}
                            </select>
                          ) : (
                            <>
                              <input
                                required
                                autoComplete="off"
                                inputMode="text"
                                aria-label={field.label}
                                value={answers[field.id] ?? ""}
                                onChange={(e) =>
                                  setAnswers((a) => ({
                                    ...a,
                                    [field.id]: e.target.value,
                                  }))
                                }
                              />
                              <small>
                                Decimal or fraction · tolerance ±
                                {field.tolerance}
                                {field.kind === "angle" ? " rad modulo 2π" : ""}
                              </small>
                            </>
                          )}
                        </label>
                      ))}
                    </div>
                    <label>
                      Implementation scratchpad (optional, never executed)
                      <textarea
                        spellCheck={false}
                        rows={5}
                        maxLength={8000}
                        value={artifact}
                        onChange={(e) => setArtifact(e.target.value)}
                        placeholder="Write code or explain your method. Save it with your practice answer; it is not implementation evidence."
                      />
                    </label>
                    <label>
                      Outside assistance
                      <select
                        value={declared}
                        onChange={(e) => setDeclared(Number(e.target.value))}
                      >
                        <option value={0}>A0 · I worked independently</option>
                        <option value={1}>A1 · Conceptual hint</option>
                        <option value={2}>A2 · Guided steps</option>
                        <option value={3}>
                          A3 · Solution or equivalent AI assistance
                        </option>
                      </select>
                    </label>
                    <button className="button primary" type="submit">
                      Check practice answer <ArrowRight size={17} />
                    </button>
                  </fieldset>
                </form>
              )}
              <div className="v2-actions">
                {[1, 2, 3].map((level) => (
                  <button
                    type="button"
                    key={level}
                    className="button"
                    disabled={
                      busy ||
                      attempt.status === "submitted" ||
                      attempt.item.fields.length === 0
                    }
                    onClick={() =>
                      attempt.purpose === "verify" &&
                      attempt.observedAssistance === 0
                        ? setPendingHelp(level)
                        : void run(() => loadHelp(level))
                    }
                  >
                    {level === 1
                      ? "A1 · Concept hint"
                      : level === 2
                        ? "A2 · Next step"
                        : "A3 · Worked solution"}
                  </button>
                ))}
              </div>
              <p className="muted">
                Highest observed assistance: A{attempt.observedAssistance}.
                Reloading or changing tabs cannot erase recorded help.
              </p>
              {pendingHelp !== null && (
                <div className="v2-notice" role="status">
                  <p>
                    Opening help makes this verification attempt assisted and
                    ineligible for independent evidence. You can continue
                    learning and request another fresh check later.
                  </p>
                  <button
                    className="button"
                    disabled={busy}
                    onClick={() => void run(() => loadHelp(pendingHelp))}
                  >
                    Continue with assisted attempt
                  </button>
                  <button
                    className="button"
                    onClick={() => setPendingHelp(null)}
                  >
                    Keep working independently
                  </button>
                </div>
              )}
              {hint && (
                <div className="v2-feedback" role="status">
                  {hint}
                </div>
              )}
              {attempt.result &&
                ("unverifiable" in attempt.result ? (
                  <p>
                    Retained history; this source cannot currently be regraded.
                  </p>
                ) : (
                  <div className="v2-feedback" role="status">
                    <h3>
                      {attempt.result.passed
                        ? "Correct practice answer"
                        : "A useful gap to work on"}
                    </h3>
                    <p>
                      {attempt.result.claim} · effective assistance A
                      {attempt.result.effectiveAssistance}
                    </p>
                    <ul>
                      {attempt.result.fields.map((f) => (
                        <li key={f.id}>
                          {f.label}: {f.correct ? "correct" : "needs revision"}{" "}
                          · expected {readableAnswer(f.expected)}
                        </li>
                      ))}
                    </ul>
                    <p>{attempt.result.solution}</p>
                    <p>{attempt.result.remediation}</p>
                    {"scopes" in attempt.result && (
                      <ul>
                        {attempt.result.scopes.map((s) => (
                          <li key={s.objective + s.dimension}>
                            {s.objective} · {s.dimension}: {s.outcome} (
                            {s.reason})
                          </li>
                        ))}
                      </ul>
                    )}
                    {attempt.result.artifact && (
                      <details>
                        <summary>
                          Saved implementation notes · unverified
                        </summary>
                        <pre>{attempt.result.artifact}</pre>
                      </details>
                    )}
                  </div>
                ))}
              {attempt.status === "submitted" &&
                attempt.purpose === "practice" &&
                attempt.item.fields.length > 0 && (
                  <button
                    className="button primary"
                    disabled={busy}
                    onClick={() =>
                      void run(() => issue(attempt.source, attempt.item.route))
                    }
                  >
                    Choose the next available task <RotateCcw size={17} />
                  </button>
                )}
            </section>
          )}
          <section className="panel">
            <h2>Keep the workflow flexible.</h2>
            <p>
              Learn → Practice → Apply → Verify → Review. Start where it helps.
              Learn the supplied model, reconstruct the equations, implement
              locally if useful, check your work, and return after a delay.
              Reading or AI-generated solutions do not prove independence.
            </p>
            <p>
              <strong>
                Progress is measured by what you can independently explain,
                implement, and verify — not by how many videos you watch.
              </strong>
            </p>
            <Link className="button" href="/tutor">
              Open the manual Socratic tutor handoff
            </Link>
          </section>
          {data.manualActivities.map((a) => (
            <section className="panel" key={a.id}>
              <div className="eyebrow">
                Independent coding · manual, unverified
              </div>
              <h2>{a.title}</h2>
              <p>{a.instructions}</p>
              <Link className="button" href={"/lessons/" + a.topicId}>
                Programming foundation
              </Link>
            </section>
          ))}
          <section className="panel">
            <h2>Your objective practice history</h2>
            <p>
              History is preserved. Practice counts do not change your existing
              topic level.
            </p>
            <ul className="v2-history">
              {history.map((a) => (
                <li key={a.id}>
                  <button
                    className="button"
                    disabled={busy}
                    onClick={() =>
                      void run(async () =>
                        open(await v2<Attempt>("attempts/" + a.id)),
                      )
                    }
                  >
                    {a.source} · {(a.route ?? "default").replaceAll("-", " ")} ·{" "}
                    {a.status === "issued"
                      ? "Resume open attempt"
                      : "View saved practice"}
                  </button>
                  <span>
                    {new Date(a.issuedAt).toLocaleDateString("en-GB")}
                  </span>
                </li>
              ))}
            </ul>
            {cursor && (
              <button
                className="button"
                disabled={busy}
                onClick={() => void run(() => loadHistory(cursor))}
              >
                Load more history
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
