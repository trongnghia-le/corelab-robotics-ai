"use client";
import type { Answers, Assistance, Question } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
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
  const { t } = useI18n();
  return (
    <div className="assistance-select">
      <label>
        {t("assist.label")}
        <select
          aria-label={t("assist.label")}
          value={value}
          onChange={(e) => onChange(e.target.value as Assistance)}
        >
          <option value="A0">{t("assist.A0")}</option>
          <option value="A1">{t("assist.A1")}</option>
          <option value="A2">{t("assist.A2")}</option>
          <option value="A3">{t("assist.A3")}</option>
        </select>
      </label>
      <details className="details-disclosure">
        <summary>{t("common.details")}</summary>
        <p className="small muted">{t("assist.note")}</p>
      </details>
    </div>
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
  const { t } = useI18n();
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
        {q.critical && <span>{t("question.critical")}</span>}
        <span>
          {isObjective(q) ? t("question.auto") : t("question.rubric")}
        </span>
      </div>
      <details className="details-disclosure">
        <summary>{t("common.details")}</summary>
        <div className="question-tags">
          <span>{q.dimension}</span>
          <span>
            {info.label} — {info.goal}
          </span>
        </div>
      </details>
      {q.skillLabel && (
        <p className="small muted">
          {t("question.skill")}: {q.skillLabel}
        </p>
      )}
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
          {t("question.number")}
          <input
            aria-label={`Answer ${q.id}`}
            required
            type="text"
            inputMode="decimal"
            placeholder={t("question.numberPlaceholder")}
            value={answers[q.id] ?? ""}
            onChange={(e) => onAnswer(q.id, e.target.value)}
          />
        </label>
      ) : (
        <>
          <textarea
            aria-label={t("question.response")}
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
