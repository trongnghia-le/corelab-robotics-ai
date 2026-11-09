"use client";
// The study desk docked on the right of every page (a bottom sheet on narrow
// screens). Width and open state are remembered per browser; Ctrl+\ toggles it.
import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";

const Desk = dynamic(() => import("./desk").then((m) => m.Desk), {
  ssr: false,
  loading: () => <p className="desk-loading">…</p>,
});

const OPEN_KEY = "corelab:desk-panel";
const WIDTH_KEY = "corelab:desk-width";
const MIN = 340;
const DEFAULT = 520;
/** The lesson keeps at least this much room beside the panel. */
const LESSON_MIN = 420;

function stored(key: string) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Private mode: the panel still works, it just is not remembered.
  }
}

const clampWidth = (w: number) =>
  Math.round(Math.max(MIN, Math.min(w, window.innerWidth - LESSON_MIN, 1100)));

export function useDeskPanel() {
  const [open, setOpenState] = useState(false);
  useEffect(() => {
    setOpenState(stored(OPEN_KEY) === "1");
  }, []);
  const setOpen = useCallback((next: boolean) => {
    setOpenState(next);
    store(OPEN_KEY, next ? "1" : "0");
  }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "\\") {
        e.preventDefault();
        setOpenState((o) => {
          store(OPEN_KEY, o ? "0" : "1");
          return !o;
        });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return { open, setOpen };
}

export function DeskPanel({
  onClose,
  onPopOut,
}: {
  onClose: () => void;
  onPopOut: () => void;
}) {
  const [width, setWidth] = useState(DEFAULT);
  const dragging = useRef(false);
  useEffect(() => {
    const saved = Number(stored(WIDTH_KEY));
    setWidth(clampWidth(saved || DEFAULT));
    const onResize = () => setWidth((w) => clampWidth(w));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  useEffect(() => {
    document.documentElement.style.setProperty("--desk-w", `${width}px`);
  }, [width]);
  useEffect(
    () => () => {
      document.documentElement.style.removeProperty("--desk-w");
    },
    [],
  );
  const resize = (next: number) => {
    const w = clampWidth(next);
    setWidth(w);
    store(WIDTH_KEY, String(w));
  };
  return (
    <aside className="desk-panel" aria-label="Study desk">
      <div
        className="desk-resizer"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize the study desk"
        aria-valuenow={width}
        aria-valuemin={MIN}
        tabIndex={0}
        onPointerDown={(e) => {
          dragging.current = true;
          e.currentTarget.setPointerCapture(e.pointerId);
          document.body.classList.add("is-resizing");
        }}
        onPointerMove={(e) => {
          if (dragging.current) resize(window.innerWidth - e.clientX);
        }}
        onPointerUp={(e) => {
          dragging.current = false;
          e.currentTarget.releasePointerCapture(e.pointerId);
          document.body.classList.remove("is-resizing");
        }}
        onDoubleClick={() => resize(DEFAULT)}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") resize(width + 32);
          if (e.key === "ArrowRight") resize(width - 32);
        }}
      />
      <Desk embedded onClose={onClose} onPopOut={onPopOut} />
    </aside>
  );
}
