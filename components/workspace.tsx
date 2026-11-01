"use client";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Dashboard } from "./dashboard";
const Catalog = dynamic(() => import("./catalog").then((m) => m.Catalog));
const TopicPage = dynamic(() => import("./topic").then((m) => m.TopicPage));
const Paths = dynamic(() => import("./tools").then((m) => m.Paths));
const Practice = dynamic(() => import("./tools").then((m) => m.Practice));
const Tutor = dynamic(() => import("./tools").then((m) => m.Tutor));
const Settings = dynamic(() => import("./tools").then((m) => m.Settings));
const Sources = dynamic(() => import("./tools").then((m) => m.Sources));
const V2Explorer = dynamic(() =>
  import("./v2/explorer").then((m) => m.V2Explorer),
);
const V2BackupPanel = dynamic(() =>
  import("./v2/backup-panel").then((m) => m.V2BackupPanel),
);
export function Workspace({
  route,
  v2Enabled = false,
}: {
  route: string[];
  v2Enabled?: boolean;
}) {
  if (!route.length)
    return (
      <>
        {v2Enabled && (
          <div className="page v2-home-link">
            <Link className="button primary" href="/objectives">
              Open CoreLab V2 · objective learning
            </Link>
          </div>
        )}
        <Dashboard />
      </>
    );
  const [page, id] = route;
  if (page === "objectives" && v2Enabled)
    return <V2Explorer key={id ?? "all"} objective={id} />;
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
  if (page === "practice")
    return (
      <>
        {v2Enabled && (
          <div className="page v2-home-link">
            <Link className="button primary" href="/objectives">
              Recommended · Explore · More Practice in V2
            </Link>
          </div>
        )}
        <Practice />
      </>
    );
  if (page === "tutor") return <Tutor />;
  if (page === "settings")
    return <Settings v2Panel={v2Enabled ? <V2BackupPanel /> : undefined} />;
  return <Sources />;
}
