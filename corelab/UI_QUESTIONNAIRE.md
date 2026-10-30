# CORELAB UI — Câu hỏi thiết kế (đã chốt: single-user, local, tối giản, màu cam)

Trả lời bằng mã, ví dụ `1B 2A 3C...`. Có thể ghi chú ngắn nếu muốn. Mục dấu ★ là gợi ý mặc định của mình, **chưa chốt**.

**1. Sắc độ cam chủ đạo (accent)**
A. Cam sáng tươi (#F97316) ★
B. Cam trầm/đất (#D9602E)
C. Cam đỏ đậm (#EA580C)
D. Gửi mã hex khác.

**2. Nền sáng và cảm giác tổng thể**
A. Trắng tinh, trắng-xám, rất technical
B. Kem ấm (#FAF8F4), thoải mái đọc lâu ★
C. Xám rất nhạt, tương phản mạnh.

**3. Hình thức tổng thể**
A. Tối giản kiểu Linear/Notion, gần như không trang trí ★
B. Dashboard kiểu GitHub, thông tin dày và kỹ thuật
C. Apple-like, nhiều không gian trắng, thẻ lớn.

**4. Kiểu bố cục navigation trên laptop**
A. Sidebar trái cố định, nội dung ở giữa ★
B. Sidebar thu gọn chỉ icon
C. Thanh menu ngang phía trên.

**5. Trang Dashboard phải ưu tiên điều gì?**
A. Một thẻ lớn 'Học tiếp' + 2-3 việc cần làm ★
B. Toàn cảnh kỹ năng/yếu điểm, module charts trước
C. Lịch học và review hôm nay trước.

**6. Roadmap muốn nhìn dạng gì?**
A. Danh sách theo domain, thu gọn/mở rộng, dễ quét ★
B. Cây kiến thức dạng dependency graph
C. Cả hai, mặc định danh sách (graph nếu mở).

**7. Trang Lesson ưu tiên layout nào?**
A. Cột nội dung rộng giữa, mục lục nhỏ bên phải ★
B. Chia đôi: lý thuyết bên trái + bài tập bên phải
C. Toàn chiều ngang, chuyển tab Theory/Practice/Test.

**8. Mật độ thông tin**
A. Thoáng, chữ lớn, ít dòng mỗi màn hình
B. Cân bằng, đọc lâu thoải mái ★
C. Rất cô đọng, ít cuộn, giống IDE.

**9. Cách hiển thị tiến độ và mastery**
A. Nhãn văn bản rõ (Unassessed / L1–L4) ★
B. Thanh tiến độ và số liệu kèm nhãn
C. Dạng bảng năng lực theo chiều C/M/I/T (kèm nhãn).

**10. Kiểu hiển thị toán và code**
A. Giống sách giáo khoa hiện đại: công thức rộng, code block thoáng ★
B. Giống IDE/technical docs: code nổi bật, nội dung dày
C. Code có thể ẩn/hiện, ưu tiên đọc lý thuyết.

**11. Chế độ giao diện**
A. Light mode mặc định, dark mode thêm sau ★
B. Light + dark ngay MVP
C. Chỉ light mode, không cần dark.

**12. Điện thoại và tablet**
A. Laptop-first, mobile xem tiến độ/đọc là đủ ★
B. Mobile cần học và làm quiz tương đương laptop
C. Chỉ quan tâm desktop.

**13. Tín hiệu tương tác/động họa**
A. Hầu như tĩnh, phản hồi rất nhẹ ★
B. Chuyển động nhẹ có chủ đích (hover/expand)
C. Nhiều animation cho knowledge graph/progress.

**14. Chọn 3 màn hình quan trọng nhất cho MVP**
A. Dashboard + Lesson + Assessment ★
B. Dashboard + Roadmap + Lesson
C. Roadmap + Lesson + Assessment
(Lưu ý: các màn khác vẫn có, chỉ xác định mức đầu tư UI.)

**15. Có ảnh chụp website/app bạn muốn học theo phong cách không?**
A. Không, dùng các phương án trên và thiết kế hệ thống nhất quán ★
B. Có, mình gửi 1–3 screenshot/link
C. Muốn xem wireframe của CoreLab rồi điều chỉnh.

## Ràng buộc đã duyệt (không hỏi lại)
- Màu cam, tối giản, gọn, dễ tập trung học; không phải web thương mại.
- Local single user, không auth, không external LLM API.
- Mọi kỹ năng ban đầu Unassessed; hiển thị rõ gap, recommendation, lesson, assessment.
- 3 trụ cột Robotics, Computer Vision, RL, có Foundations và Cognitive Robotics.
