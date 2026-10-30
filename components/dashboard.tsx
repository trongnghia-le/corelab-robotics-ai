"use client";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Target,
  ShieldCheck,
  GitBranch,
  Clock3,
  FlaskConical,
  BookOpen,
  ChevronRight,
} from "lucide-react";
import { useCore, Loading } from "./provider";
import { PageHeading, Status, dateText, TopicChips } from "./ui";
import { domains, topics, topicMap } from "@/lib/curriculum";
export function Dashboard() {
  const { state } = useCore();
  if (!state) return <Loading />;
  const { progress, mastery, recommendations } = state;
  const rec = recommendations[0];
  const topic = rec ? topicMap[rec.topicId] : null;
  const verified = topics.filter((t) => mastery[t.id].level > 0),
    attempted = new Set(progress.attempts.map((a) => a.topicId));
  const gaps = topics.filter((t) => mastery[t.id].gap),
    due = progress.reviews.filter((r) => mastery[r.topicId].reviewDue);
  const recent = [
    ...progress.attempts.map((a) => ({
      id: a.id,
      topicId: a.topicId,
      at: a.at,
      text: `Diagnostic · ${a.grade.score}% · ${a.assistance}`,
      kind: "assessment",
    })),
    ...progress.sessions.map((s) => ({
      id: s.id,
      topicId: s.topicId,
      at: s.at,
      text: {
        reading: "Đã đọc bài",
        practice: "Thực hành",
        note: "Ghi chú",
        difficulty: "Ghi nhận khó khăn",
        self_assessment: "Tự đánh giá",
        ai_feedback: "Phản hồi AI · chưa kiểm chứng",
      }[s.kind],
      kind: s.kind,
    })),
  ]
    .sort((a, b) => b.at.localeCompare(a.at))
    .slice(0, 5);
  const last = progress.sessions.filter((s) => s.kind === "reading").at(-1);
  return (
    <div className="page dashboard">
      <PageHeading
        eyebrow="YOUR RESEARCH WORKSPACE"
        title="Xây nền tảng. Đi xa hơn."
        description="Mỗi bước tiến đều bắt đầu từ một điều bạn thực sự hiểu."
      >
        <Link className="button" href="/paths">
          <GitBranch size={16} />
          Lộ trình của tôi
        </Link>
      </PageHeading>
      <div className="dashboard-grid">
        <section className="focus-card">
          <div className="section-kicker">
            <span className="accent-dot" />
            BƯỚC TIẾP THEO{" "}
            <span className="priority-pill">FOUNDATION FIRST</span>
          </div>
          {topic && rec ? (
            <>
              <div className="focus-title">
                <span className="topic-code">{topic.id}</span>
                <h2>{topic.title}</h2>
              </div>
              <p className="focus-description">{rec.reason}</p>
              <div className="reason-box">
                <Target size={17} />
                <div>
                  <strong>Vì sao học bài này?</strong>
                  <p>{rec.exercise}</p>
                </div>
              </div>
              <div className="focus-bottom">
                <Link
                  className="button primary"
                  href={
                    rec.kind === "assess" || rec.kind === "review"
                      ? `/assessments/${topic.id}`
                      : rec.kind === "practice"
                        ? `/practice?topic=${topic.id}`
                        : `/lessons/${topic.id}`
                  }
                >
                  {rec.kind === "review"
                    ? "Ôn tập ngay"
                    : rec.kind === "assess"
                      ? "Bắt đầu diagnostic"
                      : "Tiếp tục học"}
                  <ArrowRight size={17} />
                </Link>
                <span className="muted small">
                  <Clock3 size={14} />
                  Học theo năng lực, không theo lịch
                </span>
              </div>
            </>
          ) : (
            <>
              <h2>Nền tảng tiếp theo của bạn</h2>
              <p>
                Chưa có bài phù hợp với các tiền đề đã kiểm chứng. Xem Roadmap
                và chọn chủ đề cần bổ sung.
              </p>
              <Link className="button primary" href="/roadmap">
                Mở Roadmap
                <ArrowRight size={16} />
              </Link>
            </>
          )}
        </section>
        <section className="panel focus-aside">
          <div className="panel-heading">
            <h2>Điểm xuất phát</h2>
            <ShieldCheck size={18} />
          </div>
          <p className="muted small">Năng lực được ghi nhận bằng bằng chứng.</p>
          <div className="evidence-stat">
            <strong>{verified.length}</strong>
            <span>
              chủ đề có bằng chứng
              <br />
              <small>trong {topics.length} chủ đề</small>
            </span>
          </div>
          <div className="aside-stat">
            <span>Đã thử đánh giá</span>
            <strong>{attempted.size} chủ đề</strong>
          </div>
          <div className="aside-stat">
            <span>Đến hạn ôn tập</span>
            <strong>{due.length} chủ đề</strong>
          </div>
          <div className="quiet-note">
            {verified.length
              ? "Xem C/M/I/T để biết chính xác bằng chứng hiện có."
              : "Chưa đánh giá là một điểm bắt đầu, không phải điểm 0."}
          </div>
        </section>
      </div>
      <div className="section-title">
        <h2>Bản đồ năng lực</h2>
        <Link href="/roadmap">
          Xem toàn bộ Roadmap
          <ArrowUpRight size={15} />
        </Link>
      </div>
      <section className="panel domain-table">
        <div className="table-head">
          <span>LĨNH VỰC</span>
          <span>BẰNG CHỨNG</span>
          <span>TRẠNG THÁI</span>
        </div>
        {domains.map((d, i) => {
          const ts = topics.filter((t) => t.domain === d),
            vs = ts.filter((t) => mastery[t.id].level > 0);
          return (
            <Link
              className="domain-row"
              href={`/roadmap?domain=${encodeURIComponent(d)}`}
              key={d}
            >
              <span>
                <span className="domain-index">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <strong>{d}</strong>
              </span>
              <span className="muted small">
                {vs.length
                  ? `${vs.length} chủ đề đã kiểm chứng`
                  : "Chưa có bằng chứng"}
              </span>
              <span className={vs.length ? "verified-text small" : "status"}>
                {vs.length ? "Có bằng chứng" : "Chưa đánh giá"}
                <ChevronRight size={14} />
              </span>
            </Link>
          );
        })}
      </section>
      <div className="two-columns">
        <section className="panel">
          <div className="panel-heading">
            <h2>Cần chú ý</h2>
            <GitBranch size={18} />
          </div>
          {gaps.length ? (
            <div className="stack">
              {gaps.slice(0, 3).map((t) => (
                <Link
                  className="attention-row"
                  href={`/assessments/${t.id}`}
                  key={t.id}
                >
                  <span className="mono">{t.id}</span>
                  <span>
                    {t.title}
                    <small>Lần thử gần nhất còn điểm cần sửa</small>
                  </span>
                  <ArrowRight size={15} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-inline">
              <ShieldCheck size={23} />
              <p>
                {progress.attempts.length
                  ? "Chưa phát hiện điểm hổng qua các lần thử."
                  : "Chưa đủ bằng chứng để xác định điểm mạnh hoặc điểm hổng."}
              </p>
              <Link href="/assessments/M01">
                Bắt đầu diagnostic M01
                <ArrowRight size={14} />
              </Link>
            </div>
          )}
          {due.length > 0 && (
            <div className="review-block">
              <strong className="warning-text">Cần ôn tập</strong>
              {due.slice(0, 3).map((r) => (
                <Link href={`/assessments/${r.topicId}`} key={r.topicId}>
                  {r.topicId} · {topicMap[r.topicId].title}
                  <ArrowRight size={14} />
                </Link>
              ))}
            </div>
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Hoạt động gần đây</h2>
            <Clock3 size={18} />
          </div>
          {recent.length ? (
            <div className="activity-list">
              {recent.map((item) => (
                <Link href={`/assessments/${item.topicId}`} key={item.id}>
                  <span className="activity-dot" />
                  <div>
                    <strong>
                      {item.topicId} · {item.text}
                    </strong>
                    <small>{dateText(item.at)}</small>
                  </div>
                  <ChevronRight size={14} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-inline">
              <BookOpen size={23} />
              <p>
                Workspace của bạn đang sẵn sàng.
                <br />
                Bắt đầu từ một câu hỏi nhỏ.
              </p>
              <Link href="/lessons/M01">
                Mở bài học đầu tiên
                <ArrowRight size={14} />
              </Link>
            </div>
          )}
        </section>
      </div>
      {last && (
        <section className="resume-line">
          <BookOpen size={18} />
          <div>
            <strong>
              Quay lại {last.topicId} · {topicMap[last.topicId].title}
            </strong>
            <span>
              Đã đọc · {dateText(last.at)} · đọc bài không tăng mastery
            </span>
          </div>
          <Link className="button" href={`/lessons/${last.topicId}`}>
            Tiếp tục
            <ArrowRight size={15} />
          </Link>
        </section>
      )}
      {verified.length > 0 && (
        <section className="panel">
          <h2>Điểm mạnh có bằng chứng</h2>
          <div className="stack">
            {verified.slice(0, 4).map((t) => (
              <div className="between" key={t.id}>
                <Link href={`/assessments/${t.id}`}>
                  {t.id} · {t.title}
                </Link>
                <Status mastery={mastery[t.id]} />
              </div>
            ))}
          </div>
        </section>
      )}
      <div className="quick-actions">
        <Link href="/practice">
          <FlaskConical size={20} />
          <div>
            <strong>Tự triển khai & kiểm thử</strong>
            <span>Thực hành ngoài trình duyệt, theo tốc độ của bạn.</span>
          </div>
          <ArrowUpRight size={18} />
        </Link>
        <Link href="/tutor">
          <Target size={20} />
          <div>
            <strong>Mang câu hỏi đến AI Tutor</strong>
            <span>Sao chép ngữ cảnh, giữ bằng chứng ở CoreLab.</span>
          </div>
          <ArrowUpRight size={18} />
        </Link>
      </div>
      {recommendations.length > 1 && (
        <details className="secondary-recs">
          <summary>
            Nhánh học song song phù hợp ({recommendations.length - 1})
          </summary>
          {recommendations.slice(1).map((r) => (
            <div key={r.topicId}>
              <Link href={`/lessons/${r.topicId}`}>
                {r.topicId} · {topicMap[r.topicId].title}
              </Link>
              <p>{r.reason}</p>
              <TopicChips ids={r.prerequisites} />
            </div>
          ))}
        </details>
      )}
    </div>
  );
}
