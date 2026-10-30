import type { LessonMedia } from "@/lib/media";
export function ConceptIllustration({
  illustration,
}: {
  illustration: LessonMedia["illustrations"][number];
}) {
  const id = illustration.id;
  return (
    <figure className="concept-illustration">
      <svg
        viewBox="0 0 560 210"
        role="img"
        aria-label={illustration.description}
      >
        {id === "projection" ? (
          <>
            <path d="M70 165 H500 M70 165 V20" stroke="#778598" />
            <path d="M70 165 L450 35" stroke="#7ea7d8" strokeDasharray="5 4" />
            <path d="M70 165 L360 35" stroke="#f97316" strokeWidth="4" />
            <path
              d="M70 165 L369 63 L360 35"
              stroke="#84b39b"
              strokeWidth="3"
              fill="none"
            />
            <text x="320" y="26">
              u
            </text>
            <text x="385" y="95">
              projection
            </text>
            <text x="100" y="195">
              u = projᵥu + residual, residual · v = 0
            </text>
          </>
        ) : id === "frames" ? (
          <>
            <path
              d="M80 165 H175 M80 165 V70"
              stroke="#7ea7d8"
              strokeWidth="3"
            />
            <path
              d="M80 165 L260 105 L390 50"
              stroke="#f97316"
              strokeWidth="7"
              fill="none"
            />
            <path
              d="M260 105 L340 75 M260 105 L230 25"
              stroke="#84b39b"
              strokeWidth="3"
            />
            <circle cx="260" cy="105" r="7" fill="#d7e0eb" />
            <text x="60" y="190">
              world frame
            </text>
            <text x="315" y="140">
              link frame
            </text>
            <text x="335" y="180">
              p_world = R p_link + t
            </text>
          </>
        ) : id === "backpropagation" ? (
          <>
            {[100, 270, 440].map((x, col) => (
              <g key={x}>
                {[65, 115, 165].map((y) => (
                  <g key={y}>
                    {col < 2 &&
                      [65, 115, 165].map((y2) => (
                        <line
                          key={y2}
                          x1={x + 12}
                          y1={y}
                          x2={x + 158}
                          y2={y2}
                          stroke="#435365"
                        />
                      ))}
                    <circle
                      cx={x}
                      cy={y}
                      r="13"
                      fill="#17222d"
                      stroke={col === 1 ? "#f97316" : "#7ea7d8"}
                      strokeWidth="2"
                    />
                  </g>
                ))}
                <text x={x - 35} y="195">
                  {["input", "hidden", "output"][col]}
                </text>
              </g>
            ))}
            <path d="M100 25 H440 M440 35 H100" stroke="#84b39b" />
            <text x="145" y="18">
              forward → activations · gradients ← backward
            </text>
          </>
        ) : id === "mdp" ? (
          <>
            <rect
              x="50"
              y="65"
              width="150"
              height="80"
              rx="8"
              fill="#17222d"
              stroke="#f97316"
            />
            <rect
              x="350"
              y="65"
              width="160"
              height="80"
              rx="8"
              fill="#17222d"
              stroke="#7ea7d8"
            />
            <text x="95" y="112">
              Agent
            </text>
            <text x="370" y="112">
              Environment
            </text>
            <path
              d="M200 80 H350 l-10 -6 m10 6 l-10 6 M350 130 H200 l10 -6 m-10 6 l10 6"
              fill="none"
              stroke="#84b39b"
              strokeWidth="2"
            />
            <text x="225" y="65">
              action aₜ →
            </text>
            <text x="207" y="163">
              ← state sₜ₊₁, reward rₜ₊₁
            </text>
            <text x="110" y="195">
              Markov model: p(s′, r | s, a)
            </text>
          </>
        ) : (
          <>
            <text x="20" y="75">
              reference
            </text>
            <circle cx="130" cy="100" r="22" fill="none" stroke="#84b39b" />
            <text x="122" y="106">
              Σ
            </text>
            <rect
              x="205"
              y="70"
              width="105"
              height="60"
              fill="#17222d"
              stroke="#f97316"
            />
            <rect
              x="380"
              y="70"
              width="110"
              height="60"
              fill="#17222d"
              stroke="#7ea7d8"
            />
            <text x="215" y="105">
              Controller
            </text>
            <text x="405" y="105">
              Plant
            </text>
            <path
              d="M20 100 H108 M152 100 H205 M310 100 H380 M490 100 H530 V170 H130 V122"
              stroke="#84b39b"
              fill="none"
              strokeWidth="2"
            />
            <text x="170" y="90">
              e
            </text>
            <text x="335" y="90">
              u
            </text>
            <text x="515" y="90">
              y
            </text>
            <text x="143" y="152">
              − y
            </text>
            <text x="220" y="194">
              feedback: e = reference − output
            </text>
          </>
        )}
      </svg>
      <figcaption>
        {illustration.description}{" "}
        <span className="small muted">{illustration.attribution}</span>
      </figcaption>
    </figure>
  );
}
