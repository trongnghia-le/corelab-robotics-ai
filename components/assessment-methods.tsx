"use client";
import Link from "next/link";
import {
  knowledgeTypes,
  knowledgeTypeFor,
  knowledgeTypeInfo,
} from "@/lib/assessment";
import { weaknessUrl } from "@/lib/weaknesses";
import { practices } from "@/lib/practice";
import type { TopicPayload } from "@/lib/types";
export function AssessmentMethods({
  id,
  data,
}: {
  id: string;
  data: TopicPayload;
}) {
  return (
    <section className="panel assessment-methods">
      <h2>Choose evidence that fits the knowledge</h2>
      <p className="small muted">
        Knowledge type chooses how to assess. C/M/I/T describes what the
        evidence demonstrates.
      </p>
      <div className="method-grid">
        {knowledgeTypes.map((type) => {
          const info = knowledgeTypeInfo[type];
          const q = data.assessment?.questions.find(
            (q) => knowledgeTypeFor(q) === type,
          );
          const skill = data.practiceSkills?.find((s) =>
            s.knowledgeTypes.includes(type),
          );
          const lab = type === "implementation" && ["M02", "PY01"].includes(id);
          const assignment =
            type === "implementation" &&
            practices.some((p) => p.topicId === id);
          return (
            <div key={type}>
              <strong>
                {info.label} — {info.goal}
              </strong>
              <p>{q?.recommendedMethod ?? info.method}</p>
              {type === "implementation" && (lab || assignment) ? (
                <>
                  <Link className="text-link" href={`/practice?topic=${id}`}>
                    {lab
                      ? "Open signed local verifier"
                      : "Open local assignment"}
                  </Link>
                  <small>
                    {lab
                      ? "Supported A0 reports can demonstrate I."
                      : "No signed verifier for this assignment; results remain self-reported."}
                  </small>
                </>
              ) : q ? (
                <>
                  <a className="text-link" href={`#assessment-${q.id}`}>
                    {q.kind === "short"
                      ? "Open rubric response"
                      : "Open diagnostic questions"}
                  </a>
                  <small>
                    {q.kind === "short"
                      ? "Open responses remain unverified."
                      : "Objective answers use the authored contract."}
                  </small>
                </>
              ) : skill ? (
                <>
                  <Link
                    className="text-link"
                    href={weaknessUrl(id, skill.tag) + "#targeted-practice"}
                  >
                    Open focused {type} practice
                  </Link>
                  <small>
                    Focused practice does not replace the full diagnostic.
                  </small>
                </>
              ) : (
                <span className="muted small">
                  No authored assessment available for this type yet.
                </span>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
