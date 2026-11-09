"use client";
import type { LessonMedia } from "@/lib/media";
import { useI18n } from "@/lib/i18n";

// Vietnamese captions for the illustrations listed in lesson-media.v1.json.
const captionVi: Record<string, string> = {
  feedback:
    "Phản hồi âm so sánh tín hiệu tham chiếu với đầu ra đo được của plant.",
  projection:
    "Tách một vector thành hình chiếu song song và phần dư vuông góc.",
  frames: "Hai phép quay khớp tương đối nối đế, khuỷu và điểm cuối.",
  backpropagation: "Tích lũy ngược dùng lại đạo hàm cục bộ của từng lớp.",
  mdp: "Mô hình chuyển trạng thái Markov chỉ phụ thuộc trạng thái và hành động hiện tại.",
};
export function ConceptIllustration({
  illustration,
}: {
  illustration: LessonMedia["illustrations"][number];
}) {
  const id = illustration.id;
  const { tx, lang } = useI18n();
  return (
    <figure className="concept-illustration">
      <svg
        viewBox="0 0 560 210"
        role="img"
        aria-label={illustration.description}
      >
        {id === "projection" ? (
          <>
            <path d="M70 165 H500 M70 165 V20" stroke="#7f8690" />
            <path d="M70 165 L450 35" stroke="#94a9c2" strokeDasharray="5 4" />
            <path d="M70 165 L360 35" stroke="#d98a52" strokeWidth="4" />
            <path
              d="M70 165 L369 63 L360 35"
              stroke="#90a79b"
              strokeWidth="3"
              fill="none"
            />
            <text x="320" y="26">
              u
            </text>
            <text x="385" y="95">
              {tx("projection", "hình chiếu")}
            </text>
            <text x="100" y="195">
              {tx(
                "u = projᵥu + residual, residual · v = 0",
                "u = projᵥu + phần dư, phần dư · v = 0",
              )}
            </text>
          </>
        ) : id === "frames" ? (
          <>
            <path
              d="M80 165 H175 M80 165 V70"
              stroke="#94a9c2"
              strokeWidth="3"
            />
            <path
              d="M80 165 L260 105 L390 50"
              stroke="#d98a52"
              strokeWidth="7"
              fill="none"
            />
            <path
              d="M260 105 L340 75 M260 105 L230 25"
              stroke="#90a79b"
              strokeWidth="3"
            />
            <circle cx="260" cy="105" r="7" fill="#dce0e6" />
            <text x="60" y="190">
              {tx("world frame", "khung thế giới")}
            </text>
            <text x="315" y="140">
              {tx("link frame", "khung khâu")}
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
                          stroke="#4b535d"
                        />
                      ))}
                    <circle
                      cx={x}
                      cy={y}
                      r="13"
                      fill="#1f2225"
                      stroke={col === 1 ? "#d98a52" : "#94a9c2"}
                      strokeWidth="2"
                    />
                  </g>
                ))}
                <text x={x - 35} y="195">
                  {
                    (lang === "vi"
                      ? ["đầu vào", "ẩn", "đầu ra"]
                      : ["input", "hidden", "output"])[col]
                  }
                </text>
              </g>
            ))}
            <path d="M100 25 H440 M440 35 H100" stroke="#90a79b" />
            <text x="145" y="18">
              {tx(
                "forward → activations · gradients ← backward",
                "forward → kích hoạt · gradient ← backward",
              )}
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
              fill="#1f2225"
              stroke="#d98a52"
            />
            <rect
              x="350"
              y="65"
              width="160"
              height="80"
              rx="8"
              fill="#1f2225"
              stroke="#94a9c2"
            />
            <text x="95" y="112">
              Agent
            </text>
            <text x="370" y="112">
              {tx("Environment", "Môi trường")}
            </text>
            <path
              d="M200 80 H350 l-10 -6 m10 6 l-10 6 M350 130 H200 l10 -6 m-10 6 l10 6"
              fill="none"
              stroke="#90a79b"
              strokeWidth="2"
            />
            <text x="225" y="65">
              {tx("action aₜ →", "hành động aₜ →")}
            </text>
            <text x="207" y="163">
              {tx(
                "← state sₜ₊₁, reward rₜ₊₁",
                "← trạng thái sₜ₊₁, phần thưởng rₜ₊₁",
              )}
            </text>
            <text x="110" y="195">
              {tx(
                "Markov model: p(s′, r | s, a)",
                "Mô hình Markov: p(s′, r | s, a)",
              )}
            </text>
          </>
        ) : (
          <>
            <text x="20" y="75">
              {tx("reference", "tham chiếu")}
            </text>
            <circle cx="130" cy="100" r="22" fill="none" stroke="#90a79b" />
            <text x="122" y="106">
              Σ
            </text>
            <rect
              x="205"
              y="70"
              width="105"
              height="60"
              fill="#1f2225"
              stroke="#d98a52"
            />
            <rect
              x="380"
              y="70"
              width="110"
              height="60"
              fill="#1f2225"
              stroke="#94a9c2"
            />
            <text x="215" y="105">
              {tx("Controller", "Bộ điều khiển")}
            </text>
            <text x="405" y="105">
              Plant
            </text>
            <path
              d="M20 100 H108 M152 100 H205 M310 100 H380 M490 100 H530 V170 H130 V122"
              stroke="#90a79b"
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
              {tx(
                "feedback: e = reference − output",
                "phản hồi: e = tham chiếu − đầu ra",
              )}
            </text>
          </>
        )}
      </svg>
      <figcaption>
        {(lang === "vi" && captionVi[id]) || illustration.description}{" "}
        <span className="small muted">
          {tx(illustration.attribution, "Hình minh họa SVG gốc của CoreLab.")}
        </span>
      </figcaption>
    </figure>
  );
}
