---
{"title": "Cột mốc capstone 8: tích hợp toàn hệ thống, khoảng cách sim-to-real và đánh giá trung thực", "summary": "Chạy toàn bộ stack CoreBot Tidy trên hàng trăm episode có seed, so với một twin bị nhiễu loạn được niêm phong của chính trình mô phỏng của bạn, và báo cáo tỉ lệ thành công bằng cận Wilson, kiểm định ghép cặp, khoảng bootstrap và bảng phân loại lỗi.", "objectives": ["Chạy benchmark toàn hệ thống trên các episode có seed và ghi mọi kết quả kèm nguyên nhân gốc.", "Báo cáo tỉ lệ thành công bằng cận Wilson và so sánh hai điều kiện bằng kiểm định chính xác ghép cặp và khoảng bootstrap.", "Ước lượng khoảng cách sim-to-real so với một twin bị nhiễu loạn được niêm phong và thử thu hẹp một phần bằng system identification.", "Giữ seed dùng để chỉnh tách biệt với seed đánh giá và nêu giả thuyết trước khi chạy thí nghiệm.", "Xây ngân sách lỗi từ bảng phân loại lỗi và quyết định sửa gì trước."]}
---

## Vì sao điều này quan trọng

Đến nay mỗi cột mốc có một đơn vị bạn kiểm thử riêng được: vòng điều khiển bánh, bộ lọc, bộ lập kế hoạch, cú gắp. CAP08 là nơi các mảnh ghép gặp nhau, và cũng là nơi xuất hiện sai lầm nghiên cứu phổ biến nhất: một con số trông đẹp chỉ vì cách đo. Một robot "chạy tốt" trên chính các seed bạn đã chỉnh, báo cáo thành một phần trăm duy nhất, chứng minh rất ít. Một robot được đánh giá trên seed mới, với khoảng tin cậy, so sánh ghép cặp với chính các ablation của nó và một bảng lý do thất bại, cho người lạ (và chính bạn sau này) biết nên tin điều gì.

Cột mốc này cũng đặt câu hỏi mọi dự án robot rồi sẽ gặp: trình mô phỏng cách thực tế bao xa? Bạn không có robot thật (tầng phần cứng là tùy chọn), nên bạn xây thứ gần nhất: một **twin được niêm phong**, bản sao của thế giới của bạn với các nhiễu loạn ẩn. Bạn được chạy thí nghiệm trên nó, nhưng không được đọc tham số của nó. Bạn mất bao nhiêu thành công trên twin, và lấy lại được bao nhiêu bằng system identification, là một mô hình nhỏ và trung thực của việc chuyển từ sim sang thực. Nó dùng lại ý tưởng của [S09 Sim2Real](/lessons/S09), thống kê của [RS03 Statistical Inference](/lessons/RS03) và phân tích lỗi của [RS05 Error Analysis](/lessons/RS05).

## Trực giác

![Kiến trúc hệ thống CoreBot Tidy: cảm biến và thế giới MuJoCo, đế firmware-in-the-loop, ước lượng, lập bản đồ và kế hoạch, nhận thức, thao tác và kỹ năng học, lớp tác vụ ngôn ngữ, bộ giám sát an toàn và harness đánh giá](/lesson-figures/CAP-architecture.svg)

*Dải tô bóng ở dưới cùng của kiến trúc là harness đánh giá. CAP08 là cột mốc đầu tiên chủ yếu sống ở đó.*

Hãy coi harness là một phòng thí nghiệm, không phải buổi demo. Trong demo bạn chọn lần chạy đẹp. Trong phòng thí nghiệm bạn cố định quy trình trước, chạy, và báo cáo điều đã xảy ra kể cả phần đáng xấu hổ. Ba thói quen tạo nên khác biệt:

- **Seed là đơn vị thí nghiệm.** Mỗi episode là một seed (bố cục cảnh, tư thế vật, câu lệnh). Seed dùng để chỉnh không bao giờ xuất hiện trong đánh giá.
- **Mọi con số có một khoảng.** Tỉ lệ thành công là ước lượng từ mẫu hữu hạn; khoảng cho biết nó có thể dịch chuyển bao nhiêu nếu chạy lại với seed mới.
- **Mọi thất bại có một nguyên nhân.** "Nó fail" không phải dữ liệu. `GRASP_SLIP` khác `LOCALISATION` cho bạn biết mười giờ tới đi đâu.

Cột mốc này dùng công sức từ [CAP02](/lessons/CAP02) (liên kết firmware và hiệu chỉnh odometry, bạn sẽ làm lại với twin), [CAP06](/lessons/CAP06) (kỹ năng học và domain randomisation mà bạn ablate) và [CAP07](/lessons/CAP07) (parser và bộ giám sát an toàn có vi phạm phải bằng 0). Các cột mốc trước ([CAP03](/lessons/CAP03) đến [CAP05](/lessons/CAP05)) cung cấp bộ ước lượng, bộ lập kế hoạch và pipeline gắp mà giờ bạn chạy từ đầu đến cuối.

## Lý thuyết và suy dẫn

Đây là các ghi chú tích hợp: vài công thức và giao diện mà CAP08 phụ thuộc, mỗi cái kèm chủ đề dạy nó.

![Sơ đồ: cùng một stack chạy trên thế giới nominal và trên twin niêm phong có nhiễu loạn ẩn; episode được ghi vào episodes.jsonl, metrics.py tính lại cận Wilson, kiểm định ghép cặp và bảng lỗi, còn seed chỉnh được giữ tách khỏi seed đánh giá](/lesson-figures/CAP08.svg)

### 1. Tỉ lệ thành công với khoảng Wilson ([RS03](/lessons/RS03))

Với $k$ lần thành công trong $n$ episode độc lập, ước lượng điểm là $\hat p=k/n$. Khoảng điểm Wilson tại $z=1.96$ là
$$\frac{\hat p+\frac{z^2}{2n}\ \pm\ z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}.$$
Nó nằm trong $[0,1]$ và ứng xử tốt với $n$ nhỏ và $\hat p$ gần 0 hoặc 1, khác với công thức sách giáo khoa $\hat p\pm z\sqrt{\hat p(1-\hat p)/n}$. Gate của cột mốc này viết trên cận **dưới**, vì cận dưới là khẳng định bạn bảo vệ được. Quy tắc ngón tay cái để lập kế hoạch: nửa độ rộng tại $\hat p=0.8$ khoảng $1.96\sqrt{0.16/n}$, nên $n\approx 246$ episode cho $\pm0.05$ và $n\approx 61$ cho $\pm0.10$.

### 2. So sánh ghép cặp hai điều kiện (McNemar, [RS03](/lessons/RS03))

Các ablation dùng lại cùng seed với lần chạy nominal, nên kết quả được ghép cặp. Đếm các seed bất đồng: $b$ = nominal thành công và ablation thất bại, $c$ = ngược lại. Dưới giả thuyết không (không có hiệu ứng), mỗi seed bất đồng rơi về hai phía với xác suất như nhau, nên $b\sim\text{Binomial}(b+c,\tfrac12)$ và p-value chính xác hai phía là
$$p=\min\Bigl(1,\ 2\sum_{i=0}^{\min(b,c)}\binom{b+c}{i}2^{-(b+c)}\Bigr).$$
Các seed mà cả hai đều thành công hoặc đều thất bại không mang thông tin về sự khác biệt. Hãy báo cả hiệu ứng, $(b-c)/n_{\text{pairs}}$ tính bằng điểm phần trăm, vì một hiệu ứng nhỏ vẫn có thể có ý nghĩa còn hiệu ứng lớn có thể không có ý nghĩa ở $n=30$.

### 3. Nhiều so sánh (kiểm định bội, [RS03](/lessons/RS03))

Bốn ablation nghĩa là bốn phép kiểm định. Ở mức 0.05 mỗi phép, xác suất có ít nhất một báo động giả dưới giả thuyết không là $1-0.95^4\approx0.19$. Thủ tục Holm so p-value nhỏ nhất với $\alpha/4$, p-value kế tiếp với $\alpha/3$, v.v., dừng ở lần trượt đầu tiên. Hãy nêu trong báo cáo bạn đã chạy bao nhiêu so sánh.

### 4. Khoảng bootstrap cho một trung bình ([RS03](/lessons/RS03))

Với đại lượng không có công thức gọn (thời lượng trung vị, sai số cross-track trung bình), lấy mẫu lại các episode có hoàn lại $B=2000$ lần, tính thống kê mỗi lần, và lấy phân vị 2.5 % và 97.5 %. Nó giả định các episode là các lần bốc hoán đổi được, chính vì vậy seed phải độc lập.

### 5. Ước lượng khoảng cách sim-to-real ([S09](/lessons/S09))

Gọi $p_{\text{nom}}$ và $p_{\text{twin}}$ là tỉ lệ thành công trên hai thế giới. Khoảng cách là $\Delta=p_{\text{nom}}-p_{\text{twin}}$. Với mẫu độc lập dùng khoảng hỗn hợp Newcombe xây từ hai cận Wilson $(\ell_i,u_i)$:
$$\Bigl[\Delta-\sqrt{(\hat p_1-\ell_1)^2+(u_2-\hat p_2)^2},\ \ \Delta+\sqrt{(u_1-\hat p_1)^2+(\hat p_2-\ell_2)^2}\Bigr].$$
Nếu bạn chạy cùng seed trên cả hai thế giới có thể dùng McNemar. Hãy nhớ twin là gì: một họ nhiễu loạn cụ thể (bán kính bánh, track width, khối lượng, ma sát, độ trễ camera, nhiễu lidar), không phải "thực tế". Ước lượng cho bạn biết stack nhạy thế nào với các sai số loại này và cỡ này.

### 6. Ngân sách lỗi và độ trễ ([RS05](/lessons/RS05), [CAP02](/lessons/CAP02))

Với số lỗi $F_j$ theo từng nguyên nhân gốc và $N$ episode, sửa hoàn toàn nguyên nhân $j$ sẽ nâng thành công lên tối đa $(k+F_j)/N$. Sắp xếp nguyên nhân theo $F_j$ và xử lý cột cao nhất trước. Với độ trễ, trung vị từng khâu không cộng được chính xác: trung vị của tổng không bằng tổng các trung vị. Hãy log thời gian từng khâu cho mỗi episode và tính trung vị của **tổng** thời gian từ nhận thức đến lệnh; bài kiểm thử chấp nhận giới hạn 100 ms (ở 0.5 m/s robot đi 5 cm trong thời gian đó).

## Ví dụ có lời giải

Mọi giá trị dưới đây là minh họa, không đến từ một lần chạy thật.

Một lần chạy tham chiếu tạo ra 120 episode nominal (seed 1000 đến 1119), 80 episode twin (seed 1120 đến 1199) và bốn ablation 30 seed ghép cặp (seed 1000 đến 1029). Việc chỉnh chỉ dùng seed 0 đến 99.

| Split | n | Thành công | Tỉ lệ | Wilson 95 % |
|---|---|---|---|---|
| nominal | 120 | 94 | 0.783 | [0.701, 0.848] |
| twin (trước hiệu chỉnh lại) | 80 | 46 | 0.575 | [0.466, 0.677] |

Gate nominal đạt: tỉ lệ ít nhất 0.70 và cận dưới 0.701 ít nhất 0.60. Khoảng cách là $\Delta=0.208$ với khoảng Newcombe $[0.077,0.335]$: có thật, nhưng độ lớn còn bất định (mẫu twin nhỏ).

| Ablation (30 seed ghép cặp) | Tỉ lệ | $b$ | $c$ | p chính xác | hiệu ứng (pp) |
|---|---|---|---|---|---|
| không cập nhật landmark | 0.40 | 15 | 2 | 0.0023 | +43.3 |
| không có chính sách DR | 0.60 | 11 | 4 | 0.118 | +23.3 |
| gắp bằng script thay vì học | 0.73 | 7 | 4 | 0.549 | +10.0 |
| tắt bộ giám sát an toàn | 0.67 | 8 | 3 | 0.227 | +16.7 |

Với Holm trên bốn phép kiểm định, p-value nhỏ nhất phải thắng $0.05/4=0.0125$: chỉ "không landmark" thắng ($4\times0.0023=0.0094$ sau hiệu chỉnh). Câu trung thực cho báo cáo là: "Bỏ cập nhật landmark làm giảm thành công khoảng 43 điểm (p chính xác ghép cặp = 0.0023, Holm 0.009); chúng tôi không tìm thấy bằng chứng đáng tin cho ba hiệu ứng còn lại ở n = 30."

Các lần thất bại trong 108 episode thất bại của mọi lần chạy (26 nominal + 34 twin + 48 trong bốn ablation): `GRASP_SLIP` 36, `DETECTION` 22, `PLACE_MISS` 14, `LOCALISATION` 13, `NAV_TIMEOUT` 9, `PARSE` 5, `OTHER` 5, `SAFETY_STOP` 3, `FIRMWARE_LINK` 1. Tổng đếm bằng 108 và mọi lần thất bại đều có nguyên nhân. Hiệu chỉnh lại bán kính bánh và track width trên twin giảm RMSE cross-track từ 0.112 m xuống 0.071 m, cải thiện tương đối 37 %, đạt tiêu chí 25 %. Độ trễ trung vị từ nhận thức đến lệnh: 71 ms.

Có thể tính lại các số trên bằng script này (chạy với thư viện chuẩn cộng `evalkit.py`):

```python
# Stdlib only. Needs evalkit.py from CAP01 on the path (src/corebot/evalkit.py in your repo).
from corebot.evalkit import wilson_interval, paired_mcnemar

k, n = 94, 120                       # illustrative nominal result
lo, hi = wilson_interval(k, n)
print(f"nominal  {k}/{n} = {k / n:.3f}  Wilson95 [{lo:.3f}, {hi:.3f}]")
kt, nt = 46, 80                      # illustrative twin result
lot, hit = wilson_interval(kt, nt)
print(f"twin     {kt}/{nt} = {kt / nt:.3f}  Wilson95 [{lot:.3f}, {hit:.3f}]")
print(f"no_landmarks paired: b=15 c=2  p = {paired_mcnemar(15, 2):.4f}")
print(f"no_supervisor paired: b=8 c=3  p = {paired_mcnemar(8, 3):.4f}")
# Holm correction for the four ablation p-values, smallest first
ps = sorted([paired_mcnemar(15, 2), 0.118, 0.227, 0.549])
adj = [min(1.0, (len(ps) - i) * p) for i, p in enumerate(ps)]
print("Holm step-down thresholds 0.05/4, 0.05/3, 0.05/2, 0.05/1; first adjusted p =", round(adj[0], 4))
```

## Bài tập

1. **(Dễ)** *Cận Wilson.* Lần thử nghiệm đầu cho 27 thành công trong 30 episode. Tính khoảng Wilson 95 % và giải thích vì sao bạn không chỉ báo cáo ước lượng điểm 0.90. Nó đã thỏa gate cận dưới 0.60 chưa?
2. **(Dễ)** *Lập kế hoạch n.* Bạn kỳ vọng tỉ lệ thành công gần 0.8. Cần bao nhiêu episode để nửa độ rộng Wilson khoảng 0.10, và khoảng 0.05? Vì sao cột mốc yêu cầu ít nhất 100 episode nominal?
3. **(Trung bình)** *Kiểm định ghép cặp.* Trong 10 seed bất đồng, lần chạy nominal thắng 9 và lần ablation thắng 1 ($b=9$, $c=1$). Tính p-value McNemar chính xác. Lặp lại với $b=6$, $c=2$ và giải thích các seed đồng nhất đóng góp gì.
4. **(Trung bình)** *So sánh bội.* Bốn ablation của bạn cho p-value 0.0023, 0.118, 0.227 và 0.549. Cái nào qua được Holm ở 0.05? Bạn sẽ viết gì về ba cái còn lại?
5. **(Trung bình)** *Vệ sinh seed.* Bạn chỉnh ngưỡng trên seed 0-99 và báo cáo 84 thành công trên chính 100 seed đó. Một đồng nghiệp chạy lại 100 seed mới và được 72. Con số đầu sai ở đâu, và bạn sẽ thiết lập quy trình thế nào để vấn đề không thể xảy ra?
6. **(Trung bình)** *Diễn giải khoảng cách.* Nominal 94/120 và twin 46/80. Dùng khoảng Newcombe $[0.077,0.335]$, nêu điều bạn có thể và không thể khẳng định về khoảng cách sim-to-real của robot. Nêu một lý do khoảng cách thật có thể lớn hơn khoảng cách twin.
7. **(Trung bình)** *Ngân sách độ trễ.* Trung vị theo từng episode của các khâu là nhận thức 38 ms, lập kế hoạch 21 ms, đóng gói lệnh và liên kết 9 ms. Một đồng nghiệp nói ngân sách "cộng lại 68 ms nên đạt giới hạn 100 ms". Lập luận sai ở đâu, và chính xác cần log và kiểm thử gì?
8. **(Khó)** *Ngân sách lỗi.* Trong 26 episode nominal thất bại, 9 là `GRASP_SLIP`. Ước lượng tỉ lệ thành công tốt nhất nếu loại hẳn nguyên nhân đó, cho khoảng Wilson của tỉ lệ lỗi gắp, và quyết định nên dành thêm 10 giờ cho gắp hay cho nhận diện (6 lỗi).
9. **(Khó)** *Kết quả hiệu chỉnh lại.* Sau sysid trên twin, RMSE cross-track giảm từ 0.112 m xuống 0.095 m. Tiêu chí 25 % của cột mốc có đạt không? Thay vào đó phải nộp gì, và điều gì bị cấm khi cố cải thiện?
10. **(Khó, mini-project)** *Thiết kế nghiên cứu ablation.* Viết `docs/experiments.md` trước khi chạy ablation: với mỗi trong bốn ablation, một giả thuyết có hướng và độ lớn dự đoán, seed, n, phép kiểm định, cách hiệu chỉnh so sánh bội, và một kết quả khiến bạn nghi ngờ chính pipeline (không phải robot).

## Cài đặt tham khảo

Đây là khung của `bench/metrics.py`, module tính lại mọi con số được báo cáo từ log episode. Hãy cài đặt nó bằng thư viện chuẩn và `evalkit.py` (xem [CAP01](/lessons/CAP01) để biết cách tải). Bài kiểm thử nghiệm thu import `CAUSES`, `compute_metrics` và `seed_overlap` từ nó.

```python
"""bench/metrics.py: recompute every reported number from runs/final/episodes.jsonl.

Nothing in the report or in metrics.json may come from anywhere else.
"""
from __future__ import annotations

from typing import Iterable, Sequence

CAUSES = ("NAV_TIMEOUT", "LOCALISATION", "DETECTION", "GRASP_SLIP", "PLACE_MISS",
          "PARSE", "SAFETY_STOP", "FIRMWARE_LINK", "OTHER")


def by_split(episodes: Iterable[dict], split: str) -> list[dict]:
    """Episodes whose "split" equals `split` (nominal, twin, twin_recal, abl:<name>), in file order."""
    raise NotImplementedError


def split_stats(eps: Sequence[dict]) -> dict:
    """n, successes, rate, wilson_lo, wilson_hi (95 %), median_duration_s of one split."""
    raise NotImplementedError


def failure_table(eps: Sequence[dict]) -> dict[str, int]:
    """Counts per failure_cause over the FAILED episodes only. A missing cause is counted under None."""
    raise NotImplementedError


def paired_counts(a_eps: Sequence[dict], b_eps: Sequence[dict]) -> tuple[int, int, int]:
    """(b, c, pairs) over the seeds present in both lists.
    b = A succeeded and B failed, c = A failed and B succeeded. Concordant pairs carry no information."""
    raise NotImplementedError


def newcombe_diff(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Newcombe hybrid-score 95 % CI for p1 - p2 from the two Wilson intervals (independent samples)."""
    raise NotImplementedError


def compute_metrics(episodes: Sequence[dict]) -> dict:
    """The dict stored as runs/final/metrics.json (see "Expected output" for the keys)."""
    raise NotImplementedError


def seed_overlap(tuning_seeds: Iterable[int], episodes: Sequence[dict]) -> list[int]:
    """Seeds used for tuning that also appear in a nominal or twin evaluation episode. Must be empty."""
    raise NotImplementedError
```

## Thực hành độc lập

### Mục tiêu
Chạy toàn bộ stack CoreBot Tidy từ đầu đến cuối trên các episode có seed, đánh giá nó trên thế giới nominal và trên một twin nhiễu loạn được niêm phong, ablate bốn quyết định thiết kế bằng thống kê đúng đắn, phân loại mọi thất bại, và qua bộ kiểm thử nghiệm thu CAP08. Trọng số trong điểm tốt nghiệp: 14 trên 100.

### Thiết lập
Làm việc trong `~/corebot-capstone` (tạo ở [CAP01](/lessons/CAP01)). Python 3.11 trở lên, thư viện chuẩn cộng các gói bạn đã ghim trong `pyproject.toml`; `corebot/evalkit.py` từ CAP01 phải có sẵn. Hãy tính ngân sách tính toán: 120 + 80 + 120 episode ablation là khoảng 320 episode; nếu mỗi episode mất 30 s thời gian thực thì cần khoảng 3 giờ, nên hãy chạy nền và ghi log ra đĩa. Đường rút gọn (60 nominal + 40 twin) dành cho máy chậm nhưng khi đó gate 100 và 60 episode sẽ trượt; hãy lập kế hoạch cho phù hợp.

```bash
cd ~/corebot-capstone
mkdir -p bench runs/final tests/acceptance
# bench/metrics.py       <- the reference skeleton above, implemented
# bench/run_bench.py     <- your episode runner (starter stubs below)
python -m pytest -q tests/acceptance/test_cap08.py
python bench/metrics.py            # recomputes runs/final/metrics.json from episodes.jsonl
```

### Nhiệm vụ
1. **Kế hoạch seed.** Viết `configs/bench.yaml` và `runs/final/tuning_seeds.txt` (seed 0-99). Seed đánh giá: nominal 1000-1119, twin 1120-1199; ablation dùng lại 30 seed nominal đầu. Lớp câu lệnh: gắp đơn, hai vật, có vật gây nhiễu, rải trên 5 cảnh.
2. **Bộ chạy.** `bench/run_bench.py` chạy một episode có seed mỗi lần gọi, ghi một dòng JSON với các trường của `EpisodeRecord`, và phân loại mỗi thất bại bằng một trong chín nguyên nhân từ các sự kiện đã log.
3. **Metric.** Cài đặt `bench/metrics.py`; `python bench/metrics.py` ghi `runs/final/metrics.json` và phải tái tạo y hệt khi chạy lại.
4. **Twin niêm phong.** Tạo `models/corebot_real.xml` bằng một bộ sinh làm nhiễu bán kính bánh (khoảng +3 %), track width (khoảng -2 %), khối lượng (+15 %), ma sát (-25 %), độ trễ camera (+30 ms) và nhiễu lidar (x2). Dùng `--secret-seed $RANDOM` một lần; không in, log hay commit seed; không bao giờ mở file XML tạo ra.
5. **Thí nghiệm twin và hiệu chỉnh lại.** Chạy step test và lái hình vuông trên twin, nhận dạng lại bán kính bánh, track width và ma sát (phương pháp của [CAP02](/lessons/CAP02)), cập nhật tham số nominal, và chạy lại split twin thành `twin_recal`. Viết `runs/final/twin_recal.json`.
6. **Ablation.** Bốn ablation trên 30 seed ghép cặp mỗi cái: không cập nhật landmark, không có chính sách DR, gắp bằng script thay vì học, tắt bộ giám sát.
7. **Đăng ký trước.** Commit `docs/experiments.md` (giả thuyết, dự đoán, kiểm định) trước lần chạy ablation đầu tiên; chỉnh sửa sau đó chỉ qua commit mới nói rõ lý do.
8. **Phân tích lỗi.** Viết `docs/error_budget.md`: bảng lỗi, mức lợi tốt nhất cho hai nguyên nhân hàng đầu, quyết định của bạn và bằng chứng.

### Code khởi đầu
`make_real_twin.py` được cho sẵn vì mục tiêu của bài tập là đánh giá, không phải bộ sinh. Nó không in gì về nhiễu loạn; hãy chỉnh các mẫu thuộc tính trong `apply` cho khớp với MJCF của bạn (friction là bộ ba trong MuJoCo, nên hãy nhân số đầu tiên).

```python
"""Sealed twin generator: writes models/corebot_real.xml and prints NOTHING about the perturbation.

Usage: python make_real_twin.py --secret-seed $RANDOM     (do not log, print or commit the seed)
"""
import argparse
import json
import random
import re

# nominal size of each perturbation (the lesson tells you these); the actual factor is jittered
# by +-30 % so that you can identify the twin but not read it off.
NOMINAL = {"wheel_radius": +0.03, "track_width": -0.02, "mass": +0.15, "friction": -0.25,
           "camera_latency_s": 0.030, "lidar_noise_scale": 2.0}


def draw(secret_seed: int) -> dict:
    """Perturbation factors for one twin; deterministic in the secret seed."""
    rng = random.Random(secret_seed)
    out = {}
    for key, nominal in NOMINAL.items():
        jitter = rng.uniform(0.7, 1.3)
        out[key] = nominal * jitter if key != "lidar_noise_scale" else 1 + (nominal - 1) * jitter
    return out


def apply(xml_text: str, p: dict) -> str:
    """Scale the attributes your MJCF uses. Adapt the patterns to your own model file."""
    def scale(attr, factor, text):
        pattern = re.compile(rf'({attr}=")([-0-9.eE]+)(")')
        return pattern.sub(lambda m: f"{m.group(1)}{float(m.group(2)) * factor:.6g}{m.group(3)}", text)
    xml_text = scale("wheel_radius", 1 + p["wheel_radius"], xml_text)
    xml_text = scale("track_width", 1 + p["track_width"], xml_text)
    xml_text = scale("mass", 1 + p["mass"], xml_text)
    xml_text = scale("friction", 1 + p["friction"], xml_text)
    return xml_text


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret-seed", type=int, required=True)
    ap.add_argument("--src", default="models/corebot.xml")
    ap.add_argument("--dst", default="models/corebot_real.xml")
    a = ap.parse_args()
    params = draw(a.secret_seed)
    with open(a.src) as f:
        text = apply(f.read(), params)
    with open(a.dst, "w") as f:
        f.write(text)
    # Runtime knobs (latency, lidar noise) are read from a file that only the bench loads:
    with open(a.dst + ".runtime.json", "w") as f:
        json.dump({"camera_latency_s": params["camera_latency_s"],
                   "lidar_noise_scale": params["lidar_noise_scale"]}, f)
```

Bộ chạy và bước sysid là các khung giao diện để bạn điền bằng stack của riêng mình.

```python
"""bench/run_bench.py and bench/sysid_twin.py: interface stubs (fill in with your own stack)."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict


@dataclass
class EpisodeRecord:
    seed: int
    split: str                      # "nominal" | "twin" | "twin_recal" | "abl:<name>"
    instruction_class: str          # "single" | "two_object" | "distractor"
    success: bool
    failure_cause: str | None       # one of metrics.CAUSES when success is False, else None
    duration_s: float               # simulated time
    safety_violations: int
    latency_ms: dict                # {"perception": .., "plan": .., "perception_to_command": ..}
    git_hash: str


def run_episode(seed: int, split: str, config: dict) -> EpisodeRecord:
    """Run ONE seeded end-to-end episode (parse -> navigate -> grasp -> place) and classify its outcome.

    Rules: no wall-clock randomness; the failure cause is decided from logged events, not guessed;
    a twin split loads models/corebot_real.xml but never reads its parameters.
    """
    raise NotImplementedError


def run_split(seeds: range, split: str, config: dict, out_path: str) -> None:
    """Append one JSON line per episode to out_path (create parent dirs, never overwrite old lines)."""
    raise NotImplementedError


def recalibrate(twin_episodes: list[dict], nominal_params: dict) -> dict:
    """System identification on EXPERIMENTS run on the twin (step tests, square drives).
    Returns new wheel_radius, track_width and friction estimates. May not read the twin's XML."""
    raise NotImplementedError


if __name__ == "__main__":
    print(json.dumps(asdict(EpisodeRecord(0, "nominal", "single", True, None, 91.2, 0,
                                          {"perception": 38.0, "plan": 21.0, "perception_to_command": 70.0}, "a1b2c3d"))))
```

### Kiểm thử
`tests/acceptance/test_cap08.py` chỉ đọc các artefact dưới `runs/final/`. Các kiểm tra đánh dấu G là gate (một gate trượt giữ cột mốc ở trạng thái "đang làm"). Các ngưỡng là giá trị khởi đầu tạm thời (xem lý do trong kế hoạch); hãy siết chặt chúng khi bạn đã có lần chạy tham chiếu của riêng mình.

- Toàn vẹn (G): ít nhất 100 episode nominal và 60 twin, vì $n\ge100$ cho nửa độ rộng Wilson khoảng 0.08 tại $p=0.8$; seed duy nhất trong mỗi split; tính lại khớp với `metrics.json`.
- Thành công nominal (G): tỉ lệ ít nhất 0.70 và cận dưới Wilson ít nhất 0.60, vì một stack không làm nổi 70 % tác vụ gắp đơn thì chưa được tích hợp; thời lượng trung vị tối đa 180 s.
- Không vi phạm an toàn (G): mọi vi phạm tốc độ vùng người hay e-stop không chốt là lỗi thiết kế, không phải thống kê. Hãy nhớ con số này nghĩa là gì: bộ giám sát bảo vệ một mô phỏng, nên không có vi phạm ở đây là kết quả dạy học về phân tích nguy cơ và tiêm lỗi, không phải chứng nhận an toàn.
- Thành công twin ít nhất 0.50 và hiệu chỉnh lại: twin cố ý khắc nghiệt; hoặc cải thiện tương đối ít nhất 25 % (RMSE cross-track hoặc thành công) hoặc một kết quả âm tường minh kèm CI.
- Ablation: ít nhất bốn cái với $n\ge30$ (đủ cặp để phát hiện hiệu ứng lớn khoảng 40 điểm) và ít nhất một mục McNemar.
- Phân loại: ít nhất 90 % lần thất bại có nguyên nhân thuộc danh sách cố định và tổng đếm bằng số lần thất bại.
- Độ trễ: trung vị từ nhận thức đến lệnh tối đa 100 ms.
- Vệ sinh seed: không có seed chỉnh nào xuất hiện trong đánh giá nominal hay twin.

```python
"""CAP08 acceptance tests. Gates (G) are the checks that must pass to graduate."""
import json
import pathlib
import re

from bench.metrics import CAUSES, compute_metrics, seed_overlap
from corebot.evalkit import load_episodes, wilson_interval

RUNS = pathlib.Path("runs/final")
REQUIRED = {"seed", "split", "success", "failure_cause", "duration_s",
            "safety_violations", "latency_ms", "git_hash"}


def _eps():
    return load_episodes(RUNS / "episodes.jsonl")


def _split(name):
    return [e for e in _eps() if e["split"] == name]


def test_artefact_integrity():                                    # G
    eps = _eps()
    nominal, twin = _split("nominal"), _split("twin")
    assert len(nominal) >= 100 and len(twin) >= 60
    for name in {e["split"] for e in eps}:
        seeds = [e["seed"] for e in eps if e["split"] == name]
        assert len(seeds) == len(set(seeds)), f"duplicate seeds in {name}"
    assert all(REQUIRED <= set(e) for e in eps)
    assert all(re.fullmatch(r"[0-9a-f]{7,40}", e["git_hash"]) for e in eps)
    stored = json.loads((RUNS / "metrics.json").read_text())
    fresh = json.loads(json.dumps(compute_metrics(eps)))      # same float formatting as the file

    def same(a, b):
        if isinstance(a, dict):
            return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
        if isinstance(a, list):
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if isinstance(a, float) or isinstance(b, float):
            return abs(a - b) < 1e-9
        return a == b
    assert same(stored, fresh), "metrics.json does not match a recomputation from the logs"


def test_nominal_success():                                       # G
    nominal = _split("nominal")
    k = sum(e["success"] for e in nominal)
    lo, _ = wilson_interval(k, len(nominal))
    assert k / len(nominal) >= 0.70 and lo >= 0.60
    durations = sorted(e["duration_s"] for e in nominal)
    assert durations[len(durations) // 2] <= 180.0


def test_zero_safety_violations():                                # G
    assert sum(e["safety_violations"] for e in _eps()) == 0


def test_twin_success_and_recalibration():
    twin = _split("twin")
    assert sum(e["success"] for e in twin) / len(twin) >= 0.50
    r = json.loads((RUNS / "twin_recal.json").read_text())
    if r.get("negative_result"):
        assert {"ci_lo", "ci_hi"} <= set(r), "a negative result must carry its CI"
    else:
        before, after = r["before"]["cross_track_rmse_m"], r["after"]["cross_track_rmse_m"]
        better_rmse = (before - after) / before >= 0.25
        better_succ = (r["after"]["success"] - r["before"]["success"]) / r["before"]["success"] >= 0.25
        assert better_rmse or better_succ


def test_ablations():
    m = json.loads((RUNS / "metrics.json").read_text())["ablations"]
    assert len(m) >= 4
    for name, a in m.items():
        assert a["n"] >= 30, name
        assert 0.0 <= a["wilson_lo"] <= a["wilson_hi"] <= 1.0, name
    assert any("mcnemar_p" in a and "effect_pp" in a for a in m.values())
    assert {"no_landmarks", "no_dr_policy", "scripted_grasp", "no_supervisor"} <= set(m)


def test_failure_taxonomy():
    eps = _eps()
    fails = [e for e in eps if not e["success"]]
    labelled = [e for e in fails if e["failure_cause"] in CAUSES]
    assert len(labelled) / len(fails) >= 0.90
    m = json.loads((RUNS / "metrics.json").read_text())["failures"]
    assert sum(m["by_cause"].values()) == m["total"] == len(fails)


def test_latency_budget():
    nominal = sorted(e["latency_ms"]["perception_to_command"] for e in _split("nominal"))
    assert nominal[len(nominal) // 2] <= 100.0


def test_seed_hygiene():
    tuning = [int(x) for x in (RUNS / "tuning_seeds.txt").read_text().split()]
    assert seed_overlap(tuning, _eps()) == []
```

### Kết quả mong đợi
Với bộ artefact đầy đủ:

```
........                                                                 [100%]
8 passed in 0.9s
```

`runs/final/metrics.json` rút gọn của lần chạy minh họa (các khóa bạn phải tạo; giá trị của bạn sẽ khác):

```json
{
  "nominal": {
    "n": 120,
    "successes": 94,
    "rate": 0.783,
    "wilson_lo": 0.701,
    "wilson_hi": 0.848,
    "median_duration_s": 118.4
  },
  "twin": {
    "n": 80,
    "successes": 46,
    "rate": 0.575,
    "wilson_lo": 0.466,
    "wilson_hi": 0.677
  },
  "gap": {
    "difference": 0.208,
    "ci_lo": 0.077,
    "ci_hi": 0.335
  },
  "safety_violations": 0,
  "failures": {
    "total": 108,
    "by_cause": {
      "GRASP_SLIP": 36,
      "DETECTION": 22,
      "PLACE_MISS": 14,
      "LOCALISATION": 13,
      "NAV_TIMEOUT": 9,
      "PARSE": 5,
      "OTHER": 5,
      "SAFETY_STOP": 3,
      "FIRMWARE_LINK": 1
    }
  },
  "latency_perception_to_command_ms_median": 71.0,
  "ablations": {
    "no_landmarks": {
      "n": 30,
      "rate": 0.4,
      "wilson_lo": 0.246,
      "wilson_hi": 0.577,
      "b": 15,
      "c": 2,
      "mcnemar_p": 0.00235,
      "effect_pp": 43.3
    }
  }
}
```

Khi chưa có artefact, các test fail với `FileNotFoundError` hoặc `NotImplementedError`; đó là trạng thái xuất phát có chủ ý.

### Thử thách mở rộng
Thêm điều kiện thứ năm nhắm vào nguyên nhân thất bại lớn nhất của bạn và chứng minh bằng kiểm định ghép cặp xem nó có giúp không. Nâng cao: thay đoạn chờ theo script trong bộ giám sát bằng bộ ước lượng khoảng cách người học được và chứng minh tỉ lệ dừng nhầm vẫn tối đa 5 %. Tầng phần cứng tùy chọn (không điểm nào phụ thuộc vào nó; kèm bảng thật so với sim nó có thể là stretch cho Distinction của CAP09, và không bao giờ thay thế một gate trượt): phát lại step test CAP02 trên đế ESP32 thật so với đế mô phỏng và thêm bảng thật so với sim (thời gian xác lập, vọt lố, sai số xác lập); với SO-101 thật, chạy 20 lần gắp và báo cáo khoảng Wilson bên cạnh kết quả mô phỏng. Giữ bánh xe hở mặt đất trong các lần chạy đầu, dùng điện áp tối đa 12 V, có cầu chì trên đường pin và tuân theo quy tắc pin và điện của HW03 (không sạc hay để pin lithium không giám sát).

### Thực hành với thư viện
Đối chiếu các hàm của bạn với SciPy và statsmodels. Cận Wilson nên khớp đến khoảng $10^{-4}$ (bạn dùng $z=1.96$, SciPy dùng phân vị chính xác), và p-value McNemar chính xác nên khớp nhiều chữ số.

```python
# Needs: pip install scipy statsmodels   (cross-check of your own bench/metrics.py)
import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar

# 1. Wilson interval: SciPy gives the same numbers as evalkit.wilson_interval (z = 1.96 vs 1.959964: 1e-4 apart)
ci = stats.binomtest(94, 120).proportion_ci(confidence_level=0.95, method="wilson")
print("wilson  :", round(ci.low, 3), round(ci.high, 3))           # about 0.701 0.848

# 2. Exact McNemar on the discordant counts b=15, c=2 (table rows: A ok/fail, columns: B ok/fail)
table = [[0, 15], [2, 0]]            # only the off-diagonal cells enter the exact test
print("mcnemar :", mcnemar(table, exact=True).pvalue)                # about 0.00235

# 3. Percentile bootstrap of the mean success over 30 paired seeds
outcomes = np.array([1] * 22 + [0] * 8)
res = stats.bootstrap((outcomes,), np.mean, confidence_level=0.95, n_resamples=5000,
                      method="percentile", random_state=0)
print("bootstrap:", res.confidence_interval)
```

## Kiểm chứng

Kiểm tra số bằng tay trước khi tin code: Wilson 94/120 khoảng [0.70, 0.85]; McNemar với $b=15$, $c=2$ là $2\sum_{i\le2}\binom{17}{i}/2^{17}=2\cdot154/131072=0.0023$. Chạy `python bench/metrics.py` hai lần và diff đầu ra; sửa tay một dòng episode và xác nhận test toàn vẹn fail. Chạy cùng một seed hai lần và so kết quả (tính xác định từ [CAP01](/lessons/CAP01)). Xác nhận `tuning_seeds.txt` và seed đánh giá không giao nhau bằng một phép giao tập hợp một dòng. Điểm số: CAP08 có trọng số 14 trên 100 trong điểm tốt nghiệp (60 % kiểm tra tự động, 40 % rubric của người: thiết kế thí nghiệm, tính trung thực thống kê, phân tích lỗi, hiểu biết về điều mô phỏng không cho thấy). Gate: toàn vẹn artefact, thành công nominal, không vi phạm an toàn. Tốt nghiệp đòi hỏi không vi phạm an toàn ở đây, mọi gate đạt, và mọi cột mốc ít nhất 60.

## Lỗi thường gặp

- Chỉnh trên seed đánh giá nên tỉ lệ báo cáo bị lạc quan.
- Báo cáo trung bình không có khoảng, hoặc so 30 episode với 120 như thể ngang nhau.
- Chọn lần chạy tốt nhất trong nhiều lần ("chọn seed") rồi gọi đó là kết quả.
- Tính không xác định không được log: seed theo đồng hồ, duyệt set không có thứ tự, huấn luyện đa luồng làm đổi chính sách.
- Quá khớp với twin bằng cách đọc tham số của nó hoặc chỉnh ngưỡng trên seed đánh giá twin.
- Bảng phân loại lỗi mà mọi thứ là `OTHER`, nên ngân sách lỗi không nói gì.
- Khai thác lỗi của trình mô phỏng (vật xuyên thành thùng) và tính là thành công; hãy xem video vài lần thành công để kiểm tra.
- Chạy nhiều kiểm định và chỉ báo cái có ý nghĩa (không hiệu chỉnh, không nêu số phép kiểm định).
- Coi twin là thực tế: nó ước lượng độ nhạy với một họ nhiễu loạn, không hơn.

## Phương án khác và đánh đổi

Wilson là mặc định tốt; khoảng Clopper-Pearson bảo thủ (rộng hơn, đảm bảo độ phủ), khoảng Agresti-Coull là xấp xỉ đơn giản. Kiểm định hoán vị trên kết quả ghép cặp cho cùng đáp án với McNemar chính xác với kết quả nhị phân nhưng còn dùng được cho metric liên tục. Hậu nghiệm Beta-Binomial kiểu Bayes cho khoảng tin cậy Bayes và câu "xác suất A tốt hơn B" trực quan; dùng nó nếu bạn nêu được prior. Thay vì twin ẩn, bạn có thể dùng dải domain randomisation làm bài stress test (CAP06), rẻ hơn nhưng bạn thấy được các nhiễu loạn. Robot thật là phép thử đúng; tầng phần cứng là cách rẻ để nếm thử. Nhiều episode hơn thắng thống kê khéo: nếu hai điều kiện chồng lấn, hãy chạy thêm seed trước khi tranh luận về phương pháp.

## Vận dụng và ghi nhớ

Cột mốc này chuẩn bị cho [CAP09](/lessons/CAP09), nơi mọi con số trong báo cáo phải đến từ `metrics.json` bạn xây ở đây, và nó áp dụng [S09](/lessons/S09), [RS03](/lessons/RS03) và [RS05](/lessons/RS05) vào hệ thống của chính bạn. Ngoài capstone, cùng quy trình đó (seed cố định, tập kiểm thử giữ riêng, khoảng tin cậy, so sánh ghép cặp, phân loại lỗi) đánh giá được bất kỳ mô hình hay robot nào. Câu hỏi ôn:

1. Viết công thức khoảng Wilson từ trí nhớ và nói vì sao dùng cận dưới làm gate.
2. Kiểm định McNemar ghép cặp dùng những seed nào, và bỏ qua seed nào?
3. Vì sao trung vị của tổng độ trễ khác tổng các trung vị?
4. Bạn được làm gì với twin niêm phong, và không được làm gì?
5. Liệt kê chín nguyên nhân lỗi và nói nguyên nhân nào bạn đoán sẽ chi phối stack của mình, trước khi nhìn dữ liệu.

## Đáp án bài tập

1. Wilson cho 27/30: $[0.744,0.965]$. Ước lượng điểm che giấu đầu dưới gần 0.74; với $n=30$ tỉ lệ thật dễ là 0.8. Cận dưới 0.744 trên 0.60, nhưng gate cần ít nhất 100 episode, nên lần thử 30 episode chỉ cho biết bạn đang đi đúng hướng.
2. Nửa độ rộng $1.96\sqrt{0.16/n}$: $\pm0.10$ cần $n\approx61$ ($1.96^2\cdot0.16/0.01=61.5$), $\pm0.05$ cần $n\approx246$. Ít nhất 100 episode nominal cho nửa độ rộng khoảng 0.08 tại $p=0.8$, một thỏa hiệp giữa độ chính xác và ngân sách tính toán.
3. $b=9$, $c=1$: $n=10$, $p=2\,(1+10)/1024=0.0215$: có ý nghĩa ở 0.05. $b=6$, $c=2$: $n=8$, $p=2\,(1+8+28)/256=0.289$: không có bằng chứng. Các seed đồng nhất (cùng thành công hoặc cùng thất bại) không nói gì điều kiện nào tốt hơn; chúng chỉ cho thấy các seed đó dễ hay khó.
4. Sắp xếp: 0.0023 so với $0.05/4=0.0125$: đạt; 0.118 so với $0.05/3=0.0167$: trượt, dừng. Chỉ cái đầu qua. Báo ba cái còn lại là "chưa có bằng chứng đáng tin ở n = 30", không phải "không có hiệu ứng": với 30 cặp bạn chỉ phát hiện được hiệu ứng lớn; hãy nêu độ lớn hiệu ứng và CI.
5. 84/100 được đo trên các seed đã định hình ngưỡng, nên chệch lên (việc chỉnh hấp thụ nhiễu của chính các cảnh đó). 72/100 trên seed mới (Wilson $[0.625,0.799]$) là con số trung thực. Quy trình: ghi danh sách seed chỉnh và seed đánh giá ra file từ đầu, cấm seed đánh giá trong code chỉnh, và thêm test `seed_overlap`.
6. Bạn có thể khẳng định rằng, với họ nhiễu loạn này và các n này, thành công giảm khoảng 21 điểm và khoảng hợp lý là 8 đến 34 điểm. Bạn không thể khẳng định robot thật mất 21 điểm. Khoảng cách thật có thể lớn hơn vì có những hiệu ứng không mô hình hóa mà twin không có tham số cho (backlash, lực kéo cáp, ánh sáng, độ mềm tiếp xúc, miếng đệm gắp trượt), và vì thế giới thật làm nhiễu mọi thứ cùng lúc chứ không trong các dải bạn đã dự đoán.
7. Tổng các trung vị từng khâu không phải trung vị của tổng, và các khâu có tương quan (một frame chậm thì chậm ở mọi nơi). Độ trễ liên kết hay hàng đợi cũng có thể thiếu. Hãy log mốc thời gian từng khâu và tổng theo từng episode (hoặc frame), kiểm thử trung vị của tổng tối đa 100 ms, và xem cả phân vị 95 vì các đột biến thỉnh thoảng quan trọng với an toàn.
8. Tốt nhất $(94+9)/120=0.858$ (Wilson 95 % $[0.785,0.910]$ nếu thật sự xảy ra). Tỉ lệ lỗi gắp là $9/26=0.35$, Wilson $[0.19,0.54]$, khá rộng: dữ liệu nói gắp có thể là cột lớn nhất nhưng chưa vượt nhận diện (6/26) một cách chắc chắn. Hãy dành giờ cho gắp nếu nguyên nhân đã hiểu (phân tích trượt từ bảng phân loại), nhưng kiểm tra lại sau khi sửa với seed mới; ngân sách là kim chỉ nam, không phải bằng chứng.
9. Cải thiện $(0.112-0.095)/0.112=15\%<25\%$: không đạt. Nộp kết quả âm bằng văn bản: `negative_result: true` với CI của chênh lệch RMSE (bootstrap trên episode) trong `twin_recal.json`, và giải thích điều gì giới hạn việc nhận dạng (ví dụ ma sát được kích thích kém bởi các thí nghiệm của bạn). Bị cấm: đọc XML hay tham số của twin, hoặc chỉnh trên seed đánh giá twin.
10. Một tài liệu tốt nêu, với mỗi ablation, hướng và độ lớn dự đoán (ví dụ "không landmark: thấp hơn 30 đến 50 điểm vì heading trôi"), cố định n = 30 seed ghép cặp từ 1000-1029, kiểm định McNemar chính xác với Holm trên bốn, và kết quả nghi ngờ pipeline: ví dụ "nếu ablation tắt bộ giám sát làm đổi thành công hơn 20 điểm trong khi không có hazard nào xảy ra, bộ giám sát của tôi đang can thiệp vào vận hành bình thường, hoặc công tắc ablation bị hỏng".

## Đọc thêm

- [Henderson et al., Deep Reinforcement Learning that Matters](https://arxiv.org/abs/1709.06560): seed, phương sai và báo cáo trung thực.
- [Tobin et al., Domain Randomization](https://arxiv.org/abs/1703.06907): vì sao làm nhiễu trình mô phỏng giúp chuyển giao.
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval): so sánh Wilson, Clopper-Pearson và các khoảng khác.
- [McNemar's test (Wikipedia)](https://en.wikipedia.org/wiki/McNemar%27s_test): kiểm định ghép cặp cho kết quả nhị phân.
- [Bootstrapping (statistics) (Wikipedia)](https://en.wikipedia.org/wiki/Bootstrapping_(statistics)): khoảng phân vị.
- [MuJoCo documentation: the simulation loop](https://mujoco.readthedocs.io/en/stable/programming/simulation.html): tính xác định và bước mô phỏng.
- **Luyện tập thêm:** [TidyBot (arXiv 2305.05658)](https://arxiv.org/abs/2305.05658) báo cáo một hệ thống dọn dẹp nhà được đánh giá qua nhiều lần thử.
