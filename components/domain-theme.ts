// Presentation only: shared curriculum/exercise aliases never affect assessment.
const domainTones = {
  Mathematics: "blue",
  Programming: "lime",
  Python: "lime",
  "Programming & C++": "lime",
  Algorithms: "lime",
  "Machine Learning": "violet",
  ML: "violet",
  "ML & CV": "violet",
  "ML & data": "violet",
  "Computer Vision": "teal",
  CV: "teal",
  Robotics: "orange",
  "Hardware & Embedded": "green",
  Control: "orange",
  Planning: "orange",
  "Reinforcement & Robot Learning": "rose",
  RL: "rose",
  "Embodied & Cognitive Robotics": "red",
  "Scientific Research": "amber",
  Capstone: "fuchsia",
} as const;

export function domainTone(domain: string | undefined) {
  return domainTones[domain as keyof typeof domainTones] ?? "neutral";
}
