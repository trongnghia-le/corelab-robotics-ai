// LaTeX snippets for the study desk's formula toolbar. `tex` is inserted at
// the cursor; `▮` marks where the selection goes (or where the cursor lands).
// `block` snippets need display math ($$ … $$) on their own lines.

export type MathSnippet = {
  label: string;
  tex: string;
  block?: boolean;
  /** Rendered on the button when `tex` is too long to show. */
  preview?: string;
};

export type MathGroup = {
  id: string;
  en: string;
  vi: string;
  items: MathSnippet[];
};

const s = (tex: string, label = tex, extra: Partial<MathSnippet> = {}) => ({
  label,
  tex,
  ...extra,
});

export const mathGroups: MathGroup[] = [
  {
    id: "basic",
    en: "Basic",
    vi: "Cơ bản",
    items: [
      s("\\frac{▮}{}", "fraction", { preview: "\\frac{a}{b}" }),
      s("▮^{}", "power", { preview: "x^{n}" }),
      s("▮_{}", "subscript", { preview: "x_{i}" }),
      s("\\sqrt{▮}", "square root", { preview: "\\sqrt{x}" }),
      s("\\sqrt[n]{▮}", "n-th root", { preview: "\\sqrt[n]{x}" }),
      s("\\left( ▮ \\right)", "brackets", {
        preview: "\\left(\\tfrac{a}{b}\\right)",
      }),
      s("\\lvert ▮ \\rvert", "absolute value", {
        preview: "\\lvert x \\rvert",
      }),
      s("\\pm"),
      s("\\times"),
      s("\\cdot"),
      s("\\div"),
      s("\\approx"),
      s("\\neq"),
      s("\\leq"),
      s("\\geq"),
      s("\\ll"),
      s("\\gg"),
      s("\\propto"),
      s("\\infty"),
      s("^{\\circ}", "degrees", { preview: "90^{\\circ}" }),
      s("\\text{▮}", "text", { preview: "\\text{m/s}" }),
      s("\\,\\mathrm{▮}", "unit", { preview: "9.81\\,\\mathrm{m/s^2}" }),
    ],
  },
  {
    id: "greek",
    en: "Greek",
    vi: "Hy Lạp",
    items: [
      "alpha",
      "beta",
      "gamma",
      "delta",
      "epsilon",
      "varepsilon",
      "zeta",
      "eta",
      "theta",
      "kappa",
      "lambda",
      "mu",
      "nu",
      "xi",
      "pi",
      "rho",
      "sigma",
      "tau",
      "phi",
      "varphi",
      "chi",
      "psi",
      "omega",
      "Gamma",
      "Delta",
      "Theta",
      "Lambda",
      "Pi",
      "Sigma",
      "Phi",
      "Psi",
      "Omega",
    ].map((g) => s(`\\${g}`)),
  },
  {
    id: "calculus",
    en: "Calculus",
    vi: "Giải tích",
    items: [
      s("\\frac{d ▮}{d x}", "derivative", { preview: "\\frac{df}{dx}" }),
      s("\\frac{d^{2} ▮}{d x^{2}}", "second derivative", {
        preview: "\\frac{d^2f}{dx^2}",
      }),
      s("\\frac{\\partial ▮}{\\partial x}", "partial", {
        preview: "\\frac{\\partial f}{\\partial x}",
      }),
      s("\\dot{▮}", "time derivative", { preview: "\\dot{x}" }),
      s("\\ddot{▮}", "second time derivative", { preview: "\\ddot{x}" }),
      s("\\int_{a}^{b} ▮ \\, dx", "integral", { preview: "\\int_a^b f\\,dx" }),
      s("\\iint_{D} ▮ \\, dA", "double integral", {
        preview: "\\iint_D f\\,dA",
      }),
      s("\\sum_{i=1}^{n} ▮", "sum", { preview: "\\sum_{i=1}^{n}" }),
      s("\\prod_{i=1}^{n} ▮", "product", { preview: "\\prod_{i=1}^{n}" }),
      s("\\lim_{x \\to 0} ▮", "limit", { preview: "\\lim_{x\\to 0}" }),
      s("\\nabla ▮", "gradient", { preview: "\\nabla f" }),
      s("\\nabla^{2} ▮", "Laplacian", { preview: "\\nabla^2 f" }),
      s("e^{▮}", "exponential", { preview: "e^{x}" }),
      s("\\ln ▮", "ln", { preview: "\\ln x" }),
      s("\\log ▮", "log", { preview: "\\log x" }),
      s("\\sin ▮", "sin", { preview: "\\sin\\theta" }),
      s("\\cos ▮", "cos", { preview: "\\cos\\theta" }),
      s("\\tan ▮", "tan", { preview: "\\tan\\theta" }),
      s("\\operatorname{atan2}(y, x)", "atan2"),
      s("\\Delta ▮", "change", { preview: "\\Delta t" }),
      s("\\mathcal{O}(▮)", "big O", { preview: "\\mathcal{O}(n^2)" }),
    ],
  },
  {
    id: "linear",
    en: "Linear algebra",
    vi: "Đại số tuyến tính",
    items: [
      s("\\mathbf{▮}", "bold vector", { preview: "\\mathbf{v}" }),
      s("\\vec{▮}", "arrow vector", { preview: "\\vec{v}" }),
      s("\\hat{▮}", "unit vector / estimate", { preview: "\\hat{x}" }),
      s("\\begin{bmatrix} ▮ & \\\\ & \\end{bmatrix}", "2×2 matrix", {
        preview: "\\begin{bmatrix}a&b\\\\c&d\\end{bmatrix}",
      }),
      s(
        "\\begin{bmatrix} ▮ & & \\\\ & & \\\\ & & \\end{bmatrix}",
        "3×3 matrix",
        {
          preview: "\\begin{bmatrix}1&0&0\\\\0&1&0\\\\0&0&1\\end{bmatrix}",
        },
      ),
      s("\\begin{bmatrix} ▮ \\\\ \\\\ \\end{bmatrix}", "column vector", {
        preview: "\\begin{bmatrix}x\\\\y\\\\z\\end{bmatrix}",
      }),
      s("▮^{\\top}", "transpose", { preview: "A^{\\top}" }),
      s("▮^{-1}", "inverse", { preview: "A^{-1}" }),
      s("\\det(▮)", "determinant", { preview: "\\det(A)" }),
      s("\\operatorname{tr}(▮)", "trace", { preview: "\\operatorname{tr}(A)" }),
      s("\\lVert ▮ \\rVert", "norm", { preview: "\\lVert x \\rVert" }),
      s("\\langle ▮, \\rangle", "inner product", {
        preview: "\\langle u, v\\rangle",
      }),
      s("\\times", "cross product", { preview: "a \\times b" }),
      s("\\otimes"),
      s("I_{n}", "identity", { preview: "I_n" }),
      s("\\mathbb{R}^{n}", "real space", { preview: "\\mathbb{R}^{n}" }),
      s("A \\mathbf{v} = \\lambda \\mathbf{v}", "eigen"),
      s("\\operatorname{rank}(▮)", "rank", {
        preview: "\\operatorname{rank}(A)",
      }),
    ],
  },
  {
    id: "probability",
    en: "Probability",
    vi: "Xác suất",
    items: [
      s("P(▮)", "probability", { preview: "P(A)" }),
      s("P(▮ \\mid )", "conditional", { preview: "P(A \\mid B)" }),
      s("\\mathbb{E}[▮]", "expectation", { preview: "\\mathbb{E}[X]" }),
      s("\\operatorname{Var}(▮)", "variance", {
        preview: "\\operatorname{Var}(X)",
      }),
      s("\\operatorname{Cov}(▮, )", "covariance", {
        preview: "\\operatorname{Cov}(X,Y)",
      }),
      s("\\mathcal{N}(\\mu, \\sigma^{2})", "normal"),
      s("\\sim"),
      s("P(A \\mid B) = \\frac{P(B \\mid A)\\, P(A)}{P(B)}", "Bayes", {
        block: true,
      }),
      s("\\bar{▮}", "mean", { preview: "\\bar{x}" }),
      s("\\binom{n}{k}", "binomial"),
      s("\\arg\\max_{▮}", "argmax", { preview: "\\arg\\max_{\\theta}" }),
      s("\\arg\\min_{▮}", "argmin", { preview: "\\arg\\min_{x}" }),
    ],
  },
  {
    id: "structure",
    en: "Layout & logic",
    vi: "Cấu trúc & logic",
    items: [
      s("\\begin{aligned}\n▮ &= \\\\\n  &= \n\\end{aligned}", "aligned steps", {
        block: true,
        preview: "\\begin{aligned}y&=a\\\\&=b\\end{aligned}",
      }),
      s(
        "f(x) = \\begin{cases} ▮ & \\text{if } x \\ge 0 \\\\ & \\text{otherwise} \\end{cases}",
        "cases",
        {
          block: true,
          preview: "\\begin{cases}a&x\\ge0\\\\b&\\text{else}\\end{cases}",
        },
      ),
      s("\\boxed{▮}", "box result", { preview: "\\boxed{x=2}" }),
      s("\\underbrace{▮}_{\\text{}}", "underbrace", {
        preview: "\\underbrace{a+b}_{n}",
      }),
      s("\\overset{!}{=}", "must equal", { preview: "\\overset{!}{=}" }),
      s("\\Rightarrow"),
      s("\\Leftrightarrow"),
      s("\\to"),
      s("\\mapsto"),
      s("\\therefore"),
      s("\\forall"),
      s("\\exists"),
      s("\\in"),
      s("\\notin"),
      s("\\subseteq"),
      s("\\cup"),
      s("\\cap"),
      s("\\emptyset"),
      s("\\land"),
      s("\\lor"),
      s("\\neg"),
      s("\\equiv"),
      s("\\triangleq", "defined as"),
    ],
  },
  {
    id: "robotics",
    en: "Robotics",
    vi: "Robotics",
    items: [
      s(
        "R(\\theta) = \\begin{bmatrix} \\cos\\theta & -\\sin\\theta \\\\ \\sin\\theta & \\cos\\theta \\end{bmatrix}",
        "2D rotation",
        { block: true, preview: "R(\\theta)" },
      ),
      s(
        "T = \\begin{bmatrix} R & \\mathbf{p} \\\\ \\mathbf{0}^{\\top} & 1 \\end{bmatrix}",
        "homogeneous transform",
        { block: true, preview: "\\begin{bmatrix}R&p\\\\0&1\\end{bmatrix}" },
      ),
      s("{}^{A}T_{B}", "frame transform", { preview: "{}^{A}T_{B}" }),
      s(
        "\\dot{\\mathbf{x}} = J(\\mathbf{q})\\, \\dot{\\mathbf{q}}",
        "Jacobian",
        {
          preview: "\\dot x = J\\dot q",
        },
      ),
      s(
        "M(\\mathbf{q})\\ddot{\\mathbf{q}} + C(\\mathbf{q},\\dot{\\mathbf{q}})\\dot{\\mathbf{q}} + \\mathbf{g}(\\mathbf{q}) = \\boldsymbol{\\tau}",
        "manipulator dynamics",
        { block: true, preview: "M\\ddot q + C\\dot q + g = \\tau" },
      ),
      s(
        "u(t) = K_p e(t) + K_i \\int_0^t e(\\tau)\\, d\\tau + K_d \\frac{de}{dt}",
        "PID",
        { block: true, preview: "K_p e + K_i\\!\\int e + K_d\\dot e" },
      ),
      s(
        "\\begin{aligned}\n\\hat{x}^- &= F \\hat{x} + B u \\\\\nP^- &= F P F^{\\top} + Q \\\\\nK &= P^- H^{\\top} (H P^- H^{\\top} + R)^{-1} \\\\\n\\hat{x} &= \\hat{x}^- + K (z - H \\hat{x}^-) \\\\\nP &= (I - K H) P^-\n\\end{aligned}",
        "Kalman filter",
        { block: true, preview: "K = P^-H^\\top(HP^-H^\\top+R)^{-1}" },
      ),
      s("\\dot{\\mathbf{x}} = A\\mathbf{x} + B\\mathbf{u}", "state space", {
        preview: "\\dot x = Ax + Bu",
      }),
      s(
        "J = \\int_0^\\infty \\left( \\mathbf{x}^{\\top} Q \\mathbf{x} + \\mathbf{u}^{\\top} R \\mathbf{u} \\right) dt",
        "LQR cost",
        { block: true, preview: "\\int x^\\top Qx + u^\\top Ru" },
      ),
      s(
        "V(s) = \\max_{a} \\Big[ r(s,a) + \\gamma \\sum_{s'} P(s' \\mid s,a)\\, V(s') \\Big]",
        "Bellman",
        { block: true, preview: "V(s)=\\max_a[r+\\gamma V']" },
      ),
      s(
        "\\mathbf{v} = \\boldsymbol{\\omega} \\times \\mathbf{r}",
        "rigid velocity",
        {
          preview: "v = \\omega \\times r",
        },
      ),
      s("P = V I", "electric power", { preview: "P = VI" }),
    ],
  },
];

/**
 * Formulas written in a lesson body, de-duplicated: display equations first
 * ($$ … $$, inserted as blocks), then substantial inline ones ($ … $ with an
 * equation or relation), so lessons that only use inline math still offer some.
 * Code blocks are skipped.
 */
export function lessonFormulas(body: string, limit = 40) {
  const prose = body.replace(/```[\s\S]*?```/g, "");
  const seen = new Set<string>();
  const out: { tex: string; block: boolean }[] = [];
  const add = (tex: string, block: boolean) => {
    if (!tex || seen.has(tex) || out.length >= limit) return;
    seen.add(tex);
    out.push({ tex, block });
  };
  for (const m of prose.matchAll(/\$\$([\s\S]+?)\$\$/g)) add(m[1].trim(), true);
  const inline = prose.replace(/\$\$[\s\S]+?\$\$/g, "");
  for (const m of inline.matchAll(/(?<![\\$])\$([^$\n]{6,160})\$/g)) {
    const tex = m[1].trim();
    if (/[=<>]|\\(le|ge|approx|propto|to)\b/.test(tex)) add(tex, false);
  }
  return out;
}

/** Whether `pos` sits inside $…$ or $$…$$ in `text` (unescaped dollars). */
export function insideMath(text: string, pos: number) {
  const before = text.slice(0, pos).replace(/\\\$/g, "");
  const display = (before.match(/\$\$/g) ?? []).length;
  if (display % 2 === 1) return true;
  const single = (before.replace(/\$\$/g, "").match(/\$/g) ?? []).length;
  return single % 2 === 1;
}

/**
 * Insert a snippet into `text`, replacing the selection [start, end).
 * Outside math it is wrapped in $…$ (or $$…$$ on its own lines for block
 * snippets). Returns the new text and where the cursor should go.
 */
export function insertSnippet(
  text: string,
  start: number,
  end: number,
  snippet: { tex: string; block?: boolean; raw?: boolean },
) {
  const selected = text.slice(start, end);
  const marker = snippet.tex.indexOf("▮");
  let tex = snippet.tex.replace("▮", selected);
  let caret = marker >= 0 ? marker + selected.length : tex.length;
  if (!snippet.raw && !insideMath(text, start)) {
    if (snippet.block) {
      const lead = start > 0 && text[start - 1] !== "\n" ? "\n\n" : "";
      const open = `${lead}$$\n`;
      tex = `${open}${tex}\n$$\n`;
      caret += open.length;
    } else {
      // A "$" right next to the new one would read as "$$" (display math).
      const lead = text[start - 1] === "$" ? " " : "";
      const tail = text[end] === "$" ? " " : "";
      tex = `${lead}$${tex}$${tail}`;
      caret += 1 + lead.length;
    }
  }
  return {
    text: text.slice(0, start) + tex + text.slice(end),
    caret: start + caret,
  };
}

export const noteTemplates = {
  formula: {
    en: "\n### Formula name\n\n$$\n\n$$\n\n- **Symbols:** \n- **Units:** \n- **When to use:** \n- **Assumptions / limits:** \n- **Example:** \n",
    vi: "\n### Tên công thức\n\n$$\n\n$$\n\n- **Ký hiệu:** \n- **Đơn vị:** \n- **Khi nào dùng:** \n- **Giả thiết / giới hạn:** \n- **Ví dụ:** \n",
  },
  lesson: {
    en: "## Key ideas\n\n- \n\n## Formulas\n\n$$\n\n$$\n\n## Worked example\n\n\n## Questions I still have\n\n- \n\n## Common mistakes\n\n- \n",
    vi: "## Ý chính\n\n- \n\n## Công thức\n\n$$\n\n$$\n\n## Ví dụ đã giải\n\n\n## Câu hỏi còn thắc mắc\n\n- \n\n## Lỗi hay gặp\n\n- \n",
  },
};
