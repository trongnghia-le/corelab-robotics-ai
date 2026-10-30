"use client";
import { useEffect, useRef, useState } from "react";
import { Play, ExternalLink } from "lucide-react";
import type { ResolvedMedia, VideoResource } from "@/lib/media";
import { embedUrl } from "@/lib/video-player";
function VideoCard({ video }: { video: VideoResource }) {
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
          Original source & attribution
        </a>{" "}
        · checked {video.verifiedOn}
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
                  ? "Load the YouTube player when you are ready."
                  : "You appear to be offline. The lesson and demos work locally."}
              </p>
              <button
                className="button primary"
                disabled={!online}
                onClick={() => {
                  setLoaded(true);
                }}
              >
                Load video player
              </button>
              <span className="small muted">
                No autoplay. Loading connects to YouTube.
              </span>
            </div>
          )}
        </div>
      )}
      {!online && (
        <p role="status">
          Video needs an Internet connection. Continue with the local theory,
          examples and interactive demo.
        </p>
      )}
      <p className="video-fallback">
        <a
          className="button"
          href={video.watchUrl}
          target="_blank"
          rel="noreferrer"
        >
          Open original video <ExternalLink size={15} />
        </a>
        <span className="small muted">
          {src
            ? "If playback is blocked or unavailable, open the original or continue below."
            : "This lecture opens on its original site."}
        </span>
      </p>
      <details>
        <summary>What to look for</summary>
        <ul>
          {video.objectives.map((goal) => (
            <li key={goal}>{goal}</li>
          ))}
        </ul>
        <p className="small">
          Pause and explain one visual in your own words. Predict a numerical
          example, then check it with the lesson or demo. These activities do
          not award mastery.
        </p>
      </details>
    </section>
  );
}
export function LessonMedia({ media }: { media: ResolvedMedia }) {
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
      <nav className="media-navigation" aria-label="Lesson learning modes">
        <button onClick={watch}>Watch & explore</button>
        <button onClick={theory}>Continue theory</button>
        <span className="small muted">Your player stays open as you read.</span>
      </nav>
      <section id="lesson-media" className="lesson-media panel">
        <div className="eyebrow">WATCH · THEN EXPLORE</div>
        <h2>Recommended video</h2>
        {media.videos.length ? (
          <>
            <div className="video-selection" aria-label="Choose a lecture">
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
            No verified video is curated for this topic yet. Continue with the
            local explanations and practice below.
          </p>
        )}
        <p className="small muted">
          Videos are optional third-party resources. Watching does not change
          verified mastery.
        </p>
      </section>
    </>
  );
}
