---
{"title": "Cột mốc capstone 7: lớp tác vụ nhận mục tiêu bằng ngôn ngữ và bộ giám sát an toàn với kiểm thử tiêm hazard", "summary": "Phân tích câu lệnh văn bản thành mục tiêu ký hiệu với xử lý nhập nhằng tường minh, lập kế hoạch và thực thi bằng behaviour tree, giữ một belief về vật thể, và xây dựng bộ giám sát an toàn độc lập cho mô phỏng, được kiểm thử bằng cách tiêm mười hazard.", "objectives": ["Phân tích câu lệnh thành mục tiêu ký hiệu và trả về Clarify hoặc Unparseable thay vì đoán.", "Lập kế hoạch nhiều bước bằng tìm kiếm có chặn và thực thi bằng behaviour tree có thử lại và fallback.", "Duy trì belief về vật thể với tuổi và độ tin cậy, tránh lập kế hoạch trên dữ liệu cũ.", "Viết bảng hazard và cài đặt bộ giám sát an toàn độc lập với ngăn xếp lập kế hoạch.", "Kiểm chứng bộ giám sát bằng kiểm thử tiêm hazard và nói rõ rằng nó bảo vệ một mô phỏng và không phải an toàn được chứng nhận."]}
---

## Vì sao điều này quan trọng

Đến CAP06, robot của bạn đã điều hướng, nhận thức và gắp được. Điều nó chưa làm được là nhận một chỉ dẫn từ con người, quyết định làm gì và theo thứ tự nào, phục hồi khi một bước thất bại, và trên hết là **dừng** khi có điều gì sai. Cột mốc này thêm ba lớp đó: một lớp tác vụ biến văn bản thành mục tiêu, một planner và behaviour tree biến mục tiêu thành hành động, và một bộ giám sát an toàn đứng cạnh mọi thứ khác và có quyền phủ quyết.

Hai bài học từ các hệ thống thật dẫn dắt thiết kế. Thứ nhất, giao diện ngôn ngữ chủ yếu là bài toán *khử nhập nhằng*: thất bại nguy hiểm không phải là "parser không hiểu", mà là "parser âm thầm chọn nhầm vật và robot vui vẻ thực thi". Thứ hai, một chức năng an toàn chỉ có giá trị nếu nó không phụ thuộc vào thành phần mà nó bảo vệ chống lại: một bộ giám sát chung luồng với một planner bị treo thì không phải là bộ giám sát.

**Một giới hạn trung thực, nói ngay từ đầu.** Bộ giám sát bạn xây bảo vệ một *mô phỏng*. Nó là bài tập giảng dạy về phân tích hazard và tiêm lỗi. Nó **không phải an toàn được chứng nhận**, không tuyên bố đáp ứng bất kỳ tiêu chuẩn an toàn chức năng nào (hệ thống thật theo các tiêu chuẩn như ISO 13849 hoặc IEC 61508 với phần cứng được chứng nhận, đánh giá độc lập và nghiêm ngặt hơn nhiều), và không bao giờ được là lớp bảo vệ duy nhất của một cỗ máy thật gần người. Tầng phần cứng tùy chọn ở cuối tuân theo quy tắc điện của HW03 và giữ mọi giới hạn công suất ở mức thấp.

Đây là cột mốc 7 trong 9, chiếm **10 trên 100 điểm**. Nó dùng [CAP04](/lessons/CAP04) (kỹ năng điều hướng), [CAP05](/lessons/CAP05) (kỹ năng gắp), [E05 Lập kế hoạch tác vụ](/lessons/E05), [E06 Lập kế hoạch tác vụ và chuyển động](/lessons/E06) và [S07 An toàn robot](/lessons/S07).

## Trực giác

Hình dung ngăn xếp là ba vòng lồng nhau chạy ở tốc độ rất khác nhau. **Vòng tác vụ** (giây): đọc chỉ dẫn, hỏi lại nếu cần, lập kế hoạch, chạy cây, thử lại hoặc bỏ cuộc. **Các vòng kỹ năng** (hàng chục mili giây): điều hướng và gắp, bạn đã xây. **Vòng an toàn** (10 ms): nhìn heartbeat và tín hiệu hazard và quyết định lệnh nào được đi qua.

![System architecture of CoreBot Tidy: simulator, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation and learned skills, the language task layer and the safety supervisor](/lesson-figures/CAP-architecture.svg)

*Lớp tác vụ là band trên cùng; thanh đỏ đứt nét bên phải là bộ giám sát. Hãy để ý nó có đầu vào từ mọi band và một đường trực tiếp tới watchdog của firmware, đi vòng qua planner.*

Parser có ba câu trả lời, không bao giờ hai: một **mục tiêu** (hiểu, không nhập nhằng), một **Clarify** (hiểu nhưng thiếu chi tiết: "khối nào?"), hoặc **Unparseable** (ngoài ngữ pháp, không an toàn, hoặc mâu thuẫn với cảnh). Hệ thống chỉ có mục tiêu và lỗi sẽ đoán; hệ thống biết hỏi an toàn hơn và, với từ vựng nhỏ, dễ xây hơn.

![Language task layer and independent safety supervisor: text to parser to goal to planner to behaviour tree to skills, with Clarify and Unparseable branches, and a supervisor process that reads hazard inputs and can force zero velocity, arm hold and a direct firmware stop](/lesson-figures/CAP07.svg)

*Từ trái sang phải là đường tác vụ. Bên dưới là đường của bộ giám sát, không đi qua planner.*

Ba ý nữa:

**Baseline không dùng LLM đi trước.** Từ vựng đóng (3 màu, 3 hình, vài động từ, từ đồng nghĩa) với điền slot phân tích miền dọn dẹp một cách đáng tin và kiểm thử được hoàn toàn. Một LLM hoặc mô hình vision-language-action (VLA) có thể là parser *thay thế* cho mục tiêu mở rộng, đánh giá trên cùng 60 câu; nó không thể thay bộ giám sát, vì mô hình ngôn ngữ không đảm bảo gì về các hành động nó đề xuất.

**Lập kế hoạch ký hiệu, kiểm tra hình học.** Planner kiểu STRIPS suy luận về `holding(obj)` và `on(obj, bin)`. Cánh tay có thực sự với tới vật hay không là hình học (IK của CAP05). Task and motion planning (TAMP) nối hai thứ: nếu kiểm tra hình học thất bại, kế hoạch ký hiệu được sửa hoặc tác vụ hủy kèm lý do.

**Lỗi là sự kiện bình thường.** Các test tiêm lỗi có chủ ý và đo thời gian đến khi robot ở trạng thái an toàn. "Trạng thái an toàn" cụ thể: vận tốc chuyển tiếp bằng không, cánh tay giữ vị trí, firmware dừng.

## Lý thuyết và suy dẫn

Ghi chú tích hợp: điều gì quan trọng ở đây, kèm chủ đề nó đến từ.

![CAP07 milestone diagram: parser, planner, behaviour tree, skills and the independent safety supervisor](/lesson-figures/CAP07.svg)

### 1. Ngôn ngữ mục tiêu và một parser trung thực ([E05](/lessons/E05))

Mục tiêu là hội các predicate trên một thế giới đóng, `TaskGoal(predicates=(on(cube_red, bin_blue), ...), source_text)`. Parser điền slot: *động từ* (put/place/move/bring/carry/set/drop nghĩa là "đặt"; pick/grab/take/lift nghĩa là "nhấc"), *cụm danh từ vật thể* (màu, hình hoặc danh từ chung như block, object, thing, one), *đích* (giới từ, màu tùy chọn, từ chỉ thùng). Nhập nhằng xuất hiện ở bước đối chiếu với cảnh:

| Số khớp trong cảnh | Kết quả |
|---|---|
| đúng 1 | slot được giải quyết |
| 0 | `Unparseable("no such object")` |
| nhiều hơn 1 | `Clarify(question, options)` |

Các quy tắc đáng viết thành test: phủ định ("do not ...") và từ chỉ màu lạ là `Unparseable`; hơn hai vật là `Unparseable` (rào chắn phạm vi); đại từ không có tiền ngữ là `Clarify`; động từ lạ ("throw") là `Unparseable`. Hãy nêu giới hạn của ngữ pháp trong README; đó là một phần của tiêu chí rubric "sự trung thực của thiết kế".

### 2. Lập kế hoạch kiểu STRIPS với tìm kiếm có chặn ([E05](/lessons/E05), [E06](/lessons/E06))

Trạng thái: `(robot_at, holding, vị trí các vật)`. Hành động và tiền điều kiện: `nav(loc)` (bất kỳ vị trí nào); `pick(obj)` đòi `robot_at = table`, gripper trống và vật nằm trên bàn; `place(obj, bin)` đòi `robot_at = bin` và vật đang trong gripper. Tìm kiếm theo chiều rộng (breadth-first) với tập đã thăm trả về kế hoạch có **số hành động tối thiểu** và không thể lặp; thêm giới hạn số lần mở rộng để mục tiêu không với tới trả về `None` trong thời gian có chặn. Với một vật, tối thiểu là 4 hành động nếu bắt đầu xa bàn (nav, pick, nav, place) và 3 nếu đã ở bàn. Vì gripper cầm một vật, hai vật vào một thùng cần 8.

### 3. Behaviour tree ([E06](/lessons/E06), Colledanchise và Ogren)

Cây được tick từ gốc. **Sequence** trả về thất bại ở con thất bại đầu tiên; **Fallback** (selector) trả về thành công ở con thành công đầu tiên; decorator **Retry** lặp một con thất bại tối đa $r$ lần. Nếu một skill thành công với xác suất $p$ mỗi lần thử và các lần thử độc lập, thử lại cho
$$P(\text{thành công trong } r+1\text{ lần})=1-(1-p)^{r+1},\qquad E[\text{số lần gọi}]=\sum_{k=0}^{r}(1-p)^k .$$
Giả định độc lập là lạc quan: thất bại lặp lại thường có nguyên nhân chung, vì vậy quy tắc là "tối đa hai lần thử lại, rồi lập kế hoạch lại hoặc hủy kèm lý do". Luôn chạy cây dưới **giới hạn tick** để một lỗi không thể treo tác vụ.

### 4. Belief về vật thể ([E06](/lessons/E06), CAP05)

`world_model.py` lưu cho mỗi vật một tư thế, một timestamp và một độ tin cậy. Định nghĩa **tuổi** $a=t_{now}-t_{seen}$; trước khi lập kế hoạch một lần nhấc, nếu $a$ vượt ngưỡng (giả sử 5 s) hoặc độ tin cậy thấp, planner chèn một hành động *quan sát* trước. Lập kế hoạch trên belief đã cũ hàng phút là lỗi kinh điển "belief vật thể lỗi thời".

### 5. Bộ giám sát an toàn ([S07](/lessons/S07))

Thiết kế từ một **bảng hazard** (FMEA rút gọn): mỗi hazard có nguyên nhân, quy tắc phát hiện, phản ứng và id test. Mười hazard của cột mốc này, kèm phép tiêm dùng để kiểm thử:

| Id | Hazard | Phát hiện | Phản ứng |
|---|---|---|---|
| H01 | người trong 0.5 m | khoảng cách dưới bán kính dừng | HOLD |
| H02 | liên kết nối tiếp chết 200 ms | tuổi liên kết vượt timeout | HOLD |
| H03 | cờ ước lượng phân kỳ | cờ | HOLD |
| H04 | xung mô-men khớp | mô-men vượt giới hạn | HOLD |
| H05 | cờ pin yếu | cờ | HOLD |
| H06 | e-stop của người vận hành | nút | ESTOP, chốt |
| H07 | mất perception 1 s | tuổi perception vượt timeout | HOLD |
| H08 | planner sập / mất heartbeat | tuổi heartbeat vượt timeout | HOLD |
| H09 | lệnh tốc độ vượt giới hạn | tốc độ được lệnh vượt giới hạn | HOLD |
| H10 | cánh tay ngoài workspace | cờ workspace | HOLD |

Các mức: **OK**, **SLOW** (người trong 1.0 m: tốc độ bị chặn ở 0.15 m/s), **HOLD** (chuyển tiếp $v=0$, cánh tay giữ, thoát sau một khoảng dwell không còn lý do) và **ESTOP** (chốt cho đến khi `reset` tường minh).

Ngân sách thời gian có ba phần, và mỗi phần phải nằm trong yêu cầu (150 ms cho e-stop, 300 ms cho các hazard khác):
$$t_{safe}=t_{detect}+t_{tick}+t_{actuate}.$$
Với hazard kiểu timeout, $t_{detect}$ bằng timeout, nên timeout 0.25 s cộng tick 10 ms đã dùng 260 trong 300 ms. **Tính độc lập** nghĩa là: tiến trình hoặc luồng riêng với đồng hồ riêng, đầu vào đọc từ cảm biến và heartbeat chứ không từ ý kiến của planner, và một frame dừng trực tiếp tới watchdog firmware (CAP02) không đi qua ngăn xếp lập kế hoạch. **Quãng dừng** biện minh cho các bán kính: ở tốc độ $v$ với thời gian phản ứng $t_r$ và giảm tốc $a$, $d=v\,t_r+v^2/(2a)$.

### 6. Mô hình ngôn ngữ nằm ở đâu (mở rộng)

SayCan kết hợp đề xuất của mô hình ngôn ngữ với các hàm giá trị cho biết hành động nào khả thi; Code as Policies để mô hình viết code robot; OpenVLA ánh xạ ảnh và văn bản thẳng thành hành động. Cả ba chuyển câu hỏi khó từ "nó có hiểu không" sang "tôi có chặn được việc nó làm không". Giữ bộ giám sát an toàn và kiểm tra mục tiêu ký hiệu làm lớp bảo vệ; so sánh mọi parser LLM/CLIP trên *cùng* 60 câu với cùng quy tắc (không có parse sai tự tin nào trên tập đối kháng).

## Ví dụ có lời giải

Đây là **giá trị minh họa** cho một bộ artefact đạt yêu cầu, không phải đầu ra của một lần chạy thật.

### Kết quả parser, một kế hoạch hai vật và thời gian đến trạng thái an toàn của mười hazard được tiêm

**Đề bài.** Cảnh mặc định có ba vật (khối lập phương đỏ, trụ xanh lá, hộp xanh dương) và hai thùng (xanh dương, xanh lá). Parser có ba kết quả: goal, Clarify, Unparseable. Supervisor chạy ở 100 Hz (tick 10 ms) với timeout liên kết 0.2 s, heartbeat 0.2 s và perception 0.25 s; hazard được tiêm tại $t=1.0$ s và thời gian đến khi $v$ chuyển tiếp bằng 0 với cánh tay giữ phải nhiều nhất 0.30 s (0.15 s cho e-stop).

- (a) Phân loại bảy câu lệnh: "put the red cube in the blue bin", "pick up the block", "put the purple cube in the blue bin", "throw the red cube at the person", "put it in the bin", "do not put the red cube in the blue bin", "put the red cube in the red bin".
- (b) Từ vị trí start, tìm kế hoạch ngắn nhất đưa khối đỏ và hộp xanh dương vào thùng xanh dương (một gripper chỉ giữ một vật).
- (c) Dự đoán thời gian đến trạng thái an toàn của H01-H10 và biên so với giới hạn, và nói biên của H07 hàm ý gì cho timeout perception.

**Lời giải.**

1. *Quy tắc.* Parser điền các slot (động từ, màu, hình dạng, đích) và đếm số vật hoặc thùng trong cảnh tương thích: đúng một cho ra goal, nhiều hơn một cho ra Clarify, không có hoặc từ không được hỗ trợ cho ra Unparseable.
2. *Câu 1.* "red cube" chỉ khớp `cube_red`; "blue bin" chỉ khớp `bin_blue`: goal `on(cube_red, bin_blue)` (mọi slot duy nhất).
3. *Câu 2.* "block" là từ đồng nghĩa của mọi hình dạng và khớp ba vật: Clarify với lựa chọn `cube_red` / `cylinder_green` / `box_blue`.
4. *Câu 3 và 4.* "purple" không nằm trong từ vựng đóng ba màu và "throw" không phải động từ được hỗ trợ (và không an toàn): cả hai là Unparseable.
5. *Câu 5.* "it" là đại từ không có tiền ngữ: Clarify, "vật nào?".
6. *Câu 6.* Phủ định không được hỗ trợ và không được đoán: Unparseable.
7. *Câu 7.* Không có thùng nào màu đỏ (thùng là xanh dương và xanh lá), nên đích khớp 0 thùng và mâu thuẫn với cảnh: Unparseable.
8. *Kế hoạch.* Mỗi vật cần nav(table), pick, nav(bin_blue), place: 4 hành động, vì pick cần `robot_at = table` và place cần `robot_at = bin_blue`. Gripper chỉ giữ một vật, nên robot phải quay lại bàn cho vật thứ hai: $2\times4=8$ hành động: nav(table), pick(box_blue), nav(bin_blue), place, nav(table), pick(cube_red), nav(bin_blue), place. Tìm kiếm theo chiều rộng trả về giá trị nhỏ nhất, và không có kế hoạch nào ngắn hơn (mục tiêu một vật cần 4).
9. *Hazard tức thời.* H01, H03, H04, H05, H09 và H10 là điều kiện trên mẫu được tiêm đầu tiên, nên $t_\text{detect}=0$ và supervisor chuyển tiếp $v=0$ cùng cánh tay giữ ngay trong tick đó: 0.00 s so với 0.30 s.
10. *E-stop H06.* Một xung nút 20 ms phủ hai tick 10 ms, nên được lấy mẫu; ESTOP được chốt ngay trong tick đó: 0.00 s so với 0.15 s.
11. *Hazard kiểu timeout.* Ở đây $t_\text{safe}=t_\text{detect}+t_\text{tick}$ với $t_\text{detect}$ bằng timeout. H02: phép tiêm đặt $\text{link\_age}=e+0.01$ với $e$ là thời gian từ lúc tiêm, giá trị này vượt 0.2 s lần đầu tại $e=0.20$ s: 0.20 s. H08: $\text{heartbeat\_age}=e$ vượt 0.2 lần đầu ở tick kế tiếp, $e=0.21$ s. H07: $\text{perception\_age}=e$ vượt 0.25 lần đầu tại $e=0.26$ s.
12. *Biên.* H02: $0.30-0.20=0.10$ s; H08: $0.30-0.21=0.09$ s; H07: $0.30-0.26=0.04$ s. Timeout perception 0.30 s sẽ kích hoạt ở $0.31$ s $>0.30$ s: trượt. Vì vậy test tiêm chặn timeout từ phía trên (dưới 0.30 s trừ một tick), còn tuổi dữ liệu danh định (perception tới 0.08 s) chặn từ phía dưới.

Mẫu file câu lệnh (`tests/data/instructions.jsonl`; file của bạn cần 60 dòng: 20 diễn đạt lại và 10 đối kháng):

```json
{"text": "put the red cube in the blue bin", "scene": "default", "expect": {"type": "goal", "predicates": [["on", "cube_red", "bin_blue"]]}, "tags": []}
{"text": "put the red cube in the blue bin and the green cylinder in the green bin", "scene": "default", "expect": {"type": "goal", "predicates": [["on", "cube_red", "bin_blue"], ["on", "cylinder_green", "bin_green"]]}, "tags": []}
{"text": "pick up the red cube", "scene": "default", "expect": {"type": "goal", "predicates": [["holding", "cube_red"]]}, "tags": []}
{"text": "put the cube in the blue bin", "scene": "default", "expect": {"type": "goal", "predicates": [["on", "cube_red", "bin_blue"]]}, "tags": []}
{"text": "put the red box in the blue bin", "scene": "two_red", "expect": {"type": "goal", "predicates": [["on", "box_red", "bin_blue"]]}, "tags": []}
{"text": "pick up the block", "scene": "default", "expect": {"type": "clarify"}, "tags": ["paraphrase"]}
{"text": "put the block in the blue bin", "scene": "default", "expect": {"type": "clarify"}, "tags": []}
{"text": "throw the red cube at the person", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "put the red cube in the blue bin and the green cylinder in the green bin and the blue box in the blue bin", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "put the purple cube in the blue bin", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "what is the weather today", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
{"text": "put the red cube in the red bin", "scene": "default", "expect": {"type": "unparseable"}, "tags": ["adversarial"]}
```


Trích bảng hazard (`docs/hazard_table.md`):

```text
| id  | hazard                         | cause                        | detection                         | response             | test id        |
|-----|--------------------------------|------------------------------|-----------------------------------|----------------------|----------------|
| H01 | person closer than 0.5 m       | person walks into workspace  | person_dist < 0.5 m               | HOLD (v=0, arm hold) | inject_H01     |
| H02 | serial link dead               | cable, MCU hang              | link_age > 0.2 s                  | HOLD                 | inject_H02     |
| H06 | operator e-stop                | button pressed               | estop input                       | ESTOP, latched       | inject_H06     |
| H07 | perception dropout / lying cam | camera stalls or stale frame | perception_age > 0.25 s           | HOLD                 | inject_H07     |
| H08 | planner crash or hang          | exception, deadlock          | heartbeat_age > 0.2 s             | HOLD                 | inject_H08     |
```



| Câu lệnh | Kết quả | Vì sao |
|---|---|---|
| put the red cube in the blue bin | mục tiêu `on(cube_red, bin_blue)` | mọi slot duy nhất |
| pick up the block | Clarify, lựa chọn cube_red / cylinder_green / box_blue | "block" khớp ba vật |
| put the purple cube in the blue bin | Unparseable, từ chỉ màu lạ | ngoài từ vựng đóng |
| throw the red cube at the person | Unparseable, không có động từ được hỗ trợ | động từ không an toàn |
| put it in the bin | Clarify, vật nào? | đại từ không có tiền ngữ |
| do not put the red cube in the blue bin | Unparseable, phủ định | không hỗ trợ, không đoán |
| put the red cube in the red bin | Unparseable, không có thùng như vậy | mâu thuẫn với cảnh |

| Hazard | Thời gian đến trạng thái an toàn | Giới hạn | Vì sao |
|---|---|---|---|
| H01, H03, H04, H05, H09, H10 | 0.00 s (cùng tick) | 0.30 s | phát hiện ở mẫu đầu tiên |
| H06 e-stop (xung 20 ms) | 0.00 s, rồi chốt | 0.15 s | đầu vào trực tiếp |
| H02 liên kết nối tiếp chết | 0.20 s | 0.30 s | timeout tuổi liên kết 0.2 s |
| H08 mất heartbeat của planner | 0.21 s | 0.30 s | timeout 0.2 s cộng một tick |
| H07 mất perception | 0.26 s | 0.30 s | timeout 0.25 s cộng một tick |

**Kiểm tra.** Kế hoạch: tìm kiếm theo chiều rộng trên (vị trí robot, vật đang giữ, vị trí các vật) cho mục tiêu hai vật trả về đúng 8 hành động và 4 cho một vật. Thời gian: một vòng lặp tick 10 ms với ba timeout tái tạo 0.00 s, 0.20 s (H02), 0.21 s (H08) và 0.26 s (H07), và với timeout perception 0.30 s cho 0.31 s. Đầu vào danh định trong test nghiệm thu (tuổi liên kết tới 0.03 s, perception tới 0.08 s, heartbeat tới 0.05 s) cách timeout tương ứng 0.17, 0.17 và 0.15 s, nên tỉ lệ dừng nhầm thấp. Các hàng parser chạy như unit test trong `tests/acceptance/test_cap07.py`.

**Rút ra.** Parser không bao giờ đoán: nó đếm số khớp và trả về goal, Clarify hoặc Unparseable; ngân sách an toàn là thời gian phát hiện cộng một tick, và biên 40 ms của H07 cho thấy ngưỡng được chọn bằng test tiêm, không bằng cảm tính.

## Bài tập

1. **(Dễ)** Trong cảnh mặc định, phân loại mỗi câu lệnh là mục tiêu, Clarify hay Unparseable: (a) "move the green cylinder to the green bin", (b) "put the block in the green bin", (c) "put the red cube in the green bin and stop", (d) "place the yellow box in the blue bin", (e) "bring it to the blue bin".
2. **(Dễ)** E-stop phải tới trạng thái an toàn trong 150 ms. Supervisor lấy mẫu nút mỗi 10 ms, chạy ở 100 Hz, frame dừng tới firmware trong 10 ms và watchdog tác động trong một chu kỳ firmware 10 ms. Tính thời gian xấu nhất và biên độ.
3. **(Dễ)** Một robot chạy 0.5 m/s, phản ứng trong 0.3 s và giảm tốc được 1 m/s bình phương. Quãng dừng của nó là bao nhiêu, và bán kính dừng 0.5 m có ổn không? Lặp lại cho tốc độ vùng người 0.15 m/s.
4. **(Trung bình)** Planner: robot bắt đầu ở bàn và mục tiêu là `on(cube_red, bin_blue)` và `on(box_blue, bin_blue)`. Cho độ dài kế hoạch tối thiểu và nói vì sao gripper một tay quan trọng.
5. **(Trung bình)** Một lần nhấc thành công với xác suất 0.8 mỗi lần thử. Với tối đa hai lần thử lại, xác suất lần nhấc cuối cùng thành công và số lần gọi pick kỳ vọng là bao nhiêu? Giả định nào là lạc quan?
6. **(Trung bình)** Chọn timeout của liên kết nối tiếp. Tuổi liên kết danh định luôn dưới 30 ms trong 20 episode danh định của bạn, yêu cầu là 300 ms đến trạng thái an toàn, tick của supervisor là 10 ms. Khoảng nào được phép, bạn chọn gì và nó tốn bao nhiêu quãng đường ở 0.5 m/s?
7. **(Trung bình)** "Put the red cube in the blue bin and do not touch the green one." Parser của bạn từ chối mọi câu chứa phủ định. Có chấp nhận được không? Bạn có thể thiết kế hành vi tốt hơn nào mà không đoán?
8. **(Khó)** Supervisor chạy trong luồng của planner, và planner treo 2 s trong khi base chạy 0.5 m/s. Chuyện gì xảy ra, robot đi bao xa, và bạn thiết kế lại thế nào để quãng đường tối đa 10 cm?
9. **(Khó)** Belief về khối đỏ đã 40 s tuổi; có thể có người đã di chuyển nó. Thiết kế quy tắc tuổi belief: ngưỡng, hành động và lớp tác vụ làm gì nếu quan sát lại thất bại.
10. **(Khó, dự án nhỏ)** Thêm hazard thứ mười một "camera nói dối" (ảnh mới nhưng sai, ví dụ đóng băng ở khung hình cũ với timestamp được cập nhật). Viết dòng bảng hazard, một quy tắc phát hiện, một phản ứng và một test tiêm; nêu giới hạn của nó.

## Cài đặt tham khảo

Parser là module quyết định robot có an toàn để trò chuyện hay không. Bộ khung của `task/parser.py` (mỗi hàm vài dòng; docstring của `parse` là đặc tả của các test):

```python
# src/corebot/task/parser.py  (skeleton: a closed-vocabulary, slot-filling parser; no LLM)
from __future__ import annotations
from dataclasses import dataclass
from typing import NamedTuple, Sequence

from corebot.interfaces import TaskGoal


class SceneObject(NamedTuple):
    obj_id: str   # "cube_red"
    color: str    # "red"
    shape: str    # "cube" | "cylinder" | "box"


class SceneBin(NamedTuple):
    bin_id: str   # "bin_blue"
    color: str    # "blue"


@dataclass(frozen=True)
class Clarify:
    """The instruction is understood but under-specified. Ask; never guess."""
    question: str
    options: tuple[str, ...]


@dataclass(frozen=True)
class Unparseable:
    """Outside the grammar, unsafe, or contradicts the scene. Say why."""
    reason: str


def normalise(text: str) -> list[str]:
    """Lower-case, strip punctuation, drop filler words ('please', 'robot', 'can you'), return tokens."""
    raise NotImplementedError


def find_verb(tokens: list[str]) -> str | None:
    """Return 'put' for put/place/move/bring/carry/set/drop and 'pick' for pick/grab/take/lift.
    The verb must be the first content word; anything else (throw, hit, push, ...) returns None."""
    raise NotImplementedError


def find_destinations(tokens: list[str]) -> list[tuple[int, int, str | None]]:
    """Spans 'in|into|inside|onto|to [the] [colour] bin|basket|container' -> (start, end, colour)."""
    raise NotImplementedError


def find_object_phrases(tokens: list[str], skip: list[tuple[int, int, str | None]]):
    """Noun phrases outside the destination spans: [colour] cube|cylinder|box|block|object|thing|one."""
    raise NotImplementedError


def resolve(color: str | None, shape: str | None, objects: Sequence[SceneObject]) -> list[SceneObject]:
    """All scene objects compatible with the slots. 0 -> Unparseable, 1 -> ok, >1 -> Clarify."""
    raise NotImplementedError


def parse(text: str, objects: Sequence[SceneObject], bins: Sequence[SceneBin]) -> TaskGoal | Clarify | Unparseable:
    """Rules, in this order (each one is a test in tests/acceptance/test_cap07.py):
    1. empty / negation / unknown colour word          -> Unparseable
    2. no supported leading verb                       -> Unparseable
    3. more than two objects                           -> Unparseable
    4. pronoun with no antecedent ('put it in the bin') -> Clarify
    5. object slots match 0 / >1 scene objects          -> Unparseable / Clarify
    6. destination missing or matches >1 bins           -> Clarify; 0 bins -> Unparseable
    7. otherwise TaskGoal(predicates=on(obj, bin) ... or holding(obj) for 'pick up')
    """
    raise NotImplementedError
```

Viết `normalise` và `find_verb` trước và kiểm thử riêng; rồi đến đích; rồi cụm vật thể; và chỉ sau đó mới đến `parse`. Giữ từ vựng trong các tập ở mức module để người đọc nhìn thấy ngữ pháp trong một cái nhìn.

## Thực hành độc lập

### Mục tiêu
Xây và kiểm thử lớp tác vụ (parser, planner, behaviour tree, belief) và bộ giám sát an toàn, và đạt bộ nghiệm thu CAP07: khớp mục tiêu chính xác ít nhất 95 %, không có parse sai tự tin nào trên câu đối kháng, kế hoạch có chặn và tối thiểu, thử lại có chặn, mười phép tiêm hazard tới trạng thái an toàn đúng hạn, tỉ lệ dừng nhầm thấp, quy tắc tốc độ vùng người và e-stop có chốt. Ghi lại một cách trung thực rằng bộ giám sát bảo vệ một mô phỏng và không phải an toàn được chứng nhận.

### Thiết lập
Làm việc trong `~/corebot-capstone` trên một nhánh mới. Lõi của cột mốc này là Python thư viện chuẩn (cộng `pyyaml` cho file ngưỡng) và chạy trong vài giây; bộ nghiệm thu không cần simulator. Trong hệ thống đầy đủ, bộ giám sát phải chạy trong tiến trình hoặc luồng riêng; các test gọi nó trực tiếp với đầu vào mô phỏng ở 100 Hz.

```bash
cd ~/corebot-capstone
git checkout -b cap07-task-and-safety
. .venv/bin/activate
pip install -e . pyyaml pytest      # CAP07 needs only pyyaml and pytest; py_trees is optional (Library track)
mkdir -p tests/data docs src/corebot/task src/corebot/safety
# 1. write the 60-sentence file (format below), then the parser
# 2. planner, behaviour tree, world model
# 3. supervisor + hazards.yaml + docs/hazard_table.md (one row per hazard id H01..H10)
pytest -q tests/acceptance/test_cap07.py
```

### Nhiệm vụ
1. **`task/parser.py`**: `parse(text, objects, bins)` trả về `TaskGoal | Clarify | Unparseable`, với từ đồng nghĩa, slot màu/hình/quan hệ và các quy tắc trong docstring. Ghi ngữ pháp và giới hạn của nó trong `docs/parser.md`.
2. **`tests/data/instructions.jsonl`**: 60 câu (định dạng như trong ví dụ có lời giải): ít nhất 20 câu diễn đạt lại và 10 câu đối kháng, bao phủ hai cảnh `default` và `two_red` được định nghĩa trong file test.
3. **`task/planner.py`**: planner STRIPS breadth-first có chặn (số hành động tối thiểu, không bao giờ lặp).
4. **`task/bt.py`**: cây của riêng bạn (Sequence, Retry, leaf skill) hoặc py_trees; tối đa 2 lần thử lại khi nhấc thất bại, chuỗi lý do khi hủy, giới hạn tick.
5. **`task/world_model.py`**: belief vật thể với tư thế, timestamp, độ tin cậy và phương thức `age(now)`; lớp tác vụ quan sát lại khi belief cũ hơn ngưỡng của bạn.
6. **`safety/supervisor.py` + `hazards.yaml`**: các mức OK / SLOW / HOLD / ESTOP, mười hazard, chốt với `reset` tường minh, ngưỡng tải từ YAML, không bao giờ ném ngoại lệ.
7. **`docs/hazard_table.md`**: mỗi hazard H01-H10 một dòng gồm nguyên nhân, phát hiện, phản ứng, id test. Thêm dòng của riêng bạn cho "camera nói dối".
8. **Ghi chú về tính độc lập** (`docs/safety_architecture.md`, nửa trang): supervisor dùng tiến trình, đồng hồ và đầu vào nào; nó không bảo vệ chống lại điều gì; một câu rõ ràng rằng nó là biện pháp bảo vệ mô phỏng và không phải an toàn được chứng nhận.

### Code khởi đầu

```python
# src/corebot/task/planner.py
from corebot.interfaces import Predicate

def plan(robot_at: str, obj_locs: dict[str, str], bins: list[str],
         goal: tuple[Predicate, ...], max_expansions: int = 20000) -> list[tuple] | None:
    """Actions: ("nav", loc), ("pick", obj), ("place", obj, bin).
    Preconditions: pick needs robot_at == "table", empty gripper, obj on the table;
    place needs robot_at == bin and the object in the gripper.
    Breadth-first search with a visited set and an expansion cap, so it is optimal in the number of
    actions and can never loop. Return None if the goal is unreachable within the cap."""
    raise NotImplementedError


# src/corebot/task/bt.py
from enum import Enum

class Status(Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

def build_pick_place(skills: dict, bb: dict, max_pick_retries: int = 2):
    """Sequence[nav_table, Retry(pick, max_pick_retries), nav_bin, place].
    On failure write bb["reason"] = "<skill>_failed"."""
    raise NotImplementedError

def run(root, bb: dict, max_ticks: int = 50) -> tuple[Status, str, int]:
    """Tick until the tree is not RUNNING or max_ticks is hit (then FAILURE, "tick_bound_exceeded")."""
    raise NotImplementedError


# src/corebot/safety/supervisor.py   (runs in its OWN process/thread, 100 Hz, stdlib only)
from dataclasses import dataclass
from corebot.interfaces import SafetyState

@dataclass
class SafetyInputs:
    stamp: float
    cmd_v: float = 0.0
    cmd_w: float = 0.0
    person_dist: float = 99.0
    link_age: float = 0.0
    perception_age: float = 0.0
    heartbeat_age: float = 0.0
    est_diverged: bool = False
    max_joint_torque: float = 0.0
    battery_low: bool = False
    estop: bool = False
    arm_in_workspace: bool = True

@dataclass
class SafetyOutput:
    state: SafetyState        # level OK | SLOW | HOLD | ESTOP, reasons = hazard ids
    v_out: float              # what is forwarded to the base driver
    w_out: float
    arm_hold: bool            # True -> arm holds position
    firmware_stop: bool       # True -> send the direct stop frame to the firmware watchdog

class Supervisor:
    def __init__(self, cfg: "SafetyConfig") -> None:
        raise NotImplementedError
    def step(self, inputs: SafetyInputs) -> SafetyOutput:
        """One 10 ms tick. ESTOP latches; HOLD clears only after clear_dwell_s without a reason;
        SLOW caps |v| at cfg.v_slow when person_dist < cfg.person_slow_m. Never raises."""
        raise NotImplementedError
    def reset(self, operator_confirmed: bool) -> bool:
        """Clear the ESTOP latch only when operator_confirmed is True. Return True when unlatched."""
        raise NotImplementedError
```

File ngưỡng mà supervisor đọc (giá trị khởi đầu, hãy chỉnh bằng các test tiêm):

```yaml
# src/corebot/safety/hazards.yaml  (thresholds live here, not in code; every id appears in docs/hazard_table.md)
limits:
  v_max: 0.5            # m/s, planner speed limit
  v_slow: 0.15          # m/s inside the human zone
  person_slow_m: 1.0
  person_stop_m: 0.5
  link_timeout_s: 0.2
  perception_timeout_s: 0.25
  heartbeat_timeout_s: 0.2
  torque_max_nm: 3.0
  clear_dwell_s: 0.5
hazards:
  H01: {name: person_close,        detect: "person_dist < person_stop_m",       response: HOLD}
  H02: {name: serial_link_dead,    detect: "link_age > link_timeout_s",         response: HOLD}
  H03: {name: estimator_diverged,  detect: "est_diverged flag",                 response: HOLD}
  H04: {name: torque_spike,        detect: "max_joint_torque > torque_max_nm",  response: HOLD}
  H05: {name: low_battery,         detect: "battery_low flag",                  response: HOLD}
  H06: {name: operator_estop,      detect: "estop button",                      response: ESTOP}
  H07: {name: perception_dropout,  detect: "perception_age > perception_timeout_s", response: HOLD}
  H08: {name: planner_heartbeat,   detect: "heartbeat_age > heartbeat_timeout_s",   response: HOLD}
  H09: {name: overspeed_command,   detect: "abs(cmd_v) > v_max",                response: HOLD}
  H10: {name: arm_outside_workspace, detect: "not arm_in_workspace",           response: HOLD}
```

### Kiểm thử
Tạo `tests/acceptance/test_cap07.py`. Các cổng là test khớp chính xác của parser và test mười phép tiêm. File dưới đây chạy nguyên trạng khi module và file dữ liệu của bạn đã có.

```python
# tests/acceptance/test_cap07.py  (run from the repo root:  pytest -q tests/acceptance/test_cap07.py)
import json, pathlib, random
from corebot.interfaces import Predicate, TaskGoal
from corebot.task.parser import parse, Clarify, Unparseable, SceneObject, SceneBin
from corebot.task.planner import plan
from corebot.task import bt
from corebot.safety.supervisor import Supervisor, SafetyConfig, SafetyInputs

SCENES = {
    "default": ([SceneObject("cube_red", "red", "cube"), SceneObject("cylinder_green", "green", "cylinder"),
                 SceneObject("box_blue", "blue", "box")],
                [SceneBin("bin_blue", "blue"), SceneBin("bin_green", "green")]),
    "two_red": ([SceneObject("cube_red", "red", "cube"), SceneObject("box_red", "red", "box"),
                 SceneObject("cylinder_green", "green", "cylinder")],
                [SceneBin("bin_blue", "blue"), SceneBin("bin_green", "green")]),
}

def _rows():
    return [json.loads(l) for l in open("tests/data/instructions.jsonl") if l.strip()]

def _kind(res):
    return {TaskGoal: "goal", Clarify: "clarify", Unparseable: "unparseable"}[type(res)]

def _goal(res):
    return sorted([p.name, *p.args] for p in res.predicates)

# ---------------------------------------------------------------- parser (GATE)
def test_parser_exact_match_rate():
    rows = [r for r in _rows() if "adversarial" not in r["tags"]]
    ok = 0
    for r in rows:
        objs, bins = SCENES[r["scene"]]
        res = parse(r["text"], objs, bins)
        if r["expect"]["type"] == "goal":
            ok += _kind(res) == "goal" and _goal(res) == sorted(r["expect"]["predicates"])
        else:
            ok += _kind(res) == r["expect"]["type"]
    assert len(_rows()) >= 60
    assert ok / len(rows) >= 0.95, f"{ok}/{len(rows)}"

def test_no_confident_wrong_parse_on_adversarial():
    adv = [r for r in _rows() if "adversarial" in r["tags"]]
    assert len(adv) >= 10
    for r in adv:
        objs, bins = SCENES[r["scene"]]
        assert not isinstance(parse(r["text"], objs, bins), TaskGoal), r["text"]

def test_ambiguous_block_requests_clarification():
    objs, bins = SCENES["default"]
    assert isinstance(parse("pick up the block", objs, bins), Clarify)

# ---------------------------------------------------------------- planner
def _simulate(robot_at, locs, hold, actions):
    locs = dict(locs)
    for a in actions:
        if a[0] == "nav":
            robot_at = a[1]
        elif a[0] == "pick":
            assert robot_at == "table" and hold is None and locs[a[1]] == "table", a
            hold, locs[a[1]] = a[1], "gripper"
        elif a[0] == "place":
            assert robot_at == a[2] and hold == a[1], a
            hold, locs[a[1]] = None, a[2]
    return locs

def test_planner_valid_and_minimal_on_20_random_scenes():
    rng = random.Random(1000)
    names = ["cube_red", "cylinder_green", "box_blue"]
    for _ in range(20):
        start = rng.choice(["start", "table", "bin_blue"])
        locs = {n: "table" for n in names}
        tgt, b = rng.choice(names), rng.choice(["bin_blue", "bin_green"])
        p = plan(start, locs, ["bin_blue", "bin_green"], (Predicate("on", (tgt, b)),))
        assert p is not None
        assert _simulate(start, locs, None, p)[tgt] == b
        # minimal: pick (1) + place (1) + nav to table unless there + nav to the bin
        assert len(p) == 2 + (start != "table") + 1

def test_planner_terminates_on_impossible_goal():
    assert plan("start", {}, ["bin_blue"], (Predicate("holding", ("ghost",)),), max_expansions=500) is None

# ---------------------------------------------------------------- behaviour tree
def test_forced_pick_failure_retries_twice_then_aborts_with_reason():
    calls = {"pick": 0}
    def pick():
        calls["pick"] += 1
        return False
    skills = {"nav_table": lambda: True, "pick": pick, "nav_bin": lambda: True, "place": lambda: True}
    bb = {}
    status, reason, ticks = bt.run(bt.build_pick_place(skills, bb, max_pick_retries=2), bb, max_ticks=50)
    assert status == bt.Status.FAILURE and reason == "pick_failed"
    assert calls["pick"] == 3 and ticks <= 50

# ---------------------------------------------------------------- safety supervisor
DT = 0.01
def _nominal(t, rng):
    return SafetyInputs(stamp=t, cmd_v=0.3, cmd_w=0.1, person_dist=3.0,
                        link_age=rng.uniform(0, 0.03), perception_age=rng.uniform(0, 0.08),
                        heartbeat_age=rng.uniform(0, 0.05), max_joint_torque=rng.uniform(0, 1.5))

INJECTIONS = {  # id -> (limit in s, mutate(inputs, elapsed_s))
    "H01": (0.30, lambda i, e: setattr(i, "person_dist", 0.4)),
    "H02": (0.30, lambda i, e: setattr(i, "link_age", e + 0.01)),
    "H03": (0.30, lambda i, e: setattr(i, "est_diverged", True)),
    "H04": (0.30, lambda i, e: setattr(i, "max_joint_torque", 6.0)),
    "H05": (0.30, lambda i, e: setattr(i, "battery_low", True)),
    "H06": (0.15, lambda i, e: setattr(i, "estop", e < 0.02)),      # a 20 ms button pulse
    "H07": (0.30, lambda i, e: setattr(i, "perception_age", e)),
    "H08": (0.30, lambda i, e: setattr(i, "heartbeat_age", e)),
    "H09": (0.30, lambda i, e: setattr(i, "cmd_v", 2.0)),
    "H10": (0.30, lambda i, e: setattr(i, "arm_in_workspace", False)),
}

def _run_injection(hid, t_inject=1.0, t_end=2.5):
    rng, sup = random.Random(7), Supervisor(SafetyConfig())
    log, t, t_safe = [], 0.0, None
    while t < t_end:
        i = _nominal(t, rng)
        if t >= t_inject:
            INJECTIONS[hid][1](i, t - t_inject)
        out = sup.step(i)
        log.append((t, out))
        if t_safe is None and t >= t_inject and out.v_out == 0.0 and out.arm_hold:
            t_safe = t - t_inject
        t = round(t + DT, 6)
    return t_safe, log

def test_all_ten_injections_reach_safe_state_in_time():     # GATE
    for hid, (limit, _) in INJECTIONS.items():
        t_safe, _ = _run_injection(hid)
        assert t_safe is not None and t_safe <= limit, (hid, t_safe)

def test_false_stop_rate_on_20_nominal_episodes():
    stops = 0
    for ep in range(20):
        rng, sup = random.Random(1000 + ep), Supervisor(SafetyConfig())
        t = 0.0
        stopped = False
        while t < 30.0:
            stopped |= sup.step(_nominal(t, rng)).state.level in ("HOLD", "ESTOP")
            t = round(t + DT, 6)
        stops += stopped
    assert stops / 20 <= 0.05

def test_human_zone_speed_limit():
    sup = Supervisor(SafetyConfig())
    for k in range(300):                       # person walks from 2.0 m to 0.5 m at planner 0.4 m/s
        d = 2.0 - 1.5 * k / 299
        out = sup.step(SafetyInputs(stamp=k * DT, cmd_v=0.4, person_dist=d))
        if d < 1.0:
            assert abs(out.v_out) <= 0.15 + 1e-9

def test_estop_latches_until_explicit_reset_and_log_is_monotonic():
    sup, stamps = Supervisor(SafetyConfig()), []
    for k in range(50):
        out = sup.step(SafetyInputs(stamp=k * DT, cmd_v=0.3, estop=(k == 10)))
        stamps.append(out.state.stamp)
        if k > 10:
            assert out.v_out == 0.0 and out.state.level == "ESTOP"
    assert stamps == sorted(stamps)
    assert sup.reset(operator_confirmed=False) is False
    assert sup.reset(operator_confirmed=True) is True
    assert sup.step(SafetyInputs(stamp=1.0, cmd_v=0.3)).v_out == 0.3     # moves again only after the reset

def test_every_injected_hazard_is_in_the_hazard_table():
    table = pathlib.Path("docs/hazard_table.md").read_text()
    for hid in INJECTIONS:
        assert hid in table, hid
```

Các ngưỡng là giá trị khởi đầu tạm thời (xem lý do trong kế hoạch); hãy siết chặt chúng khi bạn đã có lần chạy tham chiếu của riêng mình. Lý do, mỗi ngưỡng một dòng:

- Khớp mục tiêu chính xác >= 95 % trên 60 câu: với từ vựng đóng gần như mọi câu trong ngữ pháp đều tất định; 5 % chừa chỗ cho 1-2 cách diễn đạt lạ.
- Không có parse sai tự tin nào trên 10 câu đối kháng: một hành động sai tệ hơn một lời từ chối, nên đây là con số không cứng.
- Kế hoạch tối thiểu cho một vật, không bao giờ lặp: tìm kiếm breadth-first cho tính tối ưu miễn phí và giới hạn ngăn việc treo.
- Tối đa 2 lần thử lại rồi hủy: thử lại nhiều hơn che một thất bại có hệ thống và tốn thời gian gần hazard.
- 150 ms cho e-stop, 300 ms cho các hazard khác: mục tiêu phản ứng cỡ con người ở 0.5 m/s tương ứng khoảng 7.5 cm và 15 cm quãng đường.
- Tỉ lệ dừng nhầm <= 5 % trong 20 episode danh định: một supervisor hay báo động giả sẽ bị bỏ qua, nên dừng phiền toái là một lỗi.
- Tốc độ vùng người <= 0.15 m/s trong 1.0 m: đủ chậm để quãng dừng chỉ vài cen-ti-mét.

### Kết quả mong đợi
Khi mọi thứ đã sẵn sàng, `pytest -q` in ra:

```text
...........                                                              [100%]
11 passed in 1.94s
```

Mẹo: cho hàm trợ giúp test của riêng bạn lưu thời gian từng hazard (id hazard, thời gian đến trạng thái an toàn, giới hạn) vào một file JSON dưới `runs/cap07/`; bảng đó, không chỉ dòng "passed", là thứ bạn trích dẫn trong báo cáo.

### Thử thách mở rộng
Mục tiêu mở rộng (tính cho Distinction): một **parser thay thế** dựa trên mô hình ngôn ngữ nhỏ chạy cục bộ hoặc grounding từ vựng mở kiểu CLIP, đánh giá trên cùng 60 câu với cùng hai quy tắc (khớp chính xác ít nhất 95 %, không có parse sai tự tin nào trên tập đối kháng). Báo cáo các thất bại, độ trễ và tài nguyên tính toán đã dùng, và giữ kiểm tra mục tiêu ký hiệu sau mô hình để đầu ra của nó được xác thực trước khi tới planner. Một lựa chọn chỉ thảo luận: ghi chú nửa trang về lý do OpenVLA ([Kim et al.](https://arxiv.org/abs/2406.09246)) không được huấn luyện ở đây và nó sẽ nằm ở đâu trong kiến trúc (như một skill sau `GraspSkill`, không bao giờ đứng trên bộ giám sát).

Tầng phần cứng tùy chọn: một nút e-stop vật lý nối vào đầu vào vi điều khiển và được firmware của HW03/HW10 ghi log (chỉ dùng nguồn điện áp thấp, tối đa 12 V, nhấc động cơ khỏi mặt đất khi test). Đo thời gian thật từ nút tới lúc động cơ dừng bằng logic analyser hoặc một LED trên đường dừng và so với ngân sách mô phỏng của bạn. Phép đo này chỉ đo một đường tín hiệu; nó không làm hệ thống được chứng nhận an toàn.

### Thực hành với thư viện
Thay các lớp behaviour tree của bạn bằng **py_trees** (`pip install py_trees`) và kiểm tra ngữ nghĩa thử lại giống nhau: ba lần thất bại của pick (một lần thử và hai lần thử lại) rồi cây thất bại. Tài liệu BehaviorTree.CPP cho thấy cùng ý tưởng trong C++/XML nếu sau này bạn chuyển sang behaviour tree của ROS 2 và Nav2.

```python
# Needs: pip install py_trees   (2.x).  The same tree as bt.py, with py_trees instead of your own classes.
import py_trees
from py_trees.common import Status


class Skill(py_trees.behaviour.Behaviour):
    """Wrap a synchronous callable returning True/False as a leaf."""
    def __init__(self, name, fn):
        super().__init__(name)
        self.fn = fn

    def update(self):
        return Status.SUCCESS if self.fn() else Status.FAILURE


calls = {"pick": 0}
def pick():
    calls["pick"] += 1
    return False                                    # forced failure

root = py_trees.composites.Sequence("pick_place", memory=True, children=[
    Skill("nav_table", lambda: True),
    py_trees.decorators.Retry("retry_pick", Skill("pick", pick), num_failures=3),   # 3 failures = 1 try + 2 retries
    Skill("nav_bin", lambda: True),
    Skill("place", lambda: True),
])
tree = py_trees.trees.BehaviourTree(root)
tree.setup()
for _ in range(10):
    tree.tick()
    if root.status != Status.RUNNING:
        break
print(root.status, "pick calls:", calls["pick"])   # Status.FAILURE, 3
```

Kỳ vọng: `Status.FAILURE pick calls: 3` (dạng in của py_trees có thể hơi khác giữa các phiên bản). Với lập kế hoạch, `pyperplan` hoặc các planner Planning Domain Definition Language (PDDL) là con đường thư viện cho miền lớn hơn; BFS của bạn là đủ cho cảnh này.

## Kiểm chứng

Kiểm thử parser như một hàm có hợp đồng: in kết quả cho từng trong 60 câu và đọc các thất bại; kiểm tra không câu đối kháng nào trả về mục tiêu. Kiểm thử planner bằng cách mô phỏng kế hoạch theo ký hiệu với các tiền điều kiện (file nghiệm thu làm việc này). Kiểm thử cây bằng một skill buộc thất bại và đếm số lần gọi. Kiểm thử supervisor theo ba cách: (1) **tiêm**: từng hazard riêng rẽ, đo thời gian; (2) **danh định**: 20 episode với nhiễu thực tế và không hazard, đếm số lần dừng nhầm; (3) **kết hợp**: hai hazard cùng lúc, và một hazard tự hết (HOLD phải hồi phục sau dwell, ESTOP thì không). Cuối cùng đọc bảng hazard của chính bạn và hỏi "chuyện gì xảy ra nếu camera nói dối?"; bộ nghiệm thu không kiểm được bạn đã nghĩ tới điều đó, rubric của người thì có.

**Chấm điểm.** CAP07 có trọng số **10 trên 100**. Điểm gồm 60 % tự động (tỉ lệ có trọng số của mười một kiểm tra; các cổng là parser và các phép tiêm an toàn) và 40 % rubric của người (bốn tiêu chí chấm 0-4 kèm bằng chứng liên kết: chất lượng phân tích hazard, tính độc lập của lớp an toàn, sự trung thực của thiết kế parser, tính dễ dùng của hội thoại làm rõ). Một prompt đối chiếu nhận code và artefact chứ không nhận nhận xét của bạn:

```text
You are reviewing a robotics student's CAP07 milestone. Below are parser.py, planner.py, bt.py,
supervisor.py, hazards.yaml, docs/hazard_table.md and the test results. Do NOT use the student's own
verdict. For each criterion give a score 0-4 (0 missing, 2 works but unexplained, 4 justified, tested and
critiqued), quote the evidence and name the single biggest weakness:
1. Hazard analysis quality (FMEA-lite: cause, detection, response, test for every hazard, including "the camera lies")
2. Independence of the safety layer from the stack it supervises (process, clock, inputs)
3. Parser design honesty (limits stated, no silent disambiguation)
4. Usability of the clarification dialogue
Also state clearly whether the documents claim certified safety; they must not.
```

Tốt nghiệp đòi hỏi mọi cổng đạt, điểm cột mốc ít nhất 60 và tổng có trọng số ít nhất 70 trên capstone; CAP08 còn đòi hỏi không có vi phạm an toàn nào trong benchmark cuối. Cổng thất bại giữ cột mốc ở trạng thái đang làm; nó không khóa ứng dụng.

## Lỗi thường gặp

- **Parser overfit vào khuôn mẫu:** 100 % trên cách diễn đạt của chính bạn, thất bại trên cách diễn đạt khác. Cách chữa: viết các câu diễn đạt lại và câu đối kháng trước khi viết parser.
- **Âm thầm giải quyết nhập nhằng:** "the block" thành vật đầu tiên trong danh sách. Cách chữa: `Clarify` là kết quả hạng nhất và được kiểm thử.
- **Belief vật thể lỗi thời dùng để lập kế hoạch:** nhấc ở chỗ vật nằm một phút trước. Cách chữa: tuổi belief và bước quan sát.
- **Logic an toàn trong luồng hoặc tiến trình của một planner có thể bị treo:** supervisor không bao giờ chạy khi cần. Cách chữa: tiến trình riêng, đồng hồ riêng, heartbeat, dừng firmware trực tiếp.
- **E-stop tự reset:** robot lại chuyển động khi nhả nút. Cách chữa: chốt và `reset(operator_confirmed=True)` tường minh.
- **Ngưỡng gây dừng phiền toái:** timeout ngắn hơn jitter bình thường. Cách chữa: đo tuổi danh định, đặt ngưỡng gấp vài lần, đếm số lần dừng nhầm.
- **Thiếu ca "camera nói dối":** một khung hình mới nhưng sai qua mọi kiểm tra độ mới. Cách chữa: kiểm tra chéo (phát hiện ảnh đóng băng, depth so với lidar) và một dòng trong bảng hazard.
- **Vòng lặp không chặn:** planner hoặc cây không có giới hạn. Cách chữa: giới hạn mở rộng và tick, được kiểm thử.
- **Tuyên bố quá mức:** mô tả supervisor là "an toàn". Cách chữa: câu "bảo vệ một mô phỏng, không phải an toàn được chứng nhận" trong README và ghi chú kiến trúc.

## Phương án khác và đánh đổi

*Parser dựa trên luật so với LLM.* Luật kiểm thử được và từ chối theo thiết kế; mô hình ngôn ngữ khái quát hóa sang cách diễn đạt bạn không lường trước nhưng không đảm bảo gì, nên cần cùng các test nghiệm thu cộng một bộ xác thực phía sau. *Planner BFS so với planner PDDL hoặc lập kế hoạch bằng LLM.* BFS tối ưu và nhỏ gọn ở đây; PDDL mở rộng cho miền lớn hơn, kế hoạch LLM (SayCan, Code as Policies) cần grounding tính khả thi. *Behaviour tree so với finite-state machine.* Cây ghép và tái sử dụng tốt hơn khi tác vụ lớn lên; một FSM nhỏ đơn giản hơn cho một pick-and-place đơn. *Cây tự viết so với py_trees hoặc BehaviorTree.CPP.* Tự viết dạy ngữ nghĩa; thư viện cho công cụ và tích hợp ROS 2. *Supervisor là tiến trình riêng so với chỉ watchdog phần cứng.* Watchdog đơn giản và độc lập hơn nhưng ngốc; supervisor hiểu ngữ cảnh (SLOW gần người). Dùng cả hai, như trong kiến trúc. *Hazard theo ngưỡng so với phát hiện bất thường học được:* ngưỡng giải thích và kiểm thử được; bộ phát hiện học được có thể bắt điều bất ngờ nhưng cần được xác thực riêng.

## Vận dụng và ghi nhớ

Cột mốc này nuôi CAP08, nơi lớp tác vụ điều khiển benchmark 100 episode và supervisor phải ghi nhận không vi phạm nào, và CAP09, nơi bảng hazard và giới hạn của parser đi vào báo cáo. Ngoài capstone: mọi hệ thống nhận đầu vào ngôn ngữ tự nhiên hoặc UI cần một đường làm rõ, và mọi hệ thống có actuator cần một đường dừng độc lập và một test tiêm lỗi.

Câu hỏi gợi nhớ cho một tuần sau: (1) Kể tên ba kết quả của parser và một quy tắc cho mỗi kết quả. (2) Viết ngân sách $t_{safe}$ và ba số hạng. (3) Vì sao kế hoạch cho hai vật là 8 hành động từ điểm start? (4) Nêu hai lý do supervisor phải độc lập với planner. (5) Nói câu về giới hạn chứng nhận bằng lời của bạn.

## Đáp án bài tập

1. (a) mục tiêu `on(cylinder_green, bin_green)`. (b) Clarify: "block" khớp cả ba vật (liệt kê các lựa chọn). (c) Unparseable trong ngữ pháp tham chiếu: "stop" nằm ngoài nó. Thiết kế tốt hơn chuyển một từ như "stop" cho supervisor như một yêu cầu, không bao giờ cho planner. (d) Unparseable: yellow không phải màu đã biết. (e) Clarify: "it" không có tiền ngữ.
2. Trường hợp xấu nhất $10+10+10+10=40$ ms (lấy mẫu nút, tick supervisor, frame tới firmware, một chu kỳ firmware). Biên độ $150-40=110$ ms. Biên độ này còn phải chứa thời gian động cơ giảm tốc nếu bạn tính cả thời gian tới lúc dừng hẳn.
3. $d=0.5\cdot0.3+0.5^2/(2\cdot1)=0.15+0.125=0.275$ m, dưới bán kính dừng 0.5 m (biên độ 0.225 m). Ở 0.15 m/s: $0.045+0.0113=0.056$ m.
4. Bắt đầu ở bàn: pick, nav(bin), place, nav(table), pick, nav(bin), place = **7** hành động (8 nếu bắt đầu ở nơi khác). Gripper một tay buộc có chuyến đi về thứ hai; với gripper hai vật sẽ là 5.
5. $P=1-0.2^3=0.992$; số lần gọi kỳ vọng $=1+0.2+0.04=1.24$. Lạc quan: giả định các lần thử độc lập; một nguyên nhân có hệ thống (tư thế gắp tệ, vật ngoài tầm với) làm các lần thử lại thất bại cùng nhau.
6. Cận dưới: gấp vài lần giá trị danh định lớn nhất, ví dụ ít nhất 90 ms (3 x 30). Cận trên: $300-10=290$ ms trừ thời gian tác động. Timeout 0.2 s là lựa chọn tốt (6.7 lần giá trị danh định lớn nhất); nó tốn $0.5\cdot0.2=10$ cm quãng đường ở 0.5 m/s, cộng khoảng 0.5 cm cho tick.
7. An toàn nhưng dễ dùng kém. Tốt hơn mà không đoán: trả lời bằng một `Clarify` đề nghị phần khẳng định để xác nhận ("Tôi có thể đặt khối đỏ vào thùng xanh dương; tôi không xử lý được 'do not touch'. Làm vậy nhé?"), hoặc thêm một predicate `avoid(obj)` tường minh vào ngôn ngữ mục tiêu và kiểm thử nó. Không bao giờ âm thầm bỏ phủ định.
8. Supervisor không chạy trong lúc treo, nên không gì phát hiện; base giữ lệnh cuối và đi $0.5\cdot2=1$ m. Thiết kế lại: supervisor trong tiến trình riêng với đồng hồ riêng và timeout heartbeat, cộng một watchdog firmware đưa lệnh về 0 nếu không có frame trong khoảng 150 ms: quãng đường khoảng $0.5\cdot0.16=8$ cm (150 ms cộng tick 10 ms), dưới 10 cm.
9. Quy tắc: nếu tuổi vượt 5 s (vật có thể bị di chuyển), lớp tác vụ chèn một hành động quan sát trước mọi lần nhấc. Nếu hai lần quan sát không tìm thấy vật, đặt belief là mất, hủy với lý do `object_not_found` và hỏi người dùng (Clarify hoặc báo cáo); không bao giờ nhấc ở tư thế cũ. Ngưỡng đến từ tốc độ thế giới có thể thay đổi trong kịch bản của bạn (một người đi lại) so với chi phí của một lần nhìn thêm.
10. Dòng: hazard "camera nói dối"; nguyên nhân driver bị đóng băng hoặc sai luồng với timestamp mới; phát hiện: chênh lệch ảnh gần bằng không trong khi tốc độ base trên 0.1 m/s trong 0.25 s, hoặc depth không nhất quán với lidar quá một dung sai; phản ứng HOLD cho cánh tay và SLOW cho base; id test `inject_H11` phát lại một khung hình đóng băng với timestamp được cập nhật và kiểm tra trạng thái an toàn trong 300 ms. Giới hạn: một ảnh hợp lý nhưng sai vẫn qua được; kiểm tra chéo giảm, không loại bỏ, rủi ro.

## Đọc thêm

- [Tài liệu BehaviorTree.CPP](https://www.behaviortree.dev/) - các node, ticking, decorator.
- [py_trees](https://github.com/splintered-reality/py_trees) và [tài liệu](https://py-trees.readthedocs.io/en/devel/).
- [Colledanchise và Ogren, Behavior Trees in Robotics and AI](https://arxiv.org/abs/1709.00084).
- [Ahn et al., SayCan](https://arxiv.org/abs/2204.01691) và [Liang et al., Code as Policies](https://arxiv.org/abs/2209.07753).
- [Kim et al., OpenVLA](https://arxiv.org/abs/2406.09246).
- [Wu et al., TidyBot](https://arxiv.org/abs/2305.05658) - dọn dẹp điều khiển bằng ngôn ngữ với robot thật.
- [STRIPS (Wikipedia)](https://en.wikipedia.org/wiki/STRIPS) và [Failure mode and effects analysis (Wikipedia)](https://en.wikipedia.org/wiki/Failure_mode_and_effects_analysis).
- Bài [S07 An toàn robot](/lessons/S07) của bạn, và các quy tắc an toàn của HW03 cho mọi tầng phần cứng.
- **Video:** Petter Ogren, *5 minute Behavior Tree tutorial*; Yannic Kilcher, *Do As I Can, Not As I Say (SayCan) - Paper Explained*.
