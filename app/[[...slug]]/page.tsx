import { Suspense } from "react";
import { notFound } from "next/navigation";
import { topicMap } from "@/lib/curriculum";
import { Workspace } from "@/components/workspace";
import { enabled } from "@/lib/v2/contracts";
export const dynamic = "force-dynamic";
export default async function Page({
  params,
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  const { slug = [] } = await params;
  const v2Enabled = enabled();
  if (slug[0] === "objectives") {
    if (!v2Enabled || slug.length > 2) notFound();
    if (slug[1]) {
      const { catalog } = await import("@/lib/v2/content");
      if (
        !catalog().families.some((f) =>
          f.items.some((i) => i.objectiveId === slug[1]),
        )
      )
        notFound();
    }
    return <Workspace route={slug} v2Enabled />;
  }
  const valid = [
    "roadmap",
    "lessons",
    "assessments",
    "paths",
    "practice",
    "tutor",
    "settings",
    "sources",
  ];
  if (
    slug.length > 2 ||
    (slug.length > 0 && !valid.includes(slug[0])) ||
    (slug.length === 2 &&
      (!["lessons", "assessments"].includes(slug[0]) || !topicMap[slug[1]]))
  )
    notFound();
  return (
    <Suspense fallback={<div className="page">Loading CoreLab…</div>}>
      <Workspace route={slug} v2Enabled={v2Enabled} />
    </Suspense>
  );
}
