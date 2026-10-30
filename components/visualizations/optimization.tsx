"use client";
import { useState } from "react";
import {
  gradientStep,
  quadratic,
  pidResponse,
  type Vec2,
} from "@/lib/visualization-math";
import { Demo, Slider, Plot, fmt } from "./common";
export function GradientDescent() {
  const [rate, setRate] = useState(0.4),
    [start, setStart] = useState(4),
    [history, setHistory] = useState([4]);
  const current = history.at(-1)!;
  function step(n: number) {
    setHistory((old) => {
      const next = [...old];
      for (let i = 0; i < n && next.length < 101; i++) {
        const value = gradientStep(next.at(-1)!, rate);
        if (!Number.isFinite(value) || Math.abs(value) > 10000) break;
        next.push(value);
      }
      return next;
    });
  }
  return (
    <Demo
      title="Gradient descent"
      description="Minimize J(x)=½x². Predict which learning rates converge, oscillate, or diverge, then step through the updates."
      reset={() => {
        setRate(0.4);
        setStart(4);
        setHistory([4]);
      }}
      example="At x=4 and α=0.4, ∇J=4 and x_next=4−0.4×4=2.4. For this quadratic, 0<α<2 converges, α=2 oscillates, and α>2 diverges. This 1D example does not imply that all neural-network losses are convex."
    >
      <div className="demo-grid">
        <div>
          <Slider
            label="Learning rate α"
            value={rate}
            min={0.05}
            max={2.5}
            step={0.05}
            onChange={setRate}
          />
          <Slider
            label="Starting x (restarts trajectory)"
            value={start}
            min={-5}
            max={5}
            onChange={(x) => {
              setStart(x);
              setHistory([x]);
            }}
          />
          <div className="demo-actions">
            <button
              disabled={history.length >= 101 || Math.abs(current) > 4000}
              onClick={() => step(1)}
            >
              Step once
            </button>
            <button
              disabled={history.length >= 101 || Math.abs(current) > 4000}
              onClick={() => step(10)}
            >
              Step 10 times
            </button>
          </div>
          <p>
            <code>xₖ₊₁ = xₖ − α∇J(xₖ) = (1−α)xₖ</code>
          </p>
          <p>
            Step {history.length - 1}: x={fmt(current)}, J=
            {fmt(quadratic(current))}
          </p>
          <p>
            {rate < 2
              ? "Convergent for this quadratic."
              : rate === 2
                ? "Oscillates without reducing the loss."
                : "Divergent: the distance grows."}{" "}
            Display stops after 100 steps or before |x| exceeds 10,000.
          </p>
        </div>
        <Plot
          series={[
            {
              label: "J(xₖ)",
              color: "#f97316",
              points: history.map((x, k) => [k, quadratic(x)] as Vec2),
            },
          ]}
          xLabel="step"
          yLabel="loss"
          caption="Loss after each update. Vertical scale follows the trajectory."
        />
      </div>
    </Demo>
  );
}
export function PID() {
  const [kp, setKp] = useState(2),
    [ki, setKi] = useState(0.5),
    [kd, setKd] = useState(0);
  const response = pidResponse(kp, ki, kd),
    last = response.at(-1)!,
    peak = Math.max(...response.map((p) => p.y));
  return (
    <Demo
      title="PID step response"
      description="Track a unit reference using a normalized first-order plant. Change one gain at a time and explain offset, overshoot, and damping."
      reset={() => {
        setKp(2);
        setKi(0.5);
        setKd(0);
      }}
      example="With Kp=2, Ki=Kd=0, the steady output is Kp/(1+Kp)=2/3, leaving a 1/3 error. Integral action can remove that offset. This ideal, noise-free model uses derivative on measurement and unlimited actuation; it omits saturation, windup, delay and hardware dynamics."
    >
      <div className="demo-grid">
        <div>
          <Slider
            label="Proportional gain Kp"
            value={kp}
            min={0}
            max={8}
            onChange={setKp}
          />
          <Slider
            label="Integral gain Ki"
            value={ki}
            min={0}
            max={8}
            onChange={setKi}
          />
          <Slider
            label="Derivative gain Kd"
            value={kd}
            min={0}
            max={4}
            onChange={setKd}
          />
          <p>
            <code>
              e=1−y; z′=e; u=Kp·e+Ki·z−Kd·y′
              <br />
              y′=−y+u = (Kp·e+Ki·z−y)/(1+Kd)
            </code>
          </p>
          <p>Euler step 0.01 s · simulated duration 16 s</p>
          <p>
            Final y={fmt(last.y)} · error={fmt(1 - last.y)} · peak={fmt(peak)} ·
            final u={fmt(last.u)}
          </p>
        </div>
        <Plot
          series={[
            {
              label: "reference",
              color: "#7ea7d8",
              points: [
                [0, 1],
                [16, 1],
              ],
            },
            {
              label: "output y",
              color: "#f97316",
              points: response.map((p) => [p.t, p.y]),
            },
          ]}
          xLabel="s"
          yLabel="output"
          caption="Unit reference (blue) versus plant response (orange)."
        />
      </div>
    </Demo>
  );
}
