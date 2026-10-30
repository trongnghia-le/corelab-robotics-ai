"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="page empty-state">
      <h1>Unable to open workspace.</h1>
      <p>
        Your progress is still stored in SQLite. Try opening the page again.
      </p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
