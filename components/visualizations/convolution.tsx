"use client";
import { useState } from "react";
import { convolve } from "@/lib/visualization-math";
import { Demo } from "./common";
const image = () => Array.from({ length: 5 }, () => [0, 0, 1, 1, 1]);
const edge = () => [
  [-1, 0, 1],
  [-1, 0, 1],
  [-1, 0, 1],
];
export function Convolution() {
  const [input, setInput] = useState(image),
    [kernel, setKernel] = useState(edge),
    [cell, setCell] = useState<[number, number]>([1, 1]);
  const output = convolve(input, kernel),
    [r, c] = cell;
  const terms = kernel.flatMap((row, kr) =>
    row.map((w, kc) => `${input[r + kr][c + kc]}×(${w})`),
  );
  return (
    <Demo
      title="CNN convolution: a sliding kernel"
      description="Edit the image or kernel and select an output cell to inspect its receptive field. CNNs usually use cross-correlation: the kernel is not flipped."
      reset={() => {
        setInput(image());
        setKernel(edge());
        setCell([1, 1]);
      }}
      example="The default vertical-edge kernel sums three right-minus-left differences. At output (1,1), the patch columns are [0,1,1], so each row contributes 1 and the output is 3. A 5×5 input with a 3×3 kernel, stride 1 and no padding gives a 3×3 output. There is no bias or activation here."
    >
      <div className="convolution-grids">
        <div>
          <h3>Input 5×5</h3>
          <div
            className="number-grid"
            style={{ gridTemplateColumns: "repeat(5,minmax(0,1fr))" }}
          >
            {input.flatMap((row, ir) =>
              row.map((v, ic) => (
                <label
                  key={`${ir}-${ic}`}
                  className={
                    ir >= r && ir < r + 3 && ic >= c && ic < c + 3
                      ? "selected"
                      : ""
                  }
                >
                  <span className="sr-only">
                    Input row {ir + 1} column {ic + 1}
                  </span>
                  <input
                    type="number"
                    min={-9}
                    max={9}
                    step={1}
                    value={v}
                    onChange={(e) =>
                      setInput((old) =>
                        old.map((line, i) =>
                          line.map((x, j) =>
                            i === ir && j === ic
                              ? Math.max(
                                  -9,
                                  Math.min(9, Number(e.target.value)),
                                )
                              : x,
                          ),
                        ),
                      )
                    }
                  />
                </label>
              )),
            )}
          </div>
        </div>
        <div>
          <h3>Kernel 3×3</h3>
          <div className="number-grid">
            {kernel.flatMap((row, ir) =>
              row.map((v, ic) => (
                <label key={`${ir}-${ic}`}>
                  <span className="sr-only">
                    Kernel row {ir + 1} column {ic + 1}
                  </span>
                  <input
                    type="number"
                    min={-9}
                    max={9}
                    step={1}
                    value={v}
                    onChange={(e) =>
                      setKernel((old) =>
                        old.map((line, i) =>
                          line.map((x, j) =>
                            i === ir && j === ic
                              ? Math.max(
                                  -9,
                                  Math.min(9, Number(e.target.value)),
                                )
                              : x,
                          ),
                        ),
                      )
                    }
                  />
                </label>
              )),
            )}
          </div>
          <div className="demo-actions">
            <button
              onClick={() =>
                setKernel([
                  [0, 0, 0],
                  [0, 1, 0],
                  [0, 0, 0],
                ])
              }
            >
              Identity
            </button>
            <button onClick={() => setKernel(edge())}>Edge</button>
          </div>
        </div>
        <div>
          <h3>Output 3×3</h3>
          <div className="number-grid">
            {output.flatMap((row, ir) =>
              row.map((v, ic) => (
                <button
                  key={`${ir}-${ic}`}
                  aria-label={`Output row ${ir + 1} column ${ic + 1}: ${v}`}
                  aria-pressed={ir === r && ic === c}
                  onClick={() => setCell([ir, ic])}
                >
                  {v}
                </button>
              )),
            )}
          </div>
        </div>
      </div>
      <p>
        <code>Y[r,c] = ΣᵢΣⱼ X[r+i,c+j] K[i,j]</code>
      </p>
      <p className="convolution-sum" aria-live="polite">
        <code>
          Y[{r},{c}] = {terms.join(" + ")} = {output[r][c]}
        </code>
      </p>
      <p className="small">
        Highlighted input cells form the selected output&apos;s 3×3 receptive
        field. All indices in the equation start at zero.
      </p>
    </Demo>
  );
}
