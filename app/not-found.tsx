import Link from "next/link";
export default function NotFound() {
  return (
    <div className="page empty-state">
      <span className="eyebrow">404 · KHÔNG TÌM THẤY</span>
      <h1>Chủ đề này chưa có trong workspace.</h1>
      <p>Quay lại bản đồ để tìm một chủ đề hợp lệ.</p>
      <Link className="button primary" href="/roadmap">
        Mở Roadmap
      </Link>
    </div>
  );
}
