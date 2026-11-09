"use client";
import { useEffect, useRef } from "react";
import { useI18n } from "@/lib/i18n";

// Dashboard sketch: CoreLab's subjects as a constellation whose pulses converge
// on a robot. Original, decorative; colours come from the subject tones.
type Node = { en: string; vi: string; x: number; y: number; tone: string };
const NODES: Node[] = [
  { en: "Maths", vi: "Toán", x: 48, y: 52, tone: "blue" },
  { en: "Coding", vi: "Lập trình", x: 48, y: 124, tone: "lime" },
  { en: "Hardware", vi: "Phần cứng", x: 48, y: 196, tone: "green" },
  { en: "ML", vi: "ML", x: 140, y: 40, tone: "violet" },
  { en: "Robotics", vi: "Robotics", x: 140, y: 112, tone: "orange" },
  { en: "Research", vi: "Nghiên cứu", x: 140, y: 196, tone: "amber" },
  { en: "Vision", vi: "Thị giác", x: 232, y: 52, tone: "teal" },
  { en: "RL", vi: "RL", x: 232, y: 124, tone: "rose" },
  { en: "Embodied AI", vi: "Embodied AI", x: 232, y: 196, tone: "red" },
];
const ROBOT = { x: 332, y: 124 };
const EDGES: [number, number][] = [
  [0, 3],
  [0, 4],
  [1, 3],
  [1, 5],
  [2, 5],
  [2, 4],
  [3, 6],
  [3, 7],
  [4, 7],
  [4, 8],
  [5, 8],
  [6, 9],
  [7, 9],
  [8, 9],
];
const point = (i: number) => (i === 9 ? ROBOT : NODES[i]);

export function RoboticsConcept({
  idPrefix = "robotics-concept",
}: {
  idPrefix?: string;
}) {
  const { tx, lang } = useI18n();
  const svg = useRef<SVGSVGElement>(null);
  useEffect(() => {
    // SMIL motion ignores CSS media queries: pause it for reduced motion.
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches)
      svg.current?.pauseAnimations?.();
  }, []);
  return (
    <figure className="robotics-concept">
      <div className="robotics-concept-label">
        {tx(
          "FROM FIRST PRINCIPLES TO ROBOT BEHAVIOUR",
          "TỪ NGUYÊN LÝ CƠ BẢN ĐẾN HÀNH VI ROBOT",
        )}
      </div>
      <svg
        ref={svg}
        className="constellation"
        viewBox="0 0 380 250"
        role="img"
        aria-labelledby={`${idPrefix}-title`}
      >
        <title id={`${idPrefix}-title`}>
          {tx(
            "CoreLab subjects connected as a constellation that converges on a robot",
            "Các mảng kiến thức của CoreLab nối thành chòm sao hội tụ vào một robot",
          )}
        </title>
        {EDGES.map(([a, b], k) => {
          const p = point(a),
            q = point(b),
            mx = (p.x + q.x) / 2;
          return (
            <path
              key={k}
              id={`${idPrefix}-e${k}`}
              className="constellation-edge"
              d={`M${p.x},${p.y} C${mx},${p.y} ${mx},${q.y} ${q.x},${q.y}`}
            />
          );
        })}
        {EDGES.map(([a], k) => (
          <g key={k} data-domain-tone={NODES[a].tone}>
            <circle r="2.6" className="constellation-pulse">
              <animateMotion
                dur="2.8s"
                begin={`-${((k * 0.37) % 2.8).toFixed(2)}s`}
                repeatCount="indefinite"
              >
                <mpath href={`#${idPrefix}-e${k}`} />
              </animateMotion>
            </circle>
          </g>
        ))}
        {NODES.map((n, i) => (
          <g key={n.en} data-domain-tone={n.tone}>
            <circle
              className="constellation-node"
              cx={n.x}
              cy={n.y}
              r="9"
              style={{ animationDelay: `${(i * 0.33).toFixed(2)}s` }}
            />
            <text
              className="constellation-label"
              x={n.x}
              y={n.y + 24}
              textAnchor="middle"
            >
              {lang === "vi" ? n.vi : n.en}
            </text>
          </g>
        ))}
        <g transform={`translate(${ROBOT.x} ${ROBOT.y})`}>
          <circle r="30" className="constellation-halo" />
          <rect
            x="-12"
            y="-9"
            width="24"
            height="18"
            rx="5"
            className="constellation-robot"
          />
          <circle cx="-5" r="2.4" className="constellation-eye" />
          <circle cx="5" r="2.4" className="constellation-eye" />
          <path d="M0 -9 V-15" className="constellation-antenna" />
          <circle cy="-17" r="2.2" className="constellation-eye" />
        </g>
        <text
          className="constellation-label is-robot"
          x={ROBOT.x}
          y={ROBOT.y + 48}
          textAnchor="middle"
        >
          Robot
        </text>
      </svg>
      <figcaption>
        {tx(
          "Ten subjects converge on one robot",
          "Mười mảng kiến thức hội tụ thành một robot",
        )}
        <span>{tx("Concept illustration", "Hình minh họa khái niệm")}</span>
      </figcaption>
    </figure>
  );
}
