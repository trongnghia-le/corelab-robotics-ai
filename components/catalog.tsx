"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Search,
  List,
  Network,
  BookOpen,
  ArrowUpRight,
  ChevronRight,
} from "lucide-react";
import { topics, domains } from "@/lib/curriculum";
import { useCore, Loading } from "./provider";
import { PageHeading, Status } from "./ui";
const Graph = dynamic(() => import("./graph").then((m) => m.Graph), {
  ssr: false,
  loading: () => <div className="graph-loading">Đang mở đồ thị…</div>,
});
export function Catalog({
  mode,
}: {
  mode: "roadmap" | "lessons" | "assessments";
}) {
  const { state } = useCore();
  const params = useSearchParams();
  const [query, setQuery] = useState(""),
    [domain, setDomain] = useState(params.get("domain") ?? ""),
    [priority, setPriority] = useState(""),
    [status, setStatus] = useState(""),
    [view, setView] = useState<"list" | "graph">("list");
  if (!state) return <Loading />;
  const isRoad = mode === "roadmap";
  const visible = topics.filter(
    (t) =>
      (isRoad || state.lessonIds.includes(t.id)) &&
      (!domain || t.domain === domain) &&
      (!priority || t.priority === priority) &&
      (!status || state.mastery[t.id].status === status) &&
      `${t.id} ${t.title} ${t.domain}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <div className="page">
      <PageHeading
        eyebrow={
          isRoad
            ? "THE LONG-TERM MAP"
            : mode === "lessons"
              ? "LEARN FROM FIRST PRINCIPLES"
              : "EVIDENCE, NOT CHECKBOXES"
        }
        title={
          isRoad
            ? "Roadmap tri thức"
            : mode === "lessons"
              ? "Không chỉ đọc. Hiểu sâu."
              : "Kiểm chứng điều bạn hiểu."
        }
        description={
          isRoad
            ? `${topics.length} chủ đề liên kết bởi tiền đề. Một bản đồ dài hạn, không phải danh sách bắt buộc.`
            : mode === "lessons"
              ? `${state.lessonIds.length} bài học đã biên soạn. Bắt đầu từ nền tảng, tiến lên bằng bằng chứng.`
              : "Diagnostic ngắn, phản hồi rõ ràng, bằng chứng có thể truy vết."
        }
      />
      {mode === "assessments" && (
        <div className="info-banner">
          <BookOpen size={18} />
          <span>
            Quiz A0 đạt ≥80% và không sai câu critical mới kiểm chứng. Câu trả
            lời mở được đối chiếu rubric, không tự động tăng mastery.
          </span>
        </div>
      )}
      <div className="catalog-toolbar">
        <label className="search-field">
          <Search size={17} />
          <input
            aria-label="Tìm chủ đề"
            placeholder="Tìm theo tên hoặc mã chủ đề…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd>/</kbd>
        </label>
        {isRoad && (
          <div className="segmented" aria-label="Chế độ hiển thị">
            <button
              aria-pressed={view === "list"}
              className={view === "list" ? "selected" : ""}
              onClick={() => setView("list")}
            >
              <List size={16} />
              Danh sách
            </button>
            <button
              aria-pressed={view === "graph"}
              className={view === "graph" ? "selected" : ""}
              onClick={() => setView("graph")}
            >
              <Network size={16} />
              Đồ thị
            </button>
          </div>
        )}
      </div>
      <div className="filters">
        <select
          aria-label="Lọc lĩnh vực"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        >
          <option value="">Tất cả lĩnh vực</option>
          {domains.map((d) => (
            <option key={d}>{d}</option>
          ))}
        </select>
        <select
          aria-label="Lọc ưu tiên"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="">Mọi mức ưu tiên</option>
          <option value="P0">P0 · Core</option>
          <option value="P1">P1 · Applied</option>
          <option value="P2">P2 · Extension</option>
        </select>
        <select
          aria-label="Lọc trạng thái"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">Mọi trạng thái</option>
          <option value="unassessed">Chưa đánh giá</option>
          <option value="in_progress">Đang học</option>
          <option value="provisional">Tự đánh giá</option>
          <option value="verified">Đã kiểm chứng</option>
        </select>
        <span className="result-count">{visible.length} chủ đề</span>
      </div>
      {view === "graph" && isRoad ? (
        <Graph
          domain={domain || domains[0]}
          query={query}
          priority={priority}
          status={status}
          mastery={state.mastery}
        />
      ) : visible.length === 0 ? (
        <div className="empty-state">
          <Search size={25} />
          <h2>Không tìm thấy chủ đề</h2>
          <p>Thử từ khóa ngắn hơn hoặc bỏ bộ lọc.</p>
          <button
            onClick={() => {
              setQuery("");
              setDomain("");
              setPriority("");
              setStatus("");
            }}
          >
            Xóa bộ lọc
          </button>
        </div>
      ) : isRoad ? (
        <div className="roadmap-groups">
          {domains
            .filter((d) => visible.some((t) => t.domain === d))
            .map((d) => (
              <section key={d}>
                <div className="domain-heading">
                  <h2>{d}</h2>
                  <span>
                    {visible.filter((t) => t.domain === d).length} chủ đề
                  </span>
                </div>
                <div className="panel topic-list">
                  {visible
                    .filter((t) => t.domain === d)
                    .map((t) => (
                      <div className="topic-list-row" key={t.id}>
                        <Link className="topic-main" href={`/lessons/${t.id}`}>
                          <span className="topic-id">{t.id}</span>
                          <div>
                            <strong>{t.title}</strong>
                            <small>
                              {state.lessonIds.includes(t.id)
                                ? "Bài học đầy đủ + diagnostic"
                                : "Overview · chưa có bài học đầy đủ"}
                            </small>
                          </div>
                        </Link>
                        <span className={`priority ${t.priority}`}>
                          {t.priority}
                        </span>
                        <span className="prereq-count">
                          {t.prerequisites.length
                            ? `${t.prerequisites.length} tiền đề`
                            : "Nền tảng"}
                        </span>
                        <Status mastery={state.mastery[t.id]} />
                        <Link
                          className="icon-button"
                          href={`/lessons/${t.id}`}
                          aria-label={`Mở ${t.id}`}
                        >
                          <ChevronRight size={17} />
                        </Link>
                      </div>
                    ))}
                </div>
              </section>
            ))}
        </div>
      ) : (
        <div className="lesson-grid">
          {visible.map((t) => (
            <Link href={`/${mode}/${t.id}`} className="lesson-card" key={t.id}>
              <div className="between">
                <span className="topic-code">{t.id}</span>
                <span className={`priority ${t.priority}`}>{t.priority}</span>
              </div>
              <span className="small muted">{t.domain}</span>
              <h2>{t.title}</h2>
              <Status mastery={state.mastery[t.id]} />
              <div className="lesson-card-bottom">
                <span>
                  {mode === "lessons"
                    ? "Lý thuyết · Ví dụ · Thực hành"
                    : "Concept · Math · Rubric"}
                </span>
                <ArrowUpRight size={17} />
              </div>
            </Link>
          ))}
        </div>
      )}
      <div className="catalog-note">
        <strong>P0</strong> Nền tảng cốt lõi <span>·</span>
        <strong>P1</strong> Ứng dụng <span>·</span>
        <strong>P2</strong> Mở rộng nghiên cứu. Bạn có thể mở mọi chủ đề; tiền
        đề hướng dẫn việc học, không khóa trang.
      </div>
    </div>
  );
}
