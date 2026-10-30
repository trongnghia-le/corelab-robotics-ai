"use client";
import { useId, type ReactNode } from "react";
import type { Vec2 } from "@/lib/visualization-math";
export function Slider({
  label,
  value,
  min,
  max,
  step = 0.1,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="visual-slider">
      <span>{label}</span>
      <input
        aria-label={label}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <output>{value.toFixed(step < 1 ? 2 : 0)}</output>
    </label>
  );
}
export function Demo({
  title,
  description,
  reset,
  children,
  example,
}: {
  title: string;
  description: string;
  reset: () => void;
  children: ReactNode;
  example: string;
}) {
  return (
    <section className="concept-demo panel" aria-label={title}>
      <div className="demo-heading">
        <div>
          <div className="eyebrow">EXPLORE · PREDICT, CHANGE, EXPLAIN</div>
          <h2>{title}</h2>
        </div>
        <button className="button" onClick={reset}>
          Reset
        </button>
      </div>
      <p>{description}</p>
      {children}
      <details className="demo-example">
        <summary>Worked example & model limits</summary>
        <p>{example}</p>
      </details>
      <p className="small muted">
        Exploration only. Verify understanding through independent practice and
        assessment.
      </p>
    </section>
  );
}
export const fmt = (v: number) => (Math.abs(v) < 0.0005 ? 0 : v).toFixed(2);
export const pair = (v: Vec2) => `(${fmt(v[0])}, ${fmt(v[1])})`;
export function Plane({
  lines,
  points = [],
  extent = 5,
  caption,
}: {
  lines: {
    from?: Vec2;
    to: Vec2;
    color: string;
    dashed?: boolean;
    label?: string;
    labelOffset?: Vec2;
    thick?: boolean;
  }[];
  points?: { point: Vec2; color: string }[];
  extent?: number;
  caption: string;
}) {
  const marker = useId().replace(/:/g, "");
  const s = 125 / extent,
    x = (v: number) => 170 + v * s,
    y = (v: number) => 145 - v * s;
  return (
    <figure>
      <svg viewBox="0 0 340 290" role="img" aria-label={caption}>
        <defs>
          {["#f97316", "#84b39b", "#7ea7d8", "#d8c08b"].map((color, i) => (
            <marker
              key={color}
              id={`${marker}${i}`}
              markerWidth="5"
              markerHeight="5"
              refX="4"
              refY="2.5"
              orient="auto"
            >
              <path d="M0 0 L5 2.5 L0 5" fill={color} />
            </marker>
          ))}
        </defs>
        {[-2, -1, 0, 1, 2].map((i) => (
          <g key={i}>
            <line
              x1={x((i * extent) / 2)}
              y1="20"
              x2={x((i * extent) / 2)}
              y2="270"
              stroke="#28303a"
            />
            <line
              x1="40"
              y1={y((i * extent) / 2)}
              x2="300"
              y2={y((i * extent) / 2)}
              stroke="#28303a"
            />
          </g>
        ))}
        <path d="M35 145 H310 M170 15 V275" stroke="#778598" />
        <text x="310" y="138">
          x
        </text>
        <text x="178" y="20">
          y
        </text>
        {lines.map((line, i) => (
          <g key={i}>
            <line
              x1={x(line.from?.[0] ?? 0)}
              y1={y(line.from?.[1] ?? 0)}
              x2={x(line.to[0])}
              y2={y(line.to[1])}
              stroke={line.color}
              strokeWidth={line.thick ? 6 : 2.5}
              strokeDasharray={line.dashed ? "5 4" : undefined}
              markerEnd={
                line.thick || line.dashed
                  ? undefined
                  : `url(#${marker}${Math.max(0, ["#f97316", "#84b39b", "#7ea7d8", "#d8c08b"].indexOf(line.color))})`
              }
            />
            {line.label && (
              <text
                x={x(line.to[0]) + (line.labelOffset?.[0] ?? 7)}
                y={y(line.to[1]) + (line.labelOffset?.[1] ?? -8)}
                style={{ fill: line.color }}
              >
                {line.label}
              </text>
            )}
          </g>
        ))}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={x(p.point[0])}
            cy={y(p.point[1])}
            r="5"
            fill={p.color}
          />
        ))}
        <text x="40" y="285">
          Axis range ±{fmt(extent)}
        </text>
      </svg>
      <figcaption>{caption}</figcaption>
    </figure>
  );
}
export function Plot({
  series,
  xLabel,
  yLabel,
  caption,
}: {
  series: { points: Vec2[]; color: string; label: string }[];
  xLabel: string;
  yLabel: string;
  caption: string;
}) {
  const all = series.flatMap((s) => s.points),
    xmin = Math.min(0, ...all.map((p) => p[0])),
    xmax = Math.max(1, ...all.map((p) => p[0])),
    ymin = Math.min(0, ...all.map((p) => p[1])),
    ymax = Math.max(1, ...all.map((p) => p[1]));
  const x = (v: number) => 45 + (270 * (v - xmin)) / (xmax - xmin),
    y = (v: number) => 240 - (210 * (v - ymin)) / (ymax - ymin);
  return (
    <figure>
      <svg viewBox="0 0 340 290" role="img" aria-label={caption}>
        <path d="M45 20 V240 H320" stroke="#778598" fill="none" />
        {series.map((s) => (
          <polyline
            key={s.label}
            points={s.points.map((p) => `${x(p[0])},${y(p[1])}`).join(" ")}
            fill="none"
            stroke={s.color}
            strokeWidth="2.5"
          />
        ))}
        <text x="45" y="265">
          {fmt(xmin)}
        </text>
        <text x="275" y="265">
          {fmt(xmax)} {xLabel}
        </text>
        <text x="5" y="30">
          {fmt(ymax)}
        </text>
        <text x="5" y="238">
          {fmt(ymin)}
        </text>
        <text x="50" y="18">
          {yLabel}
        </text>
      </svg>
      <figcaption>
        {caption}{" "}
        {series.map((s) => (
          <span key={s.label} style={{ color: s.color }}>
            {" "}
            · {s.label}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
