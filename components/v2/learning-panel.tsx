"use client";
import Link from "next/link";
import { useState } from "react";
import { LessonMarkdown } from "../markdown";
import type { objectiveDetail } from "@/lib/v2/read-model";
import { v2 } from "./client";
type Data = ReturnType<typeof objectiveDetail>;
type Kit = Data["kits"][number];
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
}: {
  data: Data;
  objective?: string;
  busy: boolean;
  onCheck: (
    source: string,
    scope?: { objective: string; dimension: "C" | "M" },
  ) => void;
  onGoal?: (id: string) => void;
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
  return (
    <>
      {current ? (
        <section className="panel">
          <div className="eyebrow">
            Objective v{current.version} · {current.topicId}
          </div>
          <h2>{current.title}</h2>
          <p>{current.statement}</p>
          <p className="muted">
            Outside this scope: {current.excludes.join("; ")}.
          </p>
          <p>
            C:{" "}
            {admitted.has(current.id + "/C")
              ? "independently admitted"
              : "not admitted"}{" "}
            · M:{" "}
            {admitted.has(current.id + "/M")
              ? "independently admitted"
              : "not admitted"}{" "}
            · I: unavailable · Transfer: qualified reviewer required.
          </p>
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
                You can skip these suggestions. They never change your existing
                topic level.
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
        <section className="panel">
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
      )}
      {data.bridge && (
        <section className="panel">
          <LessonMarkdown body={data.bridge} />
        </section>
      )}
      {visibleKits.length > 0 && (
        <section aria-label="Manual numerical labs" className="v2-card-grid">
          {visibleKits.map((k) => (
            <KitCard key={k.id} kit={k} />
          ))}
        </section>
      )}
      {!objective && (
        <details className="panel">
          <summary>
            Explore the 22-lab roadmap and optional external resources
          </summary>
          <p>
            {data.kits.length} manual numerical kits are available. The other
            lab implementations are planned. Related practice below is partial
            preparation, not a completed lab or evidence. Simulator, ROS and
            hardware integrations are not available.
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
      <section className="panel">
        <h2>Verify independently · C and M</h2>
        <p>
          Verify directly whenever you want. Known answers, hints and external
          help cannot establish an independent pass. Coverage is judged
          separately for each objective and dimension.
        </p>
        {data.forms
          .filter((f) => !objective || f.objectives.includes(objective))
          .map((f) => (
            <div key={f.id} className="v2-actions">
              <button
                className="button"
                disabled={busy || !f.available}
                onClick={() => onCheck(f.id)}
              >
                {f.id === "F-FRAMES"
                  ? "Fresh Frames check"
                  : "Fresh Planar FK check"}
              </button>
              {!f.available && <span>{f.reason}. No attempt is issued.</span>}
            </div>
          ))}
        {data.reviews.length > 0 ? (
          <ul>
            {data.reviews
              .filter((r) => !objective || r.objective === objective)
              .map((r) => (
                <li key={r.objective + r.dimension}>
                  {r.objective} · {r.dimension} ·{" "}
                  {r.dueNow
                    ? "Due"
                    : "Due " + new Date(r.due).toLocaleDateString("en-GB")}
                  <button
                    className="button"
                    disabled={busy || !r.available}
                    onClick={() =>
                      onCheck(
                        r.objective === "R04.planar-fk"
                          ? "RV-R04"
                          : "RV-FRAMES",
                        { objective: r.objective, dimension: r.dimension },
                      )
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
            No active objective reviews yet. Due reviews start after an admitted
            C/M check; early retrieval is practice. Existing topic reviews
            remain available.
          </p>
        )}
      </section>
    </>
  );
}
