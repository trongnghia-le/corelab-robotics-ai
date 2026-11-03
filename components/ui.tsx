"use client";
import Link from "next/link";
import { CheckCircle2, ArrowRight, Clock3 } from "lucide-react";
import type { Mastery } from "@/lib/types";
import { dimensions } from "@/lib/types";
import { useCore } from "./provider";
import { useI18n, formatDuration } from "@/lib/i18n";
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
  const { t } = useI18n();
  return (
    <span className={`status ${mastery.status}`}>
      {mastery.level > 0 ? (
        <>
          <CheckCircle2 size={13} />
          {t("status.mastered")}
        </>
      ) : mastery.provisionalLevel > 0 ? (
        t("status.selfRated")
      ) : mastery.status === "in_progress" ? (
        t("status.practised")
      ) : (
        t("status.notStarted")
      )}
      {mastery.reviewDue ? ` · ${t("status.reviewDue")}` : ""}
    </span>
  );
}
export function TopicChips({ ids }: { ids: string[] }) {
  const { t } = useI18n();
  const { title } = useCore();
  return (
    <div className="chips">
      {ids.length ? (
        ids.map((id) => (
          <Link href={`/lessons/${id}`} className="chip" key={id}>
            <span className="mono">{id}</span> {title(id)}
          </Link>
        ))
      ) : (
        <span className="muted small">{t("common.noPrereqs")}</span>
      )}
    </div>
  );
}
export function Matrix({ mastery }: { mastery: Mastery }) {
  const { t } = useI18n();
  return (
    <div className="competency-matrix">
      {dimensions.map((d) => (
        <div key={d}>
          <span className="dimension-letter">{d}</span>
          <strong>{t(`dim.${d}`)}</strong>
          <span className={mastery.dimensions[d] ? "verified-text" : "muted"}>
            {mastery.dimensions[d]
              ? t("matrix.evidence", { n: mastery.dimensions[d] })
              : t("matrix.none")}
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
  const { lang } = useI18n();
  return (
    <span className="time">
      <Clock3 size={14} />
      {formatDuration(minutes, lang)}
    </span>
  );
}
export function dateText(value: string) {
  const vi =
    typeof document !== "undefined" && document.documentElement.lang === "vi";
  return new Intl.DateTimeFormat(vi ? "vi-VN" : "en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(new Date(value));
}
