import Link from "next/link";
import { RoboticsConcept } from "../robotics-concept";
import {
  ArrowRight,
  Network,
  Move3D,
  ScanEye,
  BrainCircuit,
  Workflow,
} from "lucide-react";

const startingPoints = [
  {
    title: "Robot motion",
    note: "Frames & kinematics",
    href: "/objectives/R04.planar-fk",
    Icon: Move3D,
  },
  {
    title: "Computer vision",
    note: "Camera geometry",
    href: "/objectives/V03.pinhole",
    Icon: ScanEye,
  },
  {
    title: "Machine learning",
    note: "Gradients & models",
    href: "/objectives/ML05.shared-gradient",
    Icon: BrainCircuit,
  },
  {
    title: "RL & decisions",
    note: "Values & actions",
    href: "/objectives/RL02.bellman-value",
    Icon: Workflow,
  },
];

export function RoboticsHero() {
  return (
    <section className="robotics-hero" aria-labelledby="robotics-hero-title">
      <div className="robotics-hero-main">
        <div className="robotics-hero-copy">
          <div className="eyebrow">CORELAB · ROBOTICS & AI LEARNING LAB</div>
          <h1 id="robotics-hero-title">
            Learn <span>Robotics & AI.</span>
            <br />
            From first principles.
          </h1>
          <p>
            Build the mathematics, code and intuition behind robots that sense,
            learn, plan and act.
          </p>
          <p className="robotics-foundations">
            Math → Programming → Perception → Planning & Control
          </p>
          <div className="v2-header-actions">
            <a className="button primary" href="#v2-practice">
              Explore exercises <ArrowRight size={17} aria-hidden="true" />
            </a>
            <Link className="button" href="/roadmap">
              <Network size={17} aria-hidden="true" /> Open curriculum
            </Link>
          </div>
          <div className="robotics-hero-footnote">
            Learn. Build. Prove.{" "}
            <span>Start in software. No robot required.</span>
          </div>
        </div>
        <RoboticsConcept />
      </div>
      <nav
        className="robotics-starting-points"
        aria-label="Robotics and AI starting points"
      >
        {startingPoints.map(({ title, note, href, Icon }) => (
          <Link href={href} key={href}>
            <Icon size={21} aria-hidden="true" />
            <span>
              <strong>{title}</strong>
              <small>{note}</small>
            </span>
            <ArrowRight size={15} aria-hidden="true" />
          </Link>
        ))}
      </nav>
    </section>
  );
}
