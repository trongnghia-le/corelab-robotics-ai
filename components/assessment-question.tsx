"use client";
import type { Answers, Assistance, Question } from "@/lib/types";
import {
  knowledgeTypeFor,
  knowledgeTypeInfo,
  isObjective,
} from "@/lib/assessment";
export function AssistanceSelect({
  value,
  onChange,
}: {
  value: Assistance;
  onChange: (value: Assistance) => void;
}) {
  return (
    <label>
      Assistance level
      <select
        aria-label="Assistance level"
        value={value}
        onChange={(e) => onChange(e.target.value as Assistance)}
      >
        <option value="A0">A0 · Independent, no assistance</option>
        <option value="A1">A1 · Conceptual hint</option>
        <option value="A2">A2 · Specific hint / example</option>
        <option value="A3">A3 · Solution from AI / reference</option>
      </select>
    </label>
  );
}
export function AssessmentQuestion({
  question: q,
  index,
  answers,
  onAnswer,
  requireShort = false,
}: {
  question: Question;
  index: number;
  answers: Answers;
  onAnswer: (id: string, value: string) => void;
  requireShort?: boolean;
}) {
  const type = knowledgeTypeFor(q),
    info = knowledgeTypeInfo[type];
  return (
    <fieldset className="question panel" id={`assessment-${q.id}`}>
      <legend>
        <span className="question-number">
          {String(index + 1).padStart(2, "0")}
        </span>
        <span>{q.prompt}</span>
      </legend>
      <div className="question-tags">
        <span>{q.dimension}</span>
        {q.critical && <span>CRITICAL</span>}
        <span>
          {info.label} — {info.goal}
        </span>
        <span>
          {isObjective(q) ? "OBJECTIVE CHECK" : "RUBRIC · UNVERIFIED"}
        </span>
      </div>
      {q.skillLabel && <p className="small muted">Skill: {q.skillLabel}</p>}
      {q.kind === "choice" ? (
        <div className="choices">
          {q.options?.map((o, j) => (
            <label
              className={
                answers[q.id] === String(j) ? "choice chosen" : "choice"
              }
              key={o}
            >
              <input
                required
                type="radio"
                name={q.id}
                value={j}
                checked={answers[q.id] === String(j)}
                onChange={(e) => onAnswer(q.id, e.target.value)}
              />
              <span>{o}</span>
            </label>
          ))}
        </div>
      ) : q.kind === "number" ? (
        <label className="number-answer">
          Answer (use a decimal point)
          <input
            aria-label={`Answer ${q.id}`}
            required
            type="text"
            inputMode="decimal"
            placeholder="Enter a number…"
            value={answers[q.id] ?? ""}
            onChange={(e) => onAnswer(q.id, e.target.value)}
          />
        </label>
      ) : (
        <>
          <textarea
            aria-label="Rubric response"
            rows={5}
            maxLength={10000}
            required={requireShort}
            value={answers[q.id] ?? ""}
            onChange={(e) => onAnswer(q.id, e.target.value)}
          />
          <ul className="rubric">
            {q.rubric?.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </>
      )}
    </fieldset>
  );
}
