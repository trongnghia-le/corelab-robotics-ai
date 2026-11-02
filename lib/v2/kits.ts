import { readFileSync } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import type { Store } from "../storage";
import { canonical, digest, hash, strictJSON, V2Error } from "./contracts";
import { insert, meta, nextSequence, write, type DB } from "./db";
import { attemptById, expose } from "./records";
import type { Attempt } from "./state";
import { fingerprintCandidates } from "./assessments";
import type { Item } from "./content";

const definitions = [
  {
    id: "L01-SE2",
    title: "Frames self-check kit",
    topic: "R03",
    objectives: [
      "M12.frame-labels",
      "M12.point-vs-direction",
      "R03.compose-invert-se2",
      "R03.rotation-validity",
    ],
    description:
      "Implement six SE(2) operations with noncommuting, inverse, shape, proper-rotation and nonmutation fixtures.",
  },
  {
    id: "L02-planar",
    title: "Planar FK self-check kit",
    topic: "R04",
    objectives: ["R04.planar-fk"],
    description:
      "Implement a planar two-link pose, including unequal links, folded and stretched configurations, orientation and invalid inputs.",
  },
  {
    id: "L03-odometry",
    title: "Odometry self-check kit",
    topic: "R02",
    objectives: ["R02.exact-arc"],
    description:
      "Implement wheel/body velocity conversion and exact planar odometry. Check nonzero initial headings, reverse motion, pure spin, small arcs, units and invalid inputs. No calibration or physical-position claim.",
  },
  {
    id: "L04-pid",
    title: "Bounded feedback self-check kit",
    topic: "C01",
    objectives: ["C01.bounded-step"],
    description:
      "Implement bounded P and PI steps with anti-windup on a declared toy integrator, a closed-loop simulation and settling/overshoot metrics. Practice beyond the one-step objective; no actuator, torque or hardware claim.",
  },
  {
    id: "L06-jacobian-ik",
    title: "Jacobian and IK self-check kit",
    topic: "R06",
    objectives: ["R06.planar-jacobian", "R05.planar-ik"],
    description:
      "Implement a planar 2R endpoint Jacobian, determinant and tip velocity, both analytic IK branches with joint limits, and a bounded numerical solver that reports failure honestly. No 6D/twist Jacobian or hardware claim.",
  },
  {
    id: "L07-trajectory",
    title: "Trajectory time-law self-check kit",
    topic: "M05",
    objectives: ["M05.trapezoid-profile"],
    description:
      "Implement a one-axis triangular/trapezoidal time law: phases, minimum and slower durations, sampling, impossible requests and a common duration for two joints. Numerical self-check only; no jerk, torque or robot claim.",
  },
  {
    id: "L09-localization",
    title: "Grid Bayes localization self-check kit",
    topic: "C06",
    objectives: ["C06.grid-bayes"],
    description:
      "Manual numerical self-check of a 1-D histogram Bayes filter (ring or walls, noisy motion kernel, toy door sensor) and deterministic particle weights, ESS and systematic resampling. No SLAM, real sensor or simulator.",
  },
  {
    id: "L10-kalman",
    title: "Linear Kalman and fusion self-check kit",
    topic: "C07",
    objectives: ["C07.linear-kalman"],
    description:
      "Original numerical self-check for declared scalar and 2-state linear Kalman steps: predict, innovation, gain, update, sequential vs information-form fusion, NIS replay. No EKF/UKF, ensembles or sensors.",
  },
  {
    id: "L11-planning",
    title: "Grid search and swept collision self-check kit",
    topic: "E02",
    objectives: ["E02.grid-astar"],
    description:
      "Manual self-check: grid A* with declared costs and corner rule, heuristic, budgeted search with honest failure, exact segment-rectangle and swept-square tests. Exhaustive-Dijkstra oracle on small grids; no RRT/PRM, arms or simulator.",
  },
  {
    id: "L21-identification",
    title: "First-order identification self-check kit",
    topic: "S08",
    objectives: ["S08.parameter-fit"],
    description:
      "Original numerical self-check for a declared first-order model on synthetic logs: normal equations, least-squares fit, held-out residual, condition number and identifiability, parameter std, bounded randomisation. No robot data or sim-to-real.",
  },
  {
    id: "L16-camera",
    title: "Pinhole camera and calibration self-check kit",
    topic: "V04",
    objectives: ["V04.calibration-residual"],
    description:
      "Original numerical self-check for an ideal pinhole with a declared rigid transform: project, deproject, invalid depth, reprojection RMS, two-line intrinsic fit and held-out evaluation. No images, distortion or devices.",
  },
  {
    id: "L19-imitation",
    title: "Episode QA and imitation baseline self-check kit",
    topic: "RL17",
    objectives: ["RL17.bc-qa"],
    description:
      "Manual numerical self-check of episode QA (named defects, duplicates, lag), session-grouped splits, leakage audit and a train-only least-squares BC line against a mean-action baseline. Tiny lists only; no neural policy, LeRobot or real robot data.",
  },
  {
    id: "L15-executive",
    title: "Executive and watchdog self-check kit",
    topic: "S07",
    objectives: ["S07.watchdog-executive"],
    description:
      "Manual self-check: mock pick-and-deliver state machine with guards, timestamp watchdog, cancel/fault, bounded retry and recovery, trace replay and a no-motion-while-unsafe monitor. Table and exhaustive checks; simulation only, no hardware or certification.",
  },
  {
    id: "L18-grasp",
    title: "Parallel-jaw friction grasp self-check kit",
    topic: "R08",
    objectives: ["R08.friction-grasp"],
    description:
      "Original analytic self-check for a two-pad Coulomb grasp: safety factor, minimum squeeze, friction cone and a threshold retention observer over synthetic traces. No physics engine or hardware.",
  },
  {
    id: "L20-rl",
    title: "RL experiment core self-check kit",
    topic: "RL06",
    objectives: ["RL06.tabular-update"],
    description:
      "Manual numerical self-check of Q-learning/SARSA updates with terminal vs time-limit bootstrapping, epsilon-greedy probabilities, returns, value iteration, per-seed statistics and a reward-loophole check. Tiny tables; no simulator or training.",
  },
  {
    id: "L12-description",
    title: "Robot description and TF self-check kit",
    topic: "S04",
    objectives: ["S04.urdf-chain"],
    description:
      "Original numerical self-check: parse a serial URDF-like string, validate its structure, compute base-to-link and link-to-link transforms and joint axes in the base frame. No meshes, xacro, ROS or TF2 runtime, no hardware.",
  },
  {
    id: "L05-replay",
    title: "Replay node core self-check kit",
    topic: "S03",
    objectives: ["S03.replay-node"],
    description:
      "Implement a ROS-free odometry node core replayed on a recorded message list (frame, stamp, gap, reset policies), a minimal fault reproducer, and a test suite judged against valid and buggy cores. Replay only; no ROS, DDS, TF2 or robot.",
  },
  {
    id: "L17-alignment",
    title: "Visual alignment self-check kit",
    topic: "V03",
    objectives: ["V03.visual-servo-step"],
    description:
      "Original numerical self-check on a synthetic pan/tilt pinhole: exact projection, pixel error, label/age/depth target selection, saturated servo step, cancel on stale or lost target, finite convergence suite. No images, devices or physics.",
  },
  {
    id: "L13-navigation",
    title: "Pure-pursuit path follower self-check kit",
    topic: "C10",
    objectives: ["C10.path-follow"],
    description:
      "Manual self-check: nearest-point distance, lookahead point on a polyline, curvature 2*y_L/d^2, speed/turn-rate saturation, closed-loop unicycle simulation and trace evaluation. Offline kinematic toy; no Nav2, ROS, TF or costmaps.",
  },
  {
    id: "L22-reasoning",
    title: "Belief and task-reasoning self-check kit",
    topic: "E03",
    objectives: ["E03.belief-plan"],
    description:
      "Manual self-check of STRIPS-style steps, belief updates, weighted posteriors, conditional plan checks with counterexample worlds and groundedness on a tiny symbolic toy. Exact enumeration; no perception, LLM or cognition certification.",
  },
  {
    id: "L08-dynamics",
    title: "Pendulum dynamics and computed-torque self-check kit",
    topic: "R07",
    objectives: ["R07.pendulum-model"],
    description:
      "Implement a one-link pendulum: acceleration, energy, Euler/semi-implicit/RK4 steps, energy drift, computed torque with a limit, closed-loop hold and an energy-based model check. Numerical toy only; no hardware or multi-link claim.",
  },
  {
    id: "L14-interfaces",
    title: "Mock interfaces self-check kit",
    topic: "S10",
    objectives: ["S10.mock-joint-interface"],
    description:
      "Original numerical MOCK self-check: interface lifecycle and limits, trajectory validator with named reasons, action-client state machine, joint-segment box check. No ros2_control, MoveIt, real controller or hardware.",
  },
] as const;
// Keep the original shared sample bytes unchanged: they are part of both old
// kit hashes. New kits use separate immutable manifests.
const sampleFiles: Record<string, string> = {
  "L14-interfaces": "L14-interfaces.samples.v1.json",
  "L08-dynamics": "L08-dynamics.samples.v1.json",
  "L22-reasoning": "L22-reasoning.samples.v1.json",
  "L13-navigation": "L13-navigation.samples.v1.json",
  "L17-alignment": "L17-alignment.samples.v1.json",
  "L05-replay": "L05-replay.samples.v1.json",
  "L12-description": "L12-description.samples.v1.json",
  "L20-rl": "L20-rl.samples.v1.json",
  "L18-grasp": "L18-grasp.samples.v1.json",
  "L15-executive": "L15-executive.samples.v1.json",
  "L19-imitation": "L19-imitation.samples.v1.json",
  "L16-camera": "L16-camera.samples.v1.json",
  "L21-identification": "L21-identification.samples.v1.json",
  "L11-planning": "L11-planning.samples.v1.json",
  "L10-kalman": "L10-kalman.samples.v1.json",
  "L09-localization": "L09-localization.samples.v1.json",
  "L07-trajectory": "L07-trajectory.samples.v1.json",
  "L03-odometry": "L03-odometry.samples.v1.json",
  "L04-pid": "L04-pid.samples.v1.json",
  "L06-jacobian-ik": "L06-jacobian-ik.samples.v1.json",
};
export function kitFiles() {
  return definitions.map((d) => ({
    code: "content/labs/" + d.id + ".v1.py",
    samples: "content/labs/" + (sampleFiles[d.id] ?? "samples.v1.json"),
  }));
}
export function kits() {
  return definitions.map((d) => ({
    ...d,
    version: 1,
    status: "manual-unverified" as const,
    review:
      "Author-tested; owner-assigned AI technical/adversarial review. Manual self-check only",
    verifiedI: "unavailable" as const,
  }));
}
function source(id: string) {
  const d = definitions.find((d) => d.id === id);
  if (!d)
    throw new V2Error(
      "not_found",
      "No authored self-check kit exists with this ID",
      404,
    );
  const filename = d.id + ".v1.py";
  const content = readFileSync(
    path.join(process.cwd(), "content/labs", filename),
    "utf8",
  );
  const sampleBytes = readFileSync(
    path.join(
      process.cwd(),
      "content/labs",
      sampleFiles[id] ?? "samples.v1.json",
    ),
    "utf8",
  );
  const samples = z
    .object({
      schema: z.literal("corelab-kit-samples/1"),
      kits: z.record(
        z.string(),
        z
          .array(
            z
              .object({
                structure: z.string(),
                inputs: z.record(z.string(), z.unknown()),
              })
              .strict(),
          )
          .max(50),
      ),
    })
    .strict()
    .parse(strictJSON(sampleBytes));
  return {
    ...d,
    filename,
    content,
    samples: samples.kits[id] ?? [],
    hash: hash(content + "\n" + sampleBytes),
  };
}
export function kitFingerprints(id: string) {
  const kit = source(id);
  const sampleFps = kit.samples.flatMap((sample) =>
    fingerprintCandidates({
      ...sample,
      id: "kit-sample",
      route: "sample",
      difficulty: 1,
      objectiveId: kit.objectives[0],
      prompt: "Manual kit sample",
      fields: [],
      hints: [],
      solution: "",
      remediation: "",
    } as Item),
  );
  return [
    ...new Set([
      digest({
        structure: "corelab-kit-download/1",
        source: kit.id,
        hash: kit.hash,
      }),
      ...sampleFps,
    ]),
  ];
}
const frozenSchema = z
  .object({
    kit: z.enum(definitions.map((d) => d.id)),
    version: z.literal(1),
    title: z.string().max(100),
    description: z.string().max(1000),
    fileHash: z.string().length(64),
  })
  .strict();
export function publicKitAttempt(db: DB, a: Attempt) {
  const frozen = frozenSchema.parse(strictJSON(a.instance_json));
  return {
    id: a.id,
    purpose: a.purpose,
    status: a.status,
    source: a.source_id,
    sourceVersion: a.source_version,
    observedAssistance: a.observed_level,
    issuedAt: a.issued_at,
    submittedAt: a.submitted_at,
    repeat: true,
    item: {
      id: a.id,
      route: "manual-self-check",
      difficulty: 2,
      objectiveId: "Manual kit: no implementation evidence",
      prompt: frozen.description,
      fields: [] as {
        id: string;
        label: string;
        kind: "number" | "angle" | "choice";
        options?: string[];
        tolerance: number;
      }[],
    },
    result:
      a.status === "submitted"
        ? {
            unverifiable: true as const,
            claim:
              "Manual self-report recorded. No result was verified or signed.",
          }
        : null,
    reviewStatus:
      "Manual self-check only; use the lab card to record that you ran your tests",
    verifiedI: "unavailable",
  };
}
export function downloadKit(store: Store, id: string) {
  const kit = source(id);
  return write(store.db, () => {
    const at = new Date().toISOString();
    const frozen = {
      kit: kit.id,
      version: 1 as const,
      title: kit.title,
      description: kit.description,
      fileHash: kit.hash,
    };
    // Resource identity plus authored sample exposure relations. Formula study
    // does not expose every future procedure check; identical samples do count.
    const fps = kitFingerprints(id);
    const a: Attempt = {
      id: randomUUID(),
      purpose: "practice",
      source_kind: "kit",
      source_id: kit.id,
      source_version: 1,
      source_hash: kit.hash,
      route: "manual-self-check",
      policy_version: 1,
      objective_refs: canonical(
        kit.objectives.map((id) => ({ id, version: 1 })),
      ),
      instance_json: canonical(frozen),
      fingerprints: canonical(fps),
      status: "issued",
      issued_at: at,
      issued_seq: nextSequence(store.db),
      submitted_at: null,
      closed_seq: null,
      observed_level: 0,
      declared_level: null,
      submission_json: null,
      submission_hash: null,
      grade_json: null,
      history_epoch: Number(meta(store.db, "current_history_epoch")),
    };
    insert(store.db, "v2_attempts", a);
    expose(store.db, a, "issued", at);
    expose(store.db, a, "kit_download", at);
    return { ...kit, attemptId: a.id };
  });
}
export function selfReportKit(store: Store, id: string, input: unknown) {
  const req = z
    .object({
      attemptId: z.uuid(),
      ran: z.boolean(),
      declaredAssistance: z.number().int().min(0).max(3),
    })
    .strict()
    .parse(input);
  return write(store.db, () => {
    const a = attemptById(store.db, req.attemptId);
    if (
      a.source_kind !== "kit" ||
      a.source_id !== id ||
      a.purpose !== "practice"
    )
      throw new V2Error(
        "wrong_purpose",
        "This is not a matching manual-kit practice attempt",
      );
    const kit = source(id),
      frozen = frozenSchema.parse(strictJSON(a.instance_json));
    if (kit.hash !== a.source_hash || kit.hash !== frozen.fileHash)
      throw new V2Error(
        "source_unavailable",
        "The original kit version is unavailable; its history is preserved",
        503,
      );
    const submission = {
        ran: req.ran,
        declaredAssistance: req.declaredAssistance,
      },
      submissionHash = digest(submission);
    if (a.status === "submitted") {
      if (a.submission_hash !== submissionHash)
        throw new V2Error(
          "attempt_closed",
          "This self-report is already closed",
          409,
        );
    } else {
      const at = new Date().toISOString();
      if (Date.parse(at) < Date.parse(a.issued_at))
        throw new V2Error(
          "clock_regression",
          "Clock moved backwards; no self-report saved",
          409,
        );
      store.db
        .prepare(
          "UPDATE v2_attempts SET status='submitted',submitted_at=?,closed_seq=?,declared_level=?,submission_json=?,submission_hash=?,grade_json=? WHERE id=?",
        )
        .run(
          at,
          nextSequence(store.db),
          req.declaredAssistance,
          canonical(submission),
          submissionHash,
          canonical({ claim: "manual_self_report_only", ran: req.ran }),
          a.id,
        );
    }
    return {
      recorded: true,
      ran: req.ran,
      claim:
        "Manual self-report only. No verification, signature or mastery evidence.",
      verifiedI: "unavailable",
    };
  });
}
