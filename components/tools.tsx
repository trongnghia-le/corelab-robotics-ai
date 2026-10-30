"use client";
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
import { sources } from "@/lib/resources";
import { useCore, Loading, copyText } from "./provider";
import { useTopic, Notebook } from "./topic";
import { PageHeading, Status, TopicChips, dateText } from "./ui";
export function Practice() {
  const { state, act, busy, notify } = useCore();
  const params = useSearchParams();
  const [topic, setTopic] = useState(params.get("topic") ?? ""),
    [report, setReport] = useState("");
  if (!state) return <Loading />;
  const shown = practices.filter((p) => !topic || p.topicId === topic);
  const exact = topic && topicMap[topic];
  async function importReport(e: FormEvent) {
    e.preventDefault();
    try {
      await act({ type: "lab", report: JSON.parse(report) });
      setReport("");
      notify("Đã nhập báo cáo kiểm thử. Xem bằng chứng trong Assessments.");
    } catch (e) {
      if (e instanceof SyntaxError) notify("Báo cáo phải là JSON hợp lệ.");
    }
  }
  return (
    <div className="page">
      <PageHeading
        eyebrow="IMPLEMENT → VERIFY → TRANSFER"
        title="Tự triển khai. Tự kiểm chứng."
        description="Viết code trong VS Code và chạy kiểm thử từ terminal của bạn. CoreLab không chạy code gửi qua trình duyệt."
      />
      <div className="info-banner">
        <ShieldCheck size={19} />
        <span>
          Fixed-tests hiện hỗ trợ M02 và PY01. Các bài khác có hướng dẫn và
          notebook; kết quả tự báo cáo không tăng năng lực kiểm chứng.
        </span>
      </div>
      <div className="filters">
        <select
          aria-label="Chọn chủ đề thực hành"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        >
          <option value="">Tất cả bài thực hành</option>
          {topics.map((t) => (
            <option key={t.id} value={t.id}>
              {t.id} · {t.title}
            </option>
          ))}
        </select>
        {topic && <button onClick={() => setTopic("")}>Xem tất cả</button>}
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
                  <span className="muted small">{p.kind}</span>
                </div>
                <span className={`status ${p.verified ? "verified" : ""}`}>
                  {p.verified ? "Có fixed verifier" : "Practice · tự báo cáo"}
                </span>
              </div>
              <h2>{p.title}</h2>
              <p>{p.task}</p>
              <TopicChips ids={topicMap[p.topicId].prerequisites} />
              <div className="command-block">
                <code>{p.command}</code>
              </div>
              <div className="topic-actions">
                <a className="button" download href={p.starter}>
                  <Download size={15} />
                  Tải starter
                </a>
                <Link className="button" href={`/lessons/${p.topicId}`}>
                  Lý thuyết
                  <ArrowRight size={15} />
                </Link>
                <Link className="button" href={`/assessments/${p.topicId}`}>
                  Xem bằng chứng
                  <ArrowRight size={15} />
                </Link>
              </div>
            </div>
          </section>
        ))}
      </div>
      {shown.length === 0 && exact && (
        <div className="panel">
          <h2>Thực hành theo mục tiêu của {exact.title}</h2>
          <p>
            Chưa có fixed verifier riêng cho chủ đề này. Dùng phần Independent
            practice trong bài học hoặc định hướng ở overview, rồi ghi giả định,
            suy luận và kết quả vào notebook.
          </p>
          <Link className="button" href={`/lessons/${topic}`}>
            Mở chủ đề
            <ArrowRight size={16} />
          </Link>
        </div>
      )}
      <section className="panel import-report">
        <h2>Nhập báo cáo kiểm thử cục bộ</h2>
        <p className="muted small">
          Runner lưu hash source, thời gian, contract v1, mức trợ giúp và chữ ký
          cục bộ. A3 chỉ ghi nhận thực hành; một lần A0 mới có thể tạo bằng
          chứng I. Đây là bằng chứng học cá nhân, không phải thi có giám sát.
        </p>
        <label className="file-label">
          <Upload size={16} />
          Chọn report JSON
          <input
            aria-label="Chọn báo cáo lab"
            type="file"
            accept="application/json,.json"
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (f) {
                if (f.size > 10000) {
                  notify("Báo cáo quá lớn.");
                  return;
                }
                setReport(await f.text());
              }
            }}
          />
        </label>
        <form onSubmit={importReport}>
          <textarea
            aria-label="Báo cáo kiểm thử JSON"
            placeholder="Dán nội dung .local/M02-report.json…"
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
            Nhập báo cáo
            <Upload size={16} />
          </button>
        </form>
        <p className="small muted">
          Chỉ CLI trong terminal mới thực thi file Python. Nút này chỉ kiểm tra
          và lưu báo cáo.
        </p>
      </section>
      {topic && <Notebook key={topic} id={topic} />}
    </div>
  );
}
const milestones = [
  {
    name: "01 · Nền tảng toán & lập trình",
    description: "Ký hiệu → vector → ma trận, song song với Python và C++.",
    ids: ["M01", "PY01", "CPP01", "M02", "M03", "PY07", "CPP02", "T04"],
  },
  {
    name: "02 · Suy luận và tính toán",
    description: "Đạo hàm, xác suất, linear algebra và NumPy.",
    ids: ["M04", "M05", "M06", "M07", "M08", "PY04", "M10"],
  },
  {
    name: "03 · Machine Learning từ đầu",
    description:
      "Bài toán, baseline, gradient, neural networks và backpropagation.",
    ids: ["ML01", "ML02", "ML04", "ML05"],
  },
  {
    name: "04 · Robot geometry & control",
    description: "Cơ học, cơ cấu, frame, kinematics, dynamics và feedback.",
    ids: ["R01", "R02", "M12", "R03", "R04", "R06", "R07", "C01"],
  },
  {
    name: "05 · Vision & sequential decisions",
    description: "Ảnh số và MDP; mở các nhánh tiếp theo theo tiền đề.",
    ids: ["V01", "RL01", "RL02", "V02", "V03", "RL03"],
  },
  {
    name: "06 · Robot Learning & Cognitive Robotics",
    description:
      "Bản đồ dài hạn: học từ tương tác, biểu diễn, planning và research.",
    ids: ["RL17", "E01", "E02", "E07", "E08", "E10", "E12", "RS01", "RS02"],
  },
];
export function Paths() {
  const { state, act, busy, notify } = useCore();
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
        eyebrow="ZERO VERIFIED KNOWLEDGE → INDEPENDENT RESEARCH"
        title="Một lộ trình, nhiều nhánh mở."
        description="Đi theo tiền đề và bằng chứng. Không cần hoàn thành cả lĩnh vực để bắt đầu một nhánh phù hợp."
      />
      <section className="panel goal-panel">
        <h2>Trọng tâm học hiện tại</h2>
        <p className="muted small">
          Mặc định bắt đầu từ nền tảng. Ghim chủ đề dự án để học just-in-time
          song song; đề xuất sẽ ưu tiên chuỗi tiền đề còn thiếu.
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
              .then(() => notify("Đã cập nhật mục tiêu và đề xuất."))
              .catch(() => {});
          }}
        >
          <div className="form-row">
            <label>
              Định hướng
              <select
                aria-label="Định hướng học"
                value={selectedGoal}
                onChange={(e) => setGoal(e.target.value)}
              >
                <option>Foundations</option>
                {domains.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </label>
            <label>
              Chủ đề dự án / focus
              <select
                aria-label="Chủ đề dự án"
                value={selectedFocus}
                onChange={(e) => setFocus(e.target.value)}
              >
                <option value="">Không ghim chủ đề</option>
                {topics.map((t) => (
                  <option value={t.id} key={t.id}>
                    {t.id} · {t.title}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Vì sao chọn mục tiêu này?
            <input
              value={selectedReason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={1000}
              placeholder="Ví dụ: cần hiểu coordinate frames cho dự án camera…"
            />
          </label>
          <button disabled={busy} className="button" type="submit">
            Lưu mục tiêu
            <Route size={16} />
          </button>
        </form>
        {state.progress.focusTopic && (
          <p className="small">
            Đang ghim:{" "}
            <Link href={`/lessons/${state.progress.focusTopic}`}>
              {state.progress.focusTopic} ·{" "}
              {topicMap[state.progress.focusTopic].title}
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
              <h2>{stage.name}</h2>
              <p className="muted">{stage.description}</p>
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
                        <strong>{t.title}</strong>
                        <small>
                          {missing.length
                            ? `Tiền đề cần bằng chứng: ${missing.join(", ")}`
                            : "Có thể bắt đầu diagnostic"}
                          {!state.lessonIds.includes(id) ? " · Overview" : ""}
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
        <h2>Knowledge debt</h2>
        <p className="muted small">
          Khó khăn do bạn ghi nhận, tách biệt với lỗi phát hiện qua assessment.
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
            Chưa có khó khăn được ghi nhận. Dùng notebook trong mỗi chủ đề để
            lưu câu hỏi còn mở.
          </p>
        )}
      </section>
    </div>
  );
}
export function Tutor() {
  const { state, act, busy, notify } = useCore();
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
      ? `\nExercise:\n${ex || data?.lesson?.meta.labs.join("\n") || data?.overview.task || "Chọn bài tập phù hợp mục tiêu."}`
      : "");
  async function copy() {
    try {
      await copyText(fullContext);
      notify("Đã sao chép ngữ cảnh. Bạn tự dán vào ChatGPT Project.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Không thể sao chép.");
    }
  }
  return (
    <div className="page">
      <PageHeading
        eyebrow="CHATGPT PROJECT · MANUAL HANDOFF"
        title="Một tutor. Một nguồn sự thật."
        description="Mang đúng ngữ cảnh vào cuộc trò chuyện. CoreLab vẫn giữ tiến độ và bằng chứng trên máy bạn."
      />
      <div className="two-columns tutor-columns">
        <section className="panel">
          <h2>Chuẩn bị ngữ cảnh</h2>
          <label>
            Chủ đề
            <select
              aria-label="Chủ đề handoff"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            >
              {topics.map((t) => (
                <option value={t.id} key={t.id}>
                  {t.id} · {t.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Loại ngữ cảnh
            <select
              aria-label="Loại handoff"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="learning">Copy Learning Context</option>
              <option value="exercise">Copy Exercise for AI Tutor</option>
              <option value="debugging">Copy Debugging Context</option>
              <option value="summary">Copy Session Summary</option>
            </select>
          </label>
          <label>
            Câu hỏi / code lỗi / kết quả quan sát
            <textarea
              aria-label="Câu hỏi cho AI Tutor"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={5}
              maxLength={20000}
              placeholder="Tôi đã thử…, kỳ vọng…, nhưng quan sát thấy…"
            />
          </label>
          <button
            disabled={!data}
            onClick={() => void copy()}
            className="button primary"
          >
            <Copy size={16} />
            Sao chép ngữ cảnh
          </button>
          <p className="small muted">
            Không có dữ liệu được gửi đi qua API. Bạn xem và chủ động sao chép
            nội dung.
          </p>
        </section>
        <section className="panel">
          <h2>Xem trước nội dung</h2>
          <textarea
            className="context-output"
            aria-label="Handoff context"
            value={fullContext}
            readOnly
            rows={20}
          />
        </section>
      </div>
      <section className="panel">
        <h2>Dán phản hồi học tập</h2>
        <p className="muted">
          Phản hồi từ ChatGPT được lưu như AI-reported notes. Không thay đổi
          verified mastery.
        </p>
        <details>
          <summary>Định dạng JSON cần dùng</summary>
          <pre>
            {JSON.stringify(
              {
                schema: "corelab-feedback/1",
                topicId: topic,
                summary: "Tóm tắt phiên học",
                difficulties: ["Điểm còn khó"],
                nextSteps: ["Bước tiếp theo"],
              },
              null,
              2,
            )}
          </pre>
        </details>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            try {
              const parsed = JSON.parse(feedback);
              void act({ type: "feedback", feedback: parsed })
                .then(() => {
                  setFeedback("");
                  notify("Đã lưu phản hồi AI như ghi chú chưa kiểm chứng.");
                })
                .catch(() => {});
            } catch {
              notify("JSON chưa hợp lệ. Xem định dạng mẫu.");
            }
          }}
        >
          <textarea
            aria-label="Phản hồi AI dạng JSON"
            rows={6}
            required
            maxLength={50000}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
          <button className="button" disabled={busy || !feedback} type="submit">
            Lưu phản hồi
            <Upload size={15} />
          </button>
        </form>
      </section>
    </div>
  );
}
export function Settings() {
  const { state, act, busy, notify } = useCore();
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
      setError("Giới hạn backup: 8 MB.");
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
      setError(e instanceof Error ? e.message : "Backup chưa hợp lệ.");
    } finally {
      setValidating(false);
    }
  }
  return (
    <div className="page settings-page">
      <PageHeading
        eyebrow="YOUR DATA, ON YOUR MACHINE"
        title="Dữ liệu & cài đặt"
        description="Sao lưu tiến độ, giữ nguyên lịch sử bằng chứng và chủ động kiểm soát dữ liệu cá nhân."
      />
      <section className="panel">
        <div className="panel-heading">
          <h2>Local workspace</h2>
          <ShieldCheck size={19} />
        </div>
        <div className="settings-stats">
          <div>
            <strong>{state.progress.attempts.length}</strong>
            <span>Lần đánh giá</span>
          </div>
          <div>
            <strong>{state.progress.sessions.length}</strong>
            <span>Phiên học / ghi chú</span>
          </div>
          <div>
            <strong>{state.progress.labs.length}</strong>
            <span>Báo cáo thực hành</span>
          </div>
        </div>
        <p className="muted small">
          SQLite tại <code>.local/corelab.sqlite</code>, tự tạo khi mở ứng dụng.
          Dữ liệu cá nhân và local keys được loại khỏi Git. Ứng dụng không dùng
          analytics hoặc dịch vụ AI.
        </p>
      </section>
      <div className="two-columns">
        <section className="panel">
          <div className="tool-icon">
            <Download size={23} />
          </div>
          <h2>Sao lưu tiến độ</h2>
          <p>
            Xuất attempts, rubric versions, learning sessions, notes, knowledge
            debt, review schedules và bằng chứng lab thành JSON có schema.
          </p>
          <a
            className="button primary"
            href="/api/export"
            download="corelab-backup.json"
          >
            Xuất backup JSON
            <Download size={16} />
          </a>
          <p className="small muted">
            Backup có dữ liệu học tập cá nhân. Lưu bên ngoài repo; không đưa lên
            GitHub.
          </p>
        </section>
        <section className="panel">
          <div className="tool-icon">
            <Upload size={23} />
          </div>
          <h2>Khôi phục từ backup</h2>
          <p>
            Kiểm tra schema và bằng chứng trước khi thay thế. Một snapshot trước
            khôi phục được giữ trong SQLite để hỗ trợ phục hồi.
          </p>
          <label className="file-label">
            <FileJson size={17} />
            Chọn backup JSON
            <input
              aria-label="Chọn backup để khôi phục"
              type="file"
              accept=".json,application/json"
              onChange={(e) => void choose(e.target.files?.[0])}
            />
          </label>
          {validating && <p role="status">Đang kiểm tra…</p>}
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          {preview && (
            <div className="restore-preview">
              <p className="verified-text">
                <Check size={15} />
                Schema hợp lệ
              </p>
              <p>
                {preview.attempts} attempts · {preview.sessions} sessions ·{" "}
                {preview.labs} labs
              </p>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={confirm}
                  onChange={(e) => setConfirm(e.target.checked)}
                />
                Tôi xác nhận thay thế toàn bộ tiến độ hiện tại bằng backup đã
                chọn.
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
                      notify("Đã khôi phục tiến độ từ backup.");
                    })
                    .catch(() => {})
                }
              >
                Khôi phục và thay thế
              </button>
            </div>
          )}
        </section>
      </div>
      <section className="panel">
        <h2>Quy tắc năng lực</h2>
        <div className="level-table">
          {[
            ["L0", "Chưa có bằng chứng kiểm chứng."],
            ["L1", "Diagnostic độc lập đạt tiêu chí khái niệm."],
            [
              "L2",
              "Bằng chứng khái niệm, toán và triển khai độc lập qua fixed-tests.",
            ],
            [
              "L3",
              "Áp dụng vào bài toán mới và có retention; cần review độc lập.",
            ],
            [
              "L4",
              "Phê bình, mở rộng phương pháp với bằng chứng nghiên cứu được review.",
            ],
          ].map(([level, text]) => (
            <div key={level}>
              <span className="mono">{level}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>
        <p className="small muted">
          Quy trình hiện tại tự kiểm chứng L1, và L2 cho M02/PY01 khi đủ gates.
          Retention qua retest được ghi riêng; không tuyên bố transfer từ việc
          lặp lại quiz. L3/L4 có thể tự đánh giá provisional, chưa có contract
          chứng nhận trong bộ nội dung ban đầu.
        </p>
      </section>
    </div>
  );
}
export function Sources() {
  return (
    <div className="page">
      <PageHeading
        eyebrow="STUDY THE ORIGINALS"
        title="Tài liệu tham khảo"
        description="Ưu tiên giáo trình gốc, khóa học và tài liệu chính thức. Các liên kết cần Internet; bài học và tiến độ hoạt động cục bộ."
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
        Nội dung CoreLab được biên soạn riêng. Không phân phối sách, PDF hoặc dữ
        liệu có bản quyền. Danh mục nguồn được giữ tại
        reference/LEARNING_SOURCES.md.
      </p>
    </div>
  );
}
