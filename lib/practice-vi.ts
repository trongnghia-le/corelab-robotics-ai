// Vietnamese display text for the fixed practice assignments in practice.ts.
// Commands, starters and ids are unchanged.
export const practiceVi: Record<
  string,
  { title: string; kind: string; task: string }
> = {
  "vector-lab": {
    title: "Tích vô hướng từ trang giấy trắng",
    kind: "Lập trình + tính toán",
    task: "Viết dot(u,v), norm(v) và projection(u,v) bằng Python thuần. Với dot, hãy kiểm thử số chiều, số âm, số không, tính đối xứng và tính phân phối. Chạy bộ test cố định cho dot để tạo bằng chứng I; ghi norm và projection như phần luyện tập bổ sung.",
  },
  "python-lab": {
    title: "Hàm tính trung bình với hợp đồng rõ ràng",
    kind: "Lập trình + gỡ lỗi",
    task: "Viết mean(values) trả về trung bình cộng và ném ValueError khi đầu vào rỗng. Không làm thay đổi đầu vào. Kiểm thử giá trị âm, danh sách một phần tử, số thực và một lỗi return sớm trong vòng lặp.",
  },
  "cpp-lab": {
    title: "C++: tìm lỗi chia số nguyên",
    kind: "Gỡ lỗi + kiểm thử",
    task: "Biên dịch bản khởi đầu C++17 với cảnh báo bật. Sửa mean để trả về số thực và xử lý đầu vào rỗng. Viết một test bắt được lỗi cắt cụt số nguyên, rồi chạy với sanitizer. Ghi lại lệnh và kết quả trong sổ ghi chép như bài luyện tập tự báo cáo.",
  },
  "ml-lab": {
    title: "Hồi quy tuyến tính không dùng framework",
    kind: "So sánh thuật toán",
    task: "Cài đặt gradient descent cho y=2x+1. Kiểm tra gradient bằng sai phân trung tâm, so sánh với bình phương tối thiểu và giữ các tập train/validation/test tách biệt. Ghi lại loss, seed, learning rate và chuẩn của gradient.",
  },
  "hardware-lab": {
    title: "Pin có đủ cho buổi demo không?",
    kind: "Tính toán + datasheet",
    task: "Lập ngân sách công suất cho một robot nhỏ: liệt kê điện áp và dòng điển hình/đỉnh của từng linh kiện theo datasheet, cộng tải trên mỗi đường nguồn, thêm tổn hao của mạch ổn áp, rồi ước thời gian chạy từ dung lượng của một viên pin thật có hệ số dự phòng. Kiểm thử trường hợp dòng kẹt (stall) đỉnh, thiếu đường nối đất chung và cầu chì quá nhỏ.",
  },
  "robot-lab": {
    title: "Hai cách tính cùng một end effector",
    kind: "Lập trình + kiểm chứng",
    task: "Cài đặt động học thuận cho cánh tay hai khớp bằng lượng giác và bằng phép hợp các phép biến đổi. Dùng l₁=1, l₂=0.7; kiểm thử trạng thái duỗi thẳng, gập, góc π/2 và giới hạn tầm với. So sánh sai số mà không dùng chính phần cài đặt làm đáp án chuẩn.",
  },
  "vision-lab": {
    title: "Bắt lỗi RGB/BGR và hoán đổi trục",
    kind: "Tính toán + gỡ lỗi",
    task: "Tạo ảnh RGB 2×3 bằng NumPy với các điểm đánh dấu đỏ, xanh lá và xanh dương. Dự đoán từng pixel trước khi chạy. Kiểm tra dtype, chuẩn hóa, thứ tự hàng/cột và vòng RGB→BGR→RGB.",
  },
  "rl-lab": {
    title: "Một MDP đủ nhỏ để kiểm chứng bằng tay",
    kind: "Suy luận + thiết kế thí nghiệm",
    task: "Ở trạng thái A, finish cho phần thưởng 3 rồi kết thúc; wait cho phần thưởng 1 và quay về A. Với γ=0.5, đánh giá cả hai chính sách bằng tay và bằng policy evaluation. Đổi γ thành 0.9 và so sánh chính sách tối ưu. Kiểm tra tổng xác suất chuyển và quy ước trạng thái kết thúc.",
  },
  "research-lab": {
    title: "Một phát biểu có thể bị bác bỏ",
    kind: "Thiết kế thí nghiệm",
    task: "So sánh hai bước thời gian Euler trên một ODE có nghiệm đã biết. Khai báo trước các chỉ số độ chính xác và thời gian chạy, các nhóm đối chứng, điều kiện bác bỏ và số đo thô trước khi chạy. Không chỉ chọn lần chạy tốt nhất.",
  },
};
