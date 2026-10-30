"use client";
import { useId, useState } from "react";
export function LearningVisual({ topicId }: { topicId: string }) {
  const [first, setFirst] = useState(3),
    [second, setSecond] = useState(2);
  const marker = useId().replace(/:/g, "");
  if (topicId !== "M02" && topicId !== "R04") return null;
  const vector = topicId === "M02";
  const q1 = (first * Math.PI) / 180,
    q2 = (second * Math.PI) / 180;
  const x = vector ? first : 2 * Math.cos(q1) + 1.5 * Math.cos(q1 + q2),
    y = vector ? second : 2 * Math.sin(q1) + 1.5 * Math.sin(q1 + q2);
  const elbow = [2 * Math.cos(q1), 2 * Math.sin(q1)];
  const proj = (first + second) / 2;
  const sx = (v: number) => 170 + v * 28,
    sy = (v: number) => 145 - v * 28;
  return (
    <section className="learning-visual panel">
      <div>
        <div className="eyebrow">EXPLORE · PREDICT BEFORE MOVING A SLIDER</div>
        <h2>
          {vector
            ? "Vectors and projections"
            : "One configuration, one endpoint position"}
        </h2>
        <p>
          {vector
            ? "Change u while keeping v=(1,1). The projection lies along v; the residual is perpendicular to v."
            : "Both joint angles are relative. Predict the endpoint, then check the diagram. This is a geometry model only; it does not control a robot."}
        </p>
        <label>
          {vector ? "uₓ" : "q₁ (degrees)"}
          <input
            aria-label={vector ? "Vector x coordinate" : "Joint 1 angle"}
            type="range"
            min={vector ? -4 : -180}
            max={vector ? 4 : 180}
            step={vector ? 0.1 : 1}
            value={first}
            onChange={(e) => setFirst(Number(e.target.value))}
          />
          <output>{first}</output>
        </label>
        <label>
          {vector ? "uᵧ" : "q₂ (degrees)"}
          <input
            aria-label={vector ? "Vector y coordinate" : "Joint 2 angle"}
            type="range"
            min={vector ? -4 : -180}
            max={vector ? 4 : 180}
            step={vector ? 0.1 : 1}
            value={second}
            onChange={(e) => setSecond(Number(e.target.value))}
          />
          <output>{second}</output>
        </label>
        <code>
          {vector
            ? `projᵥ u = (${proj.toFixed(2)}, ${proj.toFixed(2)})`
            : `p = (${x.toFixed(2)}, ${y.toFixed(2)}) m`}
        </code>
        <p className="small muted">
          {vector
            ? `‖u‖₂ = ${Math.hypot(x, y).toFixed(3)} · u·v = ${(x + y).toFixed(2)}`
            : "l₁=2 m, l₂=1.5 m. Calculations use radians: q_rad=q_deg×π/180."}
        </p>
      </div>
      <figure>
        <svg
          viewBox="0 0 340 290"
          role="img"
          aria-label={
            vector
              ? `Vector u=(${x},${y}), projection (${proj},${proj}) onto v=(1,1).`
              : `Two-link arm with endpoint (${x.toFixed(2)},${y.toFixed(2)}) metres.`
          }
        >
          <defs>
            <marker
              id={marker}
              markerWidth="6"
              markerHeight="6"
              refX="5"
              refY="3"
              orient="auto"
            >
              <path d="M0 0 L6 3 L0 6" fill="#f97316" />
            </marker>
          </defs>
          {[-4, -3, -2, -1, 0, 1, 2, 3, 4].map((i) => (
            <g key={i}>
              <line x1={sx(i)} y1="20" x2={sx(i)} y2="270" stroke="#28303a" />
              <line x1="30" y1={sy(i)} x2="310" y2={sy(i)} stroke="#28303a" />
            </g>
          ))}
          <line x1="25" y1="145" x2="320" y2="145" stroke="#778598" />
          <line x1="170" y1="15" x2="170" y2="275" stroke="#778598" />
          <text x="320" y="139" fill="#a7afbd" fontSize="13">
            x
          </text>
          <text x="178" y="18" fill="#a7afbd" fontSize="13">
            y
          </text>
          {vector ? (
            <>
              <line
                x1={sx(-4)}
                y1={sy(-4)}
                x2={sx(4)}
                y2={sy(4)}
                stroke="#6582a5"
                strokeDasharray="4 4"
              />
              <line
                x1={sx(0)}
                y1={sy(0)}
                x2={sx(proj)}
                y2={sy(proj)}
                stroke="#84b39b"
                strokeWidth="3"
              />
              <line
                x1={sx(proj)}
                y1={sy(proj)}
                x2={sx(x)}
                y2={sy(y)}
                stroke="#84b39b"
                strokeDasharray="4 4"
              />
              <line
                x1={sx(0)}
                y1={sy(0)}
                x2={sx(x)}
                y2={sy(y)}
                stroke="#f97316"
                strokeWidth="3"
                markerEnd={`url(#${marker})`}
              />
              <text x={sx(x) + 8} y={sy(y) - 8} fill="#fb923c" fontSize="15">
                u
              </text>
            </>
          ) : (
            <>
              <line
                x1={sx(0)}
                y1={sy(0)}
                x2={sx(elbow[0])}
                y2={sy(elbow[1])}
                stroke="#7c8c9f"
                strokeWidth="7"
                strokeLinecap="round"
              />
              <line
                x1={sx(elbow[0])}
                y1={sy(elbow[1])}
                x2={sx(x)}
                y2={sy(y)}
                stroke="#f97316"
                strokeWidth="6"
                strokeLinecap="round"
              />
              <circle cx={sx(0)} cy={sy(0)} r="6" fill="#d7e0eb" />
              <circle
                cx={sx(elbow[0])}
                cy={sy(elbow[1])}
                r="5"
                fill="#d7e0eb"
              />
              <circle cx={sx(x)} cy={sy(y)} r="5" fill="#fbbf24" />
            </>
          )}
        </svg>
        <figcaption>
          {vector
            ? "Orange: u · Green: projection and residual · Dashed: span(v)"
            : "Joint 1 → joint 2 → endpoint · 1 m grid"}
        </figcaption>
      </figure>
    </section>
  );
}
