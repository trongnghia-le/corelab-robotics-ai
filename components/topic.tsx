"use client";
import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowRight,
  ArrowLeft,
  BookOpen,
  Check,
  Copy,
  ClipboardCheck,
  Pin,
  FileText,
} from "lucide-react";
import { topicMap, topics } from "@/lib/curriculum";
import { contextFor } from "@/lib/engine";
import type { TopicPayload, Attempt, Assistance, Answers } from "@/lib/types";
import { useCore, Loading, copyText } from "./provider";
import { TopicChips, Status, Matrix, Time, dateText } from "./ui";
import { headingId } from "./markdown";
import { LearningVisual } from "./learning-visual";
const LessonMarkdown = dynamic(
  () => import("./markdown").then((m) => m.LessonMarkdown),
  { loading: () => <p>Đang hiển thị bài học…</p> },
);
export function useTopic(id: string) {
  const [data, setData] = useState<TopicPayload | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    fetch(`/api/topics/${id}`, { signal: controller.signal })
      .then(async (r) => {
        const payload = await r.json();
        if (!r.ok) throw new Error(payload.error);
        setData(payload);
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Không thể mở chủ đề.");
      });
    return () => controller.abort();
  }, [id]);
  return { data, error };
}
export function TopicPage({
  id,
  assessment = false,
}: {
  id: string;
  assessment?: boolean;
}) {
  const { state, act, busy, notify } = useCore();
  const { data, error } = useTopic(id);
  const [context, setContext] = useState("");
  if (error)
    return (
      <div className="page empty-state" role="alert">
        <h1>Không thể mở chủ đề</h1>
        <p>{error}</p>
        <Link href="/roadmap">Quay lại Roadmap</Link>
      </div>
    );
  if (!state || !data) return <Loading />;
  const topic = topicMap[id],
    m = state.mastery[id],
    lesson = data.lesson,
    overview = data.overview;
  const objectives =
    lesson?.meta.objectives ??
    overview.concepts.map((c) => `Giải thích và kiểm chứng: ${c}.`);
  const successors = topics.filter((t) => t.prerequisites.includes(id));
  const authored = topics.filter((t) => state.lessonIds.includes(t.id));
  const pos = authored.findIndex((t) => t.id === id);
  const prev = authored[pos - 1],
    next = authored[pos + 1];
  async function copyContext() {
    const text = contextFor(id, state!.progress, objectives, "learning");
    setContext(text);
    try {
      await copyText(text);
      notify("Đã sao chép Learning Context.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Không thể sao chép.");
    }
  }
  return (
    <div className={`page topic-page ${assessment ? "assessment-page" : ""}`}>
      <div className="topic-breadcrumb">
        <Link href={assessment ? "/assessments" : "/lessons"}>
          {assessment ? "Assessments" : "Lessons"}
        </Link>
        <span>/</span>
        <Link href={`/roadmap?domain=${encodeURIComponent(topic.domain)}`}>
          {topic.domain}
        </Link>
        <span>/</span>
        <span className="mono">{id}</span>
      </div>
      <div className="topic-heading">
        <div className="topic-meta">
          <span className="topic-code">{id}</span>
          <span className={`priority ${topic.priority}`}>{topic.priority}</span>
          <Status mastery={m} />
          {lesson && <Time minutes={lesson.meta.estimated_minutes} />}
        </div>
        <h1>
          {assessment
            ? `Diagnostic · ${topic.title}`
            : (lesson?.meta.title ?? topic.title)}
        </h1>
        <p>{lesson?.meta.summary ?? overview.overview}</p>
        <div className="topic-actions">
          <Link
            className={assessment ? "button" : "button primary"}
            href={`/assessments/${id}`}
          >
            <ClipboardCheck size={16} />
            Kiểm tra năng lực
          </Link>
          <button className="button" onClick={() => void copyContext()}>
            <Copy size={15} />
            Copy Learning Context
          </button>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              void act({
                type: "goal",
                goal: state.progress.goal,
                focusTopic: id,
                focusReason: "Chủ đề được ghim từ workspace.",
              })
                .then(() => notify(`Đã ghim ${id} làm trọng tâm.`))
                .catch(() => {})
            }
          >
            <Pin size={15} />
            {state.progress.focusTopic === id
              ? "Đã ghim trọng tâm"
              : "Ghim trọng tâm"}
          </button>
          {assessment && (
            <Link className="button" href={`/lessons/${id}`}>
              <BookOpen size={15} />
              Đọc bài học
            </Link>
          )}
        </div>
      </div>
      {context && (
        <details className="context-preview">
          <summary>Xem Learning Context vừa tạo</summary>
          <textarea
            aria-label="Learning Context"
            readOnly
            value={context}
            rows={9}
          />
        </details>
      )}
      <section className="topic-prereqs">
        <h2>Tiền đề đề xuất</h2>
        <TopicChips ids={topic.prerequisites} />
        {topic.prerequisites.some((p) => state.mastery[p].level < 1) && (
          <p className="small warning-text">
            Một số tiền đề chưa được kiểm chứng. Bạn vẫn có thể học bài này; nên
            kiểm tra nền tảng trước.
          </p>
        )}
      </section>
      <Matrix mastery={m} />
      {assessment ? (
        <AssessmentWorkspace id={id} data={data} />
      ) : (
        <div className="reading-layout">
          <article className="lesson-article">
            <div className="objectives-box">
              <div className="eyebrow">SAU BÀI HỌC NÀY</div>
              <ul>
                {objectives.map((o) => (
                  <li key={o}>
                    <Check size={15} />
                    {o}
                  </li>
                ))}
              </ul>
            </div>
            {lesson ? (
              <>
                <LearningVisual topicId={id} />
                <LessonMarkdown body={lesson.body} />
                <div className="reading-complete">
                  <div>
                    <strong>Đọc xong? Chuyển từ hiểu sang kiểm chứng.</strong>
                    <p>
                      Ghi nhận việc đọc chỉ lưu hoạt động, không tăng mastery.
                    </p>
                  </div>
                  <button
                    disabled={busy}
                    onClick={() =>
                      void act({
                        type: "session",
                        topicId: id,
                        kind: "reading",
                        text: `Đã đọc ${lesson.meta.title}`,
                        minutes: 0,
                      })
                        .then(() =>
                          notify(
                            "Đã lưu hoạt động đọc. Mastery không thay đổi.",
                          ),
                        )
                        .catch(() => {})
                    }
                  >
                    Đánh dấu đã đọc
                  </button>
                </div>
                <Link className="button primary" href={`/assessments/${id}`}>
                  Bắt đầu diagnostic
                  <ArrowRight size={16} />
                </Link>
              </>
            ) : (
              <OverviewBody data={data} domain={topic.domain} />
            )}
            <Notebook id={id} />
            <div className="lesson-nav">
              {prev ? (
                <Link href={`/lessons/${prev.id}`}>
                  <ArrowLeft size={16} />
                  <span>
                    <small>Bài trước trong thư viện</small>
                    {prev.id} · {prev.title}
                  </span>
                </Link>
              ) : (
                <span />
              )}
              {next && (
                <Link href={`/lessons/${next.id}`}>
                  <span>
                    <small>Bài tiếp theo trong thư viện</small>
                    {next.id} · {next.title}
                  </span>
                  <ArrowRight size={16} />
                </Link>
              )}
            </div>
            <section className="related-topics">
              <h2>Chủ đề dùng nền tảng này</h2>
              <TopicChips ids={successors.map((t) => t.id)} />
            </section>
          </article>
          <aside className="lesson-toc">
            <div className="eyebrow">TRONG BÀI HỌC</div>
            {lesson ? (
              lesson.body
                .split("\n")
                .filter((l) => l.startsWith("## "))
                .map((l) => (
                  <a href={`#${headingId(l.slice(3))}`} key={l}>
                    {l.slice(3).split(" · ")[0]}
                  </a>
                ))
            ) : (
              <>
                <a href="#overview">Tổng quan</a>
                <a href="#application">Ứng dụng</a>
                <a href="#practice">Thực hành</a>
              </>
            )}
            <div className="toc-note">
              <FileText size={18} />
              <p>Diagnostic → Learn → Derive → Implement → Verify → Transfer</p>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
const resourceMap: Record<string, { title: string; url: string }[]> = {
  Mathematics: [
    {
      title: "MIT OCW · Linear Algebra",
      url: "https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/",
    },
  ],
  Programming: [
    { title: "Python Tutorial", url: "https://docs.python.org/3/tutorial/" },
    { title: "LearnCpp", url: "https://www.learncpp.com/" },
  ],
  "Machine Learning": [
    { title: "Dive into Deep Learning", url: "https://d2l.ai/" },
  ],
  Robotics: [
    {
      title: "Modern Robotics",
      url: "https://modernrobotics.northwestern.edu/",
    },
  ],
  "Simulation & Systems": [
    { title: "MuJoCo documentation", url: "https://mujoco.readthedocs.io/" },
  ],
  "Computer Vision": [
    { title: "Stanford CS231n", url: "https://cs231n.stanford.edu/" },
  ],
  "Reinforcement & Robot Learning": [
    {
      title: "David Silver lectures",
      url: "https://www.davidsilver.uk/teaching/",
    },
  ],
  "Embodied & Cognitive Robotics": [
    { title: "LeRobot", url: "https://github.com/huggingface/lerobot" },
  ],
  "Scientific Research": [
    { title: "CLVR publications", url: "https://clvrai.com/publications/" },
  ],
};
function OverviewBody({
  data,
  domain,
}: {
  data: TopicPayload;
  domain: string;
}) {
  return (
    <div className="prose">
      <div className="info-banner">
        Overview · Chủ đề này chưa có bài học hoặc diagnostic đầy đủ. Không có
        tiến độ giả định.
      </div>
      <h2 id="overview">Tổng quan</h2>
      <p>{data.overview.overview}</p>
      <h2 id="application">Ứng dụng thực tế</h2>
      <p>{data.overview.application}</p>
      <h2 id="practice">Định hướng tự học</h2>
      <p>{data.overview.task}</p>
      <p>
        Học từ nguồn bên dưới, tự viết suy luận và kiểm thử. Ghi chú hoặc tự
        đánh giá vẫn là bằng chứng chưa kiểm chứng.
      </p>
      <h2>Tài liệu liên quan</h2>
      <ul>
        {(resourceMap[domain] ?? resourceMap.Robotics).map((s) => (
          <li key={s.url}>
            <a href={s.url} rel="noreferrer">
              {s.title}
            </a>{" "}
            · nguồn cấp lĩnh vực; chọn chương phù hợp với mục tiêu, không phải
            một bài học tương đương.
          </li>
        ))}
      </ul>
    </div>
  );
}
export function Notebook({ id }: { id: string }) {
  const { state, act, busy, notify } = useCore();
  const [text, setText] = useState(""),
    [kind, setKind] = useState("note"),
    [minutes, setMinutes] = useState(15),
    [level, setLevel] = useState(1);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    try {
      await act({
        type: "session",
        topicId: id,
        kind,
        text,
        minutes,
        provisionalLevel: kind === "self_assessment" ? level : undefined,
      });
      setText("");
      notify("Đã lưu ghi chép cục bộ.");
    } catch {}
  }
  const notes =
    state?.progress.sessions
      .filter((s) => s.topicId === id && s.kind !== "reading")
      .slice(-5)
      .reverse() ?? [];
  return (
    <section className="notebook panel">
      <div className="panel-heading">
        <h2>Research notebook</h2>
        <FileText size={18} />
      </div>
      <p className="small muted">
        Lưu suy luận, kết quả thử nghiệm và điểm chưa rõ. Tự đánh giá tách biệt
        với năng lực kiểm chứng.
      </p>
      <form onSubmit={submit}>
        <div className="form-row">
          <label>
            Loại ghi chép
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="note">Ghi chú</option>
              <option value="difficulty">Knowledge debt · khó khăn</option>
              <option value="practice">Kết quả thực hành</option>
              <option value="self_assessment">Tự đánh giá · provisional</option>
            </select>
          </label>
          <label>
            Thời gian (phút)
            <input
              type="number"
              min="0"
              max="1440"
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            />
          </label>
          {kind === "self_assessment" && (
            <label>
              Mức tự đánh giá
              <select
                value={level}
                onChange={(e) => setLevel(Number(e.target.value))}
              >
                {[1, 2, 3, 4].map((l) => (
                  <option key={l} value={l}>
                    Provisional L{l}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        <label className="sr-only" htmlFor={`note-${id}`}>
          Nội dung ghi chép
        </label>
        <textarea
          id={`note-${id}`}
          required
          maxLength={20000}
          rows={4}
          placeholder="Tôi đã thử điều gì? Kết quả nào chưa giải thích được?"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          className="button"
          disabled={busy || !text.trim()}
          type="submit"
        >
          Lưu ghi chép
        </button>
      </form>
      {notes.length > 0 && (
        <div className="note-list">
          {notes.map((n) => (
            <div key={n.id}>
              <div className="between">
                <span className="status">
                  {n.kind}
                  {n.provisionalLevel
                    ? ` · Provisional L${n.provisionalLevel}`
                    : ""}
                </span>
                <small className="muted">{dateText(n.at)}</small>
              </div>
              <p>{n.text}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
function AssessmentWorkspace({ id, data }: { id: string; data: TopicPayload }) {
  const { state, act, busy } = useCore();
  const [answers, setAnswers] = useState<Answers>({}),
    [assistance, setAssistance] = useState<Assistance>("A0"),
    [result, setResult] = useState<Attempt | null>(null),
    [submitError, setSubmitError] = useState("");
  const assessment = data.assessment;
  if (!state) return null;
  const attempts = state.progress.attempts
    .filter((a) => a.topicId === id)
    .slice()
    .reverse();
  const m = state.mastery[id];
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitError("");
    try {
      const attempt = (await act({
        type: "attempt",
        topicId: id,
        answers,
        assistance,
      })) as Attempt;
      setResult(attempt);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "Không thể lưu lần thử.");
    }
  }
  return (
    <div className="assessment-layout">
      <section>
        <div className="panel gates">
          <h2>Bằng chứng cần có</h2>
          <ul>
            <li className={m.dimensions.C ? "verified-text" : ""}>
              {m.dimensions.C ? "✓" : "○"} L1 · Diagnostic A0 ≥80%, không sai
              câu critical.
            </li>
            <li className={m.dimensions.M ? "verified-text" : ""}>
              {m.dimensions.M ? "✓" : "○"} M · Các phép tính đạt tiêu chí của
              assessment.
            </li>
            <li className={m.dimensions.I ? "verified-text" : ""}>
              {m.dimensions.I ? "✓" : "○"} I · Tự triển khai và nhập báo cáo
              kiểm thử cục bộ hợp lệ.
            </li>
            <li className={m.dimensions.T ? "verified-text" : ""}>
              {m.dimensions.T ? "✓" : "○"} Retention · Làm lại A0 sau ít nhất 7
              ngày.
            </li>
          </ul>
          <p className="small muted">
            L2 cần bằng chứng khái niệm, toán và triển khai. L3/L4 cần bài
            chuyển giao mới hoặc đóng góp nghiên cứu được review độc lập; quiz
            này không chứng nhận các mức đó.
          </p>
          <Link href={`/practice?topic=${id}`} className="text-link">
            Mở hướng dẫn thực hành
            <ArrowRight size={14} />
          </Link>
        </div>
        {assessment ? (
          <form className="assessment-form" onSubmit={submit}>
            <div className="panel">
              <div className="between">
                <h2>Diagnostic</h2>
                <span className="mono small muted">
                  CONTRACT v{assessment.version}
                </span>
              </div>
              <p className="muted small">
                Thử trước khi xem lời giải. Câu ngắn theo rubric được lưu, không
                chấm tự động.
              </p>
              <label>
                Mức trợ giúp
                <select
                  aria-label="Mức trợ giúp"
                  value={assistance}
                  onChange={(e) => setAssistance(e.target.value as Assistance)}
                >
                  <option value="A0">A0 · Tự làm, không trợ giúp</option>
                  <option value="A1">A1 · Gợi ý khái niệm</option>
                  <option value="A2">A2 · Gợi ý cụ thể / ví dụ</option>
                  <option value="A3">A3 · Có lời giải từ AI / tài liệu</option>
                </select>
              </label>
            </div>
            {assessment.questions.map((q, i) => (
              <fieldset className="question panel" key={q.id}>
                <legend>
                  <span className="question-number">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span>{q.prompt}</span>
                </legend>
                <div className="question-tags">
                  <span>{q.dimension}</span>
                  {q.critical && <span>CRITICAL</span>}
                  <span>
                    {q.kind === "short"
                      ? "RUBRIC · CHƯA KIỂM CHỨNG"
                      : q.kind === "number"
                        ? "NUMERICAL"
                        : "CONCEPT"}
                  </span>
                </div>
                {q.kind === "choice" ? (
                  <div className="choices">
                    {q.options?.map((o, j) => (
                      <label
                        className={
                          answers[q.id] === String(j)
                            ? "choice chosen"
                            : "choice"
                        }
                        key={o}
                      >
                        <input
                          required
                          type="radio"
                          name={q.id}
                          value={j}
                          checked={answers[q.id] === String(j)}
                          onChange={(e) =>
                            setAnswers((a) => ({
                              ...a,
                              [q.id]: e.target.value,
                            }))
                          }
                        />
                        <span>{o}</span>
                      </label>
                    ))}
                  </div>
                ) : q.kind === "number" ? (
                  <label className="number-answer">
                    Đáp án (dùng dấu chấm thập phân)
                    <input
                      aria-label={`Đáp án ${q.id}`}
                      required
                      type="text"
                      inputMode="decimal"
                      placeholder="Nhập một số…"
                      value={answers[q.id] ?? ""}
                      onChange={(e) =>
                        setAnswers((a) => ({ ...a, [q.id]: e.target.value }))
                      }
                    />
                  </label>
                ) : (
                  <>
                    <textarea
                      aria-label="Câu trả lời theo rubric"
                      rows={5}
                      maxLength={10000}
                      value={answers[q.id] ?? ""}
                      onChange={(e) =>
                        setAnswers((a) => ({ ...a, [q.id]: e.target.value }))
                      }
                    />
                    <ul className="rubric">
                      {q.rubric?.map((r) => (
                        <li key={r}>{r}</li>
                      ))}
                    </ul>
                  </>
                )}
              </fieldset>
            ))}
            <button className="button primary" type="submit" disabled={busy}>
              {busy ? "Đang lưu…" : "Nộp và lưu diagnostic"}
              <ArrowRight size={16} />
            </button>
            {submitError && (
              <p role="alert" className="error-text">
                {submitError}
              </p>
            )}
          </form>
        ) : (
          <div className="panel empty-state">
            <h2>Chưa có diagnostic cho chủ đề này</h2>
            <p>
              Lưu ghi chú và kết quả tự học vào notebook. Chúng vẫn là dữ liệu
              chưa kiểm chứng.
            </p>
          </div>
        )}
        {result && (
          <div className="panel assessment-result" role="status">
            <div className="between">
              <h2>Kết quả · {result.grade.score}%</h2>
              <span
                className={`status ${result.grade.passed && result.assistance === "A0" ? "verified" : ""}`}
              >
                {result.grade.passed
                  ? result.assistance === "A0"
                    ? "Đạt diagnostic A0"
                    : "Đạt có trợ giúp · chưa kiểm chứng"
                  : "Cần học và thử lại"}
              </span>
            </div>
            <p className="muted small">
              {dateText(result.at)} · {result.assistance} · Đã lưu vào SQLite
            </p>
            {result.grade.items.map((item) => (
              <div className="feedback-item" key={item.id}>
                <strong
                  className={
                    item.correct === true
                      ? "verified-text"
                      : item.correct === false
                        ? "error-text"
                        : "muted"
                  }
                >
                  {item.id} ·{" "}
                  {item.correct === null
                    ? "Đối chiếu rubric"
                    : item.correct
                      ? "Đúng"
                      : "Chưa đúng"}
                </strong>
                <p>{item.feedback}</p>
              </div>
            ))}
            <Link className="button" href={`/lessons/${id}`}>
              Xem lại lý thuyết
              <BookOpen size={15} />
            </Link>
          </div>
        )}
        <Notebook id={id} />
      </section>
      <aside className="evidence-history">
        <div className="panel">
          <h2>Lịch sử bằng chứng</h2>
          {attempts.length ? (
            attempts.map((a) => (
              <details key={a.id}>
                <summary>
                  <strong>
                    {a.grade.score}% · {a.assistance}
                  </strong>
                  <small>{dateText(a.at)}</small>
                </summary>
                <p className="small muted">
                  Assessment v{a.assessmentVersion} · {a.id}
                </p>
                {a.grade.items.map((i) => (
                  <p className="small" key={i.id}>
                    {i.id}:{" "}
                    {i.correct === null
                      ? "Rubric"
                      : i.correct
                        ? "Đúng"
                        : "Chưa đúng"}{" "}
                    · {i.feedback}
                  </p>
                ))}
              </details>
            ))
          ) : (
            <p className="muted small">
              Chưa có lần thử nào. Không có bằng chứng không đồng nghĩa với
              không có năng lực.
            </p>
          )}
          {state.progress.labs
            .filter((l) => l.topicId === id)
            .map((l) => (
              <div className="lab-evidence" key={l.id}>
                <strong className="verified-text">
                  Báo cáo fixed-tests · {l.assistance}
                </strong>
                <small>{dateText(l.at)}</small>
                <code>SHA256 {l.sourceHash.slice(0, 16)}…</code>
                <p className="small">
                  {l.assistance === "A0"
                    ? "Có bằng chứng triển khai độc lập theo tự khai mức trợ giúp."
                    : "Có trợ giúp · chỉ tính thực hành."}
                </p>
              </div>
            ))}
        </div>
        <div className="quiet-note">
          Bằng chứng là lịch sử, không bị xóa khi lần ôn tập chưa đạt. Lần thử
          sai tạo điểm cần ôn.
        </div>
      </aside>
    </div>
  );
}
