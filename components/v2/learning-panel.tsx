"use client";
import Link from "next/link";
import { useState } from "react";
import { LessonMarkdown } from "../markdown";
import type { objectiveDetail } from "@/lib/v2/read-model";
import { v2 } from "./client";
type Data = ReturnType<typeof objectiveDetail>;
type Kit = Data["kits"][number];

function formLabel(form: Data["forms"][number]) {
  if (form.title) return "Fresh check: " + form.title;
  if (form.id === "F-FRAMES") return "Fresh Frames check";
  if (form.id === "F-R04") return "Fresh Planar FK check";
  return "Fresh objective check";
}

function KitCard({ kit }: { kit: Kit }) {
  const [attempt, setAttempt] = useState(""),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState(""),
    [assistance, setAssistance] = useState(0),
    [recorded, setRecorded] = useState(false);
  async function download() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/v2/kits/" + kit.id + "/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!response.ok) throw new Error((await response.json()).error);
      const id = response.headers.get("X-CoreLab-Attempt");
      if (!id)
        throw new Error("Download did not include a recorded practice attempt");
      const url = URL.createObjectURL(await response.blob()),
        link = document.createElement("a");
      link.href = url;
      link.download = kit.id + ".v1.py";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setAttempt(id);
      setRecorded(false);
      setMessage(
        "Downloaded. Edit the starter functions and run your own file locally. Instructions are inside the file.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    } finally {
      setBusy(false);
    }
  }
  async function report() {
    setBusy(true);
    setError("");
    try {
      const result = await v2<{ claim: string }>(
        "kits/" + kit.id + "/self-report",
        {
          attemptId: attempt,
          ran: true,
          declaredAssistance: assistance,
        },
      );
      setMessage(result.claim);
      setRecorded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Self-report failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="panel">
      <div className="eyebrow">Apply · numerical · manual self-check</div>
      <h3>{kit.title}</h3>
      <p>{kit.description}</p>
      <p className="muted">{kit.review}.</p>
      <p>
        Python 3, standard library only. No hardware, GPU or Docker required.
        CoreLab never runs this code. Run only code you trust.
      </p>
      <button
        className="button primary"
        disabled={busy}
        onClick={() => void download()}
      >
        Download {kit.title}
      </button>
      {attempt && !recorded && (
        <div className="v2-actions">
          <label>
            Assistance used for the manual lab
            <select
              value={assistance}
              onChange={(e) => setAssistance(Number(e.target.value))}
            >
              <option value={0}>A0 · Independent</option>
              <option value={1}>A1 · Concept hint</option>
              <option value={2}>A2 · Guided steps</option>
              <option value={3}>A3 · Worked solution</option>
            </select>
          </label>
          <button
            className="button"
            disabled={busy}
            onClick={() => void report()}
          >
            Record that I ran my own tests
          </button>
        </div>
      )}
      <p>
        <strong>
          Self-checks and self-reports create practice history only. Verified I
          is unavailable.
        </strong>
      </p>
      {message && <p role="status">{message}</p>}
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
    </article>
  );
}
export function LearningPanel({
  data,
  objective,
  busy,
  onCheck,
  onGoal,
  section = "all",
}: {
  data: Data;
  objective?: string;
  busy: boolean;
  onCheck: (
    source: string,
    scope?: { objective: string; dimension: "C" | "M" },
  ) => void;
  onGoal?: (id: string) => void;
  section?: "all" | "learn" | "apply" | "verify";
}) {
  const current = data.objectives.find((o) => o.id === objective);
  const [path, setPath] = useState("");
  const chosen = data.paths.find((p) => p.id === path);
  const admitted = new Set(
    data.evidence.map((e) => e.objective + "/" + e.dimension),
  );
  const visibleKits = data.kits.filter(
    (k) => !current || current.kits.includes(k.id),
  );
  const visibleForms = data.forms.filter(
    (form) => !objective || form.objectives.includes(objective),
  );
  const visibleReviews = data.reviews.filter(
    (review) => !objective || review.objective === objective,
  );
  const showLearn = section === "all" || section === "learn";
  const showApply = section === "all" || section === "apply";
  const showVerify = section === "all" || section === "verify";
  return (
    <>
      {showLearn &&
        (current ? (
          <section
            id="v2-learn"
            className="panel v2-objective-summary"
            aria-label="Learn this objective"
          >
            <div className="eyebrow">
              Objective v{current.version} · {current.topicId}
            </div>
            <h2>{current.title}</h2>
            <p>{current.statement}</p>
            <p className="muted">
              Outside this scope: {current.excludes.join("; ")}.
            </p>
            <dl className="v2-evidence-grid" aria-label="Objective evidence">
              {(
                [
                  ["C", "Concepts"],
                  ["M", "Mathematics"],
                ] as const
              ).map(([dimension, label]) => (
                <div key={dimension}>
                  <dt>
                    {dimension} · {label}
                  </dt>
                  <dd
                    className={
                      admitted.has(current.id + "/" + dimension)
                        ? "verified-text"
                        : ""
                    }
                  >
                    {admitted.has(current.id + "/" + dimension)
                      ? "Independently admitted"
                      : "No admitted result"}
                  </dd>
                </div>
              ))}
              <div>
                <dt>I · Implementation</dt>
                <dd>Unavailable</dd>
              </div>
              <div>
                <dt>Transfer</dt>
                <dd>Qualified reviewer required</dd>
              </div>
            </dl>
            {current.readiness.length > 0 && (
              <div className="v2-notice">
                <strong>
                  Optional readiness suggestions — every activity stays open
                </strong>
                <ul>
                  {current.readiness.map((r) => (
                    <li key={r.objective}>
                      <Link href={"/objectives/" + r.objective}>
                        {data.objectives.find((o) => o.id === r.objective)
                          ?.title ?? r.objective}
                      </Link>
                      {r.strength === "for-route"
                        ? " · suggested for " + r.route
                        : " · recommended"}
                    </li>
                  ))}
                </ul>
                <p>
                  You can skip these suggestions. They never change your
                  existing topic level.
                </p>
              </div>
            )}
            <div className="v2-actions">
              {current.learn.map((ref, i) => (
                <Link
                  key={i}
                  className="button"
                  href={ref.href}
                  {...(ref.type === "video"
                    ? { target: "_blank", rel: "noreferrer" }
                    : {})}
                >
                  {ref.type === "lesson"
                    ? "Learn · " + ref.topic
                    : ref.type === "bridge"
                      ? "Open optional bridge"
                      : ref.type + " · " + ref.id}
                </Link>
              ))}
            </div>
          </section>
        ) : (
          <section
            id="v2-learn"
            className="panel v2-path-picker"
            aria-label="Choose a learning direction"
          >
            <h2>Choose an optional learning path</h2>
            <p>
              These short objective paths organize authored activities. They do
              not replace the original roadmap or lock other activities.
            </p>
            <label>
              Goal or specialization
              <select
                value={path}
                onChange={(e) => {
                  setPath(e.target.value);
                  onGoal?.(e.target.value);
                }}
              >
                <option value="">Explore freely</option>
                {data.paths.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
            </label>
            {chosen && (
              <ol>
                {chosen.objectives.map((id) => (
                  <li key={id}>
                    <Link href={"/objectives/" + id}>
                      {data.objectives.find((o) => o.id === id)?.title ?? id}
                    </Link>
                  </li>
                ))}
              </ol>
            )}
          </section>
        ))}
      {showLearn && data.bridge && (
        <section className="panel">
          <LessonMarkdown body={data.bridge} />
        </section>
      )}
      {showApply && (
        <section
          id="v2-apply"
          className="v2-section"
          aria-labelledby="v2-apply-title"
        >
          <header className="v2-section-heading">
            <div>
              <div className="eyebrow">APPLY</div>
              <h2 id="v2-apply-title">Build it locally.</h2>
              <p>
                Turn the model into your own implementation. These kits record
                practice, never verified implementation evidence.
              </p>
            </div>
          </header>
          {visibleKits.length > 0 ? (
            <section
              aria-label="Manual numerical labs"
              className="v2-card-grid"
            >
              {visibleKits.map((k) => (
                <KitCard key={k.id} kit={k} />
              ))}
            </section>
          ) : (
            <div className="panel v2-empty-state">
              <h3>No manual kit for this objective yet.</h3>
              <p>
                You can still solve the authored exercises, explain your method
                and keep implementation notes.
              </p>
            </div>
          )}
          {!objective && (
            <details className="panel">
              <summary>
                Explore the 22-lab roadmap and optional external resources
              </summary>
              <p>
                {data.kits.length} manual numerical kits are available. Each
                entry states its implemented scope or planned status. Related
                practice is partial preparation, not a completed lab or
                evidence. Simulator, ROS and hardware integrations are not
                available.
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Lab</th>
                      <th>Availability</th>
                      <th>Related practice</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.labRoadmap.labs.map((lab) => (
                      <tr key={lab.id}>
                        <td>
                          <strong>{lab.title}</strong>
                          <br />
                          {lab.outcome}
                        </td>
                        <td>
                          {lab.status === "manual-self-check"
                            ? "Manual kit · no verified I"
                            : "Planned · not implemented"}
                          {!!lab.unavailable?.length && (
                            <p className="muted">
                              Unavailable: {lab.unavailable.join(", ")}
                            </p>
                          )}
                        </td>
                        <td>
                          {lab.practiceFamilies.map((id) => {
                            const f = data.families.find((f) => f.id === id);
                            return f ? (
                              <p key={id}>
                                <Link href={"/objectives/" + f.objectiveId}>
                                  {f.title}
                                </Link>
                              </p>
                            ) : null;
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <h3>Optional reading outside CoreLab</h3>
              <p>
                Foundational learning requires none of these tools or devices.
                External material has its own terms and creates no evidence.
              </p>
              <ul>
                {data.labRoadmap.resources.map((r) => (
                  <li key={r.id}>
                    <a href={r.url} target="_blank" rel="noreferrer">
                      {r.title}
                    </a>{" "}
                    · {r.pathway}
                    <p>{r.check}</p>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>
      )}
      {showVerify && (
        <section
          id="v2-verify"
          className="panel v2-verification"
          aria-labelledby="v2-verify-title"
        >
          <div className="eyebrow">VERIFY</div>
          <h2 id="v2-verify-title">Verify independently · C and M</h2>
          <p>
            Verify directly whenever you want. Known answers, hints and external
            help cannot establish an independent pass. Coverage is judged
            separately for each objective and dimension.
          </p>
          {visibleForms.map((f) => (
            <div key={f.id} className="v2-actions">
              <button
                className="button"
                disabled={busy || !f.available}
                onClick={() => onCheck(f.id)}
              >
                {formLabel(f)}
              </button>
              {!f.available && <span>{f.reason}. No attempt is issued.</span>}
            </div>
          ))}
          {visibleForms.length === 0 && (
            <p className="v2-inline-note">
              No independent C/M form is available for this objective yet.
              Practice and manual kits stay open; completing them does not
              create verified evidence.
            </p>
          )}
          <div id="v2-review" className="v2-review-section">
            <div className="eyebrow">REVIEW</div>
            <h3>Keep what you learned.</h3>
            {visibleReviews.length > 0 ? (
              <ul>
                {visibleReviews.map((r) => (
                  <li key={r.objective + r.dimension}>
                    {r.objective} · {r.dimension} ·{" "}
                    {r.dueNow
                      ? "Due"
                      : "Due " + new Date(r.due).toLocaleDateString("en-GB")}
                    <button
                      className="button"
                      disabled={busy || !r.available || !r.sourceId}
                      onClick={() =>
                        onCheck(r.sourceId!, {
                          objective: r.objective,
                          dimension: r.dimension,
                        })
                      }
                    >
                      {r.dueNow
                        ? "Review due objective"
                        : "Review now as practice"}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                No active objective reviews yet. Due reviews start after an
                admitted C/M check; early retrieval is practice. Existing topic
                reviews remain available.
              </p>
            )}
          </div>
        </section>
      )}
    </>
  );
}
