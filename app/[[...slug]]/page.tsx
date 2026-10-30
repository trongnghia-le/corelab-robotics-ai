import { Suspense } from "react";
import { notFound } from "next/navigation";
import { topicMap } from "@/lib/curriculum";
import { Workspace } from "@/components/workspace";
export default async function Page({
  params,
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  const { slug = [] } = await params;
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
    <Suspense fallback={<div className="page">Đang mở CoreLab…</div>}>
      <Workspace route={slug} />
    </Suspense>
  );
}
