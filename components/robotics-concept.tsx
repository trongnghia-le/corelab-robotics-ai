// Original static teaching illustration; it is not a simulator or grading oracle.
export function RoboticsConcept({
  idPrefix = "robotics-concept",
}: {
  idPrefix?: string;
}) {
  return (
    <figure className="robotics-concept">
      <div className="robotics-concept-label">
        FROM EQUATIONS TO ROBOT BEHAVIOR
      </div>
      <svg
        viewBox="0 0 380 250"
        role="img"
        aria-labelledby={`${idPrefix}-title`}
        aria-describedby={`${idPrefix}-desc`}
      >
        <title id={`${idPrefix}-title`}>Robotics and AI concept sketch</title>
        <desc id={`${idPrefix}-desc`}>
          A camera observes a target, a small network represents learning, and a
          two-link robot arm illustrates motion. This is a conceptual
          illustration, not a running simulation.
        </desc>
        <defs>
          <pattern
            id={`${idPrefix}-grid`}
            width="24"
            height="24"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 24 0 L 0 0 0 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect
          width="380"
          height="250"
          fill={`url(#${idPrefix}-grid)`}
          opacity="0.22"
        />
        <g
          className="robotics-sketch-muted"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path
            className="robotics-perception"
            d="M38 53 L296 111 M38 53 L326 151"
            strokeDasharray="4 6"
          />
          <path d="M38 220 H347 M68 225 V90" />
          <path d="M347 220 l-7 -4 m7 4 l-7 4 M68 90 l-4 7 m4 -7 l4 7" />
          <rect
            className="robotics-perception"
            x="21"
            y="35"
            width="31"
            height="26"
            rx="5"
          />
          <circle className="robotics-perception" cx="36" cy="48" r="7" />
          <path d="M29 35 l5 -7 h12 l5 7" />
          <path
            className="robotics-learning"
            d="M269 39 L300 59 L331 32 M269 39 L298 18 L331 32 M300 59 L335 69 M331 32 L335 69"
          />
          {[
            [269, 39],
            [300, 59],
            [331, 32],
            [298, 18],
            [335, 69],
          ].map(([cx, cy]) => (
            <circle
              className="robotics-learning"
              key={cx}
              cx={cx}
              cy={cy}
              r="5"
              fill="var(--surface-1)"
            />
          ))}
          <path d="M251 149 Q278 133 304 132" strokeDasharray="3 5" />
        </g>
        <g stroke="var(--primary)" fill="none">
          <rect
            x="289"
            y="112"
            width="38"
            height="38"
            rx="4"
            strokeDasharray="5 4"
          />
          <circle cx="308" cy="131" r="4" />
          <path
            d="M68 205 L144 119 L239 153"
            strokeWidth="14"
            strokeLinecap="round"
            opacity="0.18"
          />
          <path
            d="M68 205 L144 119 L239 153"
            strokeWidth="5"
            strokeLinecap="round"
          />
          <path
            d="M239 153 l12 -9 m-12 9 l10 12 m2 -21 l8 5 m-10 16 l8 -5"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="M68 180 A25 25 0 0 1 86 185 M128 138 A24 24 0 0 0 167 127"
            strokeWidth="1.5"
          />
          {[
            [68, 205],
            [144, 119],
            [239, 153],
          ].map(([cx, cy]) => (
            <circle
              key={cx}
              cx={cx}
              cy={cy}
              r="8"
              fill="var(--surface-1)"
              strokeWidth="3"
            />
          ))}
        </g>
        <path
          d="M49 219 v-10 h38 v10"
          fill="var(--surface-2)"
          stroke="var(--muted)"
          strokeWidth="1.5"
        />
        <g
          className="robotics-sketch-text"
          fill="currentColor"
          fontFamily="inherit"
          fontSize="12"
        >
          <text x="18" y="82">
            Perception
          </text>
          <text x="265" y="95">
            Learning
          </text>
          <text x="91" y="160">
            q₁
          </text>
          <text x="158" y="151">
            q₂
          </text>
          <text x="129" y="242">
            Robot motion
          </text>
          <text x="293" y="173">
            Target
          </text>
        </g>
      </svg>
      <figcaption>
        Sense → Learn → Plan → Act <span>Concept illustration</span>
      </figcaption>
    </figure>
  );
}
