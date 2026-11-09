---
{"title": "Cột mốc capstone 9: bản phát hành tái lập được, báo cáo kỹ thuật, demo và kiểm tra tốt nghiệp", "summary": "Đóng gói CoreBot Tidy để người lạ chạy lại được (Docker và make reproduce-smoke), viết một báo cáo khoa học ngắn có mọi con số được sinh từ log của bạn, quay video demo 3 phút, và chạy kiểm tra tốt nghiệp cuối cùng theo rubric của capstone.", "objectives": ["Đóng gói dự án để make reproduce-smoke chạy lại các episode có seed và khớp kết quả đã lưu trong môi trường sạch.", "Sinh mọi con số trong báo cáo từ file metric bằng placeholder báo lỗi khi gặp khóa không tồn tại.", "Viết báo cáo với các mục chuẩn, khẳng định được hiệu chỉnh, hạn chế và tuyên bố về khả năng tái lập.", "Lên kế hoạch và quay demo 3 phút cho thấy câu lệnh, trạng thái nội bộ của robot và kết quả.", "Tính điểm tốt nghiệp có trọng số và quyết định Pass, Merit hay Distinction theo quy tắc."]}
---

## Vì sao điều này quan trọng

Bạn có một hệ thống chạy được và một bộ số trung thực từ [CAP08](/lessons/CAP08). Phần lớn giá trị của một dự án bị mất ở bước cuối này: code chỉ chạy trên laptop của bạn, báo cáo trích số từ lần chạy cũ, demo chỉ cho thấy một episode may mắn. Cột mốc này biến dự án thành thứ người khác có thể tin và dùng lại: một bản phát hành mà người lạ chạy lại được, một báo cáo trong đó mọi con số truy được về một log, và một bản demo nói sự thật trong ba phút.

Đây cũng là cuối khóa học, nên nó khép lại bằng kiểm tra tốt nghiệp. Quy tắc cố ý đơn giản: qua các gate, mỗi cột mốc đạt 60, tổng đạt 70. Phần kiểm tra là một chương trình nhỏ bạn chạy trên điểm của chính mình, để thấy chính xác điều gì còn ngăn giữa bạn và Merit hay Distinction.

## Trực giác

![Kiến trúc hệ thống CoreBot Tidy: cảm biến và thế giới MuJoCo, đế firmware-in-the-loop, ước lượng, lập bản đồ và kế hoạch, nhận thức, thao tác và kỹ năng học, lớp tác vụ ngôn ngữ, bộ giám sát an toàn và harness đánh giá](/lesson-figures/CAP-architecture.svg)

*Phát hành nghĩa là đóng băng toàn bộ bức tranh này: code, mô hình, config, seed và log, dưới một tag.*

Hãy coi bản phát hành như một chiếc hộp niêm phong có nhãn. Bên trong: mã nguồn ở tag `v1.0`, các phụ thuộc đã ghim, firmware, log tóm tắt nhỏ, trọng số đã huấn luyện. Trên nhãn: các lệnh dựng lại những con số chính. Người đọc không cần tin bạn; họ chạy `make reproduce-smoke`, thấy sáu episode có seed kết thúc đúng như file đã lưu, rồi mới đọc báo cáo.

Báo cáo là sách hướng dẫn của chiếc hộp, viết bằng văn xuôi. Quy tắc đơn giản: **không con số nào trong phần Results do người gõ**. Các placeholder như `{{metric:nominal.wilson_lo|pct1}}` được thay từ `metrics.json`; nếu khóa không tồn tại thì build fail. Demo là đoạn giới thiệu. Nó phải cho thấy cả chuỗi (câu lệnh gõ vào, parser, ước lượng pose, detection, gắp, đặt) và không được giấu bộ giám sát an toàn.

Cột mốc này dựa trên [CAP08](/lessons/CAP08) (`metrics.json` và log), [RS07 Scientific Writing](/lessons/RS07) (cấu trúc báo cáo và khẳng định được hiệu chỉnh), [RS04 Experimental Reproducibility](/lessons/RS04) (seed, môi trường, hash), [RS09 Research Software](/lessons/RS09) (test, đóng gói, lint), [T06 Docker](/lessons/T06) (image) và [HW12 Bring-up & Debugging](/lessons/HW12) (phụ lục nhật ký debug và phụ lục phần cứng nếu bạn đã xây tầng tùy chọn).

## Lý thuyết và suy dẫn

Đây là các ghi chú tích hợp: những đặc tả mà các bài kiểm thử nghiệm thu thực thi, mỗi cái kèm chủ đề dạy nó.

![Sơ đồ: mã nguồn ở tag v1.0, Dockerfile và Makefile đưa vào make reproduce-smoke để so sáu kết quả có seed với file đã lưu; metrics.json qua render.py đi vào report.md.tmpl thành report.md; scores.json đi vào graduate.py in ra kết luận](/lesson-figures/CAP09.svg)

### 1. Kiểm tra smoke về khả năng tái lập ([RS04](/lessons/RS04))

Bạn không thể chạy lại 320 episode trong một bài test, nên bạn chạy lại một **tập smoke**: 6 seed, lưu cùng kết quả trong `runs/smoke/expected.json`. Test đạt khi một lần chạy mới (trong container, hoặc trong môi trường ảo mới) cho **đúng** cùng kết quả ở mỗi seed và xong trong 20 phút. Tính xác định dựa trên bốn thói quen: seed cố định (`numpy.random.default_rng(seed)`), code số học đơn luồng trong test (`OMP_NUM_THREADS=1`), phiên bản được ghim, và không phụ thuộc đồng hồ thật. Kết quả số thực có thể khác giữa các loại CPU, nên test smoke so **kết quả** (cờ thành công, nguyên nhân lỗi, số bước trong dung sai bạn ghi rõ), không so số thực thô.

### 2. Container và các target make ([T06](/lessons/T06), [RS09](/lessons/RS09))

Dựng image từ một base được ghim (`python:3.11.9-slim-bookworm`), cài phụ thuộc từ lock file lúc `docker build`, và chạy với `--network none` để không gì có thể bị tải khi chạy. `make` cho người đọc những lệnh ngắn: `make doctor` (đủ công cụ chưa?), `make test`, `make reproduce-smoke`, `make report`. Quickstart trong README phải tối đa 10 lệnh vì một quickstart dài là quickstart không ai làm hết.

### 3. Số từ log: placeholder ([RS07](/lessons/RS07), [RS09](/lessons/RS09))

Viết `report/report.md.tmpl` với các placeholder `{{metric:path|format}}`. `render.py` tra đường dẫn có dấu chấm trong `metrics.json`, định dạng nó (`pct1`, `f3`, `int`) và từ chối khóa lạ, định dạng lạ và mọi thứ còn chưa được điền. Lớp bảo vệ thứ hai là một test quét phần Results của template để tìm số trần (hai chữ số trở lên, hoặc số thập phân) nằm ngoài placeholder. Kết quả là khi bạn chạy lại benchmark thì báo cáo tự cập nhật, và một con số cũ là điều không thể.

### 4. Cấu trúc báo cáo và khẳng định được hiệu chỉnh ([RS07](/lessons/RS07))

Các mục bắt buộc: Abstract, Introduction, Related work (ít nhất 8 tài liệu tham khảo có URL hoặc DOI), Method, Experiments, Results, Limitations, Safety, Ethics, Reproducibility statement, References; 3000 đến 6000 từ. Hiệu chỉnh động từ theo bằng chứng: "chúng tôi đo" cho điều log cho thấy, "gợi ý" cho kết quả có khoảng rộng, "chúng tôi không thử" cho điều còn thiếu. Trong dự án này câu được hiệu chỉnh quan trọng nhất là: mọi thứ ở đây **chỉ là mô phỏng**; twin niêm phong ước lượng độ nhạy với một họ nhiễu loạn và không phải bằng chứng về robot thật. Bộ giám sát an toàn bảo vệ một mô phỏng và không phải chức năng an toàn được chứng nhận (xem [CAP07](/lessons/CAP07)). Liên kết `docs/model_card.md` cho các phần học được và `docs/hazard_table.md` cho các hazard.

### 5. Checklist phát hành ([RS09](/lessons/RS09), [HW12](/lessons/HW12))

`docs/RELEASE_CHECKLIST.md` theo checklist của Papers with Code (phụ thuộc, script huấn luyện, script đánh giá, mô hình đã huấn luyện, bảng kết quả với các lệnh tạo ra nó). Bài kiểm thử nghiệm thu đếm các ô: tất cả phải được tick. Thêm một nhật ký bring-up và debug làm phụ lục theo kiểu HW12: triệu chứng, giả thuyết, phép thử, kết quả, để người đọc thấy bạn tìm ra vấn đề thế nào.

### 6. Quy tắc tốt nghiệp

Điểm một cột mốc là $100\,(0.6\,a+0.4\,r/(4m))$ với $a$ là phân số có trọng số của các kiểm tra tự động đạt, $r$ tổng điểm rubric của bạn (0 đến 4 cho mỗi trong $m$ tiêu chí). Tổng là $\sum_i w_i s_i/100$ với trọng số CAP01 8, CAP02 12, CAP03 12, CAP04 11, CAP05 13, CAP06 12, CAP07 10, CAP08 14, CAP09 8 (cộng 100). **Tốt nghiệp** nghĩa là tất cả: mọi gate của mọi cột mốc đạt; điểm mỗi cột mốc ít nhất 60; tổng có trọng số ít nhất 70; CAP08 không có vi phạm an toàn; `make reproduce-smoke` đạt trên bản checkout sạch. **Merit**: tổng ít nhất 80. **Distinction**: tổng ít nhất 90 và ít nhất một stretch (visual odometry, chính sách sim ACT hoặc LeRobot, biến thể parser LLM hoặc CLIP, so sánh baseline Nav2, hoặc tầng phần cứng với bảng thật so với sim). Tầng phần cứng một mình không bao giờ thay thế một gate fail. Một gate fail không khóa gì trong ứng dụng: nó giữ cột mốc ở trạng thái đang làm.

## Ví dụ có lời giải

Giá trị minh họa, không từ một lần chạy thật.

### Số học tốt nghiệp, một lần chạy smoke và một câu báo cáo được render

**Đề bài.** Kết quả cuối của một học viên cho chín milestone được cho bằng phần trăm có trọng số $a$ của các kiểm tra tự động đã đạt và điểm rubric $r$ trên 16 (bốn tiêu chí chấm 0 đến 4):

| Milestone | Trọng số | $a$ | Rubric /16 |
|---|---|---|---|
| CAP01 | 8 | 1.00 | 14 |
| CAP02 | 12 | 0.90 | 13 |
| CAP03 | 12 | 0.85 | 12 |
| CAP04 | 11 | 0.90 | 12 |
| CAP05 | 13 | 0.80 | 11 |
| CAP06 | 12 | 0.75 | 10 |
| CAP07 | 10 | 0.90 | 12 |
| CAP08 | 14 | 0.90 | 13 |
| CAP09 | 8 | 1.00 | 13 |

Quy tắc: điểm milestone $s=100\,(0.6\,a+0.4\,r/16)$; tổng $=\sum_i w_i s_i/100$; tốt nghiệp cần mọi gate đạt, mọi milestone ít nhất 60, tổng ít nhất 70 và, theo dữ liệu CAP08, không có vi phạm an toàn; Pass ở 70, Merit ở 80, Distinction ở 90 cộng một stretch. Mọi gate đã đạt, CAP08 không có vi phạm an toàn và một stretch so sánh Nav2 đã được làm.

- (a) Tính chín điểm milestone, tổng có trọng số và hạng.
- (b) Một lần chạy smoke chạy lại sáu seed (1000 đến 1005) với kết quả lưu `[ok, ok, GRASP_SLIP, ok, ok, GRASP_SLIP]` trong container hết 734 s với kết quả giống hệt; giới hạn là 1200 s. Quyết định gate smoke.
- (c) Với các metric của CAP08 (94 thành công trên 120 episode nominal, v.v.), render câu đầu của đoạn trích mẫu báo cáo dưới đây.

**Lời giải.**

1. *Điểm milestone.* Vì $100\cdot0.6=60$ và $100\cdot0.4/16=2.5$, mỗi điểm là $s=60\,a+2.5\,r$. CAP01: $60\cdot1.00+2.5\cdot14=60+35=95.0$. CAP02: $54+32.5=86.5$. CAP03: $51+30=81.0$. CAP04: $54+30=84.0$. CAP05: $48+27.5=75.5$. CAP06: $45+25=70.0$. CAP07: $54+30=84.0$. CAP08: $54+32.5=86.5$. CAP09: $60+32.5=92.5$.
2. *Đóng góp có trọng số* $w_is_i/100$: $7.600+10.380+9.720+9.240+9.815+8.400+8.400+12.110+7.400=83.065$, và các trọng số cộng $8+12+12+11+13+12+10+14+8=100$, nên tổng là $83.065\approx83.1$.
3. *Hạng.* Mọi milestone ít nhất 60 (thấp nhất là CAP06 với 70.0), tổng ít nhất 70, mọi gate đạt và các điều kiện an toàn và smoke đều thỏa, nên học viên tốt nghiệp. $83.1\ge80$ cho Merit. Distinction cần $\ge90$: stretch Nav2 không nâng hạng vì giới hạn là tổng điểm, không phải stretch.
4. *Gate smoke.* Sáu kết quả lưu bằng đúng sáu kết quả chạy mới (bốn `ok`, hai `GRASP_SLIP`), và $734\ \text{s}\le1200\ \text{s}$ (20 phút): đạt, còn dư $1200-734=466$ s.
5. *Render.* Mỗi placeholder `{{metric:key|fmt}}` được thay bằng giá trị đã định dạng từ `metrics.json`: `nominal.n|int` là 120; `nominal.rate|pct1` là $94/120=0.7833\to78.3\ \%$; các cận Wilson $0.7015$ và $0.8476$ với `pct1` cho $70.1\ \%$ và $84.8\ \%$. Câu đọc là "On 120 held-out nominal episodes the system completed the task in 78.3 % of cases (Wilson 95 % interval 70.1 % to 84.8 %)". Các placeholder khác phân giải tương tự: tỉ lệ twin $46/80\to57.5\ \%$, khoảng cách `f3` $0.208$ với khoảng $0.077$ đến $0.335$, và hiệu ứng landmark $43.33$ điểm với $p=0.002$.

| Milestone | Trọng số | $a$ | Rubric /16 | Điểm |
|---|---|---|---|---|
| CAP01 | 8 | 1.00 | 14 | 95.0 |
| CAP02 | 12 | 0.90 | 13 | 86.5 |
| CAP03 | 12 | 0.85 | 12 | 81.0 |
| CAP04 | 11 | 0.90 | 12 | 84.0 |
| CAP05 | 13 | 0.80 | 11 | 75.5 |
| CAP06 | 12 | 0.75 | 10 | 70.0 |
| CAP07 | 10 | 0.90 | 12 | 84.0 |
| CAP08 | 14 | 0.90 | 13 | 86.5 |
| CAP09 | 8 | 1.00 | 13 | 92.5 |

Cùng phép tính đó bằng mã:

```python
# Standalone: the graduation arithmetic of plan section 7 with illustrative inputs (standard library only).
WEIGHTS = {"CAP01": 8, "CAP02": 12, "CAP03": 12, "CAP04": 11, "CAP05": 13,
           "CAP06": 12, "CAP07": 10, "CAP08": 14, "CAP09": 8}
# milestone: (fraction of weighted automated checks passed, rubric points out of 4 x 4 criteria)
inputs = {"CAP01": (1.00, 14), "CAP02": (0.90, 13), "CAP03": (0.85, 12), "CAP04": (0.90, 12),
          "CAP05": (0.80, 11), "CAP06": (0.75, 10), "CAP07": (0.90, 12), "CAP08": (0.90, 13), "CAP09": (1.00, 13)}
total = 0.0
for k, (auto, rubric) in inputs.items():
    score = 100 * (0.6 * auto + 0.4 * rubric / 16)
    total += WEIGHTS[k] * score / 100
    print(f"{k}  weight {WEIGHTS[k]:2d}  score {score:5.1f}")
print(f"weighted total {total:.1f}  ->", "Merit" if total >= 80 else "Pass" if total >= 70 else "not graduated")
print("Distinction needs total >= 90 AND a stretch; here the total is the limit, not the stretch.")
```


Một đoạn trích mẫu báo cáo và cách các placeholder được phân giải:

```markdown
### Results (excerpt of report.md.tmpl)

On {{metric:nominal.n|int}} held-out nominal episodes the system completed the task in
{{metric:nominal.rate|pct1}} of cases (Wilson 95 % interval {{metric:nominal.wilson_lo|pct1}} to
{{metric:nominal.wilson_hi|pct1}}). On the sealed twin the rate was {{metric:twin.rate|pct1}}; the estimated
gap is {{metric:gap.difference|f3}} (95 % CI {{metric:gap.ci_lo|f3}} to {{metric:gap.ci_hi|f3}}).
Removing landmark updates lowered success by {{metric:ablations.no_landmarks.effect_pp|f2}} points
(exact paired p = {{metric:ablations.no_landmarks.mcnemar_p|f3}}).
```


Với các metric minh họa của CAP08, câu được phân giải như ở bước 5. Đổi benchmark, chạy lại `make report`, và câu thay đổi theo.

**Kiểm tra.** Mã trên in cùng chín điểm và `weighted total 83.1 -> Merit`. Cận hợp lý: tổng phải nằm giữa điểm milestone thấp nhất và cao nhất (70.0 và 95.0), và đúng vậy; vì các trọng số cộng 100 nên tổng là trung bình có trọng số, và 83.065 gần với trung bình đơn giản của các điểm, $(95+86.5+81+84+75.5+70+84+86.5+92.5)/9=83.9$. Các số được render là giá trị CAP08 ($94/120$, Wilson $[0.701,\,0.848]$), nên đổi benchmark thì câu đổi theo.

**Rút ra.** Phán quyết tốt nghiệp là số học thuần túy trên vài con số, nên có thể được tính và kiểm toán bằng script; mọi con số trong báo cáo được sinh từ log, và một lần chạy smoke tái lập được chứng minh rằng các số chính có thể dựng lại.

## Bài tập

1. **(Dễ)** *Placeholder.* `nominal.wilson_lo` là 0.7014. `{{metric:nominal.wilson_lo|pct1}}` hiển thị thành gì, và `{{metric:nominal.n|int}}` với `n = 120.0`? Chuyện gì xảy ra với `{{metric:nominal.p95}}` nếu khóa không tồn tại?
2. **(Dễ)** *Tổng có trọng số.* Điểm các cột mốc CAP01 đến CAP09 = 90, 85, 80, 70, 75, 65, 72, 78, 88 với trọng số chính thức. Tính tổng và hạng nếu mọi gate đạt.
3. **(Trung bình)** *Kết luận.* Tổng 91, đã làm stretch Nav2, không vi phạm an toàn, smoke đạt, nhưng một gate của CAP05 fail. Kết luận là gì và bạn làm gì tiếp?
4. **(Trung bình)** *Smoke không khớp.* Chạy lại sáu seed và seed 1003 là `success` trong file đã lưu nhưng giờ là `GRASP_SLIP`. Liệt kê bốn nguyên nhân có thể của tính không xác định và thứ tự bạn sẽ kiểm tra.
5. **(Trung bình)** *Thiết kế image.* Dockerfile của một đồng đội chạy `pip install -r requirements.txt` khi container khởi động và README ghi "cần internet cho lần chạy đầu". Vì sao điều này phá vỡ khẳng định tái lập, và bạn đổi gì?
6. **(Trung bình)** *Khẳng định được hiệu chỉnh.* Viết lại "Robot của chúng tôi đạt 78 % thành công trong thế giới thật và giải quyết sim-to-real" sao cho đúng với dự án này.
7. **(Trung bình)** *Kiểm tra tham khảo.* Mục nào trong các mục sau được tính vào 8 tài liệu tham khảo: (a) "Tobin et al. 2017, https://arxiv.org/abs/1703.06907", (b) "Henderson et al. 2018, Deep RL that matters", (c) "Doe 2020, doi 10.1000/xyz123", (d) "xem Wikipedia"?
8. **(Khó)** *Storyboard demo.* Phân bổ 180 giây cho video demo. Cảnh nào bắt buộc và lớp phủ nào phải hiện? Cho độ dài các đoạn cộng đúng 180 s.
9. **(Khó)** *Merit hay Distinction.* Tổng 88, đã làm tầng phần cứng với bảng thật so với sim, mọi thứ khác đạt. Một học viên khác có tổng 92 và chỉ làm tầng phần cứng không có bảng. Quyết định cho cả hai.
10. **(Khó, mini-project)** *Chạy thử trên checkout sạch.* Clone repository vào thư mục trống, dựng container, chạy `docker run --network none ... make reproduce-smoke` và bấm giờ. Ghi mọi vấn đề (thiếu file, truy cập mạng, phiên bản không ghim, đường dẫn tuyệt đối) và sửa. Nêu quan sát nào cho thấy bản phát hành của bạn không tái lập được.

## Cài đặt tham khảo

Đây là khung của `report/render.py`, module điền placeholder và báo lỗi với mọi thứ lạ. Hãy cài đặt nó bằng thư viện chuẩn. Bài kiểm thử nghiệm thu import `render` từ nó.

```python
"""report/render.py: resolve {{metric:path|format}} placeholders from runs/final/metrics.json.

A number in the report that does not come from metrics.json is a bug, so unknown paths fail loudly.
"""
from __future__ import annotations

import re

PLACEHOLDER = re.compile(r"\{\{\s*metric:([A-Za-z0-9_.\-]+)(?:\|([a-z0-9]+))?\s*\}\}")
FORMATS = {                      # name -> formatter; add your own, keep them boring
    "int": lambda v: str(int(round(v))),
    "f2": lambda v: f"{v:.2f}",
    "f3": lambda v: f"{v:.3f}",
    "pct0": lambda v: f"{100 * v:.0f} %",
    "pct1": lambda v: f"{100 * v:.1f} %",
}


def lookup(metrics: dict, path: str) -> float:
    """Follow a dotted path such as 'nominal.wilson_lo'.

    Raises KeyError("unknown metric: <path>") if any part is missing, and
    KeyError("metric is not a number: <path>") for dicts, lists, booleans and None.
    """
    raise NotImplementedError


def render(template: str, metrics: dict) -> str:
    """Replace every placeholder (default format f3). Unknown formats raise KeyError.
    After substitution no '{{' may remain: raise ValueError otherwise."""
    raise NotImplementedError


def main() -> None:
    """Read runs/final/metrics.json and report/report.md.tmpl, write report/report.md."""
    raise NotImplementedError
```

## Thực hành độc lập

### Mục tiêu
Biến dự án đã hoàn thành thành một bản phát hành mà người lạ chạy lại được, viết báo cáo kỹ thuật từ metric của chính bạn không có số gõ tay, quay demo, hoàn tất checklist và chạy máy tính tốt nghiệp trên điểm của bạn. Trọng số trong điểm tốt nghiệp: 8 trên 100.

### Thiết lập
Làm việc trong `~/corebot-capstone`, chỉ gắn tag ứng viên `v1.0` khi cây làm việc sạch. Bạn cần Docker (tùy chọn nhưng nên có), `make`, `git`, Python 3.11 trở lên và `ruff` (`pip install ruff`). Dành khoảng 16 giờ: chừng 6 cho bản phát hành, 7 cho báo cáo, 1 cho demo, 2 cho lần chạy thử và sửa. Giữ báo cáo trong 3000 đến 6000 từ; ngắn và rõ tốt hơn dài.

```bash
cd ~/corebot-capstone
mkdir -p report/figures tools runs/smoke docs
# report/render.py        <- the reference skeleton above, implemented
# tools/release_check.py  <- starter stubs below (headings, references, checklist, smoke_matches)
# tools/graduate.py       <- weights, gates, Merit/Distinction
python -m pytest -q tests/acceptance/test_cap09.py
python tools/graduate.py docs/scores.json
```

### Nhiệm vụ
1. **Phát hành.** Thêm `Dockerfile` và `Makefile` dưới đây (đổi tên cho khớp repo), một `requirements.lock` với phiên bản chính xác, một `LICENSE` và một `README.md` có khối "Quickstart" tối đa 10 lệnh.
2. **Tập smoke.** Chọn 6 seed, chạy một lần, lưu kết quả vào `runs/smoke/expected.json` (`{"episodes": [{"seed", "success", "reason", "steps"}], "elapsed_s": 0}`), và viết `tools/compare_smoke.py`. `make reproduce-smoke` ghi `runs/smoke/actual.json` với `elapsed_s` đo được.
3. **Bộ render.** Cài đặt `report/render.py` (khung tham khảo) và `tools/release_check.py` (khung khởi đầu).
4. **Báo cáo.** Viết `report/report.md.tmpl` với các mục bắt buộc và ít nhất 8 tài liệu tham khảo; ít nhất ba hình do `report/make_figures.py` sinh từ `runs/`; mọi số trong Results qua placeholder.
5. **Model card và bảng hazard.** `docs/model_card.md` (mục đích sử dụng, dữ liệu, metric kèm CI, giới hạn của các phần học được) và `docs/hazard_table.md` (từ CAP07), cả hai được liên kết từ báo cáo.
6. **Demo.** Một video 3 phút: câu lệnh gõ vào, kết quả parse, pose của bộ ước lượng và detection được phủ lên, gắp, đặt, và một lần dừng an toàn. Thêm liên kết hoặc đường dẫn file vào README.
7. **Checklist.** Hoàn tất `docs/RELEASE_CHECKLIST.md` (chỉ tick mỗi ô sau khi bạn đã kiểm chứng mục đó).
8. **Tốt nghiệp.** Điền `docs/scores.json` (phần tự động, điểm rubric kèm bằng chứng được liên kết cho từng mục, gate, stretch), chạy `python tools/graduate.py docs/scores.json`, commit, gắn tag `v1.0`.

`Makefile` và `Dockerfile` dưới đây là bố cục tham khảo.

```make
.PHONY: doctor test reproduce reproduce-smoke report docker

doctor:                      ## tools present?
	@for t in python3 gcc cmake git; do command -v $$t >/dev/null || echo "missing: $$t"; done

test:
	python -m pytest -q tests/unit tests/acceptance

reproduce-smoke:             ## 6 seeded episodes, compare with runs/smoke/expected.json
	python bench/run_bench.py --split smoke --seeds 1000-1005 --out runs/smoke/actual.json
	python tools/compare_smoke.py runs/smoke/expected.json runs/smoke/actual.json

report:                      ## metrics.json -> report/report.md (fails on unknown keys)
	python bench/metrics.py && python report/render.py

reproduce: reproduce-smoke report

docker:
	docker build -t corebot:v1.0 .
	docker run --rm --network none corebot:v1.0 make reproduce-smoke
```

```dockerfile
FROM python:3.11.9-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
# Dependencies are baked into the image: nothing is downloaded when the container runs.
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY . .
RUN pip install --no-cache-dir -e . && cmake -S firmware -B firmware/build && cmake --build firmware/build
ENV MUJOCO_GL=osmesa OMP_NUM_THREADS=1 PYTHONHASHSEED=0
CMD ["make", "reproduce-smoke"]
```

Checklist (được tick ở đây chỉ làm ví dụ về định dạng; hãy tick của bạn khi từng mục đã được kiểm chứng):

```markdown
# Release checklist (after the ML Code Completeness Checklist of paperswithcode/releasing-research-code)

- [x] Dependencies pinned in pyproject.toml and requirements.lock
- [x] Dockerfile builds; `docker run --network none` passes reproduce-smoke
- [x] Training scripts (train_ppo.py, bc.py) with seeds and CPU config documented
- [x] Evaluation scripts (bench/run_bench.py, bench/metrics.py) regenerate metrics.json from logs
- [x] Trained weights (< 20 MB) committed or linked, with checksums
- [x] README quickstart has 10 commands or fewer
- [x] README results table lists each headline number with the command that produces it
- [x] LICENSE present; third-party assets (Menagerie SO-101) keep their licences
- [x] docs/model_card.md and docs/hazard_table.md exist and are linked from the report
- [x] Report: every number in Results comes from a placeholder; limitations and "simulation only" stated
- [x] Git tag v1.0 created on a clean working tree
- [x] Dry run on a fresh clone in a fresh venv or container completed and timed
```

### Code khởi đầu
Các khung giao diện cho các kiểm tra phát hành và máy tính tốt nghiệp:

```python
"""tools/release_check.py and tools/graduate.py: interface stubs."""
from __future__ import annotations

REQUIRED_HEADINGS = ["Abstract", "Introduction", "Related work", "Method", "Experiments", "Results",
                     "Limitations", "Safety", "Ethics", "Reproducibility statement", "References"]
WEIGHTS = {"CAP01": 8, "CAP02": 12, "CAP03": 12, "CAP04": 11, "CAP05": 13,
           "CAP06": 12, "CAP07": 10, "CAP08": 14, "CAP09": 8}
STRETCHES = {"visual_odometry", "act_sim_policy", "llm_or_clip_parser", "nav2_baseline", "hardware_real_vs_sim"}


def missing_headings(markdown: str) -> list[str]:
    """Required level-2 headings (case-insensitive) that the report lacks."""
    raise NotImplementedError


def word_count(markdown: str) -> int:
    """Words outside fenced code blocks."""
    raise NotImplementedError


def references(markdown: str) -> list[str]:
    """List items under '## References' that contain a well-formed http(s) URL or a DOI (10.xxxx/...)."""
    raise NotImplementedError


def missing_figures(markdown: str, root: str = ".") -> list[str]:
    """Image paths in ![alt](path) that do not exist under root (http links are skipped)."""
    raise NotImplementedError


def checklist(markdown: str) -> tuple[int, int]:
    """(done, total) for '- [x]' and '- [ ]' items."""
    raise NotImplementedError


def quickstart_commands(readme: str) -> int | None:
    """Command lines (no blanks, no # comments) in the first code block under a Quickstart heading; None if absent."""
    raise NotImplementedError


def smoke_matches(expected: dict, actual: dict, max_seconds: float = 1200) -> bool:
    """Stored outcomes of >= 6 smoke seeds equal a fresh rerun exactly, and the rerun took <= max_seconds."""
    raise NotImplementedError


def milestone_score(automated_fraction: float, rubric_points: float, criteria: int) -> float:
    """100 * (0.6 * automated + 0.4 * rubric_points / (4 * criteria)). ValueError for out-of-range input."""
    raise NotImplementedError


def evaluate(data: dict) -> dict:
    """Graduation verdict: keys total, scores, graduated, grade ('not graduated'|'Pass'|'Merit'|'Distinction'), reasons.
    Graduated needs: every gate passed, every milestone >= 60, weighted total >= 70, zero CAP08 safety violations,
    reproduce-smoke passed on a clean checkout. Merit: total >= 80. Distinction: total >= 90 and a known stretch."""
    raise NotImplementedError
```

### Kiểm thử
`tests/acceptance/test_cap09.py` đọc template báo cáo, `runs/final/metrics.json`, `runs/smoke/*.json`, trạng thái repository và `docs/`. Các kiểm tra đánh dấu G là gate. Các ngưỡng là giá trị khởi đầu tạm thời (xem lý do trong kế hoạch); hãy siết chặt chúng khi bạn đã có lần chạy tham chiếu của riêng mình.

- Số trong báo cáo được điền (G): template hiển thị không còn `{{`, đủ các mục bắt buộc, 3000 đến 6000 từ (một bài ngắn thì đọc được còn bài dài hiếm khi), mọi hình tồn tại, và Results không có số gõ tay.
- Tham khảo: ít nhất 8 mục có URL hoặc DOI (mức tối thiểu cho một phần related work đáng tin).
- Reproduce smoke (G): kết quả đã lưu và kết quả mới của 6 seed giống hệt và lần chạy lại mất tối đa 1200 s (người đọc sẽ không chờ lâu hơn).
- Trạng thái repository: tag `v1.0` tồn tại, cây làm việc sạch, có `LICENSE`, quickstart tối đa 10 lệnh, `ruff check .` đạt (bị bỏ qua kèm thông báo nếu chưa cài `ruff`, và điều đó tính là chưa đạt cho gate).
- Model card và bảng hazard tồn tại và báo cáo có liên kết đến chúng.
- Checklist phát hành: ít nhất 10 mục, tất cả được tick.
- Máy tính tốt nghiệp: Merit cho 89.0, không Distinction dưới 90, một gate fail nghĩa là chưa tốt nghiệp.
- File điểm của bạn đầy đủ cho cả chín cột mốc.

```python
"""CAP09 acceptance tests. Gates (G): test_report_numbers_resolve, test_reproduce_smoke_matches."""
import json
import pathlib
import re
import shutil
import subprocess

import pytest

from report.render import render
from tools.graduate import WEIGHTS, evaluate
from tools.release_check import (checklist, missing_figures, missing_headings, quickstart_commands,
                                 references, smoke_matches, word_count)

TEMPLATE = pathlib.Path("report/report.md.tmpl")


def _metrics():
    return json.loads(pathlib.Path("runs/final/metrics.json").read_text())


def _report():
    return render(TEMPLATE.read_text(), _metrics())      # raises on an unknown metric or an unresolved {{...}}


def test_report_numbers_resolve():                                # G
    text = _report()
    assert "{{" not in text and "}}" not in text
    assert missing_headings(text) == []
    assert 3000 <= word_count(text) <= 6000
    assert missing_figures(text) == []
    results = TEMPLATE.read_text().split("## Results")[1].split("\n## ")[0]
    bare = re.sub(r"\{\{[^}]*\}\}", "", results)
    assert re.findall(r"\d+\.\d+|\d{2,}", bare) == [], "a number in Results is typed by hand"


def test_references():
    assert len(references(_report())) >= 8


def test_reproduce_smoke_matches():                               # G
    expected = json.loads(pathlib.Path("runs/smoke/expected.json").read_text())
    actual = json.loads(pathlib.Path("runs/smoke/actual.json").read_text())
    assert smoke_matches(expected, actual, max_seconds=1200)


def test_repository_state():
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
    assert "v1.0" in git("tag").split()
    assert git("status", "--porcelain") == ""
    assert pathlib.Path("LICENSE").exists()
    n = quickstart_commands(pathlib.Path("README.md").read_text())
    assert n is not None and n <= 10
    if shutil.which("ruff"):
        assert subprocess.run(["ruff", "check", "."]).returncode == 0
    else:
        pytest.skip("ruff not installed: install it, this check counts as not passed for the gate")


def test_model_card_and_hazard_table_cross_referenced():
    for f in ("docs/model_card.md", "docs/hazard_table.md"):
        assert pathlib.Path(f).exists(), f
    text = TEMPLATE.read_text()
    assert "model_card.md" in text and "hazard_table.md" in text


def test_release_checklist_complete():
    done, total = checklist(pathlib.Path("docs/RELEASE_CHECKLIST.md").read_text())
    assert total >= 10 and done == total


def test_graduation_calculator():
    ok = {"milestones": {k: {"automated": 0.9, "rubric": 14, "criteria": 4, "gates_passed": True} for k in WEIGHTS},
          "cap08_safety_violations": 0, "reproduce_smoke_clean_checkout": True, "stretches": []}
    v = evaluate(ok)
    assert v["graduated"] and v["grade"] == "Merit" and abs(v["total"] - 89.0) < 0.1
    assert evaluate({**ok, "stretches": ["nav2_baseline"]})["grade"] == "Merit"        # 89 < 90: no Distinction
    bad = json.loads(json.dumps(ok)); bad["milestones"]["CAP05"]["gates_passed"] = False
    assert not evaluate(bad)["graduated"]


def test_my_scores_file_is_complete():
    v = evaluate(json.loads(pathlib.Path("docs/scores.json").read_text()))
    assert set(v["scores"]) == set(WEIGHTS)
```

### Kết quả mong đợi
Với repository sạch đã gắn tag và đủ artefact:

```
........                                                                 [100%]
8 passed in 1.4s
```

Một `docs/scores.json` mẫu (minh họa) và kết luận nó tạo ra, tổng 83.1 và hạng Merit:

```json
{
  "milestones": {
    "CAP01": {"automated": 1.00, "rubric": 14, "criteria": 4, "gates_passed": true},
    "CAP02": {"automated": 0.90, "rubric": 13, "criteria": 4, "gates_passed": true},
    "CAP03": {"automated": 0.85, "rubric": 12, "criteria": 4, "gates_passed": true},
    "CAP04": {"automated": 0.90, "rubric": 12, "criteria": 4, "gates_passed": true},
    "CAP05": {"automated": 0.80, "rubric": 11, "criteria": 4, "gates_passed": true},
    "CAP06": {"automated": 0.75, "rubric": 10, "criteria": 4, "gates_passed": true},
    "CAP07": {"automated": 0.90, "rubric": 12, "criteria": 4, "gates_passed": true},
    "CAP08": {"automated": 0.90, "rubric": 13, "criteria": 4, "gates_passed": true},
    "CAP09": {"automated": 1.00, "rubric": 13, "criteria": 4, "gates_passed": true}
  },
  "cap08_safety_violations": 0,
  "reproduce_smoke_clean_checkout": true,
  "stretches": ["nav2_baseline"]
}
```

Khi chưa có artefact, các test fail với `FileNotFoundError` hoặc `NotImplementedError`; đó là trạng thái xuất phát có chủ ý.

### Thử thách mở rộng
Thêm một workflow GitHub Actions (`.github/workflows/ci.yml`) chạy `make test` và dựng image; xuất bản demo có phụ đề; hoặc viết ghi chú "bài học rút ra" hai trang cho mỗi cột mốc và đưa vào phần thảo luận của báo cáo. Phụ lục phần cứng tùy chọn: nếu bạn đã xây đế ESP32, thêm bảng thật so với sim (thời gian xác lập, vọt lố, sai số xác lập của cùng step test) và một nhật ký bring-up kiểu HW12; đánh dấu mục là "phần cứng, không thuộc các khẳng định được chấm". Không bao giờ trình bày số mô phỏng như kết quả thế giới thật.

### Thực hành với thư viện
Dùng Jinja2 với `StrictUndefined` làm engine template chặt hơn và để `ruff` thực thi gate lint; đầu ra nên khớp với bộ render của bạn cho cùng template.

```python
# Needs: pip install jinja2 ruff     (the same checks, with industrial-strength tools)
import json
import pathlib
import subprocess

from jinja2 import Environment, StrictUndefined

metrics = json.loads(pathlib.Path("runs/final/metrics.json").read_text())

# 1. A template engine that refuses unknown keys: StrictUndefined raises instead of printing a blank.
env = Environment(undefined=StrictUndefined)
tmpl = env.from_string("Nominal success was {{ '%.1f' % (100 * m.nominal.rate) }} % (n = {{ m.nominal.n }}).")
print(tmpl.render(m=metrics))      # dotted access works on dicts; a missing key raises UndefinedError

# 2. Lint gate exactly as the acceptance test expects it
result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)
print(result.stdout or "ruff: all checks passed")
assert result.returncode == 0
```

## Kiểm chứng

Chạy toàn bộ bộ test từ một bản clone mới, không phải từ thư mục làm việc: `git clone . /tmp/check && cd /tmp/check && make test`. Đổi một số trong `metrics.json` và xác nhận báo cáo đổi theo; xóa một khóa và xác nhận `make report` fail. Đổi một kết quả smoke mong đợi và xác nhận `make reproduce-smoke` báo không khớp. Đọc báo cáo như một người lạ: bạn có tìm được lệnh tạo ra mỗi con số chính không? "Chỉ mô phỏng" có được nêu trong abstract và phần hạn chế không? Điểm số: CAP09 có trọng số 8 trên 100 (60 % tự động, 40 % rubric: độ rõ ràng và trung thực của báo cáo, tính dễ hiểu của demo, người đọc có làm lại được không, phạm vi khẳng định phù hợp). Gate: test reproduce-smoke và các số báo cáo được điền. Để tốt nghiệp, `reproduce-smoke` phải đạt trên bản checkout sạch và mọi điều kiện khác của quy tắc phải thỏa.

## Lỗi thường gặp

- Số gõ tay lệch khỏi log sau một lần chạy lại.
- Hình không có nhãn trục, đơn vị hay khoảng tin cậy.
- Docker image cần mạng lúc chạy, hoặc tag nền không ghim.
- Phụ thuộc không có phiên bản chính xác; "chạy được trên máy tôi" với một gói toàn cục.
- Giả định phần cứng không được ghi lại (GPU, màn hình, EGL so với OSMesa).
- Khẳng định kết quả sim-to-real từ mô phỏng, hoặc ngụ ý bộ giám sát là an toàn được chứng nhận.
- Cây làm việc bẩn lúc gắn tag, hoặc tag trỏ đến commit khác với báo cáo.
- Demo chỉ cho thấy episode tốt nhất; hãy cho xem một lỗi và cách hệ thống phản ứng.
- Tính không xác định ẩn: số luồng, ngẫu nhiên hóa hash, seed theo thời gian; test smoke chập chờn.
- Checklist được tick hàng loạt mà không kiểm chứng từng mục.

## Phương án khác và đánh đổi

Thay Docker bạn có thể dùng môi trường ảo mới với lock file (nhẹ hơn, nhưng gói hệ thống như `cmake` là việc của bạn) hoặc Nix (mạnh nhất, khó học nhất). Thay bộ render placeholder bạn có thể dùng notebook hoặc Quarto/Jupyter Book (tiện, nhưng dễ để sót ô cũ). Một điểm vào `make` duy nhất thì đơn giản; `just` hay `tox` cho trải nghiệm đẹp hơn. Một bài báo ngắn tốt hơn bài dài: nhiều người đọc chỉ cần abstract, một hình và phần hạn chế. Với demo, quay màn hình có phụ đề là đủ; dựng chỉn chu là tùy chọn. Nếu máy bạn không chạy được container, một đường venv có tài liệu là chấp nhận được, nhưng test smoke vẫn phải đạt từ bản checkout sạch.

## Vận dụng và ghi nhớ

Đây là cột mốc cuối, nên việc vận dụng hướng ra ngoài: cùng kỷ luật phát hành (môi trường ghim, test smoke, số được sinh ra, khẳng định hiệu chỉnh, checklist) áp dụng cho mọi dự án nghiên cứu hay portfolio, và báo cáo cùng demo là các sản phẩm bạn có thể cho người khác xem. Câu hỏi ôn:

1. Năm điều kiện của "tốt nghiệp" là gì, và điều nào chỉ liên quan đến cột mốc cuối?
2. Vì sao test smoke so kết quả chứ không so số thực dấu phẩy động thô?
3. `render.py` làm gì khi thiếu một khóa, và vì sao?
4. Viết một phiên bản được hiệu chỉnh của một khẳng định trong báo cáo của chính bạn.
5. Khác biệt giữa Merit và Distinction trong khóa học này là gì?

## Đáp án bài tập

1. $0.7014\to$ "70.1 %" (0.7014 nhân 100 làm tròn một chữ số thập phân). `120.0` với `int` hiển thị "120". Một khóa thiếu ném `KeyError("unknown metric: nominal.p95")` và build fail, đó là hành vi có chủ ý: báo cáo không bao giờ được in chỗ trống hay một con số đoán.
2. Tổng có trọng số: $8\cdot90+12\cdot85+12\cdot80+11\cdot70+13\cdot75+12\cdot65+10\cdot72+14\cdot78+8\cdot88=7741$, chia 100: 77.4. Từ 70 trở lên và dưới 80: "Pass" (đã tốt nghiệp, không có Merit), với điều kiện mỗi cột mốc ít nhất 60 (thấp nhất là 65).
3. Chưa tốt nghiệp: một gate fail chặn tốt nghiệp dù tổng thế nào. Tổng và stretch không bù được. Tiếp theo: sửa gate của CAP05 (đọc test fail, sửa nguyên nhân, chạy lại bộ nghiệm thu CAP05), cập nhật điểm, chạy lại máy tính tốt nghiệp. Khi đó Distinction có thể: tổng 91 với một stretch.
4. Nguyên nhân: (a) thư viện số học đa luồng (đặt `OMP_NUM_THREADS=1`), (b) một seed không được dùng đầy đủ (gọi ngẫu nhiên ngoài `default_rng(seed)`), (c) phiên bản thư viện hoặc CPU khác nhau giữa hai lần chạy (so lock file và `pip freeze`), (d) phụ thuộc đồng hồ thật (timeout, `time.time()` trong logic). Thứ tự kiểm tra: chạy lại cùng seed hai lần trên cùng máy; nếu khác nhau thì là (a), (b) hoặc (d); nếu giống nhau nhưng khác giữa các môi trường thì là (c). Sau đó chia đôi bằng cách tắt từng phần của pipeline.
5. Khẳng định "tái lập được" giờ phụ thuộc vào việc package index còn truy cập được và vào phiên bản nó phục vụ hôm đó; lần chạy cũng cần internet. Hãy đóng gói phụ thuộc vào image lúc build từ lock file với phiên bản chính xác, sao chép dự án vào, và chạy với `--network none` trong test. Ghi rõ tag của image nền.
6. Ví dụ: "Trong mô phỏng, hệ thống của chúng tôi hoàn thành tác vụ trong 78 % của 120 episode giữ riêng (khoảng Wilson 95 % từ 70 % đến 85 %). Trên twin nhiễu loạn niêm phong tỉ lệ là 58 %. Chúng tôi không thử trên robot thật, nên không đưa ra khẳng định nào về chuyển giao sim-to-real."
7. (a) được tính (URL), (c) được tính (DOI đúng dạng). (b) không có URL hay DOI nên không được tính cho test tự động (hãy thêm URL arXiv). (d) không phải tài liệu tham khảo.
8. Các cảnh bắt buộc: câu lệnh gõ vào và kết quả parse (15 s), định vị với lớp phủ pose và hiệp phương sai (20 s), điều hướng với đường đi đã lập (25 s), detection có nhãn được phủ và cú gắp (40 s), đặt vào thùng (20 s), một lần dừng an toàn khi có người vào vùng (25 s), một slide metric với khoảng tin cậy và câu hạn chế (20 s), tiêu đề và kết (15 s). Tổng: 15 + 20 + 25 + 40 + 20 + 25 + 20 + 15 = 180 s. Lớp phủ phải hiện pose của bộ ước lượng, detection và trạng thái bộ giám sát.
9. Tổng 88 dưới 90: Merit, dù có bảng thật so với sim. Học viên thứ hai có 92 nhưng tầng phần cứng chỉ tính là stretch khi có bảng thật so với sim, nên không đạt điều kiện Distinction: Merit, và có thể làm bảng đó (hoặc một stretch khác) để lấy Distinction. Tầng phần cứng không bao giờ thay một gate fail trong cả hai trường hợp.
10. Một nhật ký chạy thử tốt liệt kê từng lỗi và cách sửa (ví dụ "đường dẫn asset là tuyệt đối", "numpy không được ghim", "cần mạng để tải trọng số: trọng số giờ nằm trong image"), thời gian của `make reproduce-smoke` (tối đa 20 phút), và quan sát bác bỏ: bất kỳ kết quả lưu nào không khớp, bất kỳ truy cập mạng nào trong lúc chạy, hoặc kết quả khác sau lần chạy giống hệt thứ hai.

## Đọc thêm

- [Releasing research code (Papers with Code checklist)](https://github.com/paperswithcode/releasing-research-code): checklist đằng sau `RELEASE_CHECKLIST.md`.
- [Henderson et al., Deep Reinforcement Learning that Matters](https://arxiv.org/abs/1709.06560): vì sao seed, phương sai và cách báo cáo quyết định kết quả có đáng tin hay không.
- [Docker documentation: building best practices](https://docs.docker.com/build/building/best-practices/): base được ghim, các layer và image nhỏ.
- [GNU Make manual](https://www.gnu.org/software/make/manual/make.html): target và target giả (phony).
- [pytest documentation](https://docs.pytest.org/en/stable/): fixture, skip và marker mà bộ nghiệm thu dùng.
- **Luyện tập thêm:** [TidyBot (arXiv 2305.05658)](https://arxiv.org/abs/2305.05658) là ví dụ tốt về một bài báo hệ thống có tác vụ rõ, baseline và hạn chế; đọc nó như mẫu cho báo cáo của bạn.
