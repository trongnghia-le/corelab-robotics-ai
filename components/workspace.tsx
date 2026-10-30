"use client";
import dynamic from "next/dynamic";
import { Dashboard } from "./dashboard";
const Catalog = dynamic(() => import("./catalog").then((m) => m.Catalog));
const TopicPage = dynamic(() => import("./topic").then((m) => m.TopicPage));
const Paths = dynamic(() => import("./tools").then((m) => m.Paths));
const Practice = dynamic(() => import("./tools").then((m) => m.Practice));
const Tutor = dynamic(() => import("./tools").then((m) => m.Tutor));
const Settings = dynamic(() => import("./tools").then((m) => m.Settings));
const Sources = dynamic(() => import("./tools").then((m) => m.Sources));
export function Workspace({ route }: { route: string[] }) {
  if (!route.length) return <Dashboard />;
  const [page, id] = route;
  if (page === "roadmap") return <Catalog mode="roadmap" />;
  if (page === "lessons")
    return id ? <TopicPage key={id} id={id} /> : <Catalog mode="lessons" />;
  if (page === "assessments")
    return id ? (
      <TopicPage key={`assess-${id}`} id={id} assessment />
    ) : (
      <Catalog mode="assessments" />
    );
  if (page === "paths") return <Paths />;
  if (page === "practice") return <Practice />;
  if (page === "tutor") return <Tutor />;
  if (page === "settings") return <Settings />;
  return <Sources />;
}
