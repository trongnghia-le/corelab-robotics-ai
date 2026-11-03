"use client";
import { useEffect, useRef, useState } from "react";
import { Play, ExternalLink } from "lucide-react";
import type { ResolvedMedia, VideoResource } from "@/lib/media";
import { embedUrl } from "@/lib/video-player";
import { useI18n } from "@/lib/i18n";
function VideoCard({ video }: { video: VideoResource }) {
  const { tx } = useI18n();
  const [loaded, setLoaded] = useState(false),
    [online, setOnline] = useState(true);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  const src = embedUrl(video);
  return (
    <section className="video-card" aria-label={video.title}>
      <h3>{video.title}</h3>
      <p className="small">
        {video.creator} ·{" "}
        <a href={video.sourceUrl} target="_blank" rel="noreferrer">
          {tx("Original source & attribution", "Nguồn gốc và ghi công")}
        </a>{" "}
        · {tx("checked", "đã kiểm tra")} {video.verifiedOn}
      </p>
      <p>{video.description}</p>
      {src && (
        <div className="video-stage">
          {loaded ? (
            <iframe
              title={video.title}
              src={src}
              allow="encrypted-media; picture-in-picture; fullscreen"
              allowFullScreen
              referrerPolicy="strict-origin-when-cross-origin"
            />
          ) : (
            <div className="video-placeholder">
              <Play size={36} aria-hidden="true" />
              <p>
                {online
                  ? tx(
                      "Load the YouTube player when you are ready.",
                      "Hãy tải trình phát YouTube khi bạn sẵn sàng.",
                    )
                  : tx(
                      "You appear to be offline. The lesson and demos work locally.",
                      "Có vẻ bạn đang ngoại tuyến. Bài học và bản demo vẫn chạy cục bộ.",
                    )}
              </p>
              <button
                className="button primary"
                disabled={!online}
                onClick={() => {
                  setLoaded(true);
                }}
              >
                {tx("Load video player", "Tải trình phát video")}
              </button>
              <span className="small muted">
                {tx(
                  "No autoplay. Loading connects to YouTube.",
                  "Không tự phát. Khi tải sẽ kết nối tới YouTube.",
                )}
              </span>
            </div>
          )}
        </div>
      )}
      {!online && (
        <p role="status">
          {tx(
            "Video needs an Internet connection. Continue with the local theory, examples and interactive demo.",
            "Video cần kết nối Internet. Hãy tiếp tục với lý thuyết, ví dụ và bản demo tương tác cục bộ.",
          )}
        </p>
      )}
      <p className="video-fallback">
        <a
          className="button"
          href={video.watchUrl}
          target="_blank"
          rel="noreferrer"
        >
          {tx("Open original video", "Mở video gốc")} <ExternalLink size={15} />
        </a>
        <span className="small muted">
          {src
            ? tx(
                "If playback is blocked or unavailable, open the original or continue below.",
                "Nếu không phát được, hãy mở bản gốc hoặc tiếp tục bên dưới.",
              )
            : tx(
                "This lecture opens on its original site.",
                "Bài giảng này mở trên trang gốc.",
              )}
        </span>
      </p>
      <details>
        <summary>{tx("What to look for", "Cần chú ý điều gì")}</summary>
        <ul>
          {video.objectives.map((goal) => (
            <li key={goal}>{goal}</li>
          ))}
        </ul>
        <p className="small">
          {tx(
            "Pause and explain one visual in your own words. Predict a numerical example, then check it with the lesson or demo. These activities do not award mastery.",
            "Hãy tạm dừng và tự giải thích một hình minh họa bằng lời của bạn. Dự đoán một ví dụ bằng số, rồi kiểm tra với bài học hoặc bản demo. Các hoạt động này không làm tăng mức nắm vững.",
          )}
        </p>
      </details>
    </section>
  );
}
export function LessonMedia({ media }: { media: ResolvedMedia }) {
  const { tx } = useI18n();
  const [selected, setSelected] = useState(0);
  const bookmark = useRef<{ id: string; offset: number } | null>(null);
  function watch() {
    const theory = document.getElementById("lesson-theory");
    if (theory && theory.getBoundingClientRect().top <= 140) {
      const headings = [...theory.querySelectorAll<HTMLElement>("h2[id]")];
      const current =
        headings.filter((h) => h.getBoundingClientRect().top <= 140).at(-1) ??
        theory;
      bookmark.current = {
        id: current.id,
        offset: current.getBoundingClientRect().top,
      };
    }
    document
      .getElementById("lesson-media")
      ?.scrollIntoView({ block: "start", behavior: "instant" });
  }
  function theory() {
    const saved = bookmark.current,
      element = document.getElementById(saved?.id ?? "lesson-theory");
    if (element)
      window.scrollBy({
        top: element.getBoundingClientRect().top - (saved?.offset ?? 100),
        behavior: "instant",
      });
  }
  return (
    <>
      <nav
        className="media-navigation"
        aria-label={tx("Lesson learning modes", "Chế độ học của bài")}
      >
        <button onClick={watch}>
          {tx("Watch & explore", "Xem & khám phá")}
        </button>
        <button onClick={theory}>
          {tx("Continue theory", "Tiếp tục lý thuyết")}
        </button>
        <span className="small muted">
          {tx(
            "Your player stays open as you read.",
            "Trình phát vẫn mở khi bạn đọc.",
          )}
        </span>
      </nav>
      <section id="lesson-media" className="lesson-media panel">
        <div className="eyebrow">
          {tx("WATCH · THEN EXPLORE", "XEM · RỒI KHÁM PHÁ")}
        </div>
        <h2>{tx("Recommended video", "Video đề xuất")}</h2>
        {media.videos.length ? (
          <>
            <div
              className="video-selection"
              aria-label={tx("Choose a lecture", "Chọn một bài giảng")}
            >
              {media.videos.length > 1 &&
                media.videos.map((v, i) => (
                  <button
                    key={v.id}
                    aria-pressed={selected === i}
                    onClick={() => setSelected(i)}
                  >
                    {i + 1}. {v.title}
                  </button>
                ))}
            </div>
            {media.videos.map((video, i) => (
              <div key={video.id} hidden={selected !== i}>
                <VideoCard video={video} />
              </div>
            ))}
          </>
        ) : (
          <p>
            {tx(
              "No verified video is curated for this topic yet. Continue with the local explanations and practice below.",
              "Chủ đề này chưa có video đã được kiểm chứng. Hãy tiếp tục với phần giải thích và luyện tập cục bộ bên dưới.",
            )}
          </p>
        )}
        <p className="small muted">
          {tx(
            "Videos are optional third-party resources. Watching does not change verified mastery.",
            "Video là tài nguyên bên thứ ba, không bắt buộc. Xem video không làm thay đổi mức nắm vững đã kiểm chứng.",
          )}
        </p>
      </section>
    </>
  );
}
