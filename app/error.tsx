"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="page empty-state">
      <h1>Không thể mở workspace.</h1>
      <p>Tiến độ vẫn được giữ trong SQLite. Hãy thử mở lại trang.</p>
      <button onClick={reset}>Thử lại</button>
    </div>
  );
}
