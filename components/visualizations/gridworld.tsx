"use client";
import { useState } from "react";
import {
  ACTIONS,
  WALLS,
  START,
  GOAL,
  HAZARD,
  initialGrid,
  trainGrid,
} from "@/lib/visualization-math";
import { Demo, Slider, fmt } from "./common";
export function GridWorld() {
  const [training, setTraining] = useState(initialGrid),
    [alpha, setAlpha] = useState(0.3),
    [gamma, setGamma] = useState(0.95),
    [epsilon, setEpsilon] = useState(0.2),
    [selected, setSelected] = useState(START);
  const last = training.last;
  function train(n: number) {
    setTraining((old) => trainGrid(old, n, alpha, gamma, epsilon));
  }
  return (
    <Demo
      title="Q-learning GridWorld"
      description="Learn action values in a deterministic 4×4 world. Compare exploration and greedy behavior. Each click trains a bounded batch locally."
      reset={() => {
        setTraining(initialGrid());
        setAlpha(0.3);
        setGamma(0.95);
        setEpsilon(0.2);
        setSelected(START);
      }}
      example="A transition into the goal rewards +1 and ends the episode: Q←Q+α(1−Q), with no next-state bootstrap. Other moves reward −0.04; the hazard gives −1 and terminates. Walls and edges keep the agent in place. Episodes truncate at 150 steps, bootstrapping that last nonterminal transition before resetting. Seed 42 makes a given control/click sequence reproducible."
    >
      <div className="demo-grid">
        <div>
          <Slider
            label="Learning rate α"
            value={alpha}
            min={0.05}
            max={1}
            step={0.05}
            onChange={setAlpha}
          />
          <Slider
            label="Discount γ"
            value={gamma}
            min={0}
            max={1}
            step={0.05}
            onChange={setGamma}
          />
          <Slider
            label="Exploration ε"
            value={epsilon}
            min={0}
            max={1}
            step={0.05}
            onChange={setEpsilon}
          />
          <div className="demo-actions">
            <button onClick={() => train(1)}>Train 1 episode</button>
            <button onClick={() => train(50)}>Train 50 episodes</button>
          </div>
          <p aria-live="polite">
            Episodes: {training.episodes} · Goals reached: {training.successes}
          </p>
          <p>
            <code>Q(s,a) ← Q(s,a)+α[r+γ max Q(s′,a′)−Q(s,a)]</code>
          </p>
          <p className="small">
            For terminal s′, omit γ max Q. Training retains earlier Q values
            when gains change; Reset clears them. Unvisited ties display ·;
            training breaks ties with the seeded generator.
          </p>
        </div>
        <div>
          <div className="q-grid" aria-label="GridWorld policy">
            {training.q.map((row, s) => {
              const wall = WALLS.includes(s),
                terminal = s === GOAL || s === HAZARD,
                best = Math.max(...row),
                ties = row.filter((v) => v === best).length;
              return (
                <button
                  key={s}
                  disabled={wall}
                  aria-label={`Cell ${s}: ${wall ? "wall" : s === GOAL ? "goal" : s === HAZARD ? "hazard" : `best Q ${fmt(best)}`}`}
                  aria-pressed={s === selected}
                  onClick={() => setSelected(s)}
                >
                  <strong>
                    {wall
                      ? "■"
                      : s === GOAL
                        ? "G"
                        : s === HAZARD
                          ? "!"
                          : ties === 4
                            ? "·"
                            : ACTIONS[row.indexOf(best)]}
                  </strong>
                  <small>
                    {s === START
                      ? "Start"
                      : terminal
                        ? "Terminal"
                        : !wall
                          ? fmt(best)
                          : "Wall"}
                  </small>
                </button>
              );
            })}
          </div>
          <p className="small">
            ↑ → ↓ ←: greedy action · G: goal (+1) · !: hazard (−1) · ■: wall
          </p>
          <p>Cell {selected} Q values:</p>
          <div className="q-values">
            {training.q[selected].map((v, a) => (
              <span key={a}>
                {ACTIONS[a]} {fmt(v)}
              </span>
            ))}
          </div>
        </div>
      </div>
      {last && (
        <p className="small">
          <code>
            Last update: s={last.state}, a={ACTIONS[last.action]}, Q=
            {fmt(last.old)} → {fmt(last.value)}; r={last.reward},{" "}
            {last.terminal
              ? "terminal target = r"
              : `bootstrap max Q′=${fmt(last.nextMax)}`}
          </code>
        </p>
      )}
    </Demo>
  );
}
