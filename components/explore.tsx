"use client";
// Interactive "explore" blocks written inside lessons as a fenced code block:
//   ```explore
//   { "title": "...", "params": [...], "plot": {...} | "scene": {...}, "readouts": [...] }
//   ```
// The same block sits in the English and Vietnamese lesson; *_vi fields hold
// the Vietnamese labels. Expressions use lib/expr (safe, no eval).
import { useMemo, useRef, useState } from "react";
import {
  compileSpec,
  exploreSpec,
  scopeFor,
  scene3dPrimitives,
  type Fn,
  type Prim3,
  type Spec,
  type V3,
} from "@/lib/explore-spec";
import { useI18n } from "@/lib/i18n";

const COLORS: Record<string, string> = {
  blue: "#86abe2",
  orange: "#e0904f",
  green: "#6fc693",
  violet: "#ae9ce6",
  teal: "#6cc6ba",
  rose: "#e08db5",
  amber: "#e0c169",
  red: "#e58a80",
  grey: "#a7adb5",
};
const paint = (c?: string) => COLORS[c ?? ""] ?? c ?? COLORS.blue;

/** Degree-like units hug the number (35°); others get a space (0.5 m). */
const unitText = (u?: string) => (!u ? "" : /^[°%′″]/.test(u) ? u : ` ${u}`);

function nice(lo: number, hi: number) {
  const span = hi - lo || 1;
  const step = 10 ** Math.floor(Math.log10(span / 4));
  const m = [1, 2, 2.5, 5, 10].find((k) => span / (k * step) <= 6) ?? 10;
  const s = m * step,
    ticks: number[] = [];
  for (let v = Math.ceil(lo / s) * s; v <= hi + s * 1e-9; v += s)
    ticks.push(+v.toFixed(10));
  return ticks;
}
const fmt = (v: number, d = 2) =>
  Number.isFinite(v) ? (Math.abs(v) < 10 ** -d / 2 ? 0 : v).toFixed(d) : "—";

function PlotView({
  spec,
  compiled,
  scope,
  pick,
}: {
  spec: NonNullable<Spec["plot"]>;
  compiled: ReturnType<typeof compileSpec>;
  scope: Record<string, number>;
  pick: (o: { label: string; label_vi?: string }) => string;
}) {
  const W = 560,
    H = 330,
    L = 56,
    R = 16,
    T = 18,
    B = 46;
  const N = 160;
  const xs = Array.from(
    { length: N + 1 },
    (_, i) => spec.x.min + ((spec.x.max - spec.x.min) * i) / N,
  );
  const ys = compiled.series.map((f) =>
    xs.map((x) => f({ ...scope, [spec.x.name]: x })),
  );
  const finite = ys.flat().filter(Number.isFinite);
  let ylo = spec.y.min ?? Math.min(...finite, 0),
    yhi = spec.y.max ?? Math.max(...finite, 0);
  if (!(yhi > ylo)) yhi = ylo + 1;
  if (spec.y.min === undefined || spec.y.max === undefined) {
    const pad = (yhi - ylo) * 0.08;
    if (spec.y.min === undefined) ylo -= pad;
    if (spec.y.max === undefined) yhi += pad;
  }
  const X = (v: number) =>
    L + ((v - spec.x.min) / (spec.x.max - spec.x.min)) * (W - L - R);
  const Y = (v: number) => T + (1 - (v - ylo) / (yhi - ylo)) * (H - T - B);
  const clampY = (v: number) => Math.max(T - 4, Math.min(H - B + 4, Y(v)));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="explore-svg" aria-hidden="true">
      {nice(ylo, yhi).map((t) => (
        <g key={`y${t}`}>
          <line
            x1={L}
            x2={W - R}
            y1={Y(t)}
            y2={Y(t)}
            stroke="#3d4148"
            strokeWidth="1"
          />
          <text
            x={L - 8}
            y={Y(t) + 5}
            textAnchor="end"
            className="explore-tick"
          >
            {t}
          </text>
        </g>
      ))}
      {nice(spec.x.min, spec.x.max).map((t) => (
        <text
          key={`x${t}`}
          x={X(t)}
          y={H - B + 20}
          textAnchor="middle"
          className="explore-tick"
        >
          {t}
        </text>
      ))}
      <path
        d={`M${L} ${T} V${H - B} H${W - R}`}
        stroke="#a7adb5"
        fill="none"
        strokeWidth="1.5"
      />
      {ylo < 0 && yhi > 0 && (
        <line
          x1={L}
          x2={W - R}
          y1={Y(0)}
          y2={Y(0)}
          stroke="#a7adb5"
          strokeWidth="1"
        />
      )}
      {ys.map((col, i) => (
        <polyline
          key={i}
          fill="none"
          stroke={paint(spec.series[i].color)}
          strokeWidth="2.5"
          points={col
            .map((y, j) =>
              Number.isFinite(y)
                ? `${X(xs[j]).toFixed(1)},${clampY(y).toFixed(1)}`
                : "",
            )
            .filter(Boolean)
            .join(" ")}
        />
      ))}
      {compiled.points.map(([fx, fy], i) => {
        const x = fx(scope),
          y = fy(scope),
          p = spec.points![i];
        if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
        return (
          <g key={`p${i}`}>
            <circle
              cx={X(x)}
              cy={clampY(y)}
              r="5"
              fill={paint(p.color ?? "orange")}
            />
            {p.label && (
              <text x={X(x) + 8} y={clampY(y) - 8} className="explore-label">
                {pick({ label: p.label, label_vi: p.label_vi })}
              </text>
            )}
          </g>
        );
      })}
      <text
        x={(L + W - R) / 2}
        y={H - 8}
        textAnchor="middle"
        className="explore-axis"
      >
        {pick(spec.x)}
      </text>
      <text x={L} y={T - 4} className="explore-axis">
        {pick(spec.y)}
      </text>
    </svg>
  );
}

function SceneView({
  spec,
  compiled,
  scope,
  pick,
}: {
  spec: NonNullable<Spec["scene"]>;
  compiled: ReturnType<typeof compileSpec>;
  scope: Record<string, number>;
  pick: (o: { label: string; label_vi?: string }) => string;
}) {
  const W = 560,
    H = 360,
    M = 24;
  const k = Math.min(
    (W - 2 * M) / (spec.xmax - spec.xmin),
    (H - 2 * M) / (spec.ymax - spec.ymin),
  );
  const ox = (W - k * (spec.xmax - spec.xmin)) / 2,
    oy = (H - k * (spec.ymax - spec.ymin)) / 2;
  const X = (v: number) => ox + (v - spec.xmin) * k;
  const Y = (v: number) => H - oy - (v - spec.ymin) * k;
  const at = (p: readonly [Fn, Fn]) =>
    [X(p[0](scope)), Y(p[1](scope))] as const;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="explore-svg" aria-hidden="true">
      <defs>
        <marker
          id="explore-head"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" fill="context-stroke" />
        </marker>
      </defs>
      {spec.grid !== false &&
        nice(spec.xmin, spec.xmax).map((t) => (
          <line
            key={`gx${t}`}
            x1={X(t)}
            x2={X(t)}
            y1={Y(spec.ymin)}
            y2={Y(spec.ymax)}
            stroke="#2c3036"
          />
        ))}
      {spec.grid !== false &&
        nice(spec.ymin, spec.ymax).map((t) => (
          <line
            key={`gy${t}`}
            x1={X(spec.xmin)}
            x2={X(spec.xmax)}
            y1={Y(t)}
            y2={Y(t)}
            stroke="#2c3036"
          />
        ))}
      {compiled.items.map((c, i) => {
        const it = c.it,
          col = paint(it.color);
        if ((it.type === "segment" || it.type === "arrow") && "b" in c && c.b) {
          const [x1, y1] = at(c.a),
            [x2, y2] = at(c.b);
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={col}
              strokeWidth={it.width ?? (it.type === "arrow" ? 2.5 : 5)}
              strokeLinecap="round"
              strokeDasharray={
                it.type === "segment" && it.dash ? "6 6" : undefined
              }
              markerEnd={it.type === "arrow" ? "url(#explore-head)" : undefined}
            />
          );
        }
        if (it.type === "circle" && "r" in c && c.r) {
          const [cx, cy] = at(c.a);
          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={Math.max(0, c.r(scope) * k)}
              stroke={col}
              strokeWidth="2"
              fill={it.fill ? `${col}33` : "none"}
              strokeDasharray={it.dash ? "6 6" : undefined}
            />
          );
        }
        if (it.type === "polyline" && "pts" in c && c.pts) {
          return (
            <polyline
              key={i}
              fill="none"
              stroke={col}
              strokeWidth="2"
              strokeDasharray={it.dash ? "6 6" : undefined}
              points={c.pts.map((p) => at(p).join(",")).join(" ")}
            />
          );
        }
        if (it.type === "point" && "a" in c && c.a) {
          const [x, y] = at(c.a);
          return (
            <g key={i}>
              <circle
                cx={x}
                cy={y}
                r="6"
                fill="#17181b"
                stroke={col}
                strokeWidth="2.5"
              />
              {it.label && (
                <text x={x + 10} y={y - 10} className="explore-label">
                  {pick({ label: it.label, label_vi: it.label_vi })}
                </text>
              )}
            </g>
          );
        }
        if (it.type === "label" && "a" in c && c.a) {
          const [x, y] = at(c.a);
          return (
            <text key={i} x={x} y={y} className="explore-label" fill={col}>
              {pick({ label: it.text, label_vi: it.text_vi })}
            </text>
          );
        }
        return null;
      })}
    </svg>
  );
}

type Pick = (o: { label: string; label_vi?: string }) => string;

/** Orbit-camera 3D view drawn as SVG: drag (or arrow keys) to turn it. */
function Scene3DView({
  spec,
  prims,
  pick,
  resetLabel,
  hint,
}: {
  spec: NonNullable<Spec["scene3d"]>;
  prims: Prim3[];
  pick: Pick;
  resetLabel: string;
  hint: string;
}) {
  const start = {
    az: spec.view?.azimuth ?? -50,
    el: spec.view?.elevation ?? 25,
  };
  const [view, setView] = useState(start);
  const drag = useRef<{ x: number; y: number } | null>(null);
  const W = 560,
    H = 400,
    R = spec.range;
  const a = (view.az * Math.PI) / 180,
    e = (view.el * Math.PI) / 180;
  const k = (Math.min(W, H) / 2 - 18) / (R * 1.12),
    dist = R * 6;
  // World z is up. Turn about z by the azimuth, then tilt by the elevation.
  const project = (p: V3) => {
    const x1 = p[0] * Math.cos(a) - p[1] * Math.sin(a);
    const y1 = p[0] * Math.sin(a) + p[1] * Math.cos(a);
    const up = p[2] * Math.cos(e) - y1 * Math.sin(e);
    const depth = y1 * Math.cos(e) + p[2] * Math.sin(e);
    const f = dist / (dist + depth);
    return { x: W / 2 + x1 * k * f, y: H / 2 - up * k * f, d: depth };
  };
  const extra: Prim3[] = [];
  if (spec.floor !== false) {
    const ticks = nice(-R, R);
    for (const t of ticks) {
      extra.push({
        kind: "line",
        a: [t, -R, 0],
        b: [t, R, 0],
        color: "#2c3036",
        width: 1,
      });
      extra.push({
        kind: "line",
        a: [-R, t, 0],
        b: [R, t, 0],
        color: "#2c3036",
        width: 1,
      });
    }
  }
  if (spec.axes !== false) {
    const L = R * 1.1;
    (["x", "y", "z"] as const).forEach((name, i) => {
      const end: V3 = [0, 0, 0];
      end[i] = L;
      extra.push({
        kind: "line",
        a: [0, 0, 0],
        b: end,
        color: "#7d838c",
        width: 1.5,
        arrow: true,
      });
      extra.push({
        kind: "text",
        a: [end[0] * 1.06, end[1] * 1.06, end[2] * 1.06],
        label: name,
        color: "#a7adb5",
      });
    });
  }
  const all = [...extra, ...prims];
  const items = all
    .map((q, i) => {
      if (q.kind === "line") {
        const A = project(q.a),
          B = project(q.b);
        return { i, d: (A.d + B.d) / 2, q, A, B };
      }
      if (q.kind === "poly") {
        const P = q.pts.map(project);
        return { i, d: P.reduce((s, v) => s + v.d, 0) / P.length, q, P };
      }
      const A = project(q.a);
      // Points and labels sit on top of what is at the same depth.
      return { i, d: A.d - 1e-6, q, A };
    })
    .filter((it) => [it.d].every(Number.isFinite))
    .sort((u, v) => v.d - u.d);
  const onKey = (ev: React.KeyboardEvent) => {
    const step = 5;
    const moves: Record<string, [number, number]> = {
      ArrowLeft: [-step, 0],
      ArrowRight: [step, 0],
      ArrowUp: [0, step],
      ArrowDown: [0, -step],
    };
    const m = moves[ev.key];
    if (!m) return;
    ev.preventDefault();
    setView((v) => ({
      az: v.az + m[0],
      el: Math.max(-89, Math.min(89, v.el + m[1])),
    }));
  };
  return (
    <div className="explore-3d">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="explore-svg is-3d"
        tabIndex={0}
        role="application"
        aria-label={hint}
        onKeyDown={onKey}
        onPointerDown={(ev) => {
          drag.current = { x: ev.clientX, y: ev.clientY };
          ev.currentTarget.setPointerCapture(ev.pointerId);
        }}
        onPointerMove={(ev) => {
          if (!drag.current) return;
          const dx = ev.clientX - drag.current.x,
            dy = ev.clientY - drag.current.y;
          drag.current = { x: ev.clientX, y: ev.clientY };
          setView((v) => ({
            az: v.az - dx * 0.5,
            el: Math.max(-89, Math.min(89, v.el + dy * 0.5)),
          }));
        }}
        onPointerUp={() => (drag.current = null)}
        onPointerCancel={() => (drag.current = null)}
      >
        <defs>
          <marker
            id="explore-head-3d"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M0 0 L10 5 L0 10 Z" fill="context-stroke" />
          </marker>
        </defs>
        {items.map((it) => {
          const q = it.q;
          if (q.kind === "line" && "B" in it && it.B && it.A)
            return (
              <line
                key={it.i}
                x1={it.A.x}
                y1={it.A.y}
                x2={it.B.x}
                y2={it.B.y}
                stroke={paint(q.color)}
                strokeWidth={q.width}
                strokeLinecap="round"
                strokeDasharray={q.dash ? "6 6" : undefined}
                markerEnd={q.arrow ? "url(#explore-head-3d)" : undefined}
              />
            );
          if (q.kind === "poly" && "P" in it && it.P)
            return (
              <polygon
                key={it.i}
                points={it.P.map(
                  (v) => `${v.x.toFixed(1)},${v.y.toFixed(1)}`,
                ).join(" ")}
                fill={q.fill ? paint(q.color) : "none"}
                fillOpacity={q.fill ? 0.28 : 0}
                stroke={paint(q.color)}
                strokeOpacity={0.55}
                strokeWidth="1"
              />
            );
          if (q.kind === "point" && it.A)
            return (
              <g key={it.i}>
                <circle
                  cx={it.A.x}
                  cy={it.A.y}
                  r="6"
                  fill="#17181b"
                  stroke={paint(q.color)}
                  strokeWidth="2.5"
                />
                {q.label && (
                  <text
                    x={it.A.x + 10}
                    y={it.A.y - 10}
                    className="explore-label"
                  >
                    {pick({ label: q.label, label_vi: q.label_vi })}
                  </text>
                )}
              </g>
            );
          if (q.kind === "text" && it.A)
            return (
              <text
                key={it.i}
                x={it.A.x + 4}
                y={it.A.y - 4}
                className="explore-label"
                style={{ fill: paint(q.color) }}
              >
                {pick({ label: q.label, label_vi: q.label_vi })}
              </text>
            );
          return null;
        })}
      </svg>
      <div className="explore-3d-bar">
        <span className="small muted">{hint}</span>
        <button type="button" className="button" onClick={() => setView(start)}>
          {resetLabel}
        </button>
      </div>
    </div>
  );
}

export function Explore({ source }: { source: string }) {
  const { lang, tx } = useI18n();
  const pick = (o: { label: string; label_vi?: string }) =>
    lang === "vi" && o.label_vi ? o.label_vi : o.label;
  const parsed = useMemo(() => {
    try {
      const spec = exploreSpec.parse(JSON.parse(source));
      return { spec, compiled: compileSpec(spec) };
    } catch (e) {
      return { error: e instanceof Error ? e.message : String(e) };
    }
  }, [source]);
  const initial = useMemo(
    () =>
      "spec" in parsed && parsed.spec
        ? Object.fromEntries(parsed.spec.params.map((p) => [p.name, p.value]))
        : {},
    [parsed],
  );
  const [values, setValues] = useState<Record<string, number>>(initial);
  if (!("spec" in parsed) || !parsed.spec || !parsed.compiled)
    return (
      <div className="explore explore-error" role="note">
        {tx(
          "This interactive block could not be read: ",
          "Không đọc được khối tương tác này: ",
        )}
        <code>{"error" in parsed ? parsed.error?.slice(0, 200) : ""}</code>
      </div>
    );
  const { spec, compiled } = parsed;
  let scope: Record<string, number> = {};
  let failure = "";
  try {
    scope = scopeFor(spec, compiled, values);
  } catch (e) {
    failure = e instanceof Error ? e.message : String(e);
  }
  const title = lang === "vi" && spec.title_vi ? spec.title_vi : spec.title;
  const prompt = lang === "vi" && spec.prompt_vi ? spec.prompt_vi : spec.prompt;
  return (
    <section className="explore concept-demo" aria-label={title}>
      <div className="explore-head">
        <div>
          <div className="eyebrow">
            {tx(
              "TRY IT · PREDICT, MOVE, EXPLAIN",
              "THỬ NGAY · DỰ ĐOÁN, KÉO, GIẢI THÍCH",
            )}
          </div>
          <h3>{title}</h3>
        </div>
        <button
          type="button"
          className="button"
          onClick={() => setValues(initial)}
        >
          {tx("Reset", "Đặt lại")}
        </button>
      </div>
      {prompt && <p className="explore-prompt">{prompt}</p>}
      <div className="explore-body">
        <div className="explore-controls">
          {spec.params.map((p) => {
            const step = p.step ?? (p.max - p.min) / 100;
            const digits =
              step >= 1 ? 0 : Math.min(4, Math.ceil(-Math.log10(step)));
            return (
              <label key={p.name} className="explore-slider">
                <span>{pick(p)}</span>
                <input
                  type="range"
                  min={p.min}
                  max={p.max}
                  step={step}
                  value={values[p.name]}
                  aria-label={pick(p)}
                  onChange={(e) =>
                    setValues((v) => ({
                      ...v,
                      [p.name]: Number(e.target.value),
                    }))
                  }
                />
                <output>
                  {values[p.name].toFixed(digits)}
                  {unitText(p.unit)}
                </output>
              </label>
            );
          })}
          {spec.readouts && (
            <dl className="explore-readouts">
              {spec.readouts.map((r, i) => {
                let v = NaN;
                try {
                  v = compiled.readouts[i](scope);
                } catch {}
                return (
                  <div key={i}>
                    <dt>{pick(r)}</dt>
                    <dd>
                      {fmt(v, r.digits ?? 3)}
                      {unitText(r.unit)}
                    </dd>
                  </div>
                );
              })}
            </dl>
          )}
        </div>
        <div className="explore-view">
          {failure ? (
            <p className="explore-error">{failure}</p>
          ) : (
            <>
              {spec.scene3d && (
                <Scene3DView
                  spec={spec.scene3d}
                  prims={scene3dPrimitives(compiled, scope)}
                  pick={pick}
                  resetLabel={tx("Reset view", "Góc nhìn ban đầu")}
                  hint={tx(
                    "Drag or use the arrow keys to turn the 3D view.",
                    "Kéo chuột hoặc dùng phím mũi tên để xoay hình 3D.",
                  )}
                />
              )}
              {spec.scene && (
                <SceneView
                  spec={spec.scene}
                  compiled={compiled}
                  scope={scope}
                  pick={pick}
                />
              )}
              {spec.plot && (
                <PlotView
                  spec={spec.plot}
                  compiled={compiled}
                  scope={scope}
                  pick={pick}
                />
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
