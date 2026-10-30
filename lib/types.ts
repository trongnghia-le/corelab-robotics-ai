export const dimensions = ["C", "M", "I", "T"] as const;
export type Dimension = (typeof dimensions)[number];
export const dimensionNames = {
  C: "Conceptual Understanding",
  M: "Mathematical Reasoning",
  I: "Independent Implementation",
  T: "Transfer & Retention",
};
export type Assistance = "A0" | "A1" | "A2" | "A3";
export type Answers = Record<string, string>;
export type KnowledgeType =
  "concept" | "procedure" | "implementation" | "design";
export type MistakeCategory =
  | "conceptual"
  | "mathematical"
  | "procedural"
  | "implementation"
  | "method_selection"
  | "retention";
export type QuestionMetadata = {
  knowledgeType?: KnowledgeType;
  skillTags?: string[];
  skillLabel?: string;
  relatedPrerequisites?: string[];
  mistakeCategory?: MistakeCategory;
  recommendedMethod?: string;
  remediationRefs?: { label: string; href: string }[];
  verifiedLabTopicId?: "M02" | "PY01";
  equivalentTo?: string[];
};
export type Question = QuestionMetadata & {
  id: string;
  prompt: string;
  kind: "choice" | "number" | "short";
  dimension: Dimension;
  critical: boolean;
  options?: string[];
  answer?: string;
  tolerance?: number;
  explanation: string;
  rubric?: string[];
};
export type Assessment = {
  id: string;
  topicId: string;
  version: number;
  questions: Question[];
};
export type Grade = {
  score: number;
  passed: boolean;
  dimensions: Partial<Record<Dimension, boolean>>;
  items: { id: string; correct: boolean | null; feedback: string }[];
};
export type Attempt = {
  purpose?: "targeted";
  skillTag?: string;
  questionIds?: string[];
  id: string;
  topicId: string;
  assessmentVersion: number;
  at: string;
  assistance: Assistance;
  answers: Answers;
  grade: Grade;
};
export type Session = {
  id: string;
  topicId: string;
  at: string;
  kind:
    | "reading"
    | "practice"
    | "note"
    | "ai_feedback"
    | "self_assessment"
    | "difficulty";
  text: string;
  minutes: number;
  provisionalLevel?: number;
};
export type LabEvidence = {
  id: string;
  topicId: string;
  at: string;
  assistance: Assistance;
  sourceHash: string;
  report: string;
  signature: string;
  trusted: boolean;
};
export type Review = {
  topicId: string;
  due: string;
  stage: number;
  lastAttemptId: string;
};
export type Progress = {
  attempts: Attempt[];
  sessions: Session[];
  labs: LabEvidence[];
  reviews: Review[];
  goal: string;
  focusTopic: string | null;
  focusReason: string;
};
export type Mastery = {
  level: number;
  dimensions: Record<Dimension, number>;
  provisionalLevel: number;
  status: "unassessed" | "in_progress" | "provisional" | "verified";
  reviewDue: boolean;
  gap: boolean;
};
export type Recommendation = {
  topicId: string;
  kind: "learn" | "assess" | "review" | "practice";
  reason: string;
  prerequisites: string[];
  exercise: string;
  rank: number;
  weaknessKey?: string;
};
export const emptyProgress = (): Progress => ({
  attempts: [],
  sessions: [],
  labs: [],
  reviews: [],
  goal: "Foundations",
  focusTopic: null,
  focusReason: "",
});
export type LessonMeta = {
  id: string;
  module_id: string;
  title: string;
  summary: string;
  estimated_minutes: number;
  prerequisites: string[];
  source_refs: { title: string; url: string }[];
  objectives: string[];
  core_theory: string[];
  labs: string[];
  assessment_refs: string[];
  review_prompts: string[];
  extension_refs: string[];
};
export type Lesson = { meta: LessonMeta; body: string };
export type Overview = {
  concepts: string[];
  overview: string;
  application: string;
  task: string;
};
export type PracticeSkill = {
  tag: string;
  label: string;
  knowledgeTypes: KnowledgeType[];
  questionCount: number;
};
export type TopicPayload = {
  practiceSkills?: PracticeSkill[];
  lesson: Lesson | null;
  overview: Overview;
  assessment: Assessment | null;
};
export type WeaknessStatus =
  | "active"
  | "practiced_with_assistance"
  | "independently_corrected"
  | "due_for_retention_review";
export type Weakness = {
  key: string;
  topicId: string;
  skillTag: string;
  skillLabel: string;
  knowledgeType: KnowledgeType;
  failedAttempts: number;
  failureCount: number;
  questionRefs: {
    questionId: string;
    version: number;
    purpose: "diagnostic" | "targeted";
  }[];
  categories: MistakeCategory[];
  classificationSource: "authored" | "legacy-inferred";
  lastAttemptAt: string;
  lastFailedAt: string;
  lastCorrectedAt: string | null;
  latestResult:
    "incorrect" | "assisted_correct" | "independent_correct" | "verified_lab";
  status: WeaknessStatus;
  reviewDueAt: string | null;
  prerequisites: string[];
  remediation: { label: string; href: string }[];
  priority: number;
};
export type TargetedPlan = {
  topicId: string;
  skillTag: string;
  skillLabel: string;
  assessment: Assessment;
  weakness: Weakness | null;
  message: string;
  prerequisiteActivities: { topicId: string; reason: string; href: string }[];
};
export type AppState = {
  weaknesses: Weakness[];
  progress: Progress;
  mastery: Record<string, Mastery>;
  recommendations: Recommendation[];
  lessonIds: string[];
};
