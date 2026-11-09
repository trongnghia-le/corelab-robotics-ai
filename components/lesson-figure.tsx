"use client";
// Lesson figures are drawn as SVG with text in <text> elements. Inlined in the
// page they use the bundled Inter font on every machine (an <img> cannot see
// page fonts and falls back to whatever the system has, which overflows the
// labels). Vietnamese copies live in /lesson-figures/vi/ and fall back to the
// English figure when missing.
import { useEffect, useId, useState } from "react";

const cache = new Map<string, Promise<string | null>>();

function load(url: string) {
  let hit = cache.get(url);
  if (!hit) {
    hit = fetch(url)
      .then((r) => (r.ok ? r.text() : null))
      .catch(() => null);
    cache.set(url, hit);
  }
  return hit;
}

/** Repository SVG made safe to inline: no scripts or handlers, unique ids. */
export function prepareSvg(svg: string, prefix: string) {
  const start = svg.indexOf("<svg");
  if (start < 0) return null;
  let out = svg
    .slice(start)
    // The wrapper carries the accessible name; the drawing itself is hidden.
    .replace(/^<svg\b/, '<svg aria-hidden="true" focusable="false"')
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/\son[a-z]+\s*=\s*("[^"]*"|'[^']*')/gi, "")
    .replace(/(href\s*=\s*["'])\s*javascript:[^"']*/gi, "$1#");
  const ids = [...out.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
  for (const id of new Set(ids)) {
    const esc = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    out = out
      .replace(new RegExp(`(\\sid=")${esc}(")`, "g"), `$1${prefix}-${id}$2`)
      .replace(new RegExp(`url\\(#${esc}\\)`, "g"), `url(#${prefix}-${id})`)
      .replace(
        new RegExp(`((?:xlink:)?href=")#${esc}(")`, "g"),
        `$1#${prefix}-${id}$2`,
      );
  }
  return out;
}

export function LessonFigure({
  src,
  fallback,
  alt,
}: {
  src: string;
  fallback: string;
  alt: string;
}) {
  const prefix = "fig" + useId().replace(/[^a-zA-Z0-9]/g, "");
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    (async () => {
      const text =
        (await load(src)) ?? (src !== fallback ? await load(fallback) : null);
      if (!live) return;
      const ready = text ? prepareSvg(text, prefix) : null;
      if (ready) setSvg(ready);
      else setFailed(true);
    })();
    return () => {
      live = false;
    };
  }, [src, fallback, prefix]);
  if (svg)
    return (
      <span
        className="lesson-svg"
        role="img"
        aria-label={alt}
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    );
  // Before the SVG arrives, or if it cannot be inlined: the plain image.
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className="lesson-svg-fallback"
      src={failed ? fallback : src}
      alt={alt}
      loading="lazy"
      onError={(e) => {
        if (e.currentTarget.getAttribute("src") !== fallback)
          e.currentTarget.src = fallback;
      }}
    />
  );
}
