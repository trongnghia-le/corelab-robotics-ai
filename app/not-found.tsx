import Link from "next/link";
export default function NotFound() {
  return (
    <div className="page empty-state">
      <span className="eyebrow">404 · NOT FOUND</span>
      <h1>This topic is not in the workspace.</h1>
      <p>Return to the roadmap to find an available topic.</p>
      <Link className="button primary" href="/roadmap">
        Open Roadmap
      </Link>
    </div>
  );
}
