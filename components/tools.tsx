"use client";
import { CodeBlock } from "./code-block";
import { useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  Download,
  Upload,
  Copy,
  ShieldCheck,
  FileJson,
  Check,
  Route,
  ExternalLink,
} from "lucide-react";
import { topics, topicMap, domains } from "@/lib/curriculum";
import { contextFor } from "@/lib/engine";
import { practices } from "@/lib/practice";
import { practiceVi } from "@/lib/practice-vi";
import { sources } from "@/lib/resources";
import { useCore, Loading, copyText } from "./provider";
import { useTopic } from "./topic";
import { PageHeading, Status, TopicChips, dateText } from "./ui";
import { PracticeTabs, WeaknessPractice } from "./weakness-practice";
import { useI18n } from "@/lib/i18n";
export function Practice() {
  const { state, act, busy, notify, title } = useCore();
  const { t, tx, lang } = useI18n();
  const params = useSearchParams();
  const [topic, setTopic] = useState(params.get("topic") ?? ""),
    [report, setReport] = useState("");
  if (!state) return <Loading />;
  if (params.get("tab") === "weaknesses") return <WeaknessPractice />;
  const shown = practices.filter((p) => !topic || p.topicId === topic);
  const exact = topic && topicMap[topic];
  async function importReport(e: FormEvent) {
    e.preventDefault();
    try {
      await act({ type: "lab", report: JSON.parse(report) });
      setReport("");
      notify(
        tx(
          "Test report imported. View the evidence in Assessments.",
          "Đã nhập báo cáo kiểm thử. Xem kết quả trong mục Ôn tập.",
        ),
      );
    } catch (e) {
      if (e instanceof SyntaxError)
        notify(
          tx(
            "The report must contain valid JSON.",
            "Báo cáo phải là JSON hợp lệ.",
          ),
        );
    }
  }
  return (
    <div className="page">
      <PageHeading
        eyebrow={t("practice.eyebrow")}
        title={t("practice.title")}
        description={t("practice.desc")}
      />
      <PracticeTabs />
      <div className="info-banner">
        <ShieldCheck size={19} />
        <span>
          {tx(
            "Fixed tests currently support M02 and PY01. Other assignments include instructions; keep your working in the study desk. Self-reported results do not increase verified competence.",
            "Test cố định hiện hỗ trợ M02 và PY01. Các bài khác có hướng dẫn; hãy ghi bài làm trong bàn học. Kết quả tự báo cáo không làm tăng năng lực đã được kiểm chứng.",
          )}
        </span>
      </div>
      <div className="filters">
        <select
          aria-label={tx("Choose practice topic", "Chọn chủ đề luyện tập")}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        >
          <option value="">{tx("All assignments", "Tất cả bài tập")}</option>
          {topics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.id} · {title(t.id)}
            </option>
          ))}
        </select>
        {topic && (
          <button onClick={() => setTopic("")}>
            {tx("View all", "Xem tất cả")}
          </button>
        )}
      </div>
      <div className="practice-list">
        {shown.map((p, i) => (
          <section className="panel practice-card" key={p.id}>
            <div className="practice-number">
              {String(i + 1).padStart(2, "0")}
            </div>
            <div>
              <div className="between">
                <div className="chips">
                  <Link className="topic-code" href={`/lessons/${p.topicId}`}>
                    {p.topicId}
                  </Link>
                  <span className="muted small">
                    {lang === "vi"
                      ? (practiceVi[p.id]?.kind ?? p.kind)
                      : p.kind}
                  </span>
                </div>
                <span className={`status ${p.verified ? "verified" : ""}`}>
                  {p.verified
                    ? tx("Fixed verifier available", "Có bộ kiểm chứng cố định")
                    : tx("Practice · self-reported", "Luyện tập · tự báo cáo")}
                </span>
              </div>
              <h2>
                {lang === "vi" ? (practiceVi[p.id]?.title ?? p.title) : p.title}
              </h2>
              <p>
                {lang === "vi" ? (practiceVi[p.id]?.task ?? p.task) : p.task}
              </p>
              <TopicChips ids={topicMap[p.topicId].prerequisites} />
              <CodeBlock code={p.command} language="bash" />
              <div className="topic-actions">
                <a className="button" download href={p.starter}>
                  <Download size={15} />
                  {tx("Download starter", "Tải bản khởi đầu")}
                </a>
                <Link className="button" href={`/lessons/${p.topicId}`}>
                  {tx("Theory", "Lý thuyết")}
                  <ArrowRight size={15} />
                </Link>
                <Link className="button" href={`/assessments/${p.topicId}`}>
                  {tx("View evidence", "Xem kết quả")}
                  <ArrowRight size={15} />
                </Link>
              </div>
            </div>
          </section>
        ))}
      </div>
      {shown.length === 0 && exact && (
        <div className="panel">
          <h2>
            {tx("Practice the objectives for", "Luyện tập các mục tiêu của")}{" "}
            {title(exact.id)}
          </h2>
          <p>
            {tx(
              "This topic has no fixed verifier yet. Follow the independent practice section or overview guidance, then record your assumptions, reasoning, and results in the study desk.",
              "Chủ đề này chưa có bộ kiểm chứng cố định. Hãy làm theo phần luyện tập độc lập hoặc hướng dẫn tổng quan, rồi ghi giả định, lập luận và kết quả vào bàn học.",
            )}
          </p>
          <Link className="button" href={`/lessons/${topic}`}>
            {tx("Open topic", "Mở chủ đề")}
            <ArrowRight size={16} />
          </Link>
        </div>
      )}
      <section className="panel import-report">
        <h2>
          {tx("Import a local test report", "Nhập báo cáo kiểm thử cục bộ")}
        </h2>
        <p className="muted small">
          {tx(
            "The runner records the source hash, timestamp, v1 contract, assistance, and local signature. A3 records practice only; a fresh A0 run can establish I evidence. This is personal study evidence, not proctored certification.",
            "Trình chạy ghi lại mã băm mã nguồn, thời điểm, hợp đồng v1, mức trợ giúp và chữ ký cục bộ. A3 chỉ tính là luyện tập; một lần chạy A0 mới có thể tạo bằng chứng I. Đây là bằng chứng tự học cá nhân, không phải chứng nhận có giám sát.",
          )}
        </p>
        <label className="file-label">
          <Upload size={16} />
          {tx("Choose report JSON", "Chọn tệp JSON báo cáo")}
          <input
            aria-label={tx("Choose lab report", "Chọn báo cáo lab")}
            type="file"
            accept="application/json,.json"
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (f) {
                if (f.size > 10000) {
                  notify(tx("The report is too large.", "Báo cáo quá lớn."));
                  return;
                }
                setReport(await f.text());
              }
            }}
          />
        </label>
        <form onSubmit={importReport}>
          <textarea
            aria-label={tx("Test report JSON", "JSON báo cáo kiểm thử")}
            placeholder={tx(
              "Paste the contents of .local/M02-report.json…",
              "Dán nội dung của .local/M02-report.json…",
            )}
            value={report}
            onChange={(e) => setReport(e.target.value)}
            rows={6}
            required
            maxLength={10000}
          />
          <button
            className="button primary"
            type="submit"
            disabled={busy || !report}
          >
            {tx("Import report", "Nhập báo cáo")}
            <Upload size={16} />
          </button>
        </form>
        <p className="small muted">
          {tx(
            "Only the CLI in your terminal executes Python files. This button only validates and saves a report.",
            "Chỉ CLI trong terminal của bạn mới chạy các tệp Python. Nút này chỉ kiểm tra và lưu báo cáo.",
          )}
        </p>
      </section>
    </div>
  );
}
const milestones = [
  {
    name: "01 · Mathematics & programming foundations",
    description: "Notation → vectors → matrices, alongside Python and C++.",
    ids: ["M01", "PY01", "CPP01", "M02", "M03", "PY07", "CPP02", "T04"],
  },
  {
    name: "02 · Reasoning and computation",
    description: "Derivatives, probability, linear algebra, and NumPy.",
    ids: ["M04", "M05", "M06", "M07", "M08", "PY04", "M10"],
  },
  {
    name: "03 · Machine Learning from first principles",
    description:
      "Problem formulation, baselines, gradients, neural networks, and backpropagation.",
    ids: ["ML01", "ML02", "ML04", "ML05"],
  },
  {
    name: "04 · Robot geometry & control",
    description:
      "Mechanics, mechanisms, frames, kinematics, dynamics, and feedback.",
    ids: ["R01", "R02", "M12", "R03", "R04", "R06", "R07", "C01"],
  },
  {
    name: "05 · Vision & sequential decisions",
    description:
      "Digital images and MDPs; open later branches through their prerequisites.",
    ids: ["V01", "RL01", "RL02", "V02", "V03", "RL03"],
  },
  {
    name: "06 · Robot Learning & Cognitive Robotics",
    description:
      "The long-term map: interaction, representations, planning, and research.",
    ids: ["RL17", "E01", "E02", "E07", "E08", "E10", "E12", "RS01", "RS02"],
  },
];
const milestonesVi: Record<string, [string, string]> = {
  "01 · Mathematics & programming foundations": [
    "01 · Nền tảng toán và lập trình",
    "Ký hiệu → vector → ma trận, song song với Python và C++.",
  ],
  "02 · Reasoning and computation": [
    "02 · Suy luận và tính toán",
    "Đạo hàm, xác suất, đại số tuyến tính và NumPy.",
  ],
  "03 · Machine Learning from first principles": [
    "03 · Machine Learning từ nguyên lý cơ bản",
    "Đặt bài toán, baseline, gradient, mạng nơ-ron và backpropagation.",
  ],
  "04 · Robot geometry & control": [
    "04 · Hình học và điều khiển robot",
    "Cơ học, cơ cấu, hệ tọa độ, động học, động lực học và phản hồi.",
  ],
  "05 · Vision & sequential decisions": [
    "05 · Thị giác và ra quyết định tuần tự",
    "Ảnh số và MDP; các nhánh sau mở dần qua kiến thức tiên quyết.",
  ],
  "06 · Robot Learning & Cognitive Robotics": [
    "06 · Robot Learning và Cognitive Robotics",
    "Bản đồ dài hạn: tương tác, biểu diễn, lập kế hoạch và nghiên cứu.",
  ],
};
export function Paths() {
  const { t, tx, lang } = useI18n();
  const { state, act, busy, notify, title } = useCore();
  const [goal, setGoal] = useState(""),
    [focus, setFocus] = useState<string | undefined>(undefined),
    [reason, setReason] = useState<string | undefined>(undefined);
  if (!state) return <Loading />;
  const selectedGoal = goal || state.progress.goal;
  const selectedFocus = focus ?? state.progress.focusTopic ?? "";
  const selectedReason = reason ?? state.progress.focusReason;
  const debt = state.progress.sessions
    .filter((s) => s.kind === "difficulty")
    .slice()
    .reverse();
  return (
    <div className="page">
      <PageHeading
        eyebrow={t("paths.eyebrow")}
        title={t("paths.title")}
        description={t("paths.desc")}
      />
      <section className="panel goal-panel">
        <h2>{tx("Current learning focus", "Trọng tâm học hiện tại")}</h2>
        <p className="muted small">
          {tx(
            "Begin with foundations by default. Pin a project topic for parallel, just-in-time learning; recommendations prioritize its missing prerequisites.",
            "Mặc định hãy bắt đầu từ nền tảng. Ghim một chủ đề dự án để học song song, đúng lúc cần; gợi ý sẽ ưu tiên các kiến thức tiên quyết còn thiếu của nó.",
          )}
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void act({
              type: "goal",
              goal: selectedGoal,
              focusTopic: selectedFocus || null,
              focusReason: selectedReason,
            })
              .then(() =>
                notify(
                  tx(
                    "Goal and recommendations updated.",
                    "Đã cập nhật mục tiêu và gợi ý.",
                  ),
                ),
              )
              .catch(() => {});
          }}
        >
          <div className="form-row">
            <label>
              {tx("Direction", "Hướng học")}
              <select
                aria-label={tx("Learning direction", "Hướng học")}
                value={selectedGoal}
                onChange={(e) => setGoal(e.target.value)}
              >
                <option value="Foundations">
                  {tx("Foundations", "Nền tảng")}
                </option>
                {domains.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </label>
            <label>
              {tx("Project topic / focus", "Chủ đề dự án / trọng tâm")}
              <select
                aria-label={tx("Project topic", "Chủ đề dự án")}
                value={selectedFocus}
                onChange={(e) => setFocus(e.target.value)}
              >
                <option value="">
                  {tx("No pinned topic", "Chưa ghim chủ đề")}
                </option>
                {topics.map((t) => (
                  <option value={t.id} key={t.id}>
                    {t.id} · {title(t.id)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            {tx("Why choose this goal?", "Vì sao chọn mục tiêu này?")}
            <input
              value={selectedReason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={1000}
              placeholder={tx(
                "For example: understand coordinate frames for a camera project…",
                "Ví dụ: hiểu hệ tọa độ cho một dự án camera…",
              )}
            />
          </label>
          <button disabled={busy} className="button" type="submit">
            {tx("Save goal", "Lưu mục tiêu")}
            <Route size={16} />
          </button>
        </form>
        {state.progress.focusTopic && (
          <p className="small">
            {tx("Pinned:", "Đã ghim:")}{" "}
            <Link href={`/lessons/${state.progress.focusTopic}`}>
              {state.progress.focusTopic} · {title(state.progress.focusTopic)}
            </Link>{" "}
            · {state.progress.focusReason}
          </p>
        )}
      </section>
      <div className="path-timeline">
        {milestones.map((stage) => (
          <section className="path-stage" key={stage.name}>
            <span className="path-dot" />
            <div>
              <h2>
                {lang === "vi" ? milestonesVi[stage.name][0] : stage.name}
              </h2>
              <p className="muted">
                {lang === "vi"
                  ? milestonesVi[stage.name][1]
                  : stage.description}
              </p>
              <div className="panel path-topics">
                {stage.ids.map((id) => {
                  const t = topicMap[id],
                    missing = t.prerequisites.filter(
                      (p) => state.mastery[p].level < 1,
                    );
                  return (
                    <Link key={id} href={`/lessons/${id}`}>
                      <span className="topic-id">{id}</span>
                      <div>
                        <strong>{title(t.id)}</strong>
                        <small>
                          {missing.length
                            ? `${tx("Prerequisites not mastered yet:", "Kiến thức tiên quyết chưa nắm vững:")} ${missing.join(", ")}`
                            : tx(
                                "Ready to check what you know",
                                "Sẵn sàng kiểm tra kiến thức",
                              )}
                          {!state.lessonIds.includes(id)
                            ? ` · ${tx("Overview", "Tổng quan")}`
                            : ""}
                        </small>
                      </div>
                      <Status mastery={state.mastery[id]} />
                    </Link>
                  );
                })}
              </div>
            </div>
          </section>
        ))}
      </div>
      <section className="panel">
        <h2>{tx("Knowledge debt", "Chỗ còn vướng")}</h2>
        <p className="muted small">
          {tx(
            "Difficulties you recorded, separate from gaps detected by assessments.",
            "Các khó khăn bạn đã ghi lại, tách biệt với lỗ hổng do bài kiểm tra phát hiện.",
          )}
        </p>
        {debt.length ? (
          debt.slice(0, 12).map((d) => (
            <div className="debt-row" key={d.id}>
              <Link href={`/lessons/${d.topicId}`}>{d.topicId}</Link>
              <p>{d.text}</p>
              <small>{dateText(d.at)}</small>
            </div>
          ))
        ) : (
          <p className="muted">
            {tx("No difficulties recorded yet.", "Chưa ghi khó khăn nào.")}
          </p>
        )}
      </section>
    </div>
  );
}
export function Tutor() {
  const { state, act, busy, notify, title } = useCore();
  const { t, tx } = useI18n();
  const params = useSearchParams();
  const [topic, setTopic] = useState(
      params.get("topic") && topicMap[params.get("topic")!]
        ? params.get("topic")!
        : "M01",
    ),
    [kind, setKind] = useState("learning"),
    [question, setQuestion] = useState(""),
    [feedback, setFeedback] = useState("");
  const { data } = useTopic(topic);
  if (!state) return <Loading />;
  const objectives =
    data?.lesson?.meta.objectives ?? data?.overview.concepts ?? [];
  const context = contextFor(topic, state.progress, objectives, kind, question);
  const ex = practices
    .filter((p) => p.topicId === topic)
    .map((p) => p.task)
    .join("\n");
  const fullContext =
    context +
    (kind === "exercise"
      ? `\nExercise:\n${ex || data?.lesson?.meta.labs.join("\n") || data?.overview.task || "Choose an exercise that matches the objectives."}`
      : "");
  async function copy() {
    try {
      await copyText(fullContext);
      notify(
        tx(
          "Context copied. Paste it into your ChatGPT Project yourself.",
          "Đã sao chép ngữ cảnh. Hãy tự dán nó vào ChatGPT Project của bạn.",
        ),
      );
    } catch (e) {
      notify(
        e instanceof Error
          ? e.message
          : tx("Unable to copy.", "Không sao chép được."),
      );
    }
  }
  return (
    <div className="page">
      <PageHeading
        eyebrow={t("tutor.eyebrow")}
        title={t("tutor.title")}
        description={t("tutor.desc")}
      />
      <div className="two-columns tutor-columns">
        <section className="panel">
          <h2>{tx("Prepare context", "Chuẩn bị ngữ cảnh")}</h2>
          <label>
            {tx("Topic", "Chủ đề")}
            <select
              aria-label={tx("Handoff topic", "Chủ đề cần chuyển")}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            >
              {topics.map((t) => (
                <option value={t.id} key={t.id}>
                  {t.id} · {title(t.id)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {tx("Context type", "Loại ngữ cảnh")}
            <select
              aria-label={tx("Handoff type", "Loại ngữ cảnh")}
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="learning">
                {tx("Copy Learning Context", "Sao chép Learning Context")}
              </option>
              <option value="exercise">
                {tx(
                  "Copy Exercise for AI Tutor",
                  "Sao chép bài tập cho AI Tutor",
                )}
              </option>
              <option value="debugging">
                {tx("Copy Debugging Context", "Sao chép ngữ cảnh gỡ lỗi")}
              </option>
              <option value="summary">
                {tx("Copy Session Summary", "Sao chép tóm tắt buổi học")}
              </option>
            </select>
          </label>
          <label>
            {tx(
              "Question / failing code / observed result",
              "Câu hỏi / code lỗi / kết quả quan sát được",
            )}
            <textarea
              aria-label={tx("Question for AI Tutor", "Câu hỏi cho AI Tutor")}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={5}
              maxLength={20000}
              placeholder={tx(
                "I tried…, expected…, but observed…",
                "Mình đã thử…, kỳ vọng…, nhưng thấy…",
              )}
            />
          </label>
          <button
            disabled={!data}
            onClick={() => void copy()}
            className="button primary"
          >
            <Copy size={16} />
            {tx("Copy context", "Sao chép ngữ cảnh")}
          </button>
          <p className="small muted">
            {tx(
              "No data is sent through an API. Preview the content and choose what to copy.",
              "Không có dữ liệu nào được gửi qua API. Hãy xem trước nội dung và chọn phần cần sao chép.",
            )}
          </p>
        </section>
        <section className="panel">
          <h2>{tx("Content preview", "Xem trước nội dung")}</h2>
          <textarea
            className="context-output"
            aria-label={tx("Handoff context", "Ngữ cảnh chuyển giao")}
            value={fullContext}
            readOnly
            rows={20}
          />
        </section>
      </div>
      <section className="panel">
        <h2>{tx("Paste study feedback", "Dán phản hồi học tập")}</h2>
        <p className="muted">
          {tx(
            "ChatGPT feedback is stored as AI-reported notes. It does not change verified mastery.",
            "Phản hồi từ ChatGPT được lưu như ghi chú do AI báo cáo. Nó không thay đổi mức nắm vững đã kiểm chứng.",
          )}
        </p>
        <details>
          <summary>
            {tx("Required JSON format", "Định dạng JSON bắt buộc")}
          </summary>
          <CodeBlock
            language="json"
            code={JSON.stringify(
              {
                schema: "corelab-feedback/1",
                topicId: topic,
                summary: "Session summary",
                difficulties: ["Remaining difficulty"],
                nextSteps: ["Next step"],
              },
              null,
              2,
            )}
          />
        </details>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            try {
              const parsed = JSON.parse(feedback);
              void act({ type: "feedback", feedback: parsed })
                .then(() => {
                  setFeedback("");
                  notify(
                    tx(
                      "AI feedback saved as unverified notes.",
                      "Đã lưu phản hồi AI như ghi chú chưa kiểm chứng.",
                    ),
                  );
                })
                .catch(() => {});
            } catch {
              notify(
                tx(
                  "Invalid JSON. Check the example format.",
                  "JSON không hợp lệ. Hãy kiểm tra định dạng ví dụ.",
                ),
              );
            }
          }}
        >
          <textarea
            aria-label={tx("AI feedback JSON", "JSON phản hồi AI")}
            rows={6}
            required
            maxLength={50000}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
          <button className="button" disabled={busy || !feedback} type="submit">
            {tx("Save feedback", "Lưu phản hồi")}
            <Upload size={15} />
          </button>
        </form>
      </section>
    </div>
  );
}
export function Settings({ v2Panel }: { v2Panel?: React.ReactNode } = {}) {
  const { state, act, busy, notify } = useCore();
  const { t, tx } = useI18n();
  const [backup, setBackup] = useState<unknown>(null),
    [preview, setPreview] = useState<{
      attempts: number;
      sessions: number;
      labs: number;
    } | null>(null),
    [confirm, setConfirm] = useState(false),
    [error, setError] = useState(""),
    [validating, setValidating] = useState(false);
  if (!state) return <Loading />;
  async function choose(file: File | undefined) {
    setPreview(null);
    setBackup(null);
    setConfirm(false);
    setError("");
    if (!file) return;
    if (file.size > 8_000_000) {
      setError(tx("Backup limit: 8 MB.", "Giới hạn bản sao lưu: 8 MB."));
      return;
    }
    setValidating(true);
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const res = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: text,
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error);
      setBackup(parsed);
      setPreview(result);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : tx("Invalid backup.", "Bản sao lưu không hợp lệ."),
      );
    } finally {
      setValidating(false);
    }
  }
  return (
    <div className="page settings-page">
      <PageHeading
        eyebrow={t("settings.eyebrow")}
        title={t("nav.settings")}
        description={t("settings.desc")}
      />
      <section className="panel">
        <div className="panel-heading">
          <h2>{tx("Local workspace", "Không gian cục bộ")}</h2>
          <ShieldCheck size={19} />
        </div>
        <div className="settings-stats">
          <div>
            <strong>{state.progress.attempts.length}</strong>
            <span>{tx("Assessment attempts", "Lần làm bài kiểm tra")}</span>
          </div>
          <div>
            <strong>{state.progress.sessions.length}</strong>
            <span>{tx("Sessions / notes", "Buổi học / ghi chú")}</span>
          </div>
          <div>
            <strong>{state.progress.labs.length}</strong>
            <span>{tx("Practice reports", "Báo cáo luyện tập")}</span>
          </div>
        </div>
        <p className="muted small">
          {tx("SQLite at", "SQLite tại")} <code>.local/corelab.sqlite</code>
          {tx(
            ", created automatically when you open the app. Personal data and local keys are excluded from Git. The app uses no analytics or AI services.",
            ", được tạo tự động khi bạn mở ứng dụng. Dữ liệu cá nhân và khóa cục bộ không được đưa vào Git. Ứng dụng không dùng phân tích hay dịch vụ AI.",
          )}
        </p>
      </section>
      {v2Panel}
      {!v2Panel && (
        <div className="two-columns">
          <section className="panel">
            <div className="tool-icon">
              <Download size={23} />
            </div>
            <h2>{tx("Back up progress", "Sao lưu tiến độ")}</h2>
            <p>
              {tx(
                "Export attempts, rubric versions, learning sessions, notes, knowledge debt, review schedules, and lab evidence as schema-versioned JSON.",
                "Xuất các lần làm bài, phiên bản rubric, buổi học, ghi chú, chỗ còn vướng, lịch ôn tập và bằng chứng lab thành JSON có phiên bản schema.",
              )}
            </p>
            <a
              className="button primary"
              href="/api/export"
              download="corelab-backup.json"
            >
              {tx("Export backup JSON", "Xuất JSON sao lưu")}
              <Download size={16} />
            </a>
            <p className="small muted">
              {tx(
                "Backups contain personal learning data. Store them outside the repository; do not upload them to GitHub.",
                "Bản sao lưu chứa dữ liệu học tập cá nhân. Hãy lưu ngoài repository; không tải lên GitHub.",
              )}
            </p>
          </section>
          <section className="panel">
            <div className="tool-icon">
              <Upload size={23} />
            </div>
            <h2>{tx("Restore from backup", "Khôi phục từ bản sao lưu")}</h2>
            <p>
              {tx(
                "Validate the schema and evidence before replacement. A pre-restore snapshot is retained in SQLite to support recovery.",
                "Kiểm tra schema và bằng chứng trước khi thay thế. Một bản chụp trước khi khôi phục được giữ trong SQLite để hỗ trợ phục hồi.",
              )}
            </p>
            <label className="file-label">
              <FileJson size={17} />
              {tx("Choose backup JSON", "Chọn JSON sao lưu")}
              <input
                aria-label={tx(
                  "Choose backup to restore",
                  "Chọn bản sao lưu để khôi phục",
                )}
                type="file"
                accept=".json,application/json"
                onChange={(e) => void choose(e.target.files?.[0])}
              />
            </label>
            {validating && (
              <p role="status">{tx("Validating…", "Đang kiểm tra…")}</p>
            )}
            {error && (
              <p className="error-text" role="alert">
                {error}
              </p>
            )}
            {preview && (
              <div className="restore-preview">
                <p className="verified-text">
                  <Check size={15} />
                  {tx("Valid schema", "Schema hợp lệ")}
                </p>
                <p>
                  {preview.attempts} {tx("attempts", "lần làm bài")} ·{" "}
                  {preview.sessions} {tx("sessions", "buổi")} · {preview.labs}{" "}
                  {tx("labs", "lab")}
                </p>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={confirm}
                    onChange={(e) => setConfirm(e.target.checked)}
                  />
                  {tx(
                    "I confirm replacing all current progress with the selected backup.",
                    "Tôi xác nhận thay toàn bộ tiến độ hiện tại bằng bản sao lưu đã chọn.",
                  )}
                </label>
                <button
                  className="button danger"
                  disabled={!confirm || busy}
                  onClick={() =>
                    void act({ type: "restore", backup, confirm: true })
                      .then(() => {
                        setBackup(null);
                        setPreview(null);
                        setConfirm(false);
                        notify(
                          tx(
                            "Progress restored from backup.",
                            "Đã khôi phục tiến độ từ bản sao lưu.",
                          ),
                        );
                      })
                      .catch(() => {})
                  }
                >
                  {tx("Restore and replace", "Khôi phục và thay thế")}
                </button>
              </div>
            )}
          </section>
        </div>
      )}
      <section className="panel">
        <h2>{tx("Mastery rules", "Quy tắc nắm vững")}</h2>
        <div className="level-table">
          {[
            [
              "L0",
              tx(
                "No verified evidence.",
                "Chưa có bằng chứng được kiểm chứng.",
              ),
            ],
            [
              "L1",
              tx(
                "An independent check (no help) meets the conceptual criteria.",
                "Một bài kiểm tra tự làm (không trợ giúp) đạt tiêu chí về khái niệm.",
              ),
            ],
            [
              "L2",
              tx(
                "Conceptual, numerical, and independent implementation evidence through fixed tests.",
                "Bằng chứng về khái niệm, tính toán và tự cài đặt thông qua test cố định.",
              ),
            ],
            [
              "L3",
              tx(
                "Apply skills to unfamiliar problems and demonstrate retention; independent review required.",
                "Vận dụng kỹ năng vào bài toán lạ và chứng tỏ ghi nhớ; cần được đánh giá độc lập.",
              ),
            ],
            [
              "L4",
              tx(
                "Critically evaluate or extend methods with reviewed research evidence.",
                "Đánh giá phê phán hoặc mở rộng phương pháp với bằng chứng nghiên cứu đã được xem xét.",
              ),
            ],
          ].map(([level, text]) => (
            <div key={level}>
              <span className="mono">{level}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>
        <p className="small muted">
          {tx(
            "The current workflow verifies L1, and L2 for M02/PY01 when all gates are met. Retention retests are recorded separately; repeated quizzes do not establish novel transfer. L3/L4 can be provisionally self-assessed, but the initial content has no certification contracts for them.",
            "Quy trình hiện tại xác nhận L1, và L2 cho M02/PY01 khi đạt mọi điều kiện. Các lần kiểm tra lại để ghi nhớ được ghi riêng; làm lại bài trắc nghiệm không chứng minh khả năng vận dụng mới. L3/L4 có thể tự đánh giá tạm thời, nhưng nội dung ban đầu chưa có hợp đồng chứng nhận cho chúng.",
          )}
        </p>
      </section>
    </div>
  );
}
export function Sources() {
  const { t, tx } = useI18n();
  return (
    <div className="page">
      <PageHeading
        eyebrow={t("sources.eyebrow")}
        title={t("nav.sources")}
        description={t("sources.desc")}
      />
      <div className="panel source-list">
        {sources.map((s) => (
          <a href={s.url} rel="noreferrer" key={s.url}>
            <div>
              <span className="small muted">{s.domain}</span>
              <h2>{s.title}</h2>
              <span className="small muted">{new URL(s.url).hostname}</span>
            </div>
            <ExternalLink size={18} />
          </a>
        ))}
      </div>
      <p className="catalog-note">
        {tx(
          "CoreLab content is independently authored. Copyrighted books, PDFs, and datasets are not redistributed. The source collection is maintained at reference/LEARNING_SOURCES.md.",
          "Nội dung CoreLab được biên soạn độc lập. Sách, PDF và bộ dữ liệu có bản quyền không được phân phối lại. Bộ nguồn được duy trì tại reference/LEARNING_SOURCES.md.",
        )}
      </p>
    </div>
  );
}
