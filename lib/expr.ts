// A small, safe arithmetic language for interactive lesson blocks: numbers,
// variables, + - * / ^, unary minus, parentheses and a fixed set of maths
// functions. No eval, no property access, no strings.
export type Expr =
  | { k: "num"; v: number }
  | { k: "var"; name: string }
  | { k: "neg"; a: Expr }
  | { k: "bin"; op: string; a: Expr; b: Expr }
  | { k: "call"; fn: string; args: Expr[] };

const FUNCS: Record<string, (...a: number[]) => number> = {
  sin: Math.sin,
  cos: Math.cos,
  tan: Math.tan,
  asin: Math.asin,
  acos: Math.acos,
  atan: Math.atan,
  atan2: Math.atan2,
  sinh: Math.sinh,
  cosh: Math.cosh,
  tanh: Math.tanh,
  sqrt: Math.sqrt,
  exp: Math.exp,
  log: Math.log,
  ln: Math.log,
  log10: Math.log10,
  abs: Math.abs,
  min: Math.min,
  max: Math.max,
  floor: Math.floor,
  ceil: Math.ceil,
  round: Math.round,
  sign: Math.sign,
  hypot: Math.hypot,
  clamp: (x, lo, hi) => Math.min(hi, Math.max(lo, x)),
  // Step function and a smooth comparison helper for piecewise models.
  step: (x) => (x >= 0 ? 1 : 0),
  ifpos: (c, a, b) => (c > 0 ? a : b),
};
export const CONSTANTS: Record<string, number> = {
  pi: Math.PI,
  e: Math.E,
  deg: Math.PI / 180,
  g: 9.81,
};

type Tok = { t: "num" | "id" | "op"; v: string };

function tokenize(src: string): Tok[] {
  const out: Tok[] = [];
  let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) {
      i++;
      continue;
    }
    const num = /^(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?/.exec(src.slice(i));
    if (num) {
      out.push({ t: "num", v: num[0] });
      i += num[0].length;
      continue;
    }
    const id = /^[A-Za-z_][A-Za-z0-9_]*/.exec(src.slice(i));
    if (id) {
      out.push({ t: "id", v: id[0] });
      i += id[0].length;
      continue;
    }
    if ("+-*/^(),".includes(c)) {
      out.push({ t: "op", v: c });
      i++;
      continue;
    }
    throw new Error(`Unexpected "${c}" in "${src}"`);
  }
  return out;
}

export function parse(src: string): Expr {
  const toks = tokenize(src);
  let p = 0;
  const peek = () => toks[p];
  const eat = (v?: string) => {
    const t = toks[p];
    if (!t || (v !== undefined && t.v !== v))
      throw new Error(`Expected "${v ?? "a value"}" in "${src}"`);
    p++;
    return t;
  };
  // Precedence climbing: + - < * / < unary - < ^ (right associative).
  const expr = (): Expr => {
    let a = term();
    while (peek()?.v === "+" || peek()?.v === "-") {
      const op = eat().v;
      a = { k: "bin", op, a, b: term() };
    }
    return a;
  };
  const term = (): Expr => {
    let a = unary();
    while (peek()?.v === "*" || peek()?.v === "/") {
      const op = eat().v;
      a = { k: "bin", op, a, b: unary() };
    }
    return a;
  };
  const unary = (): Expr => {
    if (peek()?.v === "-") {
      eat();
      return { k: "neg", a: unary() };
    }
    if (peek()?.v === "+") {
      eat();
      return unary();
    }
    return power();
  };
  const power = (): Expr => {
    const a = atom();
    if (peek()?.v === "^") {
      eat();
      return { k: "bin", op: "^", a, b: unary() };
    }
    return a;
  };
  const atom = (): Expr => {
    const t = eat();
    if (t.t === "num") return { k: "num", v: Number(t.v) };
    if (t.t === "id") {
      if (peek()?.v === "(") {
        if (!Object.hasOwn(FUNCS, t.v))
          throw new Error(`Unknown function ${t.v}`);
        eat("(");
        const args: Expr[] = [];
        if (peek()?.v !== ")") {
          args.push(expr());
          while (peek()?.v === ",") {
            eat(",");
            args.push(expr());
          }
        }
        eat(")");
        return { k: "call", fn: t.v, args };
      }
      return { k: "var", name: t.v };
    }
    if (t.v === "(") {
      const e = expr();
      eat(")");
      return e;
    }
    throw new Error(`Unexpected "${t.v}" in "${src}"`);
  };
  const e = expr();
  if (p < toks.length) throw new Error(`Unexpected "${toks[p].v}" in "${src}"`);
  return e;
}

export function evaluate(e: Expr, scope: Record<string, number>): number {
  switch (e.k) {
    case "num":
      return e.v;
    case "var": {
      // Own properties only: never reach Object.prototype ("constructor"...).
      if (Object.hasOwn(scope, e.name)) return scope[e.name];
      if (Object.hasOwn(CONSTANTS, e.name)) return CONSTANTS[e.name];
      throw new Error(`Unknown name ${e.name}`);
    }
    case "neg":
      return -evaluate(e.a, scope);
    case "call":
      return FUNCS[e.fn](...e.args.map((a) => evaluate(a, scope)));
    case "bin": {
      const a = evaluate(e.a, scope),
        b = evaluate(e.b, scope);
      return e.op === "+"
        ? a + b
        : e.op === "-"
          ? a - b
          : e.op === "*"
            ? a * b
            : e.op === "/"
              ? a / b
              : a ** b;
    }
  }
}

/** Parse once, evaluate many times. */
export function compile(src: string) {
  const e = parse(String(src));
  return (scope: Record<string, number>) => evaluate(e, scope);
}
