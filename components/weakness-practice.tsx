"use client";
import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, RotateCcw } from "lucide-react";
import { topics, topicMap } from "@/lib/curriculum";
import { weaknessUrl, mistakeCategoryLabel } from "@/lib/weaknesses";
import type {
  Weakness,
  TargetedPlan,
  PracticeSkill,
  Answers,
  Assistance,
  Attempt,
} from "@/lib/types";
import { useCore, Loading } from "./provider";
import { PageHeading, dateText, TopicChips } from "./ui";
import { localizePlanText } from "@/lib/i18n";
import { AssistanceSelect, AssessmentQuestion } from "./assessment-question";
import { useI18n } from "@/lib/i18n";
const mistakeVi = {
  conceptual: "Hiểu sai khái niệm",
  mathematical: "Lỗi suy luận toán học",
  procedural: "Lỗi quy trình",
  implementation: "Lỗi cài đặt/gỡ lỗi",
  method_selection: "Chọn sai phương pháp",
  retention: "Quên kiến thức",
} as const;
const statusLabels = {
  active: "weak.active",
  practiced_with_assistance: "weak.assisted",
  independently_corrected: "weak.corrected",
  due_for_retention_review: "weak.retention",
} as const;
export function WeaknessStatus({ weakness }: { weakness: Weakness }) {
  const { t } = useI18n();
  return (
    <span
      className={`status ${weakness.status === "independently_corrected" ? "verified" : ""}`}
    >
      {t(statusLabels[weakness.status])}
    </span>
  );
}
export function PracticeTabs({ weaknesses = false }: { weaknesses?: boolean }) {
  const { t } = useI18n();
  return (
    <nav
      className="practice-tabs segmented"
      aria-label={t("practice.sections")}
    >
      <Link
        className={weaknesses ? "" : "selected"}
        aria-current={!weaknesses ? "page" : undefined}
        href="/practice"
      >
        {t("practice.assignments")}
      </Link>
      <Link
        className={weaknesses ? "selected" : ""}
        aria-current={weaknesses ? "page" : undefined}
        href={weaknessUrl()}
      >
        {t("practice.weaknesses")}
      </Link>
    </nav>
  );
}
export function WeaknessPractice() {
  const { state, title } = useCore();
  const { t, tx } = useI18n();
  const params = useSearchParams();
  const router = useRouter();
  const [filter, setFilter] = useState("open");
  if (!state) return <Loading />;
  const all = state.weaknesses;
  const visible = all.filter((w) =>
    filter === "all" || filter === "open"
      ? filter === "all" || w.status !== "independently_corrected"
      : w.status === filter,
  );
  const requested = params.get("topic");
  const topic =
    requested && topicMap[requested]
      ? requested
      : (all.find((w) => w.status !== "independently_corrected")?.topicId ??
        "M05");
  const skill = params.get("skill") ?? undefined;
  return (
    <div className="page">
      <PageHeading
        eyebrow={t("weak.eyebrow")}
        title={t("weak.title")}
        description={t("weak.desc")}
      />
      <PracticeTabs weaknesses />
      <div className="filters">
        <label className="sr-only" htmlFor="weakness-status">
          {tx("Filter weakness status", "Lọc theo trạng thái điểm yếu")}
        </label>
        <select
          id="weakness-status"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="open">
            {tx(
              "Needs practice or retention review",
              "Cần luyện tập hoặc ôn lại để ghi nhớ",
            )}
          </option>
          <option value="active">{t("weak.active")}</option>
          <option value="practiced_with_assistance">
            {t("weak.assisted")}
          </option>
          <option value="independently_corrected">{t("weak.corrected")}</option>
          <option value="due_for_retention_review">
            {t("weak.retention")}
          </option>
          <option value="all">
            {tx("All mistake history", "Toàn bộ lịch sử lỗi")}
          </option>
        </select>
        <span className="result-count">
          {visible.length} {tx("skills", "kỹ năng")}
        </span>
      </div>
      {visible.length ? (
        <div className="weakness-list">
          {visible.map((w) => (
            <section className="panel weakness-card" key={w.key}>
              <div className="between">
                <span className="topic-code">
                  {w.topicId} · {title(w.topicId)}
                </span>
                <WeaknessStatus weakness={w} />
              </div>
              <h2>{w.skillLabel}</h2>
              <p className="small">
                {tx(
                  `${w.failureCount} objective mistakes across ${w.failedAttempts} failed ${w.failedAttempts === 1 ? "attempt" : "attempts"}`,
                  `${w.failureCount} lỗi khách quan trong ${w.failedAttempts} lần làm chưa đạt`,
                )}{" "}
                · {tx("Last activity:", "Hoạt động gần nhất:")}{" "}
                {dateText(w.lastAttemptAt)}
              </p>
              <div className="chips">
                {w.categories.map((c) => (
                  <span className="status" key={c}>
                    {tx(mistakeCategoryLabel(c), mistakeVi[c])}
                  </span>
                ))}
              </div>
              <p className="small muted">
                {w.status === "practiced_with_assistance"
                  ? tx(
                      "Assisted success is useful practice. A fresh equivalent A0 answer is still needed.",
                      "Làm đúng khi có trợ giúp là luyện tập hữu ích. Bạn vẫn cần một câu trả lời A0 tương đương mới.",
                    )
                  : w.status === "independently_corrected"
                    ? tx(
                        "New independent evidence corrected this skill. Its failure history remains available.",
                        "Bằng chứng tự làm mới đã sửa kỹ năng này. Lịch sử lỗi vẫn được giữ lại.",
                      )
                    : w.status === "due_for_retention_review"
                      ? tx(
                          "The existing topic review schedule is due. Check retention without consulting the solution.",
                          "Đã đến lịch ôn tập của chủ đề. Hãy kiểm tra trí nhớ mà không xem lời giải.",
                        )
                      : tx(
                          "Review the specific reasoning, then try a different authored example.",
                          "Xem lại phần lập luận cụ thể, rồi thử một ví dụ khác.",
                        )}
              </p>
              <div className="topic-actions">
                <Link
                  className="button"
                  href={w.remediation[0]?.href ?? `/lessons/${w.topicId}`}
                >
                  {tx("Review Concept", "Xem lại khái niệm")}
                </Link>
                <Link
                  className="button primary"
                  href={
                    weaknessUrl(w.topicId, w.skillTag) + "#targeted-practice"
                  }
                >
                  {tx("Practice Weak Skill", "Luyện kỹ năng yếu")}
                  <ArrowRight size={15} />
                </Link>
                <Link className="button" href={`/assessments/${w.topicId}`}>
                  {tx("Retry Assessment", "Làm lại bài kiểm tra")}
                </Link>
              </div>
              <details className="weakness-provenance">
                <summary>
                  {tx(
                    "Evidence and prerequisites",
                    "Bằng chứng và kiến thức tiên quyết",
                  )}
                </summary>
                <p className="small muted">
                  {tx("Classification:", "Phân loại:")}{" "}
                  {w.classificationSource === "authored"
                    ? tx(
                        "authored skill metadata",
                        "siêu dữ liệu kỹ năng đã biên soạn",
                      )
                    : tx(
                        "legacy question format; no finer skill classification is authored",
                        "định dạng câu hỏi cũ; chưa có phân loại kỹ năng chi tiết hơn",
                      )}
                  . {tx("Latest result:", "Kết quả gần nhất:")}{" "}
                  {w.latestResult.replaceAll("_", " ")}.{" "}
                  {tx("Topic review:", "Ôn tập chủ đề:")}{" "}
                  {w.reviewDueAt
                    ? dateText(w.reviewDueAt)
                    : tx("not scheduled", "chưa lên lịch")}
                  .{" "}
                  {w.lastCorrectedAt
                    ? `${tx("Independent correction:", "Tự sửa được:")} ${dateText(w.lastCorrectedAt)}.`
                    : ""}
                </p>
                <ul>
                  {w.questionRefs.map((r) => (
                    <li
                      key={`${r.purpose}-${r.version}-${r.questionId}`}
                      className="small mono"
                    >
                      {r.purpose} v{r.version} · {r.questionId}
                    </li>
                  ))}
                </ul>
                <TopicChips ids={w.prerequisites} />
                {w.remediation.slice(1).map((ref) => (
                  <Link key={ref.href} className="text-link" href={ref.href}>
                    {ref.label}
                  </Link>
                ))}
              </details>
            </section>
          ))}
        </div>
      ) : (
        <div className="panel">
          <h2>
            {all.length
              ? tx(
                  "No skills match this filter.",
                  "Không có kỹ năng nào khớp bộ lọc này.",
                )
              : tx(
                  "No objectively graded mistakes recorded yet.",
                  "Chưa ghi nhận lỗi nào ở câu hỏi tự động chấm.",
                )}
          </h2>
          <p>
            {tx(
              "Reading and ungraded rubric responses never count as mistakes. Try a diagnostic or explore an authored practice skill below.",
              "Đọc bài và câu trả lời rubric không chấm điểm không bao giờ bị tính là lỗi. Hãy thử một bài kiểm tra hoặc khám phá một kỹ năng luyện tập bên dưới.",
            )}
          </p>
          <Link className="button" href="/assessments">
            {tx("Open reviews", "Mở mục Ôn tập")}
          </Link>
        </div>
      )}
      <section id="targeted-practice" className="targeted-section">
        <div className="section-title">
          <h2>{tx("Focused practice", "Luyện tập tập trung")}</h2>
        </div>
        <label>
          {tx("Practice topic", "Chủ đề luyện tập")}
          <select
            aria-label={tx(
              "Focused practice topic",
              "Chủ đề luyện tập tập trung",
            )}
            value={topic}
            onChange={(e) => {
              router.push(weaknessUrl(e.target.value) + "#targeted-practice");
            }}
          >
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.id} · {title(t.id)}
              </option>
            ))}
          </select>
        </label>
        <TargetedSet
          key={`${topic}:${skill ?? ""}`}
          topicId={topic}
          skill={skill}
          defaultSkill={
            all.find(
              (w) =>
                w.topicId === topic && w.status !== "independently_corrected",
            )?.skillTag ?? all.find((w) => w.topicId === topic)?.skillTag
          }
        />
      </section>
    </div>
  );
}
function TargetedSet({
  topicId,
  skill,
  defaultSkill,
}: {
  topicId: string;
  skill?: string;
  defaultSkill?: string;
}) {
  const { act, busy, title } = useCore();
  const { t, lang, tx } = useI18n();
  const [selectedSkill] = useState(() => skill ?? defaultSkill);
  const router = useRouter();
  const [data, setData] = useState<{
      skills: PracticeSkill[];
      plan: TargetedPlan;
    } | null>(null),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0),
    [answers, setAnswers] = useState<Answers>({}),
    [assistance, setAssistance] = useState<Assistance>("A0"),
    [result, setResult] = useState<Attempt | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    const params = new URLSearchParams({ topic: topicId });
    if (selectedSkill) params.set("skill", selectedSkill);
    if (lang === "vi") params.set("lang", "vi");
    fetch(`/api/practice?${params}`, { signal: controller.signal })
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.error);
        setData(body);
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Unable to load practice.");
      });
    return () => controller.abort();
  }, [topicId, selectedSkill, reload, lang]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!data) return;
    setError("");
    try {
      const attempt = (await act({
        type: "targeted_attempt",
        topicId,
        skillTag: data.plan.skillTag,
        questionIds: data.plan.assessment.questions.map((q) => q.id),
        assessmentVersion: data.plan.assessment.version,
        answers,
        assistance,
        lang,
      })) as Attempt;
      setResult(attempt);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : tx("Unable to save practice.", "Không lưu được bài luyện tập."),
      );
    }
  }
  if (!data)
    return (
      <div className="panel" role={error ? "alert" : "status"}>
        {error || tx("Loading authored practice…", "Đang tải bài luyện tập…")}
      </div>
    );
  const { plan, skills } = data;
  const objective = result?.grade.items.some((i) => i.correct !== null);
  return (
    <div>
      <label>
        {tx("Weak skill / assessment type", "Kỹ năng yếu / loại bài kiểm tra")}
        <select
          aria-label={tx(
            "Focused practice skill",
            "Kỹ năng luyện tập tập trung",
          )}
          value={plan.skillTag}
          onChange={(e) =>
            router.push(
              weaknessUrl(topicId, e.target.value) + "#targeted-practice",
            )
          }
        >
          {!skills.some((s) => s.tag === plan.skillTag) && (
            <option value={plan.skillTag}>{plan.skillLabel}</option>
          )}
          {skills.map((s) => (
            <option value={s.tag} key={s.tag}>
              {s.label} · {s.knowledgeTypes.join(" / ")}
            </option>
          ))}
        </select>
      </label>
      <div className="info-banner">{localizePlanText(plan.message, lang)}</div>
      {plan.prerequisiteActivities.length > 0 && (
        <section className="panel">
          <h3>{tx("Check the foundation", "Kiểm tra phần nền tảng")}</h3>
          {plan.prerequisiteActivities.map((a) => (
            <div key={a.topicId}>
              <p className="small">{localizePlanText(a.reason, lang)}</p>
              <Link className="button" href={a.href}>
                {tx("Check", "Kiểm tra")} {a.topicId} · {title(a.topicId)}
              </Link>
            </div>
          ))}
        </section>
      )}
      {plan.assessment.questions.length > 0 && !result && (
        <form className="assessment-form targeted-form" onSubmit={submit}>
          <div className="panel">
            <div className="between">
              <h2>{plan.skillLabel}</h2>
              <span className="mono small">
                {tx("PRACTICE", "LUYỆN TẬP")} v{plan.assessment.version}
              </span>
            </div>
            <AssistanceSelect value={assistance} onChange={setAssistance} />
          </div>
          {plan.assessment.questions.map((q, index) => (
            <AssessmentQuestion
              key={q.id}
              question={q}
              index={index}
              answers={answers}
              onAnswer={(id, value) =>
                setAnswers((a) => ({ ...a, [id]: value }))
              }
              requireShort
            />
          ))}
          <button type="submit" className="button primary" disabled={busy}>
            {tx("Save focused practice", "Lưu bài luyện tập")}
            <ArrowRight size={16} />
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      {result && (
        <section className="panel assessment-result" role="status">
          <h2>
            {objective
              ? `${tx("Focused result", "Kết quả luyện tập")} · ${result.grade.score}%`
              : tx(
                  "Rubric response saved · unverified",
                  "Đã lưu câu trả lời rubric · chưa kiểm chứng",
                )}
          </h2>
          <p>
            {tx("Assistance:", "Mức trợ giúp:")} {result.assistance}.{" "}
            {tx(
              "Focused results do not satisfy the full check or automatically raise mastery.",
              "Kết quả luyện tập tập trung không thay cho bài kiểm tra đầy đủ và không tự động tăng mức nắm vững.",
            )}
          </p>
          {result.grade.items.map((i) => (
            <div className="feedback-item" key={i.id}>
              <strong
                className={
                  i.correct === true
                    ? "verified-text"
                    : i.correct === false
                      ? "error-text"
                      : "muted"
                }
              >
                {i.id} ·{" "}
                {i.correct === null
                  ? t("assess.rubric")
                  : i.correct
                    ? t("assess.correct")
                    : t("assess.notYet")}
              </strong>
              <p>{result.localizedFeedback?.[i.id] ?? i.feedback}</p>
            </div>
          ))}
          <button
            className="button"
            onClick={() => {
              setData(null);
              setResult(null);
              setAnswers({});
              setReload((n) => n + 1);
            }}
          >
            <RotateCcw size={15} />
            {tx("Check next available set", "Kiểm tra bộ câu hỏi tiếp theo")}
          </button>
        </section>
      )}
      {!plan.assessment.questions.length && (
        <div className="topic-actions">
          <Link className="button" href={`/lessons/${topicId}`}>
            {tx("Review Concept", "Xem lại khái niệm")}
          </Link>
          <Link className="button" href={`/assessments/${topicId}`}>
            {tx("Retry Assessment", "Làm lại bài kiểm tra")}
          </Link>
        </div>
      )}
    </div>
  );
}
