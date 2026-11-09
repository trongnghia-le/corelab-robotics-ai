---
{"title": "Cột mốc capstone 6: kỹ năng gắp học được với domain randomisation và thống kê trung thực", "summary": "Bọc primitive gắp thành môi trường Gymnasium, huấn luyện PPO và chính sách behaviour cloning trên CPU, ngẫu nhiên hóa vật lý, rồi đánh giá trên seed giữ riêng bằng khoảng Wilson và bootstrap so với kỹ năng viết tay.", "objectives": ["Bọc primitive gắp thành môi trường Gymnasium với observation, action và reward có tài liệu.", "Huấn luyện PPO và chính sách behaviour cloning trên CPU trong ngân sách bước và thời gian đã nêu.", "Áp dụng domain randomisation và đánh giá trên seed và nhiễu loạn giữ riêng (held-out).", "Báo cáo tỉ lệ thành công kèm cận Wilson và bootstrap, so sánh trung thực với kỹ năng viết tay.", "Cắm kỹ năng học được vào giao diện GraspSkill phía sau một lớp bọc an toàn."]}
---

## Vì sao điều này quan trọng

Đến hết CAP05, robot của bạn gắp bằng một pipeline viết tay: nhận thức, tính động học ngược, đóng gripper. Pipeline đó dễ đọc và dễ kiểm thử, nhưng mọi tư thế vật, giá trị ma sát và độ trễ mà nó được chỉnh cho đều là giả định. Cột mốc này đặt một câu hỏi khác: một kỹ năng **học được** có thể làm primitive reach-and-grasp tốt như kỹ năng viết tay không, và quan trọng hơn, bạn có **chứng minh được bằng những con số mà bạn dám bảo vệ trước người phản biện** không?

Bản thân việc học là phần dễ: PPO trên một tác vụ nhỏ dựa trên state huấn luyện được trên CPU laptop trong chưa đầy một giờ. Phần khó là kỹ thuật xung quanh: một reward bạn giải thích được, một lần chạy lặp lại được từng bit, một khoảng randomisation bạn biện minh được, đánh giá trên các seed mà policy chưa từng thấy, và khoảng tin cậy thay cho một con số may mắn. Những thói quen này phân biệt một video demo với một kết quả. Bạn cũng sẽ sớm gặp một sự thật khó chịu: kỹ năng học được thành công 90 % trên simulator danh định có thể tụt còn 60 % khi ma sát đổi 40 %. Domain randomisation là công cụ rẻ nhất để chống lại điều đó, và đo hiệu quả của nó một cách trung thực (kể cả khi nó không giúp gì) mới là sản phẩm thật.

Đây là cột mốc 6 trong 9, chiếm **12 trên 100 điểm** của điểm tốt nghiệp. Nó dựa trực tiếp vào CAP05 (kỹ năng gắp viết tay là baseline và là bộ sinh demo của bạn), và dùng lại các ý từ [RL10 PPO](/lessons/RL10), [RL12 Thiết kế thí nghiệm RL](/lessons/RL12), [RL16 Domain randomisation](/lessons/RL16), [RL17 Imitation learning](/lessons/RL17), [E07 Chính sách robot dựa trên bắt chước](/lessons/E07) và [ML07 Đánh giá mô hình](/lessons/ML07).

## Trực giác

Hãy coi kỹ năng học được là **một cách cài đặt mới của một giao diện bạn đã có**. CAP05 đã định nghĩa giao diện kỹ năng `ScriptedGraspSkill.execute(goal, env) -> GraspResult` (gọi là giao diện `GraspSkill` trong bài này). Mọi thứ phía trên (bộ lập kế hoạch tác vụ của CAP07, benchmark toàn hệ thống của CAP08) không quan tâm kết quả đến từ động học ngược hay từ mạng nơ-ron. Việc của bạn ở CAP06 là tạo cài đặt thứ hai, huấn luyện nó, và đo nó so với cài đặt thứ nhất trong cùng điều kiện.

![System architecture of CoreBot Tidy: simulator, firmware-in-the-loop base, estimation, mapping and planning, perception, manipulation and learned skills, the language task layer and the safety supervisor](/lesson-figures/CAP-architecture.svg)

*Trong kiến trúc, kỹ năng học được nằm ở band 4 cạnh khối manipulation viết tay, sau cùng giao diện `GraspSkill`. Cột mốc này điền vào ô "Learned skill (PPO / BC policy)".*

Ba ý mang cả cột mốc.

**1. Giữ phần học thật nhỏ.** Bạn không học thị giác, điều hướng hay cả tác vụ. Bạn học một *primitive*: từ một vector state (độ lệch end-effector tới vật, vị trí vật trong frame gốc cánh tay, state khớp, độ mở gripper), xuất một bước Cartesian nhỏ và một lệnh gripper. Bài toán nhỏ huấn luyện trong vài phút, và lỗi chẩn đoán được. Policy dựa trên thị giác (CNN vào, action ra) là mục tiêu mở rộng, không phải lõi.

**2. Hai cách học cùng một primitive.** *Reinforcement learning* (PPO) khám phá hành vi bằng thử và sai với reward bạn viết. *Imitation learning* (behaviour cloning, BC) sao chép kỹ năng viết tay từ demonstration, nên không cần reward nhưng lỗi tích lũy khi policy trôi khỏi các state mà demonstration bao phủ. Chạy cả hai trên cùng môi trường và so sánh là lõi giáo dục của cột mốc.

**3. Ngẫu nhiên hóa những gì bạn không thể biết.** Simulator có một giá trị khối lượng và một giá trị ma sát; thế giới thật (và tập test giữ riêng) có nhiều giá trị. Huấn luyện trên một *phân phối* thế giới làm policy bền với cả phân phối đó, với giá là bài toán học khó hơn. Ngẫu nhiên quá ít thì không chuyển giao được; quá nhiều thì tác vụ thành bất khả thi và không học được gì.

![Learned grasp skill: a domain randomiser feeds a Gymnasium grasp environment and a PPO or behaviour-cloning policy during training; a separate evaluation harness on held-out seeds and perturbations produces Wilson bounds and a comparison with the scripted skill](/lesson-figures/CAP06.svg)

*Huấn luyện và đánh giá là hai pipeline riêng với seed riêng. Bất cứ điều gì bạn chỉnh sau khi nhìn kết quả đánh giá đều là huấn luyện.*

## Lý thuyết và suy dẫn

Đây là các ghi chú tích hợp: vài công thức, giao diện và quy tắc quan trọng ở đây, mỗi mục gắn với chủ đề nơi bạn đã học.

### 1. Môi trường là một hợp đồng ([RL09](/lessons/RL09), [RL10](/lessons/RL10), Gymnasium)

Môi trường Gymnasium có `reset(seed=...) -> (obs, info)` và `step(action) -> (obs, reward, terminated, truncated, info)`. Hãy chốt và ghi trong `docs/reward_design.md` năm thứ: vector observation (kèm đơn vị và thang chuẩn hóa), vector action (1.0 nghĩa là gì về vật lý), độ dài episode, termination so với truncation (giới hạn 60 bước là *truncation*, không phải thất bại của trạng thái tác vụ; value bootstrap của PPO xử lý hai loại khác nhau), và các số hạng reward. Mọi tính ngẫu nhiên phải đi ra từ `seed` truyền vào `reset`, dùng một `numpy.random.Generator`; nếu không thì không kết quả nào lặp lại được.

### 2. Reward shaping và các cái bẫy ([RL10](/lessons/RL10), [RL12](/lessons/RL12))

Một reward reach-and-grasp điển hình là tổng các số hạng:
$$r_t=-w_d\,\lVert x_{ee}-x_{obj}\rVert-w_a\lVert a_t\rVert^2-w_t+w_g\,\mathbb 1[\text{grasp}]+w_\ell\,\mathbb 1[\text{lift}].$$
Số hạng khoảng cách làm cho việc học *khả thi* (tín hiệu dày). Các phần thưởng một lần định nghĩa *thành công* là gì. Chi phí mỗi bước $w_t$ khiến kết thúc sớm tốt hơn chờ đợi. Lỗi kinh điển là **reward hacking**: nếu mỗi bước đều trả một lượng dương khi ở gần vật (ví dụ $e^{-10d}$), lơ lửng 60 bước có thể kiếm nhiều hơn một cú gắp thật. Hãy viết reward dưới dạng chi phí, thêm một phạt thời gian nhỏ, và luôn xem *hành vi*, không chỉ return.

### 3. Chiết khấu và giới hạn thời gian ([RL09](/lessons/RL09))

Với hệ số chiết khấu $\gamma$ thì chân trời hiệu dụng khoảng $1/(1-\gamma)$ bước. Với episode 60 bước, $\gamma=0.98$ (chân trời khoảng 50) là điểm khởi đầu hợp lý: phần thưởng nhấc vật vẫn thấy được từ bước đầu. $\gamma=0.9$ (chân trời 10) làm phần thưởng nhấc gần như vô hình lúc tiếp cận.

### 4. Domain randomisation như một phân phối ([RL16](/lessons/RL16), Tobin et al.)

Huấn luyện lấy mẫu một nhiễu loạn $\xi\sim p(\xi)$ ở mỗi `reset`: hệ số khối lượng, hệ số ma sát, độ trễ action, và với thị giác là ánh sáng và rung camera. Policy cực đại hóa $\mathbb E_{\xi}[J(\pi,\xi)]$. Quy tắc thiết kế: (a) thế giới danh định phải nằm trong khoảng; (b) khoảng phải hợp lý về vật lý; (c) ghi $\xi$ đã lấy vào mọi bản ghi episode; (d) đánh giá trên tập nhiễu loạn *giữ riêng* và trên tập danh định, và báo cáo cả hai. Độ trễ action $d$ ms ở tần số điều khiển 10 Hz nghĩa là đệm lệnh $\lceil d/100\rceil$ bước, cài đặt bằng hàng đợi FIFO trong `step`.

### 5. Imitation learning và lỗi tích lũy ([RL17](/lessons/RL17), [E07](/lessons/E07))

Behaviour cloning cực tiểu hóa $\mathbb E_{(s,a)\sim d_{\text{expert}}}\lVert\pi(s)-a\rVert^2$. Lúc test, policy ghé thăm các state từ phân phối *của chính nó*. Ross, Gordon và Bagnell (bài báo DAgger) chỉ ra rằng với lỗi mỗi bước $\epsilon$ và chân trời $T$, chi phí trường hợp xấu nhất tăng như $\epsilon T^2$ cho cloning so với $\epsilon T$ cho các phương pháp huấn luyện trên phân phối state của chính learner. Hệ quả thực tế: chia train và validation theo **demonstration**, không theo timestep (các timestep kề nhau gây rò rỉ); demo và policy phải dùng **cùng không gian action**; và MSE giữ riêng là chưa đủ, bạn phải chạy policy vòng kín.

### 6. Thống kê bạn phải báo cáo ([ML07](/lessons/ML07), [RL12](/lessons/RL12))

Với $k$ thành công trong $n$ episode độc lập, **khoảng Wilson** 95 % là
$$\frac{\hat p+\frac{z^2}{2n}\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}},\qquad z=1.96.$$
Nó cư xử hợp lý gần 0 và 1 và với $n$ nhỏ (xấp xỉ chuẩn thì không). Quy tắc mà mọi bài test nghiệm thu trong capstone dùng: seed đánh giá là `range(1000, 1000+N)`, seed huấn luyện nhỏ hơn 1000; tuyên bố về tỉ lệ thành công dùng cận **dưới**; với đường cong học qua các seed huấn luyện thì báo từng seed, trung bình và khoảng bootstrap, không bao giờ báo seed tốt nhất ([Henderson et al.](https://arxiv.org/abs/1709.06560) cho thấy riêng thói quen này đã làm đổi nhiều kết luận đã công bố). `evalkit.wilson_interval` và `evalkit.bootstrap_ci` (từ CAP01) cài đặt cả hai.

### 7. Lớp bọc an toàn

Một policy học được có thể xuất bất cứ thứ gì. Hãy bọc nó: kẹp action về $[-1,1]$, đổi sang bước Cartesian tối đa 1.5 cm, chiếu đích vào một **hộp workspace** (trên mặt bàn, trong tầm với của SO-101), và đếm (không bao giờ nuốt im lặng) mọi vi phạm mà guard phải sửa. Bài test nghiệm thu đòi hỏi không có vi phạm *chưa được sửa*; hãy ghi cả các lần sửa, vì policy cần guard ở mọi bước thì chưa học được tác vụ.

## Ví dụ có lời giải

Đây là **giá trị minh họa** cho hình dạng của một bộ artefact đạt yêu cầu, không phải đầu ra của một lần chạy thật. Số của bạn sẽ khác; *hình dạng* của bằng chứng mới là điều quan trọng.

### Ngân sách, đánh giá danh định và có nhiễu loạn, behaviour cloning và so sánh ghép cặp

**Đề bài.** Một nghiên cứu PPO dùng 4 môi trường vector hóa ở khoảng 366 bước môi trường mỗi giây (CPU laptop, một luồng torch), với giới hạn 2 M bước và 2 h. Năm seed PPO, mỗi seed được đánh giá trên 100 episode (seed 1000-1499) với 93, 95, 92, 96 và 94 thành công. Một policy có domain randomisation (DR) và một policy chỉ huấn luyện danh định được so sánh trên 100 episode có nhiễu loạn (khối lượng 0.7-1.3, ma sát 0.6-1.4, trễ +40 ms, seed 1500-1599): 81 và 58 thành công. Một policy behaviour cloning (BC) có MSE giữ riêng 0.011 so với 0.093 của baseline trung bình hằng (tỉ lệ giới hạn 0.2) và 71/100 thành công vòng kín; phép quét số demo cho MSE 0.041, 0.026, 0.017, 0.011 với 50, 100, 200, 500 demonstration. Kỹ năng viết tay CAP05 đạt 97/100 trên cùng 100 seed.

- (a) Một lần chạy 1.5 M bước mất 4100 s có nằm trong ngân sách không?
- (b) Tóm tắt đánh giá danh định (trung bình, nhỏ nhất, tỉ lệ gộp và khoảng Wilson 95 % của nó).
- (c) Tính khoảng Wilson của 81/100 và 58/100 và $z$ hai tỉ lệ cho hiệu; có thể tuyên bố gì?
- (d) Kiểm tra tỉ lệ BC và phép quét số demo, và cho khoảng Wilson của 71/100.
- (e) So sánh ghép cặp với kỹ năng viết tay (97/100) cần gì, và đã có thể nói gì?

**Lời giải.**

1. *Thông lượng.* $1.5\times10^6/4100=365.9\approx366$ bước/s, khớp với tốc độ đã nêu. $4100\ \text{s}/3600=1.14$ h. Cả $1.5\,\text{M}\le2\,\text{M}$ bước lẫn $1.14\,\text{h}\le2$ h đều thỏa; cùng tốc độ này, 2 M bước cần $2\times10^6/366=5465$ s $=1.52$ h.
2. *Đánh giá danh định.* Trung bình $=(93+95+92+96+94)/5=94\ \%$, nhỏ nhất 92 %, gộp $470/500=0.940$.
3. *Khoảng Wilson.* Với $k/n$ và $z=1.96$: $\tilde p=(\hat p+z^2/2n)/(1+z^2/n)$, nửa độ rộng $z\sqrt{\hat p(1-\hat p)/n+z^2/4n^2}/(1+z^2/n)$. Với $470/500$ ra $[0.916,\,0.958]$. Để so sánh, $27/30$ cho $[0.744,\,0.965]$: ít episode hơn khoảng 17 lần, khoảng rộng hơn khoảng năm lần (0.221 so với 0.042).
4. *Khoảng có nhiễu loạn.* $81/100\to[0.722,\,0.875]$ và $58/100\to[0.482,\,0.672]$. Hai khoảng không chồng nhau ($0.722>0.672$).
5. *Kiểm định $z$ hai tỉ lệ.* Gộp $\bar p=(81+58)/200=0.695$; $\text{SE}=\sqrt{\bar p(1-\bar p)\cdot2/100}=\sqrt{0.695\cdot0.305\cdot0.02}=0.0651$; $z=(0.81-0.58)/0.0651=3.53\approx3.5$. Điều đó ủng hộ "DR giúp ích trên tập nhiễu loạn này", với **một** seed huấn luyện cho mỗi nhánh; một báo cáo cẩn thận nói rõ điều này và thêm seed nếu tuyên bố quan trọng.
6. *Tỉ lệ BC.* $0.011/0.093=0.118\approx0.12\le0.2$: đạt. Phép quét 0.041, 0.026, 0.017, 0.011 giảm ở mọi bước, nên đơn điệu như mong đợi.
7. *BC vòng kín.* $71/100$ có khoảng Wilson $[0.615,\,0.790]$: thấp hơn PPO (gộp 0.940) và thấp hơn kỹ năng viết tay (0.97). Đây là kết quả bình thường của bắt chước không có hiệu chỉnh, và đúng điều mà phép so sánh nên cho thấy.
8. *So sánh ghép cặp.* Hai tỉ lệ riêng rẽ bỏ qua việc cả hai kỹ năng đối mặt cùng seed. Gọi $b$ là số episode chỉ kỹ năng viết tay thành công và $c$ là số episode chỉ PPO thành công; phép kiểm định chính xác (`evalkit.paired_mcnemar`) chỉ dùng $b$ và $c$. Giả định thêm ở đây (bản gốc không cho số cặp): nhánh PPO là seed huấn luyện 0 (93/100) trên cùng 100 seed. Khi đó $b-c=97-93=4$. $b+c$ nhỏ nhất có thể là 4 ($b=4$, $c=0$), cho $p=2\cdot(1/2)^4=0.125>0.05$; mọi $b+c$ lớn hơn với cùng hiệu cho $p$ lớn hơn (ví dụ $b=6$, $c=2$: $p=0.289$). Vậy khoảng cách 4 điểm trên 100 seed ghép cặp không bao giờ có ý nghĩa thống kê, và báo cáo nên nói hai kỹ năng không được tách ra.

```python
from corebot.evalkit import wilson_interval        # CAP01: python3 evalkit.py also runs a self-test

for k, n in [(27, 30), (470, 500), (81, 100), (58, 100)]:
    lo, hi = wilson_interval(k, n)
    print(f"{k}/{n}: point {k / n:.3f}, 95% Wilson [{lo:.3f}, {hi:.3f}]")
```


Đầu ra (minh họa, tính từ công thức trên):

```text
27/30: point 0.900, 95% Wilson [0.744, 0.965]
470/500: point 0.940, 95% Wilson [0.916, 0.958]
81/100: point 0.810, 95% Wilson [0.722, 0.875]
58/100: point 0.580, 95% Wilson [0.482, 0.672]
```


| Seed huấn luyện | Thành công / 100 |
|---|---|
| 0 | 93 |
| 1 | 95 |
| 2 | 92 |
| 3 | 96 |
| 4 | 94 |

| Policy | Thành công / 100 | Wilson 95 % |
|---|---|---|
| PPO có domain randomisation | 81 | [0.722, 0.875] |
| PPO không có (chỉ huấn luyện danh định) | 58 | [0.482, 0.672] |

**Kiểm tra.** Bốn dòng Wilson trong đầu ra của mã khớp công thức tay ở bước 3 (script dùng cùng công thức, và các giá trị trên đã được tính lại độc lập đến ba chữ số thập phân). Kiểm định $z$ nhất quán với kiểm định khoảng: đầu dưới 0.722 của khoảng DR vượt đầu trên 0.672 của khoảng kia 0.050, và $z=3.5$ tương ứng $p$ hai phía $\approx0.0004$. Cận kiểm tra cho (e): phép kiểm định ghép cặp chính xác không thể cho $p<0.05$ trừ khi $b+c\ge6$ với $c=0$ (ví dụ $b=6$, $c=0$ cho $p=0.031$), điều này cần khoảng cách ít nhất 6 điểm.

**Rút ra.** Báo cáo mọi tỉ lệ kèm khoảng Wilson và so sánh policy trên cùng seed; một khoảng, một phép kiểm định và số seed huấn luyện được đếm trung thực nói được điều mà ước lượng điểm không nói được.

## Bài tập

1. **(Dễ)** Một bạn học báo cáo 27 thành công trong 30 episode giữ riêng. Tính khoảng Wilson 95 % và quyết định tuyên bố "thành công ít nhất 80 %" có được ủng hộ không.
2. **(Dễ)** Huấn luyện chạy 366 bước môi trường mỗi giây. 2 M bước mất bao lâu, và có nằm trong giới hạn 2 h kèm chỗ cho đánh giá không?
3. **(Dễ)** Một reward trả $e^{-10d}$ mỗi bước theo khoảng cách $d$ từ end-effector tới vật, cộng thưởng một lần 12 khi nhấc vật. Một policy lơ lửng ở $d=2$ cm suốt 60 bước. Tính return của nó và giải thích vì sao nó có thể thắng việc gắp thật.
4. **(Trung bình)** Huấn luyện ngẫu nhiên hóa khối lượng trong $[0.8,1.2]$, ma sát trong $[0.7,1.3]$ và trễ trong $\{0,10,20,30\}$ ms. Tập giữ riêng dùng khối lượng $[0.7,1.3]$, ma sát $[0.6,1.4]$ và trễ đúng 40 ms. Bao nhiêu phần episode giữ riêng nằm hoàn toàn trong khoảng huấn luyện? Bạn sẽ đổi gì?
5. **(Trung bình)** Policy DR: 81/100 trên tập nhiễu loạn. Policy không DR: 58/100. Mỗi nhánh một seed huấn luyện. Kết luận nào có cơ sở và kết luận nào không?
6. **(Trung bình)** Một policy BC có MSE giữ riêng 0.011 (rất tốt) nhưng chỉ thành công vòng kín 71 %. Nêu hai lời giải thích và một cách sửa cho mỗi lời giải thích.
7. **(Trung bình)** Demo của bạn lưu đích vị trí khớp, nhưng policy PPO xuất delta end-effector. Mô tả một bài test rẻ tiền bắt được sự không khớp này trước khi huấn luyện.
8. **(Khó)** Cổng tái lập thất bại: hai lần chạy giống hệt nhau khác nhau $3\times10^{-3}$ ở return đánh giá được ghi. Liệt kê các nguyên nhân có khả năng theo thứ tự bạn sẽ kiểm tra.
9. **(Khó)** Năm seed PPO cho 96, 61, 90, 88 và 20 thành công trên 100. Tính trung bình, quyết định cổng học (trung bình ít nhất 90 %, nhỏ nhất ít nhất 80 %) có đạt không, và nói một báo cáo có trách nhiệm gồm những gì.
10. **(Khó, dự án nhỏ)** Thiết kế và chạy phép quét số demo (50, 100, 200, 500 demonstration): bạn ghi lại những đại lượng nào, đưa vào baseline và trường hợp biên nào, và quan sát nào khiến bạn bác bỏ "nhiều demo hơn luôn tốt hơn"?

## Cài đặt tham khảo

Module cần viết đầu tiên là `learning/envs.py`: nó là hợp đồng mà mọi thứ khác phụ thuộc. Dưới đây là bộ khung; các docstring chứa những quyết định bạn phải đưa ra và ghi lại.

```python
# src/corebot/learning/envs.py  (skeleton: fill in the NotImplementedError bodies)
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np

from corebot.learning.randomize import DomainRandomizer, Perturbation


@dataclass(frozen=True)
class RewardWeights:
    """Every term is documented in docs/reward_design.md. Change them there first."""
    reach: float = 1.0        # -w * ||ee - obj||  (dense, bounded by workspace size)
    grasp: float = 2.0        # one-off bonus when both fingers touch the object
    lift: float = 10.0        # one-off bonus when the object is >= 5 cm above the table
    action: float = 0.01      # -w * ||a||^2  (discourages jitter)
    time: float = 0.005       # -w per step (discourages hovering near the object)


class GraspReachEnv(gym.Env):
    """State-based reach-and-grasp primitive for the SO-101 (the 'learned skill').

    Observation (float32, shape (17,), roughly normalised to [-1, 1]):
        ee_pos - obj_pos (3), obj_pos in arm_base frame (3), joint positions (5),
        joint velocities (5, scaled), gripper opening (1)
    Action (float32, shape (4,), in [-1, 1]): ee delta xyz (x 1.5 cm per step) and gripper command.
    Episode: 60 steps at 10 Hz control (10 physics substeps of 1 ms each), truncated at 60.
    Success: object >= 5 cm above the table and still held 10 steps later.
    """

    metadata = {"render_modes": []}

    def __init__(self, randomizer: DomainRandomizer | None = None,
                 weights: RewardWeights = RewardWeights(), max_steps: int = 60) -> None:
        super().__init__()
        raise NotImplementedError("load models/corebot.xml, build spaces, store the randomizer")

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        """Seed ALL randomness from `seed` (np.random.Generator), sample a Perturbation,
        apply it to the model, place the object, return (obs, info)."""
        raise NotImplementedError

    def step(self, action: np.ndarray):
        """Clip the action, pass it through the action-delay queue and the workspace guard
        (never leave the safe box, never command below the table), integrate physics,
        compute reward terms, return (obs, reward, terminated, truncated, info).
        info must contain: success, joint_limit_violations, table_collisions."""
        raise NotImplementedError

    def _obs(self) -> np.ndarray:
        raise NotImplementedError

    def _apply(self, p: Perturbation) -> None:
        """Write p into model.body_mass / model.geom_friction before the episode starts."""
        raise NotImplementedError
```

Điền theo thứ tự: `_obs` (in một observation và kiểm tra đơn vị bằng tay), `reset` (seed, nhiễu loạn, đặt vật; gọi hai lần với cùng seed và assert observation bằng nhau), `step` chưa có reward (policy viết tay phải chạm tới vật), rồi từng số hạng reward một.

## Thực hành độc lập

### Mục tiêu
Tạo ra một kỹ năng reach-and-grasp học được đạt bộ nghiệm thu CAP06: huấn luyện PPO tái lập được trên CPU, thành công danh định trung bình ít nhất 90 %, thành công bền trên tập nhiễu loạn giữ riêng, một policy behaviour cloning được so với baseline hằng, không vi phạm guard, và một `GraspSkill` thay thế trực tiếp được. Ghi lại những gì các con số **không** cho thấy.

### Thiết lập
Làm việc trong `~/corebot-capstone` (tạo ở CAP01) trên một nhánh mới. Mọi thứ chạy trên CPU. Môi trường dựa trên state không cần render; biến thể dựa trên thị giác cần `MUJOCO_GL=egl` (hoặc `osmesa`, chậm hơn). Hãy ghim các phiên bản bạn dùng trong `pyproject.toml`; các dòng dưới đây là ví dụ cần đối chiếu với bản phát hành hiện tại vào ngày bạn làm.

```bash
cd ~/corebot-capstone
git checkout -b cap06-learned-skills
python3 -m venv .venv && . .venv/bin/activate
pip install -e .                             # then pip install the pins (example, check on the day):
#   mujoco>=3.2,<4  gymnasium>=0.29,<2  stable-baselines3>=2.3,<3  torch (CPU wheel)  numpy  pytest
export MUJOCO_GL=egl                         # osmesa if EGL is missing (state-based env needs no rendering)
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1   # single thread: needed for the reproducibility gate
mkdir -p runs/cap06 docs
python -m corebot.learning.train_ppo --seed 0 --steps 20000 --dr off --out runs/cap06/repro_a.json
python -m corebot.learning.train_ppo --seed 0 --steps 20000 --dr off --out runs/cap06/repro_b.json
pytest -q tests/acceptance/test_cap06.py
```

Gợi ý thời gian chạy: PPO với 4 môi trường thường chạy vài trăm bước mỗi giây trên CPU laptop, nên dự trù 1 đến 2 giờ cho cả nghiên cứu 5 seed (chạy các seed lần lượt, không song song, nếu bạn muốn số đo wall-clock sạch). Nếu lần chạy 20 k bước đầu tiên không học gì cả, hãy gỡ lỗi môi trường bằng policy viết tay trước khi đụng tới siêu tham số.

### Nhiệm vụ
1. **`learning/envs.py`**: `GraspReachEnv` như trên, cùng `docs/reward_design.md` (observation, action, từng số hạng reward và lý do, termination/truncation).
2. **`learning/randomize.py`**: `DomainRandomizer.sample(rng)` cho khối lượng, ma sát và độ trễ (thêm ánh sáng và rung camera cho biến thể thị giác). Ghi các giá trị đã lấy vào mọi episode.
3. **`learning/train_ppo.py`**: PPO của riêng bạn từ RL10 hoặc Stable-Baselines3 (xem phần Thực hành với thư viện). CLI như đã nêu, một luồng, seed nhỏ hơn 1000 để huấn luyện, đánh giá trên seed từ 1000 trở lên. Xuất `runs/cap06/ppo_seed{0..4}.json`, `repro_a.json`, `repro_b.json`, và công tắc `--dr on|off`.
4. **`learning/bc.py`**: 500 demonstration viết tay, MLP, chia theo demonstration, quét số demo 50/100/200/500, đánh giá vòng kín trên 100 seed. Xuất `bc_summary.json`.
5. **Đánh giá**: `eval_nominal.jsonl` và `eval_perturbed.jsonl` (mỗi episode một JSON: policy, seed, success, giá trị nhiễu loạn, bộ đếm vi phạm), `summary.json` (số đếm và khoảng Wilson), `meta.json` (số bước, wall clock, thiết bị).
6. **`learning/skill.py`**: `LearnedGraspSkill` cài đặt cùng chữ ký `execute(goal, env)` với `ScriptedGraspSkill` (giao diện của CAP05), được bọc bởi guard an toàn.
7. **Model card** (`docs/model_card_cap06.md`, một trang): mục đích sử dụng, dữ liệu/seed huấn luyện, khoảng DR, chỉ số kèm khoảng tin cậy, các trường hợp lỗi đã biết, và những gì *chưa* được kiểm thử.
8. **Bài học rút ra** (một trang) cho báo cáo CAP09: điều bất ngờ lớn nhất và việc đầu tiên bạn sẽ đổi.

### Code khởi đầu

```python
# src/corebot/learning/randomize.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Perturbation:
    mass_scale: float
    friction_scale: float
    delay_ms: int
    light_gain: float = 1.0       # vision only (CAP05 pipeline), unused by the state-based env
    cam_jitter_px: float = 0.0    # vision only


@dataclass(frozen=True)
class DomainRandomizer:
    """TRAIN ranges are deliberately narrower than the HELD-OUT evaluation ranges on some axes."""
    mass: tuple[float, float] = (0.8, 1.2)
    friction: tuple[float, float] = (0.7, 1.3)
    delay_ms: tuple[int, int] = (0, 30)

    def sample(self, rng: np.random.Generator) -> Perturbation:
        """Uniform draws inside the ranges; delay is an integer multiple of 10 ms."""
        raise NotImplementedError


# src/corebot/learning/train_ppo.py  (CLI contract used by the acceptance tests)
#   python -m corebot.learning.train_ppo --seed 0 --steps 20000 --dr off --out runs/cap06/repro_a.json
# The JSON it writes must contain: seed, steps, device, torch_threads, eval_return,
# eval_success, eval_n, total_env_steps, wall_clock_s.
def main(argv: list[str] | None = None) -> None:
    """Parse args, set torch.set_num_threads(1), seed python/numpy/torch/env, train, then evaluate
    on seeds >= 1000 (never on training seeds) and write the JSON."""
    raise NotImplementedError


# src/corebot/learning/bc.py
def collect_demos(n_demos: int, seed: int):
    """Run the scripted CAP05 grasp in GraspReachEnv-compatible action space and return
    (obs[N, 17], act[N, 4]). Demos must use the SAME action space as the policy."""
    raise NotImplementedError


def train_bc(obs, act, epochs: int = 200, seed: int = 0):
    """Small MLP (2 x 64), MSE loss, 80/20 split by DEMO (not by timestep), returns model and
    held-out MSE. Also return the constant-mean baseline MSE for the same split."""
    raise NotImplementedError
```

### Kiểm thử
Tạo `tests/acceptance/test_cap06.py`. Các cổng (gate) là các test tái lập, học và độ bền.

```python
# tests/acceptance/test_cap06.py  (run from the repo root:  pytest -q tests/acceptance/test_cap06.py)
import inspect, json, pathlib
from corebot.evalkit import wilson_interval, bootstrap_ci

RUN = pathlib.Path("runs/cap06")
TRAIN_SEEDS_BELOW = 1000          # training uses seeds < 1000; evaluation uses seeds >= 1000

def _json(name):
    return json.loads((RUN / name).read_text())

def _episodes(name):
    return [json.loads(l) for l in (RUN / name).read_text().splitlines() if l.strip()]

def _rate(eps):
    return sum(e["success"] for e in eps) / len(eps)

# 1. reproducibility (GATE)
def test_ppo_is_reproducible_on_cpu():
    a, b = _json("repro_a.json"), _json("repro_b.json")
    assert a["seed"] == b["seed"] == 0 and a["steps"] == b["steps"] == 20000
    assert a["device"] == b["device"] == "cpu" and a["torch_threads"] == b["torch_threads"] == 1
    assert abs(a["eval_return"] - b["eval_return"]) < 1e-6

# 2. learning on the nominal environment (GATE)
def test_ppo_nominal_success():
    seeds = [_json(f"ppo_seed{s}.json") for s in range(5)]
    assert all(p["eval_n"] >= 100 for p in seeds)
    rates = [p["eval_success"] / p["eval_n"] for p in seeds]
    assert sum(rates) / 5 >= 0.90
    assert min(rates) >= 0.80                          # reporting the best of N seeds is not allowed
    eps = [e for e in _episodes("eval_nominal.jsonl") if e["policy"] == "ppo"]
    assert len(eps) >= 500 and min(e["seed"] for e in eps) >= TRAIN_SEEDS_BELOW
    lo, _ = bootstrap_ci([float(e["success"]) for e in eps], n=2000, seed=0)
    assert lo >= 0.80

# 3. robustness to held-out perturbations (GATE)
def test_domain_randomisation_robustness():
    eps = _episodes("eval_perturbed.jsonl")
    for e in eps:                                      # the held-out set really is the stated one
        assert 0.7 <= e["mass_scale"] <= 1.3 and 0.6 <= e["friction_scale"] <= 1.4 and e["delay_ms"] == 40
        assert e["seed"] >= TRAIN_SEEDS_BELOW
    dr = [e for e in eps if e["policy"] == "ppo_dr"]
    base = [e for e in eps if e["policy"] == "ppo_nodr"]
    assert len(dr) >= 100 and len(base) >= 100
    assert _rate(dr) >= 0.70 and _rate(dr) >= _rate(base)
    summary = _json("summary.json")["perturbed"]       # CIs reported, and they match the episodes
    for name, group in (("ppo_dr", dr), ("ppo_nodr", base)):
        lo, hi = wilson_interval(sum(e["success"] for e in group), len(group))
        assert abs(summary[name]["wilson"][0] - lo) < 1e-3 and abs(summary[name]["wilson"][1] - hi) < 1e-3

# 4. behaviour cloning
def test_bc_beats_constant_baseline_and_sweep_exists():
    bc = _json("bc_summary.json")
    assert bc["heldout_mse"] <= 0.2 * bc["const_baseline_mse"]
    assert bc["closed_loop_n"] >= 100 and bc["closed_loop_success"] / bc["closed_loop_n"] >= 0.60
    assert sorted(int(k) for k in bc["sweep"]) == [50, 100, 200, 500]
    vals = [bc["sweep"][k]["heldout_mse"] for k in sorted(bc["sweep"], key=int)]
    assert all(b <= a * 1.10 for a, b in zip(vals, vals[1:])) or bc.get("sweep_note")   # monotone or explained

# 5. compute budget
def test_budget_respected():
    m = _json("meta.json")
    assert m["total_env_steps"] <= 2_000_000 and m["wall_clock_s"] <= 7200 and m["device"] == "cpu"

# 6. safety wrapper
def test_no_limit_or_table_violations():
    for name in ("eval_nominal.jsonl", "eval_perturbed.jsonl"):
        assert sum(e["joint_limit_violations"] + e["table_collisions"] for e in _episodes(name)) == 0

# 7. integration: the learned skill is a drop-in replacement of ScriptedGraspSkill
def test_learned_skill_implements_grasp_skill():
    from corebot.manipulation.grasp import ScriptedGraspSkill
    from corebot.learning.skill import LearnedGraspSkill
    want = list(inspect.signature(ScriptedGraspSkill.execute).parameters)
    assert list(inspect.signature(LearnedGraspSkill.execute).parameters) == want
```

Các ngưỡng là giá trị khởi đầu tạm thời (xem lý do trong kế hoạch); hãy siết chặt chúng khi bạn đã có lần chạy tham chiếu của riêng mình. Lý do, mỗi ngưỡng một dòng:

- Tái lập `|diff| < 1e-6`: trên một máy, một luồng, seed giống nhau phải khớp tới độ chính xác float; lệch hơn nghĩa là có tính không tất định ẩn.
- Thành công trung bình >= 0.90, cận dưới bootstrap >= 0.80, mọi seed >= 0.80: primitive dựa trên state ở quy mô phòng 4 m đủ dễ để 90 % đạt được, và sàn theo từng seed chặn kiểu "chọn seed tốt nhất".
- Độ bền >= 0.70 và không thấp hơn tỉ lệ không-DR: mất 20 điểm khi vật lý đổi 30-40 % là chấp nhận được; DR không được làm mọi thứ tệ đi.
- BC: MSE giữ riêng <= 0.2 x baseline hằng và vòng kín >= 0.60: cloning phải rõ ràng thắng "dự đoán trung bình", và vòng kín yếu hơn PPO là điều được kỳ vọng.
- Ngân sách 2 M bước / 2 h: giữ cột mốc khả thi trên CPU laptop và buộc thí nghiệm hiệu quả.
- Không vi phạm: guard là yêu cầu cứng, không phải điểm.

### Kết quả mong đợi
Khi mọi artefact đã có, `pytest -q` in ra:

```text
.......                                                                  [100%]
7 passed in 3.42s
```

Một `runs/cap06/metrics.json` rút gọn, minh họa (bản tóm tắt bạn dán vào báo cáo CAP09):

```json
{
  "milestone": "CAP06",
  "git_hash": "3fa91c2",
  "device": "cpu",
  "total_env_steps": 1500000,
  "wall_clock_s": 4100,
  "nominal": {"policy": "ppo", "seeds": 5, "episodes_per_seed": 100, "mean_success": 0.94, "bootstrap_lo": 0.92},
  "perturbed": {
    "ppo_dr":   {"k": 81, "n": 100, "wilson": [0.722, 0.875]},
    "ppo_nodr": {"k": 58, "n": 100, "wilson": [0.482, 0.672]}
  },
  "bc": {"heldout_mse": 0.011, "const_baseline_mse": 0.093, "closed_loop_success": 71, "closed_loop_n": 100},
  "violations": {"joint_limit": 0, "table_collision": 0}
}
```

### Thử thách mở rộng
Mục tiêu mở rộng (tính cho tiêu chí Distinction): huấn luyện một policy **LeRobot ACT** trên bộ dữ liệu demonstration mô phỏng theo [hướng dẫn imitation learning trong sim của LeRobot](https://huggingface.co/docs/lerobot/il_sim). Trên CPU nó chậm; phiên Colab GPU miễn phí chấp nhận được, và bạn nên báo cáo tài nguyên đã dùng. So với policy BC của bạn trên cùng 100 seed bằng cận Wilson. Mục tiêu thứ hai: PPO hoặc BC dựa trên thị giác với CNN nhỏ ở 64x64, bật randomisation ánh sáng và rung camera kèm bảng ablation.

Tầng phần cứng tùy chọn: nếu bạn có SO-101, điều khiển từ xa nó bằng LeRobot, ghi một bộ dữ liệu nhỏ và báo cáo bảng thành công **thật so với mô phỏng** với cùng thống kê. Tuân theo quy tắc an toàn điện và nguồn của HW03 (không quá 12 V, không để chuyển động không giám sát), giữ tay gần công tắc nguồn, và nhớ rằng tầng phần cứng không bao giờ thay được một cổng đang thất bại.

### Thực hành với thư viện
Thay PPO của riêng bạn bằng Stable-Baselines3 và so sánh đường cong học và wall-clock. Tài liệu SB3 có các mẹo về chuẩn hóa và đánh giá ([RL tips](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html)). Đoạn code này cần `pip install stable-baselines3 torch gymnasium` và môi trường của bạn:

```python
# Needs: pip install "stable-baselines3>=2.3,<3" "gymnasium>=0.29,<2" torch (CPU build)
import json
import time

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from corebot.learning.envs import GraspReachEnv
from corebot.learning.randomize import DomainRandomizer

torch.set_num_threads(1)                      # needed for bit-for-bit repeatability on CPU
t0 = time.time()
seed = 0
venv = make_vec_env(lambda: GraspReachEnv(DomainRandomizer()), n_envs=4, seed=seed)
venv = VecNormalize(venv, norm_obs=True, norm_reward=True)       # unnormalised observations are a classic failure
model = PPO("MlpPolicy", venv, n_steps=512, batch_size=256, learning_rate=3e-4,
            gamma=0.98, gae_lambda=0.95, ent_coef=0.0, seed=seed, device="cpu", verbose=0)
model.learn(total_timesteps=20_000)

venv.training = False                         # freeze normalisation statistics for evaluation
venv.norm_reward = False
venv.seed(1000)                               # evaluation seeds start at 1000
obs, ok, n = venv.reset(), 0, 0
while n < 100:
    action, _ = model.predict(obs, deterministic=True)
    obs, _, done, info = venv.step(action)
    for i, d in enumerate(done):
        if d:
            n += 1
            ok += bool(info[i].get("success", False))
print(json.dumps({"seed": seed, "eval_success": ok, "eval_n": n, "wall_clock_s": round(time.time() - t0)}))
```

Kỳ vọng: một dòng JSON với `eval_n` bằng 100 và số thành công, sau 20 k bước, thường thấp hơn nhiều so với kết quả 300 k bước trong ví dụ có lời giải. Khoảng cách đó là bình thường; chỉ dùng lần chạy này để kiểm tra tái lập.

## Kiểm chứng

Kiểm từng lớp trước khi tin lớp kế. **Môi trường:** policy viết tay thành công ít nhất 95 % trong `GraspReachEnv` (nếu không, bạn đang bắt PPO giải một bài bất khả thi); `reset(seed=s)` hai lần cho observation giống hệt; policy ngẫu nhiên điểm gần không. **Huấn luyện:** chạy 20 k bước hai lần và so return được ghi (cổng), rồi vẽ đường cong học cho từng seed. **Đánh giá:** seed đánh giá không được xuất hiện trong bất kỳ log huấn luyện nào; tính tay một khoảng Wilson. **Hành vi:** xem mười episode đánh giá, kể cả các lần thất bại, và viết ra lỗi trông thế nào (gắp trượt, rơi vật, guard kẹp action). Policy có return tốt mà hành vi xấu là một lỗi reward.

**Chấm điểm.** CAP06 có trọng số **12 trên 100**. Điểm gồm 60 % tự động (tỉ lệ có trọng số của bảy kiểm tra; các cổng là tái lập, học và độ bền) và 40 % rubric của người (bốn tiêu chí chấm 0-4 kèm bằng chứng liên kết: lập luận thiết kế reward, không chọn seed đẹp, kết quả âm tính trung thực, so sánh với baseline viết tay). Bạn có thể đối chiếu điểm tự chấm bằng prompt review dưới đây, prompt nhận code và artefact chứ không nhận nhận xét của chính bạn:

```text
You are reviewing a robotics student's CAP06 milestone. Below are the files envs.py, randomize.py,
train_ppo.py, bc.py, docs/reward_design.md and runs/cap06/summary.json. Do NOT use the student's own
verdict. For each criterion give a score 0-4 (0 missing, 2 works but unexplained, 4 justified, tested and
critiqued), quote the evidence (file and line or number) and name the single biggest weakness:
1. Reward design reasoning  2. Seeds and statistics honesty  3. Negative results and limits  4. Comparison with the scripted skill
```

Tốt nghiệp đòi hỏi mọi cổng đạt, điểm cột mốc ít nhất 60 và tổng có trọng số ít nhất 70 trên cả capstone. Cổng thất bại giữ cột mốc ở trạng thái "đang làm"; nó không khóa ứng dụng.

## Lỗi thường gặp

- **Reward hacking:** policy lơ lửng gần vật hoặc khai thác thưởng nhấc mà không giữ. Cách chữa: chi phí thay vì trả dương mỗi bước, phạt thời gian, xem video.
- **Reward thưa không có shaping:** 100 k bước không học được gì. Cách chữa: số hạng khoảng cách dày và curriculum từ vị trí đặt dễ.
- **Observation chưa chuẩn hóa:** thang trộn lẫn (mét cạnh vận tốc khớp) làm học đình trệ. Cách chữa: chuẩn hóa, và đóng băng thống kê lúc đánh giá.
- **Đánh giá trên seed huấn luyện:** làm phồng thành công. Cách chữa: khoảng seed rời nhau, có test kiểm tra.
- **Khoảng DR làm tác vụ bất khả thi:** policy không học gì hoặc học hành vi rụt rè trung bình. Cách chữa: nới rộng dần và kiểm tra policy viết tay vẫn thành công ở cực trị.
- **Lỗi tích lũy của BC và không khớp không gian action** giữa demo và policy. Cách chữa: test phát lại demo, thêm nhiễu vào demo, gán nhãn lại state theo policy.
- **Báo cáo seed tốt nhất trong N,** hoặc chỉnh trên tập đánh giá. Cách chữa: báo mọi seed và đóng băng siêu tham số trước khi đánh giá.
- **Tính không tất định ẩn:** torch đa luồng, `numpy` không seed, dataloader xáo trộn. Cách chữa: một luồng, một `Generator`, seed mọi thứ.
- **Guard làm thay việc:** policy cần kẹp action mới thành công. Cách chữa: ghi số lần sửa.

## Phương án khác và đánh đổi

*Học được so với viết tay.* Kỹ năng viết tay dễ đoán và không cần huấn luyện; kỹ năng học được hấp thụ được các hiệu ứng bạn chưa mô hình hóa, nhưng chỉ trong phân phối nó đã thấy. *PPO so với BC.* PPO cần reward và nhiều bước nhưng có thể vượt người dạy; BC cần demonstration tốt và không gian action khớp nhưng rẻ và hiệu quả mẫu. *Dựa trên state so với thị giác.* Dựa trên state nhanh và dễ chẩn đoán; thị giác là mục tiêu thật và nhân khối lượng tính toán lên cỡ một bậc độ lớn trên CPU. *SAC hoặc TD3 thay PPO:* thường hiệu quả mẫu hơn trên điều khiển liên tục, nhưng PPO là cái bạn đã học. *Policy ACT/diffusion* xử lý demonstration đa mode và action chunk tốt hơn MLP thường nhưng cần nhiều dữ liệu và tính toán hơn. *PPO tự viết so với Stable-Baselines3:* tự viết một lần để hiểu, dùng thư viện cho thí nghiệm bạn muốn tin cậy.

## Vận dụng và ghi nhớ

Cột mốc này nuôi CAP07 (lớp tác vụ gọi một `GraspSkill` và phải xử lý lỗi của nó bằng thử lại) và CAP08 (benchmark toàn hệ thống chạy kỹ năng viết tay và học được cạnh nhau, và phân tích khoảng cách sim-to-real dùng lại các tập nhiễu loạn và thống kê của bạn). Ngoài capstone, cùng thói quen áp dụng cho mọi kết quả học máy: seed, đánh giá giữ riêng, khoảng tin cậy, baseline.

Câu hỏi gợi nhớ cho một tuần sau: (1) Viết khoảng Wilson cho 27/30 không cần ghi chú và nói nó hàm ý gì. (2) Vì sao cận BC tăng như $\epsilon T^2$? (3) Ba điều nào làm một lần chạy PPO không tái lập được trên CPU? (4) "Held-out" nghĩa là gì với seed so với với khoảng nhiễu loạn? (5) Vì sao lớp bọc an toàn được đếm chứ không chỉ áp dụng?

## Đáp án bài tập

1. $\hat p=0.90$. Wilson: $[0.744,0.965]$. Cận dưới thấp hơn 0.80, nên "ít nhất 80 %" **không** được ủng hộ ở độ tin cậy 95 % với 30 episode, dù ước lượng điểm trông tốt. Cần khoảng 70 episode (63 thành công) để cận dưới đạt 0.80 nếu tỉ lệ thật là 0.9.
2. $2\,000\,000/366\approx5\,465$ s $=1.52$ h. Còn khoảng 0.48 h (29 phút) cho đánh giá, nghiên cứu BC và chi phí khác: sát nhưng khả thi; giảm số bước hoặc tăng số môi trường nếu đánh giá chậm.
3. Return khi lơ lửng: $60\cdot e^{-0.2}=60\cdot0.819=49.1$. Một cú gắp mất 40 bước tiếp cận (phần thưởng trung bình mỗi bước khoảng 0.5) cộng 12 cộng 20 bước ở khoảng 1.0 được khoảng $20+12+20=52$: gần bằng nhau, nên nhiễu quyết định và lơ lửng thường thắng ở đầu huấn luyện. Thưởng một lần chỉ khoảng 24 % return khi lơ lửng. Cách sửa: chi phí ($-d$), phạt thời gian, và thưởng thành công lớn hơn hoặc chỉ ở cuối.
4. Khối lượng: $0.4/0.6=67\,\%$ nằm trong; ma sát: $0.6/0.8=75\,\%$; trễ: 40 ms nằm ngoài $\{0..30\}$ nên 0 %. Phần chung là 0: mọi episode giữ riêng đều đòi ngoại suy. Thay đổi: huấn luyện trễ tới 50 ms (để 40 ms nằm trong) và nới khối lượng và ma sát ít nhất bằng khoảng giữ riêng, rồi nói rõ rằng tập giữ riêng được giữ riêng theo **seed và lần lấy mẫu episode**, không theo khoảng. Hoặc cố ý giữ khoảng huấn luyện hẹp hơn để đo ngoại suy, và báo cả phần chia trong khoảng.
5. Có cơ sở: trên tập nhiễu loạn này với các lần huấn luyện này, policy DR tốt hơn (khoảng Wilson không chồng, $z\approx3.5$ (pooled variance)). Không có cơ sở: "DR luôn giúp" hoặc bất kỳ tuyên bố độ lớn hiệu ứng nào, vì mỗi nhánh chỉ một seed huấn luyện nên phương sai giữa các seed chưa được đo; và tập giữ riêng chia sẻ giả định với phân phối huấn luyện. Chạy 3 đến 5 seed mỗi nhánh.
6. (a) Covariate shift: các lỗi nhỏ của chính policy đưa nó tới state không có trong demo; sửa bằng gán nhãn lại kiểu DAgger hoặc demo có chèn nhiễu. (b) Không khớp không gian action hoặc thời gian giữa demo và policy (hoặc observation làm lộ timestep); sửa bằng phát lại demo qua env và kiểm tra đầu vào policy khớp. (Thêm: demo đa mode, lấy trung bình hai cách tiếp cận cho ra giá trị trung bình thất bại; sửa bằng demo viết tay nhất quán hơn.)
7. Phát lại action của demo vòng hở qua môi trường: episode viết tay phải tái tạo thành công trong ít nhất 95 % trường hợp. Nếu không, không gian action khác nhau. Bài test này không cần huấn luyện.
8. (1) torch nhiều hơn một luồng hoặc phép toán không tất định; (2) một seed không áp dụng cho một thành phần (numpy toàn cục, env reset, lấy mẫu action); (3) thống kê VecNormalize hoặc xáo trộn dataloader; (4) logic phụ thuộc thời gian/wall-clock trong môi trường; (5) khác phiên bản gói hoặc BLAS giữa các lần chạy; (6) kernel GPU (không áp dụng cho CPU). Chia đôi bằng cách ghi loss sau mỗi lần cập nhật và tìm lần cập nhật đầu tiên khác nhau.
9. Trung bình $=355/5=71$ %, nhỏ nhất 20 %. Cổng thất bại ở cả trung bình lẫn nhỏ nhất. Một báo cáo có trách nhiệm cho thấy cả năm seed, trung bình kèm khoảng bootstrap, đường cong của seed hỏng, một giả thuyết (sụp đổ khám phá hoặc khởi tạo xui), và thí nghiệm bổ sung (thêm seed, learning rate khác). Đừng bỏ seed 5 và đừng báo seed 1 (96) là "kết quả".
10. Ghi: MSE giữ riêng, số thành công vòng kín trên 100 kèm khoảng Wilson, cho từng số demo và ít nhất 3 seed huấn luyện; seed huấn luyện và seed chia demo. Baseline: policy trung bình hằng (MSE) và kỹ năng viết tay (thành công). Biên: 0 demo (baseline) và 500. Bác bỏ "nhiều demo hơn luôn tốt hơn" nếu thành công không đơn điệu vượt quá các khoảng chồng nhau trong khi MSE vẫn giảm: khi đó nút thắt là lỗi tích lũy, không phải lượng dữ liệu.

## Đọc thêm

- [Spinning Up in Deep RL](https://spinningup.openai.com/en/latest/) - PPO được giải thích cùng vệ sinh thí nghiệm.
- [Tài liệu Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/) và [RL tips](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html).
- [Gymnasium Env API](https://gymnasium.farama.org/api/env/) - hợp đồng `reset` và `step`, termination so với truncation.
- [Tobin et al., Domain Randomization](https://arxiv.org/abs/1703.06907) - lập luận sim-to-real gốc.
- [Henderson et al., Deep RL that Matters](https://arxiv.org/abs/1709.06560) - vì sao seed và cách báo cáo quan trọng.
- [Schulman et al., PPO](https://arxiv.org/abs/1707.06347).
- [Ross, Gordon và Bagnell, A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning](https://arxiv.org/abs/1011.0686) - lỗi tích lũy và DAgger.
- [Zhao et al., ALOHA / ACT](https://arxiv.org/abs/2304.13705) và [tài liệu LeRobot ACT](https://huggingface.co/docs/lerobot/act).
- [Binomial proportion confidence interval (Wikipedia)](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) - Wilson và các lựa chọn khác.
- **Video:** Pieter Abbeel, *Lecture 22 Sim2Real and Domain Randomization* (CS287, UC Berkeley); *ALOHA and ACT: LeRobot Research Presentation #1* (Hugging Face).
