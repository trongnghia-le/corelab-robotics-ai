"use client";
import { useState } from "react";
import {
  add,
  dot,
  projection,
  transform,
  determinant,
  forward,
  jacobian,
  type Vec2,
  type Mat2,
} from "@/lib/visualization-math";
import { Demo, Slider, Plane, pair, fmt } from "./common";
export function Vectors() {
  const [u, setU] = useState<Vec2>([3, 2]),
    [v, setV] = useState<Vec2>([1, 1]);
  const sum = add(u, v),
    p = projection(u, v),
    extent =
      Math.max(5, ...[...u, ...v, ...sum, ...(p ?? [])].map(Math.abs)) + 1;
  return (
    <Demo
      title="Vectors and projections"
      description="Predict the sum and projection. Orange is u, blue is v, gold is u+v, and green is the projection with its perpendicular residual."
      reset={() => {
        setU([3, 2]);
        setV([1, 1]);
      }}
      example="For u=(3,2), v=(1,1): u+v=(4,3), ‖u‖=√13, u·v=5, and projᵥu=(2.5,2.5). The residual (0.5,−0.5) has zero dot product with v. Projection onto the zero vector is undefined."
    >
      <div className="demo-grid">
        <div>
          {u.map((value, i) => (
            <Slider
              key={i}
              label={`Vector ${i === 0 ? "x" : "y"} coordinate`}
              value={value}
              min={-4}
              max={4}
              onChange={(value) =>
                setU((old) => old.map((x, j) => (i === j ? value : x)) as Vec2)
              }
            />
          ))}
          {v.map((value, i) => (
            <Slider
              key={i}
              label={`v ${i === 0 ? "x" : "y"} coordinate`}
              value={value}
              min={-4}
              max={4}
              onChange={(value) =>
                setV((old) => old.map((x, j) => (i === j ? value : x)) as Vec2)
              }
            />
          ))}
          <p>
            <code>u+v = {pair(sum)}</code>
          </p>
          <p>
            <code>projᵥ u = {p ? pair(p) : "undefined (v=0)"}</code>
          </p>
          <p>
            <code>projᵥu = v(u·v)/(v·v)</code>
          </p>
          <p>
            ‖u‖₂ = {Math.hypot(...u).toFixed(3)} · u·v = {fmt(dot(u, v))}
          </p>
        </div>
        <Plane
          extent={extent}
          lines={[
            { to: u, color: "#f97316", label: "u", labelOffset: [8, 18] },
            { to: v, color: "#7ea7d8", label: "v" },
            { from: u, to: sum, color: "#7ea7d8", dashed: true },
            { to: sum, color: "#d8c08b", label: "u+v" },
            ...(p
              ? [
                  {
                    to: p,
                    color: "#84b39b",
                    label: "proj",
                    labelOffset: [-35, -14] as Vec2,
                  },
                  { from: p, to: u, color: "#84b39b", dashed: true },
                ]
              : []),
          ]}
          caption="Arrow addition and perpendicular projection; axes rescale to keep every vector visible."
        />
      </div>
    </Demo>
  );
}
export function MatrixTransform() {
  const [a, setA] = useState<Mat2>([1, 1, 0, 1]);
  const e1 = transform(a, [1, 0]),
    e2 = transform(a, [0, 1]),
    point = transform(a, [1, 1]);
  return (
    <Demo
      title="Matrix transformations"
      description="The columns of A are the transformed basis vectors. Change a coefficient or compare a rotation with a shear."
      reset={() => setA([1, 1, 0, 1])}
      example="A=[[1,1],[0,1]] maps (1,1) to (2,1). Its determinant is 1: area is preserved, angles are not. A singular matrix (det=0) collapses the plane onto a line or point."
    >
      <div className="demo-grid">
        <div>
          {a.map((value, i) => (
            <Slider
              key={i}
              label={`A row ${Math.floor(i / 2) + 1} column ${(i % 2) + 1}`}
              value={value}
              min={-2}
              max={2}
              onChange={(v) =>
                setA((old) => old.map((x, j) => (i === j ? v : x)) as Mat2)
              }
            />
          ))}
          <div className="demo-actions">
            <button onClick={() => setA([1, 0, 0, 1])}>Identity</button>
            <button onClick={() => setA([0, -1, 1, 0])}>Rotate 90°</button>
            <button onClick={() => setA([1, 1, 0, 1])}>Shear</button>
          </div>
          <p>
            <code>
              A = [[{a[0]}, {a[1]}], [{a[2]}, {a[3]}]]
            </code>
          </p>
          <p>
            <code>
              A(1,1) = {pair(point)}; det A = {fmt(determinant(a))}
            </code>
          </p>
        </div>
        <Plane
          extent={
            Math.max(
              3,
              2 * (Math.abs(a[0]) + Math.abs(a[1])),
              2 * (Math.abs(a[2]) + Math.abs(a[3])),
            ) + 0.5
          }
          lines={[
            ...[-2, -1, 0, 1, 2].flatMap((t) => [
              {
                from: transform(a, [-2, t]),
                to: transform(a, [2, t]),
                color: "#84b39b",
                dashed: true,
              },
              {
                from: transform(a, [t, -2]),
                to: transform(a, [t, 2]),
                color: "#84b39b",
                dashed: true,
              },
            ]),
            { to: e1, color: "#f97316", label: "Ae₁" },
            { to: e2, color: "#7ea7d8", label: "Ae₂" },
            { to: point, color: "#d8c08b", label: "A(1,1)" },
          ]}
          caption="Green: transformed grid. Orange/blue: basis columns; gold: mapped point. Axes rescale to keep the grid visible."
        />
      </div>
    </Demo>
  );
}
export function Robot({ velocity = false }: { velocity?: boolean }) {
  const [q, setQ] = useState<Vec2>([3, 2]),
    [speed, setSpeed] = useState<Vec2>([0.5, 0]),
    [dt, setDt] = useState(0.1);
  const r = q.map((v) => (v * Math.PI) / 180) as Vec2,
    { elbow, tip } = forward(...r),
    j = jacobian(...r),
    v = transform(j, speed),
    predicted = add(tip, [v[0] * dt, v[1] * dt]),
    actual = forward(r[0] + speed[0] * dt, r[1] + speed[1] * dt).tip;
  return (
    <Demo
      title={
        velocity
          ? "Jacobian: joint motion becomes tip velocity"
          : "One configuration, one endpoint position"
      }
      description={
        velocity
          ? "J maps joint rates in rad/s to endpoint velocity in m/s. Compare the linear prediction with a finite joint step."
          : "Both joint angles are relative. Predict the endpoint before changing a joint. This geometry model does not control a robot."
      }
      reset={() => {
        setQ([3, 2]);
        setSpeed([0.5, 0]);
        setDt(0.1);
      }}
      example="With q₁=90°, q₂=0°, l₁=2 m, l₂=1.5 m, the tip is (0,3.5) m. At q=(0,0), J=[[0,0],[3.5,1.5]]: instantaneous horizontal velocity is impossible. The Jacobian predicts only small displacements; finite rotations follow an arc."
    >
      <div className="demo-grid">
        <div>
          {q.map((value, i) => (
            <Slider
              key={i}
              label={`Joint ${i + 1} angle`}
              value={value}
              min={-180}
              max={180}
              step={1}
              onChange={(v) =>
                setQ((old) => old.map((x, j) => (i === j ? v : x)) as Vec2)
              }
            />
          ))}
          <p>
            <code>p = {pair(tip)} m</code>
          </p>
          <p>
            <code>
              x=l₁cos q₁+l₂cos(q₁+q₂)
              <br />
              y=l₁sin q₁+l₂sin(q₁+q₂)
            </code>
          </p>
          <p className="small">l₁=2 m, l₂=1.5 m · q_rad=q_deg×π/180</p>
          {velocity && (
            <>
              {speed.map((value, i) => (
                <Slider
                  key={i}
                  label={`Joint ${i + 1} rate (rad/s)`}
                  value={value}
                  min={-1}
                  max={1}
                  onChange={(v) =>
                    setSpeed(
                      (old) => old.map((x, j) => (i === j ? v : x)) as Vec2,
                    )
                  }
                />
              ))}
              <Slider
                label="Prediction interval (s)"
                value={dt}
                min={0.01}
                max={0.5}
                step={0.01}
                onChange={setDt}
              />
              <p>
                <code>
                  J = [[{fmt(j[0])}, {fmt(j[1])}], [{fmt(j[2])}, {fmt(j[3])}]]
                </code>
              </p>
              <p>
                <code>v=Jq̇={pair(v)} m/s</code>
              </p>
              <p>
                det J = {fmt(determinant(j))}
                {Math.abs(determinant(j)) < 0.05
                  ? " · Near singular: one direction is lost."
                  : ""}
              </p>
              <p>
                Prediction error:{" "}
                {Math.hypot(
                  predicted[0] - actual[0],
                  predicted[1] - actual[1],
                ).toFixed(4)}{" "}
                m
              </p>
            </>
          )}
        </div>
        <Plane
          extent={4.8}
          lines={[
            { to: elbow, color: "#7ea7d8", thick: true },
            { from: elbow, to: tip, color: "#f97316", thick: true },
            ...(velocity
              ? [{ from: tip, to: predicted, color: "#84b39b", label: "Jq̇Δt" }]
              : []),
          ]}
          points={[
            { point: [0, 0], color: "#d7e0eb" },
            { point: elbow, color: "#d7e0eb" },
            { point: tip, color: "#f97316" },
            ...(velocity ? [{ point: actual, color: "#d8c08b" }] : []),
          ]}
          caption={
            velocity
              ? "Green: linear prediction; gold: exact FK after the joint step. Fixed world x/y frame; 2.4 m grid."
              : "Blue: link 1; orange: link 2. Coordinates in the fixed world frame; 2.4 m grid."
          }
        />
      </div>
    </Demo>
  );
}
