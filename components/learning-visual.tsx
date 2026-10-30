"use client";
import dynamic from "next/dynamic";
import type { VisualizationId } from "@/lib/media";
const Vectors = dynamic(() =>
  import("./visualizations/geometry").then((m) => m.Vectors),
);
const MatrixTransform = dynamic(() =>
  import("./visualizations/geometry").then((m) => m.MatrixTransform),
);
const Robot = dynamic(() =>
  import("./visualizations/geometry").then((m) => m.Robot),
);
const GradientDescent = dynamic(() =>
  import("./visualizations/optimization").then((m) => m.GradientDescent),
);
const PID = dynamic(() =>
  import("./visualizations/optimization").then((m) => m.PID),
);
const Convolution = dynamic(() =>
  import("./visualizations/convolution").then((m) => m.Convolution),
);
const GridWorld = dynamic(() =>
  import("./visualizations/gridworld").then((m) => m.GridWorld),
);
export function LearningVisual({
  topicId,
  ids,
}: {
  topicId: string;
  ids?: VisualizationId[];
}) {
  const selected =
    ids ??
    (topicId === "M02"
      ? ["vectors"]
      : topicId === "R04"
        ? ["forward-kinematics"]
        : []);
  return (
    <>
      {selected.map((id) => (
        <div id={`explore-${id}`} key={id}>
          {id === "vectors" ? (
            <Vectors />
          ) : id === "matrices" ? (
            <MatrixTransform />
          ) : id === "gradient-descent" ? (
            <GradientDescent />
          ) : id === "forward-kinematics" ? (
            <Robot />
          ) : id === "jacobian" ? (
            <Robot velocity />
          ) : id === "pid" ? (
            <PID />
          ) : id === "convolution" ? (
            <Convolution />
          ) : id === "q-learning" ? (
            <GridWorld />
          ) : null}
        </div>
      ))}
    </>
  );
}
