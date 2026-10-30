"use client";
import Link from "next/link";
import { CheckCircle2, ArrowRight, Clock3 } from "lucide-react";
import type { Mastery } from "@/lib/types";
import { dimensions, dimensionNames } from "@/lib/types";
import { topicMap } from "@/lib/curriculum";
export function PageHeading({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children}
    </div>
  );
}
export function Status({ mastery }: { mastery: Mastery }) {
  return (
    <span className={`status ${mastery.status}`}>
      {mastery.level > 0 ? (
        <>
          <CheckCircle2 size={13} />
          Verified L{mastery.level}
        </>
      ) : mastery.provisionalLevel > 0 ? (
        `Self-assessed L${mastery.provisionalLevel}`
      ) : mastery.status === "in_progress" ? (
        "In progress"
      ) : (
        "Unassessed"
      )}
      {mastery.reviewDue ? " · Review due" : ""}
    </span>
  );
}
export function TopicChips({ ids }: { ids: string[] }) {
  return (
    <div className="chips">
      {ids.length ? (
        ids.map((id) => (
          <Link href={`/lessons/${id}`} className="chip" key={id}>
            <span className="mono">{id}</span> {topicMap[id]?.title}
          </Link>
        ))
      ) : (
        <span className="muted small">No prerequisites.</span>
      )}
    </div>
  );
}
export function Matrix({ mastery }: { mastery: Mastery }) {
  return (
    <div className="competency-matrix">
      {dimensions.map((d) => (
        <div key={d}>
          <span className="dimension-letter">{d}</span>
          <strong>{dimensionNames[d]}</strong>
          <span className={mastery.dimensions[d] ? "verified-text" : "muted"}>
            {mastery.dimensions[d]
              ? `Evidence L${mastery.dimensions[d]}`
              : "No evidence yet"}
          </span>
        </div>
      ))}
    </div>
  );
}
export function ActionLink({
  href,
  children,
  primary = false,
}: {
  href: string;
  children: React.ReactNode;
  primary?: boolean;
}) {
  return (
    <Link className={primary ? "button primary" : "button"} href={href}>
      {children}
      <ArrowRight size={16} />
    </Link>
  );
}
export function Time({ minutes }: { minutes: number }) {
  return (
    <span className="time">
      <Clock3 size={14} />
      {minutes} min
    </span>
  );
}
export function dateText(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(new Date(value));
}
