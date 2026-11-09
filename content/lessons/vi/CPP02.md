---
{"title": "Bộ nhớ, tham chiếu và vòng đời đối tượng", "summary": "Giải thích ai sở hữu một đối tượng và một tham chiếu còn hợp lệ trong bao lâu.", "objectives": ["Phân biệt giá trị, địa chỉ, con trỏ và tham chiếu.", "Nhận diện tham chiếu treo (dangling) và vùng lưu trữ bị vô hiệu hóa.", "Dùng RAII và các container chuẩn để quản lý quyền sở hữu."]}
---

## Vì sao điều này quan trọng

Giải thích ai sở hữu một đối tượng và một tham chiếu còn hợp lệ trong bao lâu. Bài học này phát triển phép tính cốt lõi trước khi yêu cầu bạn áp dụng nó vào một bối cảnh mới. Hãy làm bài chẩn đoán trước nếu bạn nghĩ mình đã biết rồi; việc từng dùng công cụ không phải là bằng chứng của sự hiểu.

## Trực giác

Con trỏ (pointer) là một giá trị có thể trỏ tới một đối tượng trong bộ nhớ; bản thân nó không phải là quyền sở hữu. Tham chiếu (reference) là một bí danh (alias). Tính đúng đắn phụ thuộc vào việc đối tượng còn tồn tại hay không và liệu có thao tác nào đã di chuyển vùng lưu trữ của nó. Vẽ vòng đời của các đối tượng thường hữu ích hơn việc nhìn chằm chằm vào địa chỉ.

Hãy hình dung bộ nhớ là một dãy tủ khóa có đánh số, và một đối tượng là nội dung của một hay nhiều tủ. *Giá trị* (value) là chính nội dung: sao chép giá trị là photocopy nội dung vào các tủ mới, và từ đó hai bản độc lập với nhau. *Con trỏ* là một mảnh giấy ghi số tủ; sao chép mảnh giấy cho hai mảnh cùng chỉ một tủ, và không có gì trên mảnh giấy cho biết tủ đó còn được thuê hay không. *Tham chiếu* là một nhãn thứ hai dán lên cùng một tủ: nó không thể để trống và không thể chuyển sang tủ khác, nhưng cũng như mảnh giấy, nó không nói gì về việc tủ còn được thuê bao lâu. Ai thuê tủ và khi nào hết hạn là *quyền sở hữu* (ownership) và *vòng đời* (lifetime) của đối tượng; đó là thuộc tính của cấu trúc chương trình (phạm vi, container, con trỏ thông minh), không phải của các con số trên mảnh giấy.

Một tình huống đầu tiên. Hãy dự đoán đầu ra của chương trình dưới đây trước khi đọc tiếp; nó được biên dịch bằng g++ 11.4.0 (`-std=c++20 -Wall -Wextra`) và không có cảnh báo.

```cpp
#include <iostream>

int main() {
    int x = 10;
    int y = x;
    int* p = &x;
    int& r = x;
    y = 20;
    *p = 30;
    r += 1;
    std::cout << "x=" << x << " y=" << y << " *p=" << *p << " r=" << r << '\n';
    std::cout << "&r == &x: " << (&r == &x) << ", &y == &x: " << (&y == &x) << '\n';
    std::cout << "sizeof(x)=" << sizeof(x) << " sizeof(p)=" << sizeof(p) << " sizeof(r)=" << sizeof(r) << '\n';
}
```

![Dòng thời gian của một lần cấp phát lại vector: con trỏ tới phần tử 0 của khối cũ có dung lượng 4 bị treo sau khi push_back thứ năm chuyển các phần tử sang khối dung lượng 8, trong khi unique_ptr chuyển một mũi tên sở hữu duy nhất.](/lesson-figures/CPP02.svg)

*Hình: hai bức tranh của cùng một kỷ luật. Bên trái, con trỏ vào một vector còn hiệu lực cho đến khi vector cấp phát lại; bên phải, quyền sở hữu một đối tượng được trao từ `a` sang `b`, để đúng một cái tên chịu trách nhiệm hủy nó.*

**Kiểm tra dự đoán.** Đầu ra là `x=31 y=20 *p=31 r=31`, rồi `&r == &x: 1, &y == &x: 0`, rồi `sizeof(x)=4 sizeof(p)=8 sizeof(r)=4`. `y` là một bản sao giá trị nên gán 20 cho nó không chạm tới `x`; `p` và `r` cùng gọi tên đối tượng `x`, nên `*p = 30` và `r += 1` là hai lần ghi vào một đối tượng (10, rồi 30, rồi 31). Tham chiếu có cùng địa chỉ với `x`, còn bản sao có địa chỉ riêng. Số cuối cần cẩn thận: `sizeof(r)` cho kích thước của đối tượng được tham chiếu (4), không phải của chính tham chiếu mà ngôn ngữ không quy định thêm, trong khi con trỏ là một đối tượng 8 byte bình thường trên máy 64 bit này.

Trực giác sai phổ biến là "con trỏ hay tham chiếu làm đối tượng còn sống". Chúng không bao giờ làm vậy: chỉ chủ sở hữu quyết định, và chủ sở hữu là một phạm vi, một container hay một con trỏ thông minh. Hình vẽ cho thấy hai cách một handle hỏng mà phần còn lại của bài phân tích: vùng lưu trữ bị *di chuyển* (vector cấp phát lại, handle chỉ vào một tủ đã bị dọn) hoặc đối tượng bị *hủy* (phạm vi kết thúc, chủ sở hữu bị reset). Trực giác sai thứ hai là một handle treo sẽ tự báo hiệu: tủ cũ thường vẫn chứa những con số có vẻ hợp lý một lúc, nên một chương trình có thể chạy đúng một nghìn lần và hỏng ở lần thứ một nghìn lẻ một, đó là lý do bài này dựa vào quy tắc và sanitizer thay vì quan sát.

## Lý thuyết và suy dẫn

Một đối tượng cục bộ tự động bị hủy khi scope của nó kết thúc. Trả về con trỏ hoặc tham chiếu tới nó để lại một handle treo. Sao chép một giá trị tạo ra một đối tượng khác với vòng đời riêng; sao chép một con trỏ chỉ tạo ra một giá trị địa chỉ khác.

`std::vector` sở hữu vùng lưu trữ phần tử liên tục (contiguous). Tăng quá dung lượng (capacity) có thể cấp phát một khối mới, di chuyển các phần tử, và vô hiệu hóa con trỏ, tham chiếu và iterator trỏ tới vùng lưu trữ cũ. Một đối tượng vector có thể vẫn còn sống trong khi con trỏ tới một phần tử cũ của nó trở nên không hợp lệ. Đừng dựa vào việc quan sát thấy địa chỉ ổn định trong một lần chạy.

RAII gắn việc giải phóng tài nguyên với việc hủy đối tượng. `std::unique_ptr<T>` sở hữu một đối tượng cấp phát động và không thể sao chép; di chuyển (move) sẽ chuyển giao quyền sở hữu. `std::shared_ptr<T>` chia sẻ quyền sở hữu bằng bộ đếm tham chiếu và có thêm chi phí. Cả hai đều không tự động làm cho việc truy cập an toàn với luồng (thread-safe). Hãy ưu tiên giá trị và container cho đến khi thật sự cần sở hữu động.

Để kiểm tra các lỗi bộ nhớ nghi ngờ, hãy biên dịch code của chính bạn với `-fsanitize=address,undefined -g`. Sanitizer phát hiện nhiều thao tác không hợp lệ được thực thi; vượt qua một lần chạy không phải là bằng chứng rằng mọi vòng đời đều đúng.

### Lưu trữ: tĩnh, tự động và động

Tiêu chuẩn phân biệt bốn thời gian lưu trữ (storage duration): tĩnh, theo luồng, tự động và động ([basic.stc.general]; cppreference, "Storage duration"). Đối tượng ở phạm vi namespace và biến cục bộ `static` có lưu trữ *tĩnh*: chúng tồn tại từ lúc chương trình bắt đầu hoặc lần dùng đầu tiên đến khi chương trình kết thúc. Biến cục bộ của một khối có lưu trữ *tự động*: được tạo khi luồng thực thi đến định nghĩa và bị hủy ở cuối khối ([basic.stc.auto]); các bản cài đặt đặt chúng trên call stack, mỗi lời gọi hàm đang hoạt động một frame, nên tạo và hủy chỉ tốn một phép dịch con trỏ. Lưu trữ *động* có được bằng `new` hoặc một allocator và kéo dài đến khi được giải phóng tường minh ([basic.stc.dynamic]); các bản cài đặt lấy nó từ heap, tốn công tìm một khối trống và một tiêu đề quản lý, và allocator an toàn đa luồng còn tốn hơn. Hệ quả thực tế: lưu trữ tự động nhanh nhưng vòng đời gắn với phạm vi và kích thước gắn với frame (một mảng cục bộ cỡ megabyte có nguy cơ tràn stack với stack mặc định 8 MB), trong khi lưu trữ động có thể sống lâu hơn hàm và có kích thước xác định lúc chạy nhưng cần một chủ sở hữu giải phóng nó đúng một lần.

Một container chuẩn là một đối tượng tự động nhỏ sở hữu một khối động. Một đối tượng `std::vector<int>` là ba con trỏ (24 byte trên nền tảng 64 bit này) nằm ở nơi biến vector nằm, còn các phần tử của nó nằm trong một khối heap riêng. Di chuyển hay hủy đối tượng vector tác động lên 24 byte đó; khối được giải phóng bởi destructor của vector. Sự tách đôi giữa *handle* và *payload* này giải thích phần lớn bài học: con trỏ tới handle còn hiệu lực chừng nào biến vector còn, còn con trỏ tới payload thì không.

**Ví dụ.** `operator new` toàn cục có thể được thay thế (cppreference, "operator new", mục "Global replacements"), ở đây chỉ để đếm số lần gọi. Chương trình dưới đây, biên dịch bằng g++ 11.4.0 (`-std=c++20 -Wall -Wextra`), đếm số lần cấp phát và số byte của ba đối tượng. Mỗi đối tượng `int local[1000]`, `std::vector<int> v(1000)` và `std::make_unique<int>(5)` tốn bao nhiêu lần cấp phát và bao nhiêu byte, và `sizeof(v)`, `sizeof(p)` bằng bao nhiêu?

```cpp
#include <cstdlib>
#include <iostream>
#include <memory>
#include <new>
#include <vector>

static int g_allocs = 0;
static std::size_t g_bytes = 0;

void* operator new(std::size_t n) {
    ++g_allocs;
    g_bytes += n;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

static void report(const char* what, int a0, std::size_t b0) {
    std::cout << what << ": " << g_allocs - a0 << " allocation(s), " << g_bytes - b0 << " bytes\n";
}

int main() {
    int a0 = g_allocs; std::size_t b0 = g_bytes;
    { int local[1000]; local[0] = 1; (void)local; }
    report("int local[1000]", a0, b0);

    a0 = g_allocs; b0 = g_bytes;
    { std::vector<int> v(1000); std::cout << "sizeof(v) = " << sizeof(v) << '\n'; }
    report("std::vector<int> v(1000)", a0, b0);

    a0 = g_allocs; b0 = g_bytes;
    { auto p = std::make_unique<int>(5); std::cout << "sizeof(p) = " << sizeof(p) << '\n'; }
    report("std::make_unique<int>(5)", a0, b0);
}
```

**Lời giải.** Mảng cục bộ có automatic storage nên không có lần gọi `operator new` nào: 0 lần cấp phát, 0 byte. Đối tượng vector `v` là một handle gồm ba con trỏ (`sizeof(v) = 24`) nằm trong frame; chỉ payload gồm 1000 `int` được cấp phát, đúng một lần, với $1000\times4=4000$ byte, còn handle 24 byte là tự động nên không được đếm. `make_unique<int>(5)` cấp phát một `int` (4 byte) trong khi handle `p` của nó là một con trỏ duy nhất (`sizeof(p) = 8`). Chương trình in ra:

```text
int local[1000]: 0 allocation(s), 0 bytes
sizeof(v) = 24
std::vector<int> v(1000): 1 allocation(s), 4000 bytes
sizeof(p) = 8
std::make_unique<int>(5): 1 allocation(s), 4 bytes
```

![Ba vùng lưu trữ cạnh nhau: tĩnh, stack với các frame, và heap với khối 4000 byte và 4 byte, mỗi handle trên stack trỏ tới khối của nó, cùng thời điểm kết thúc của từng đối tượng.](/lesson-figures/CPP02-2.svg)

*Hình: handle nằm trên stack và mất cùng khối của nó; payload nằm trên heap và mất khi destructor của chủ sở hữu giải phóng nó. Các kích thước là của ví dụ ở trên.*

### Bố cục đối tượng: kích thước, căn chỉnh và padding

Mỗi kiểu đối tượng có một *yêu cầu căn chỉnh* (alignment requirement), một lũy thừa của hai cho biết đối tượng kiểu đó có thể đặt ở những địa chỉ byte nào (cppreference, "Object", mục "Alignment"; [basic.align]). Với các kiểu cơ bản thông dụng, alignment bằng kích thước (`int` 4, `double` 8 trên nền tảng này). Các thành viên của một class được bố trí theo thứ tự khai báo, mỗi thành viên ở độ lệch kế tiếp thỏa mãn alignment của nó, và trình biên dịch chèn các byte *padding* để đạt điều đó. Alignment của class là alignment lớn nhất của các thành viên, và kích thước của nó được làm tròn lên bội của alignment đó, để mỗi phần tử của một mảng các class đó cũng được căn chỉnh (cppreference, `sizeof`: "including any additional padding required to place such object in an array"). Quy tắc cho một công thức đóng. Với các thành viên $m_1,\dots,m_k$ có kích thước $s_i$ và alignment $a_i$, các độ lệch là $o_1=0$ và $o_i=\lceil (o_{i-1}+s_{i-1})/a_i\rceil\,a_i$, alignment là $A=\max a_i$ và $\mathrm{sizeof}=\lceil (o_k+s_k)/A\rceil\,A$. Các thứ tự khai báo khác nhau của cùng các thành viên do đó có thể cho kích thước khác nhau; đặt thành viên có alignment lớn trước thường loại bỏ padding giữa chúng.

Bố cục quan trọng vì ba lý do trong mã robot: lưu lượng bộ nhớ (một struct có padding trong mảng $10^6$ điểm làm lãng phí cache và băng thông), giao diện nhị phân (một struct gửi qua dây hay lưu vào file phải có bố cục cố định, được ghi tài liệu, không phải "cái mà trình biên dịch làm ra"), và mã kiểu `memcpy` giả định không có khoảng trống. `offsetof` cho độ lệch của một thành viên của class standard-layout (cppreference, "offsetof").

**Ví dụ.** Ba thành viên có kích thước 1, 4 và 1 byte được khai báo theo hai thứ tự, `char a; int b; char c;` (`T1`) và `int b; char a; char c;` (`T2`) (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). `sizeof`, `alignof` và offset của các thành viên trong mỗi struct bằng bao nhiêu?

```cpp
#include <cstddef>
#include <iostream>

struct T1 { char a; int b; char c; };
struct T2 { int b; char a; char c; };

int main() {
    std::cout << "T1 size " << sizeof(T1) << " align " << alignof(T1) << " offsets "
              << offsetof(T1, a) << ' ' << offsetof(T1, b) << ' ' << offsetof(T1, c) << '\n';
    std::cout << "T2 size " << sizeof(T2) << " align " << alignof(T2) << " offsets "
              << offsetof(T2, b) << ' ' << offsetof(T2, a) << ' ' << offsetof(T2, c) << '\n';
}
```

**Lời giải.** Công thức offset của mục này cho ra layout, với $a_{\texttt{char}}=1$ và $a_{\texttt{int}}=4$, nên $A=4$. Với `T1`: $o_a=0$, $o_b=\lceil1/4\rceil\cdot4=4$, $o_c=\lceil(4+4)/1\rceil\cdot1=8$ và $\mathrm{sizeof}=\lceil9/4\rceil\cdot4=12$, nên 6 trong 12 byte là padding. Với `T2`: $o_b=0$, $o_a=4$, $o_c=5$ và $\mathrm{sizeof}=\lceil6/4\rceil\cdot4=8$, với 2 byte padding. Khai báo `int` trước tiết kiệm được 4 byte. Chương trình in ra:

```text
T1 size 12 align 4 offsets 0 4 8
T2 size 8 align 4 offsets 0 4 5
```

![Bản đồ byte của các struct T1 và T2 với vạch căn chỉnh 4 byte, padding được gạch chéo, kích thước 12 và 8.](/lesson-figures/CPP02-3.svg)

*Hình: cùng ba thành viên, hai thứ tự khai báo. Các khối xám là padding được chèn để thỏa mãn alignment 4 byte của `int` và làm tròn kích thước lên bội của 4.*

```explore
{
  "title": "Struct size as the alignment of the middle member grows",
  "title_vi": "Kích thước struct khi alignment của thành viên giữa tăng",
  "prompt": "Predict first: for a struct { char a; T b; char c; } how does sizeof grow when the alignment A of T doubles, and what does reordering to { T b; char a; char c; } save? Then move the slider.",
  "prompt_vi": "Dự đoán trước: với struct { char a; T b; char c; } thì sizeof tăng thế nào khi alignment A của T tăng gấp đôi, và việc sắp xếp lại thành { T b; char a; char c; } tiết kiệm được bao nhiêu? Sau đó kéo thanh trượt.",
  "params": [
    { "name": "k", "label": "log2 of the alignment of T (A = 2^k; T has size A)", "label_vi": "log2 của alignment của T (A = 2^k; T có kích thước A)", "min": 0, "max": 4, "step": 1, "value": 2, "unit": "" }
  ],
  "let": [
    { "name": "A", "expr": "2^k" },
    { "name": "ob", "expr": "A" },
    { "name": "s1", "expr": "ceil((2*A + 1)/A)*A" },
    { "name": "s2", "expr": "ceil((A + 2)/A)*A" }
  ],
  "scene": {
    "xmin": -1, "xmax": 50, "ymin": 0, "ymax": 4,
    "items": [
      { "type": "label", "at": [0, 3.5], "text": "order a, b, c", "text_vi": "thứ tự a, b, c", "color": "grey" },
      { "type": "segment", "from": [0, 3], "to": [1, 3], "color": "blue", "width": 12 },
      { "type": "segment", "from": [1, 3], "to": ["ob", 3], "color": "grey", "width": 12, "dash": true },
      { "type": "segment", "from": ["ob", 3], "to": ["ob + A", 3], "color": "orange", "width": 12 },
      { "type": "segment", "from": ["ob + A", 3], "to": ["ob + A + 1", 3], "color": "blue", "width": 12 },
      { "type": "segment", "from": ["ob + A + 1", 3], "to": ["s1", 3], "color": "grey", "width": 12, "dash": true },
      { "type": "label", "at": [0, 1.5], "text": "order b, a, c", "text_vi": "thứ tự b, a, c", "color": "grey" },
      { "type": "segment", "from": [0, 1], "to": ["A", 1], "color": "orange", "width": 12 },
      { "type": "segment", "from": ["A", 1], "to": ["A + 1", 1], "color": "blue", "width": 12 },
      { "type": "segment", "from": ["A + 1", 1], "to": ["A + 2", 1], "color": "blue", "width": 12 },
      { "type": "segment", "from": ["A + 2", 1], "to": ["s2", 1], "color": "grey", "width": 12, "dash": true }
    ]
  },
  "readouts": [
    { "label": "alignment A of T", "label_vi": "alignment A của T", "expr": "A", "unit": "B", "digits": 0 },
    { "label": "sizeof, order a, b, c", "label_vi": "sizeof, thứ tự a, b, c", "expr": "s1", "unit": "B", "digits": 0 },
    { "label": "sizeof, order b, a, c", "label_vi": "sizeof, thứ tự b, a, c", "expr": "s2", "unit": "B", "digits": 0 },
    { "label": "bytes saved by reordering", "label_vi": "số byte tiết kiệm khi sắp xếp lại", "expr": "s1 - s2", "unit": "B", "digits": 0 }
  ]
}
```

*Xanh dương là `char`, cam là `T`, xám nét đứt là padding. Thứ tự đầu cần $3A$ byte mỗi khi $A\ge2$, thứ tự sau cần $2A$; với $A=1$ không có gì để chèn.* Đáp án của câu dự đoán: cả hai kích thước tăng tỉ lệ với $A$, và mức tiết kiệm là $A$ byte (4 byte cho `int`, 8 cho `double`, 16 cho kiểu căn chỉnh 16 byte).

### Giá trị, con trỏ và tham chiếu

Một *giá trị* của kiểu class hay kiểu dựng sẵn được sao chép bằng khởi tạo sao chép: bản sao là một đối tượng mới có vùng lưu trữ và vòng đời riêng, và các thay đổi sau đó ở bên nào cũng không ảnh hưởng bên kia. Một *con trỏ* `T*` bản thân là một đối tượng giữ một địa chỉ (hoặc giá trị rỗng `nullptr`); sao chép nó là sao chép địa chỉ, nên cả hai con trỏ cùng trỏ tới một đối tượng. Một *tham chiếu* `T&` là một bí danh cố định lúc khởi tạo: nó phải gắn với một đối tượng đã có, không thể null và không thể gắn lại (cppreference, "Reference declaration"). Trong mã sinh ra, tham chiếu thường được cài đặt như con trỏ, nhưng ngôn ngữ bảo đảm ít hơn: không null, không số học, không có mảng các tham chiếu.

Quan sát then chốt của bài là không cái nào trong ba cái này nói gì về vòng đời. Một con trỏ hay tham chiếu hợp lệ đúng khi đối tượng mà nó gọi tên còn trong vòng đời và, với con trỏ vào container, phần tử chưa bị di chuyển; Core Guidelines phát biểu nửa đầu là "đừng dereference một con trỏ không hợp lệ" (ES.65) và "đừng bao giờ trả về con trỏ hay tham chiếu tới đối tượng cục bộ" (F.43). Chọn giữa chúng là một quyết định thiết kế: truyền theo giá trị khi sao chép rẻ hoặc hàm được gọi cần bản sao riêng; theo `const&` để đọc mà không sao chép (F.16); theo con trỏ khi "không có đối tượng" là một trạng thái hợp lệ (R.2 dành con trỏ thô cho các đối tượng đơn lẻ *không* được sở hữu); và không bao giờ dùng `T*` thô để diễn đạt quyền sở hữu (R.3).

**Ví dụ.** Một vector `a` được chép vào `b`, và một con trỏ `p` tới `a[0]` được chép vào `q`; sau đó ghi `9` vào `b[0]` và ghi `5` qua `q` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Cuối cùng `a[0]` và `b[0]` bằng bao nhiêu, và `p` với `q`, `&a[0]` với `&b[0]` có bằng nhau không?

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> a{1, 2, 3};
    std::vector<int> b = a;
    int* p = &a[0];
    int* q = p;
    b[0] = 9;
    *q = 5;
    std::cout << "a[0]=" << a[0] << " b[0]=" << b[0] << '\n';
    std::cout << "p == q: " << (p == q) << ", &a[0] == &b[0]: " << (&a[0] == &b[0]) << '\n';
}
```

**Lời giải.** Sao chép vector `a` vào `b` chép ba phần tử vào một khối heap mới, nên `&a[0] != &b[0]` và ghi `9` vào `b[0]` không đụng tới `a`. Sao chép con trỏ `p` vào `q` chỉ chép một địa chỉ, nên `p == q` và ghi `5` qua `q` làm đổi `a[0]`. Vậy `a[0]=5`, `b[0]=9`. Chương trình in ra:

```text
a[0]=5 b[0]=9
p == q: 1, &a[0] == &b[0]: 0
```

### Quyền sở hữu, RAII và phép di chuyển

*Quyền sở hữu* trả lời câu hỏi "ai giải phóng đối tượng này?". RAII (resource acquisition is initialization) làm cho câu trả lời mang tính cấu trúc: một đối tượng chiếm tài nguyên trong constructor sẽ giải phóng nó trong destructor, nên việc giải phóng xảy ra trên mọi đường thoát, kể cả `return` sớm và ngoại lệ (Core Guidelines R.1, R.5). `std::unique_ptr<T>` là chủ sở hữu nhỏ nhất như vậy: nó giữ một con trỏ (8 byte ở đây), xóa đối tượng trong destructor và không thể sao chép, vì hai chủ sở hữu sẽ giải phóng hai lần. Quyền sở hữu được chuyển bằng một phép *di chuyển* (move): sau `auto b = std::move(a);` đối tượng thuộc về `b` và `a` giữ `nullptr` (cppreference, `std::unique_ptr`). Di chuyển một `unique_ptr` chép một con trỏ và đặt nguồn về null; nó không chạm tới đối tượng, nên một con trỏ tới đối tượng vẫn hợp lệ qua phép di chuyển dù chủ sở hữu đã đổi.

Core Guidelines biến điều này thành các quy tắc: không gọi `new` và `delete` tường minh (R.11), diễn đạt quyền sở hữu bằng `unique_ptr` hoặc `shared_ptr` (R.20), ưu tiên `unique_ptr` trừ khi quyền sở hữu thực sự được chia sẻ (R.21), và tạo chúng bằng `make_unique` và `make_shared` (R.22, R.23). Một hàm nhận `unique_ptr` theo giá trị là một *sink*: nó tuyên bố rằng nó nhận quyền sở hữu; một hàm chỉ dùng đối tượng thì nhận `T&` hoặc `T*` (R.30).

**Ví dụ.** Quyền sở hữu các đối tượng `Probe` được chuyển giữa các `unique_ptr`, với một kiểu in ra khi được tạo và hủy (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Các đối tượng được tạo và hủy theo thứ tự nào, và sau `b = std::move(c)` ai sở hữu đối tượng nào?

```cpp
#include <iostream>
#include <memory>
#include <utility>

struct Probe {
    int id;
    explicit Probe(int i) : id(i) { std::cout << "make " << id << '\n'; }
    ~Probe() { std::cout << "drop " << id << '\n'; }
};

std::unique_ptr<Probe> pass_on(std::unique_ptr<Probe> p) { return p; }

int main() {
    auto a = std::make_unique<Probe>(1);
    auto b = std::make_unique<Probe>(2);
    auto c = pass_on(std::move(a));
    std::cout << "a empty: " << (a == nullptr) << ", c->id = " << c->id << '\n';
    b = std::move(c);
    std::cout << "after b = move(c): b->id = " << b->id << '\n';
}
```

**Lời giải.** `make_unique` tạo đối tượng 1 và 2 (`make 1`, `make 2`). Truyền `a` qua `pass_on` chuyển quyền sở hữu hai lần (vào tham số, rồi vào giá trị trả về khởi tạo `c`) mà không tạo hay hủy `Probe` nào; `a` trở nên rỗng và `c->id` bằng 1. Phép gán `b = std::move(c)` phải giải phóng thứ `b` đang sở hữu trước khi tiếp quản, nên đối tượng 2 bị hủy tại dòng đó (`drop 2`) và `b` giờ sở hữu đối tượng 1. Đối tượng 1 bị hủy đúng một lần, khi `b` ra khỏi scope ở cuối `main`. Chương trình in ra:

```text
make 1
make 2
a empty: 1, c->id = 1
drop 2
after b = move(c): b->id = 1
drop 1
```

### Vector tăng trưởng, vô hiệu hóa (invalidation) và chi phí di chuyển phần tử

Bài học nói rằng tăng quá capacity có thể làm các pointer mất hiệu lực. Các quy tắc chính xác nằm trong bảng "Iterator invalidation" của `std::vector` (cppreference): `push_back` và `emplace_back` vô hiệu hóa *mọi* iterator, pointer và reference nếu capacity thay đổi, còn nếu không thì chỉ `end()`; `insert` vô hiệu hóa tất cả nếu capacity thay đổi, nếu không thì mọi thứ từ vị trí chèn trở đi; `erase` vô hiệu hóa các phần tử bị xóa và mọi thứ sau chúng; `reserve` vô hiệu hóa tất cả nếu nó đổi capacity và không gì cả nếu không. Do đó một reference tới phần tử `i` chỉ an toàn qua `push_back` nếu bạn biết trước `size() < capacity()`, đó là một tiền điều kiện bạn nên ghi rõ hoặc ép bằng `reserve`.

Vì sao các cài đặt tăng capacity theo cấp số nhân? Giả sử capacity nhân với hệ số $g>1$ ở mỗi lần cấp phát lại, và một lần cấp phát lại ở kích thước $c$ di chuyển $c$ phần tử. Đẩy $n$ phần tử gây ra các lần cấp phát lại ở kích thước $1,g,g^2,\dots,g^{m-1}$ với $g^{m-1}<n$, nên tổng số lần di chuyển phần tử nhiều nhất là
$$\sum_{i=0}^{m-1}g^i\;<\;n\sum_{k\ge0}g^{-k}\;=\;\frac{g}{g-1}\,n .$$
Với $g=2$ đó là dưới $2n$ lần di chuyển tổng cộng, tức amortised $O(1)$ mỗi lần push; với $g=1.5$ là dưới $3n$. Ngược lại, tăng một lượng hằng số sẽ tốn $\Theta(n^2)$ lần di chuyển.

Các lần di chuyển đó là *move* hay *copy* phụ thuộc vào kiểu phần tử. `push_back` có đảm bảo ngoại lệ mạnh (strong exception guarantee; cppreference, `std::vector::push_back`): nếu cấp phát hoặc một thao tác trên phần tử ném exception, vector phải không đổi. Để giữ lời hứa này khi chuyển phần tử, cài đặt dùng `std::move_if_noexcept`, chỉ trả về rvalue nếu move constructor là `noexcept` hoặc kiểu không thể copy (cppreference, `std::move_if_noexcept`). Vì vậy một kiểu có move constructor có thể ném nhưng copy được sẽ bị *copy* ở mỗi lần cấp phát lại. Đó là lý do hiệu năng đằng sau "Make move operations `noexcept`" (C++ Core Guidelines, C.66).

**Ví dụ.** Một vector được cấp dung lượng cho 4 phần tử bằng `reserve(4)`, một con trỏ tới phần tử đầu được lưu lại, và năm phần tử được đẩy vào (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Sau lần đẩy thứ mấy thì con trỏ không còn trỏ tới dữ liệu của vector, và capacity là bao nhiêu?

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.reserve(4);
    int* p = v.data();
    for (int i = 0; i < 5; ++i) {
        v.push_back(i);
        std::cout << "size " << v.size() << " capacity " << v.capacity()
                  << " p still data(): " << (p == v.data()) << '\n';
    }
}
```

**Lời giải.** Bốn lần đẩy đầu giữ $\mathrm{size}\le\mathrm{capacity}=4$ nên không có gì bị relocate, capacity vẫn là 4 và `p` vẫn hợp lệ. Lần đẩy thứ năm gặp $\mathrm{size}=\mathrm{capacity}$ nên vector cần một khối 8, relocate bốn phần tử và giải phóng khối cũ: `size 5 capacity 8`, và `p` trỏ vào một khối đã bị giải phóng. Phép thử `p == v.data()` ở đây chỉ là chẩn đoán: sau một lần cấp phát lại, hai giá trị có thể bằng nhau do trùng hợp khi allocator dùng lại một địa chỉ (Case 2 bên dưới cho thấy đúng điều đó), và `p` vẫn không hợp lệ. Chương trình in ra:

```text
size 1 capacity 4 p still data(): 1
size 2 capacity 4 p still data(): 1
size 3 capacity 4 p still data(): 1
size 4 capacity 4 p still data(): 1
size 5 capacity 8 p still data(): 0
```

### Temporary và kéo dài thời gian sống (lifetime extension)

Một reference chỉ tốt khi đối tượng nó chỉ tới còn sống. Với temporary, ngôn ngữ chỉ có đúng một quy tắc cứu (cppreference, "Reference initialization", mục "Lifetime of a temporary"): khi một reference được *bind trực tiếp* vào một temporary (một prvalue, hoặc một data member hay phần tử mảng được chọn từ nó), temporary sống lâu bằng reference. Vì vậy `const std::string& r = make();` hợp lệ. Các ngoại lệ mới là trọng tâm:

- một temporary bind vào *tham số* reference chỉ sống đến hết biểu thức đầy đủ chứa lời gọi; nếu hàm trả về reference đó, kết quả dangling sau dấu chấm phẩy (`const auto& r = id(make());`);
- một temporary bind trong câu lệnh `return` bị hủy ở cuối biểu thức return;
- việc kéo dài không bắc cầu: reference thứ hai khởi tạo từ reference đầu không kéo dài gì, và một lời gọi hàm xen giữa làm đứt chuỗi;
- member reference của một aggregate kéo dài temporary khi khởi tạo bằng ngoặc nhọn (`A a{make()}`), nhưng không khi khởi tạo bằng ngoặc tròn (`A a(make())`, hợp lệ từ C++20).

Range-based `for` là cái bẫy kinh điển: `for (auto x : f().items())` bind range vào *kết quả của* `items()`, một reference vào temporary bị hủy trước khi vòng lặp bắt đầu nếu `items()` trả về reference. Một kiểu view như `std::string_view` có cùng tính chất với reference: `std::string_view sv = make();` để `sv` trỏ vào một string đã bị hủy. Trong mọi trường hợp này trình biên dịch chấp nhận code, và chỉ một lần chạy sanitizer thực thi dòng đó mới báo lỗi.

**Ví dụ.** Một kiểu thông báo khi được tạo và khi bị hủy cho thấy khi nào một đối tượng tạm chết (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Trong chương trình dưới đây, đối tượng tạm nào được reference giữ sống, và đối tượng còn lại bị hủy khi nào?

```cpp
#include <iostream>
#include <string>

struct Noisy {
    std::string name;
    explicit Noisy(std::string n) : name(std::move(n)) { std::cout << "make " << name << '\n'; }
    ~Noisy() { std::cout << "drop " << name << '\n'; }
};
Noisy make(const char* n) { return Noisy(n); }
const Noisy& id(const Noisy& x) { return x; }

int main() {
    const Noisy& r = make("A");
    std::cout << "after A\n";
    const Noisy& s = id(make("B"));
    std::cout << "after B, s refers to a dead object\n";
    (void)r; (void)s;
}
```

**Lời giải.** `const Noisy& r = make("A");` gắn đối tượng tạm trực tiếp vào `r`, nên lifetime extension áp dụng và `A` sống đến hết `main` (`drop A` là dòng cuối). `id(make("B"))` gắn `B` vào tham số tham chiếu của `id`, nên `B` chỉ sống đến hết full expression đó: nó bị hủy tại dấu chấm phẩy (`drop B`), trước khi dòng kế tiếp chạy, và `s` đã treo tại dòng ấy. Trình biên dịch không đưa ra cảnh báo nào, và mọi việc dùng `s` đều là hành vi không xác định. Chương trình in ra:

```text
make A
after A
make B
drop B
after B, s refers to a dead object
drop A
```

### Reference count, `weak_ptr` và ai được gọi gì

Một `shared_ptr` trỏ tới một *control block* chứa, trong số những thứ khác, số chủ sở hữu chia sẻ và số `weak_ptr`. Khi số chủ sở hữu chia sẻ về không, đối tượng được quản lý bị hủy, nhưng control block chưa được giải phóng cho đến khi số `weak_ptr` cũng về không (cppreference, `std::shared_ptr`). Với `std::make_shared`, đối tượng và control block nằm trong một lần cấp phát duy nhất (lợi ích được nêu trong R.22), nên *bộ nhớ* của đối tượng đã hết hạn chỉ được giải phóng khi `weak_ptr` cuối cùng biến mất, dù destructor của nó đã chạy. `weak_ptr::lock()` trả về một `shared_ptr` rỗng nếu đối tượng đã hết hạn, nên đó là cách an toàn để quan sát một đối tượng bạn không sở hữu. Điều này cũng giải thích vòng lặp (cycle) của Bài tập 7: với `a->peer = b; b->peer = a;` mỗi count là hai, nên sau khi các handle bên ngoài bị bỏ, mỗi node được node kia giữ sống (Core Guidelines phát biểu quy tắc là "use `std::weak_ptr` to break cycles of `shared_ptr`s", R.24). Aliasing constructor `shared_ptr<int>(owner, &owner->field)` dùng chung control block của owner, nên nó giữ sống *toàn bộ* owner trong khi trỏ vào một member.

Count cho biết ai giữ đối tượng sống; chúng không nói gì về việc một *raw reference bạn đã giữ* có an toàn không. Core Guidelines tách riêng điều này trong R.37: không truyền pointer hay reference lấy từ một smart pointer có alias, vì bất cứ thứ gì ở dưới đều có thể reset pointer đó và hủy đối tượng trong khi bạn vẫn đang dùng. Cách sửa là lấy một bản sao cục bộ ("pin") ở đỉnh cây gọi: `auto pin = g_p; f(*pin);`. Các quy tắc tham số R.32 đến R.36 sau đó cho biết một chữ ký hứa điều gì: `unique_ptr<T>` theo giá trị nhận quyền sở hữu, `unique_ptr<T>&` có thể reseat, `shared_ptr<T>` theo giá trị chia sẻ quyền sở hữu, `const shared_ptr<T>&` có thể giữ lại một count, và hàm chỉ dùng đối tượng nên nhận `T&` hoặc `T*` (R.30).

**Ví dụ.** Số đếm mạnh và yếu của một số nguyên được chia sẻ được quan sát (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). `use_count()` và `expired()` bằng bao nhiêu sau khi chép `shared_ptr`, sau khi reset một chủ sở hữu, và sau khi reset chủ cuối cùng, và khi đó `lock()` trả về gì?

```cpp
#include <iostream>
#include <memory>

int main() {
    auto a = std::make_shared<int>(42);
    std::weak_ptr<int> w = a;
    auto b = a;
    std::cout << "use_count " << a.use_count() << ", expired " << w.expired() << '\n';
    a.reset();
    std::cout << "use_count " << b.use_count() << ", expired " << w.expired() << '\n';
    b.reset();
    std::cout << "use_count " << w.use_count() << ", expired " << w.expired()
              << ", lock empty " << (w.lock() == nullptr) << '\n';
}
```

**Lời giải.** Sau `auto b = a;` có hai `shared_ptr` sở hữu số nguyên nên `use_count` bằng 2 và `weak_ptr` `w` chưa hết hạn. Reset `a` còn lại số đếm 1 và đối tượng vẫn sống. Reset `b`, chủ cuối cùng, đưa số đếm về 0 và hủy số nguyên; `w` quan sát được sự hết hạn (`expired 1`) và `lock()` trả về một `shared_ptr` rỗng thay vì con trỏ treo. Chương trình in ra:

```text
use_count 2, expired 0
use_count 1, expired 0
use_count 0, expired 1, lock empty 1
```

## Ví dụ có lời giải

### Trường hợp 1: tham chiếu tới một biến cục bộ đã bị hủy

**Đề bài.** Một hàm `const int& bad() { int x = 3; return x; }` được gọi như `const int& r = bad();` rồi `r` được in ra. Hàm anh em `int good() { int x = 3; return x; }` trả về theo giá trị. Hãy giải thích sau lời gọi mỗi bên gọi nắm giữ gì và trình biên dịch cùng sanitizer báo gì.

**Lời giải.**

1. *Tìm thời gian lưu trữ của `x`.* Nó là biến phạm vi khối, nên có lưu trữ tự động và bị hủy khi thân hàm kết thúc ([basic.stc.auto]).
2. *Lần theo `good`.* `return x;` chép giá trị 3 vào đối tượng trả về, một `int` mới thuộc biểu thức của bên gọi; hủy `x` sau đó không quan trọng. Bên gọi nắm giá trị 3.
3. *Lần theo `bad`.* Kiểu trả về là một tham chiếu, nên `return x;` gắn kết quả vào chính `x`, không có bản sao. Khi thân hàm kết thúc, `x` bị hủy, nên tham chiếu `r` ở nơi gọi gọi tên một đối tượng đã hết vòng đời: một tham chiếu treo (cppreference, "Reference declaration", mục "Dangling references"; Core Guidelines F.43).
4. *Biên dịch.* Với g++ 11.4.0 và `-std=c++20 -Wall -Wextra -g`, trình biên dịch đưa ra `warning: reference to local variable 'x' returned [-Wreturn-local-addr]` cho `bad`. Lúc chạy, chương trình không tối ưu thoát với mã 139 (SIGSEGV): GCC 11 biên dịch một lệnh trả về như vậy thành tham chiếu null. Với `-fsanitize=address,undefined` báo cáo là `runtime error: reference binding to null pointer of type 'const int'` tiếp theo là `AddressSanitizer: SEGV on unknown address 0x000000000000` tại dòng in `r`. Hành vi là không xác định, nên trình biên dịch hay mức tối ưu khác có thể in 3, hoặc rác.
5. *Chạy `good`.* Chương trình chỉ gọi `good()` và in kết quả (g++ 11.4.0, `-std=c++20 -Wall -Wextra`) in `3` và không có cảnh báo.

**Kiểm tra.** Cảnh báo là phép kiểm tra tĩnh của trình biên dịch rằng địa chỉ trả về là của một biến cục bộ; sanitizer là phép kiểm tra động. Hai bên khớp nhau. Một lập luận độc lập là số đối tượng: sau khi `good` trả về có không đối tượng `x` và một giá trị `int` ở bên gọi; sau khi `bad` trả về có không đối tượng `x` và một tham chiếu tới không gì cả.

**Rút ra.** Trả về theo giá trị luôn an toàn với một biến cục bộ; trả về tham chiếu chỉ an toàn khi đối tượng được tham chiếu sống lâu hơn lời gọi, và "nó in ra 3 một lần" không phải bằng chứng.

### Trường hợp 2: chín lần push vào một vector mới

**Đề bài.** Một `std::vector<int> v` bắt đầu rỗng. Sau lần `push_back` đầu tiên một con trỏ `int* p = v.data();` được lưu lại. Rồi tám phần tử nữa được đẩy vào từng cái một. Với libstdc++ (hệ số tăng 2), hãy liệt kê capacity sau mỗi lần push, những lần push nào cấp phát khối mới, tổng cộng có bao nhiêu lần chuyển chỗ phần tử, và khi nào `p` hợp lệ. So sánh với cận $\frac{g}{g-1}n$ của phần lý thuyết.

**Lời giải.**

1. *Quy tắc capacity.* Một lần push với $\mathrm{size}<\mathrm{capacity}$ lưu phần tử tại chỗ; ngược lại vector cấp phát một khối $g\cdot\mathrm{capacity}$ (ở đây $g=2$; lần cấp phát đầu có capacity 1), chuyển chỗ $\mathrm{size}$ phần tử và giải phóng khối cũ.
2. *Lần theo các lần push.* Push 1: capacity 1 (cấp phát). Push 2: size 1 bằng capacity 1, nên cấp phát khối mới 2 và chuyển 1 phần tử. Push 3: size 2 bằng capacity 2, khối mới 4, chuyển 2 phần tử. Push 4: size 3 < 4, tại chỗ. Push 5: size 4 bằng capacity, khối mới 8, chuyển 4 phần tử. Push 6, 7, 8: tại chỗ. Push 9: size 8 bằng capacity, khối mới 16, chuyển 8 phần tử.
3. *Đếm.* Cấp phát ở push 1, 2, 3, 5, 9: **5** lần cấp phát, capacity $1,2,4,8,16$. Chuyển chỗ: $1+2+4+8=15$.
4. *So với cận.* Cận là $\frac{g}{g-1}n=\frac{2}{1}\cdot9=18$ và $15<18$, đúng như phải thế.
5. *Hiệu lực của `p`.* Con trỏ được lấy sau push 1, từ khối capacity 1. Các push 2, 3, 5 và 9 mỗi lần thay khối, nên `p` không hợp lệ từ push 2 trở đi; nó *không* được phục hồi bởi các lần push sau tình cờ không di chuyển gì.
6. *Chạy thử.* Chương trình dưới đây in, cho mỗi lần push, capacity, có cấp phát lại hay không và giá trị `p == v.data()` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`):

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.push_back(0);
    int* p = v.data();
    std::size_t moves = 0;
    std::size_t allocs = 0;
    std::size_t cap = v.capacity();
    std::cout << "push 1: capacity " << cap << '\n';
    ++allocs;
    for (int i = 1; i < 9; ++i) {
        std::size_t old_size = v.size();
        v.push_back(i);
        bool moved = v.capacity() != cap;
        if (moved) { ++allocs; moves += old_size; cap = v.capacity(); }
        std::cout << "push " << i + 1 << ": capacity " << v.capacity()
                  << (moved ? ", reallocated" : "") << ", p == data(): " << (p == v.data()) << '\n';
    }
    std::cout << "allocations " << allocs << ", elements moved " << moves << '\n';
}
```

Đầu ra: `push 1: capacity 1`; `push 2: capacity 2, reallocated, p == data(): 0`; `push 3: capacity 4, reallocated, p == data(): 1`; `push 4: capacity 4, p == data(): 1`; `push 5: capacity 8, reallocated, p == data(): 0`; push 6 đến 8 với `capacity 8` và `0`; `push 9: capacity 16, reallocated, p == data(): 0`; và `allocations 5, elements moved 15`.

![Dòng thời gian qua chín lần push: bậc thang capacity 1, 2, 4, 8, 16 vẽ theo số thứ tự push, các lần push cấp phát lại được đánh dấu, khoảng mà con trỏ p còn gọi tên một khối sống, và các lần chuyển chỗ 1, 2, 4, 8.](/lesson-figures/CPP02-4.svg)

*Hình: bậc thang capacity của Trường hợp 2. Con trỏ `p` chỉ hợp lệ ở push 1; sự trùng hợp ở push 3 (`p == data()` đúng) là allocator dùng lại khối đã giải phóng, không phải tính hợp lệ.*

**Kiểm tra.** Các số đếm khớp với công thức đóng $\sum_{i<4}2^i=2^4-1=15$ cho bốn lần cấp phát lại sau lần cấp phát đầu, và $15<18$. Dòng gây bất ngờ là push 3, nơi `p == data()` in 1 dù khối capacity 1 đã được giải phóng ở push 2: allocator trả lại đúng địa chỉ đó cho khối mới. Vì vậy so sánh con trỏ không thể dùng để kiểm tra hiệu lực; tiêu chuẩn nói mọi con trỏ vào khối cũ đều không hợp lệ sau bất kỳ lần cấp phát lại nào (cppreference, `std::vector`, "Iterator invalidation"), bất kể giá trị của chúng.

**Rút ra.** Nhân đôi capacity cho ít lần cấp phát (5 cho 9 phần tử) và ít hơn $2n$ lần chuyển chỗ, nhưng mỗi lần đều làm mọi con trỏ mất hiệu lực, nên một con trỏ đã lưu cần `reserve` (và bảo đảm về size) hoặc phải thay bằng chỉ số.

### Trường hợp 3: sắp xếp lại các thành viên của một struct

**Đề bài.** Một bản ghi telemetry có các thành viên `char flag; double stamp; char kind; int count;`. Tính `sizeof` và các độ lệch thành viên của nó theo quy tắc bố cục, rồi tìm một thứ tự khai báo có kích thước nhỏ hơn, và xác nhận cả hai bằng cách biên dịch.

**Lời giải.**

1. *Kích thước và alignment.* `char` 1/1, `double` 8/8, `int` 4/4 (kích thước/alignment tính bằng byte trên nền tảng này). Alignment của bản ghi là $A=\max(1,8,1,4)=8$.
2. *Độ lệch theo thứ tự đã cho.* $o_{\text{flag}}=0$; $o_{\text{stamp}}=\lceil1/8\rceil\cdot8=8$; $o_{\text{kind}}=8+8=16$; $o_{\text{count}}=\lceil17/4\rceil\cdot4=20$. Cuối thành viên cuối là $20+4=24$, đã là bội của 8, nên $\mathrm{sizeof}=24$. Padding: 7 byte sau `flag`, 3 sau `kind`, không có ở cuối: 10 byte.
3. *Sắp xếp theo alignment giảm dần.* `double stamp; int count; char flag; char kind;` cho $o=0,8,12,13$; điểm cuối là 14, làm tròn lên bội của 8 cho $\mathrm{sizeof}=16$ với 2 byte padding sau `kind` (padding đuôi).
4. *Tiết kiệm.* $24-16=8$ byte mỗi bản ghi, một phần ba; với mảng $10^6$ bản ghi là 8 MB.
5. *Biên dịch.* Đầu ra của chương trình dưới đây (g++ 11.4.0, `-std=c++20 -Wall -Wextra`): `S1 size 24 align 8 offsets 0 8 16 20` và `S2 size 16 align 8 offsets 0 8 12 13`.

```cpp
#include <cstddef>
#include <iostream>

struct S1 { char a; double b; char c; int d; };
struct S2 { double b; int d; char a; char c; };

int main() {
    std::cout << "S1 size " << sizeof(S1) << " align " << alignof(S1) << " offsets "
              << offsetof(S1, a) << ' ' << offsetof(S1, b) << ' ' << offsetof(S1, c) << ' ' << offsetof(S1, d) << '\n';
    std::cout << "S2 size " << sizeof(S2) << " align " << alignof(S2) << " offsets "
              << offsetof(S2, b) << ' ' << offsetof(S2, d) << ' ' << offsetof(S2, a) << ' ' << offsetof(S2, c) << '\n';
}
```

(Trong chương trình, các thành viên được đặt tên `a, b, c, d` theo thứ tự `flag, stamp, kind, count` của bản ghi.)

**Kiểm tra.** Tải trọng là $1+8+1+4=14$ byte, nên 16 là bội nhỏ nhất của alignment chứa được nó, và không thứ tự nào làm tốt hơn; thứ tự 24 byte lãng phí 10 byte. Các độ lệch biên dịch ra bằng các độ lệch tính tay.

**Rút ra.** `sizeof` là quy tắc bố cục áp dụng cho một thứ tự cụ thể; hãy sắp xếp thành viên theo alignment giảm dần trừ khi một bố cục ngoài cố định cấm điều đó.

## Bài tập

1. **(Dễ)** Với mỗi đoạn code, hãy nói handle trả về có hợp lệ không, và vì sao: (a) `int f() { int x = 3; return x; }`; (b) `const int& g() { int x = 3; return x; }`; (c) `int* h() { static int x = 3; return &x; }`. Với đoạn không hợp lệ, hãy nêu thuật ngữ C++ chỉ thứ mà người gọi đang giữ. *(Phỏng theo: C++ Core Guidelines, F.43 on returning pointers or references to locals)*
2. **(Dễ)** Hãy dự đoán đầu ra và cho biết cuối cùng có bao nhiêu đối tượng `int` tồn tại:
   ```cpp
   auto a = std::make_unique<int>(7);
   auto b = std::move(a);
   std::cout << (a == nullptr) << ' ' << *b;
   ```
   Vì sao dòng `auto c = b;` không biên dịch được, và vì sao đó là một tính năng đối với driver robot sở hữu một device handle? *(Phỏng theo: cppreference, std::unique_ptr)*
3. **(Vừa)** **Tìm lỗi.** Một logger giữ lần quét lidar mới nhất:
   ```cpp
   struct Logger {
       const std::vector<double>* last = nullptr;
       void on_scan(const std::vector<double>& s) { last = &s; }
   };
   void tick(Logger& log) {
       std::vector<double> scan = read_lidar();   // 360 ranges
       log.on_scan(scan);
   }
   ```
   Khi nào `last` trở nên không hợp lệ? Đưa ra hai cách sửa (một cách sao chép, một cách chia sẻ quyền sở hữu) và ước lượng chi phí sao chép ở 10 Hz.
4. **(Vừa)** Code lấy `double* p = &v[0];` rồi gọi `v.push_back(x)` trong một vòng lặp. Hãy giải thích, dùng capacity, khi nào `p` không còn hợp lệ. Nếu capacity nhân đôi bắt đầu từ 1, có bao nhiêu lần cấp phát xảy ra khi push 100 phần tử, và lời gọi nào loại bỏ chúng khi bạn biết kích thước cuối?
5. **(Vừa)** Một planner và một visualiser cùng đọc một bản đồ được dựng một lần khi khởi động. Hãy quyết định giữa sao chép giá trị, `unique_ptr`, `shared_ptr<const Map>` và con trỏ thô. Biện luận lựa chọn của bạn và nêu một chi phí.
6. **(Vừa)** **Tìm lỗi.**
   ```cpp
   void load(const std::string& path) {
       Config* c = new Config();
       if (!c->read(path)) return;     // early return
       apply(*c);
       delete c;
   }
   ```
   Đường nào bị rò rỉ? Nếu một `Config` bị rò rỉ nặng 2 MB và `load` thất bại 5 lần mỗi giây, thì bao nhiêu bộ nhớ bị rò rỉ trong 10 phút? Viết lại sao cho không đường nào có thể rò rỉ. *(Phỏng theo: C++ Core Guidelines, R.11 and R.20 on owning resources)*
7. **(Khó)** Hai node giữ lẫn nhau: `struct Node { std::shared_ptr<Node> peer; };` và `a->peer = b; b->peer = a;`. Theo dõi bộ đếm tham chiếu khi các handle bên ngoài cuối cùng biến mất, giải thích vì sao các node không bao giờ bị hủy, và sửa bằng `weak_ptr`.
8. **(Khó)** **Đọc một báo cáo sanitizer.** AddressSanitizer báo `heap-use-after-free` trên một lần đọc trong `Controller::update`, với "freed by thread T0 here" trỏ vào `std::vector<Sample>::push_back` và "previously allocated" trong `Controller::record`. Hãy dựng lại lỗi có khả năng nhất, nói cách bạn xác nhận nó, và vì sao một lần chạy sạch ở chỗ khác chứng minh rất ít. *(Phỏng theo: the AddressSanitizer documentation in the Clang manual)*
9. **(Khó)** Thiết kế quyền sở hữu của một pipeline camera: một driver tạo ra các frame, một detector và một recorder tiêu thụ chúng ở các tốc độ khác nhau. Chọn kiểu cho frame và hàng đợi, ai sở hữu gì, và làm thế nào để một recorder chậm không giữ buffer của driver sống vô thời hạn.
10. **(Dự án)** Viết một class `Tracked` đếm số đối tượng còn sống. Dựng ba kịch bản (di chuyển một `unique_ptr`, hủy một phần tử của vector, ép một lần cấp phát lại vector) và assert số đếm đối tượng còn sống sau mỗi kịch bản. Chạy nó dưới `-fsanitize=address,undefined`, rồi cố ý đưa vào một tham chiếu treo và thu lại báo cáo.

11. **(Thử thách)** **Chi phí thật của `push_back`.** (a) Suy ra cận $\frac{g}{g-1}n$ cho tổng số lần di chuyển phần tử khi push $n$ lần với hệ số tăng $g$, và tính nó cho $g=2$ và $g=1.5$ tại $n=1000$. (b) Viết một kiểu phần tử đếm số lần copy và move construction, rồi khởi tạo ba phiên bản: copy được với move `noexcept`, copy được với move không `noexcept`, và chỉ-move với move không `noexcept`. Với $n=1000$ lần `emplace_back` trên một vector mới, ghi lại số lần cấp phát lại (theo dõi `capacity()`), số copy và số move cho từng loại, rồi lặp lại phiên bản đầu sau `reserve(1000)`. (c) Giải thích từng dòng của bảng bằng strong exception guarantee và `std::move_if_noexcept`. (d) Một đồng nghiệp lưu `T* p = &v[0]` và nói "tôi gọi `reserve` trước nên `p` an toàn". Nêu chính xác những thao tác nào về sau giữ `p` hợp lệ và những thao tác nào không. (adapted from cppreference, `std::vector` (Iterator invalidation), `std::vector::push_back` and `std::move_if_noexcept`; C++ Core Guidelines, C.66)
12. **(Thử thách)** **Cái nào dangling?** Biên dịch với `g++ -std=c++20 -g -fsanitize=address,undefined` và, trước khi chạy, phân loại từng trường hợp là hợp lệ hay dangling và nêu quy tắc:
    ```cpp
    std::string make() { return std::string(64, 'x'); }
    const std::string& id(const std::string& s) { return s; }
    struct H { std::vector<int> v{1, 2, 3}; const std::vector<int>& items() const { return v; } };
    H mk() { return H{}; }
    struct A { const std::string& r; };
    struct P { std::string s{std::string(64, 'y')}; };
    P mkp() { return P{}; }
    // (A)  const std::string& r = make();             use r[0]
    // (B)  const std::string& r = id(make());         use r[0]
    // (C)  std::string_view sv = make();              use sv[0]
    // (D1) A a{make()};                               use a.r[0]
    // (D2) A a(make());                               use a.r[0]
    // (E)  for (int x : mk().items()) sum += x;
    // (F)  const std::string& m = mkp().s;            use m[0]
    // (G)  const std::string& m = id(mkp().s);        use m[0]
    ```
    Báo cáo loại báo lỗi của sanitizer cho từng trường hợp thất bại. Sau đó nêu vì sao (E) hợp lệ trở lại trong C++23 nhưng (B) và (G) không bao giờ trở nên hợp lệ. (adapted from cppreference, "Reference initialization", section "Lifetime of a temporary", and "Range-based for loop", section "Temporary range initializer")
13. **(Thử thách)** **Một danh sách với `next` mạnh và `prev` yếu.** Xây dựng `struct Node { int id; std::shared_ptr<Node> next; std::weak_ptr<Node> prev; };` và một danh sách $n=3$ node với handle `head` và `tail`. (a) In `use_count()` của chủ sở hữu từng node trước khi giải phóng bất cứ thứ gì, và giải thích từng con số. (b) Dự đoán, rồi in ra, thứ tự các lời gọi destructor sau `tail.reset()` rồi `head.reset()`, dùng quy tắc rằng thân destructor chạy trước khi các member bị hủy. (c) Lặp lại với $n=10^5$ và $n=10^6$ trên stack 8 MB mặc định và báo cáo chuyện gì xảy ra; giải thích từ (b). (d) Viết phần dọn dẹp lặp (iterative) tránh vấn đề này và cho thấy $10^6$ node vượt qua. (e) Nêu điều gì thay đổi nếu `prev` là `shared_ptr`. (adapted from cppreference, `std::shared_ptr` and `std::weak_ptr`; C++ Core Guidelines, R.24)
14. **(Thử thách)** **Một reference lấy từ smart pointer có alias.** Lấy
    ```cpp
    std::shared_ptr<Widget> g_p;
    void g() { g_p = std::make_shared<Widget>(); }
    int f(Widget& w) { g(); return w.x; }
    // main: g_p = std::make_shared<Widget>(); std::cout << f(*g_p);
    ```
    (a) Nói chính xác đối tượng nào bị hủy và khi nào, và bạn kỳ vọng báo cáo sanitizer nào. (b) Đưa ra ba cách sửa (pin một bản sao cục bộ, đổi chữ ký, tái cấu trúc quyền sở hữu) và chi phí của từng cách. (c) Gán cho mỗi chữ ký `void a(Widget&)`, `void b(Widget*)`, `void c(std::unique_ptr<Widget>)`, `void d(std::unique_ptr<Widget>&)`, `void e(std::shared_ptr<Widget>)`, `void h(const std::shared_ptr<Widget>&)` hợp đồng mà nó hứa, dùng R.30 đến R.36. (d) Cách sửa 1 có giúp được không nếu `g()` reset một `unique_ptr<Widget>` toàn cục? Vì sao có hay không? (adapted from C++ Core Guidelines, R.30 to R.37, in particular R.37)

## Cài đặt tham khảo

Hãy đọc hợp đồng (contract) trước. Dự đoán đầu ra trước khi chạy code ở máy bạn. Phần này dùng để học; bài nộp sao chép từ đây là thực hành có hỗ trợ, không phải bằng chứng độc lập.

```cpp
#include <memory>
#include <cassert>
int main() {
    auto a = std::make_unique<int>(7);
    auto b = std::move(a);
    assert(!a);
    assert(*b == 7);
} // b releases the object here
```

## Thực hành độc lập

### Mục tiêu
Làm cho quyền sở hữu quan sát được: đếm các đối tượng còn sống khi di chuyển, hủy và cấp phát lại, và xem một vector làm vô hiệu một địa chỉ đã lưu. Kết thúc bằng việc chạy chương trình dưới các sanitizer.

### Chuẩn bị
Một trình biên dịch C++17. Đặt code khởi đầu và các bài kiểm thử vào `lab.cpp` rồi build bằng `g++ -std=c++17 -Wall -Wextra -Wpedantic -g lab.cpp -o lab && ./lab`; sau đó build lại với `-fsanitize=address,undefined`.

### Nhiệm vụ
1. Cài đặt `make_tracked` và `transfer`; trước khi chạy, hãy dự đoán `Tracked::live` sau mỗi dòng của khối kiểm thử đầu tiên.
2. Cài đặt `pick_larger`; kiểm tra rằng đối tượng bị loại bỏ được hủy mà không cần `delete` tường minh nào.
3. Cài đặt `make_ramp` trả về theo giá trị và giải thích vì sao điều này an toàn.
4. Cài đặt `reallocation_moves_storage` và `weak_expires_after_reset`.
5. Build lại với sanitizer. Sau đó trong một file nháp hãy lấy `int* p = &v[0]`, push cho đến khi cấp phát lại, đọc `*p`, và ghi lại báo cáo của sanitizer (đừng giữ nó trong file lab).

### Code khởi đầu
```cpp
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

struct Tracked {                       // given: counts live objects
    static int live;
    int id;
    explicit Tracked(int i) : id(i) { ++live; }
    Tracked(const Tracked&) = delete;
    Tracked& operator=(const Tracked&) = delete;
    ~Tracked() { --live; }
};
int Tracked::live = 0;

// Create a Tracked with this id, owned by the returned unique_ptr.
std::unique_ptr<Tracked> make_tracked(int id) { throw std::logic_error("not implemented"); }

// Take ownership of p and give it back to the caller (move, never copy).
std::unique_ptr<Tracked> transfer(std::unique_ptr<Tracked> p) { throw std::logic_error("not implemented"); }

// Return the object with the larger id; the other one must be destroyed.
std::unique_ptr<Tracked> pick_larger(std::unique_ptr<Tracked> a, std::unique_ptr<Tracked> b) { throw std::logic_error("not implemented"); }

// Return n values 0.0, 1.0, ... by value (no pointers to locals).
std::vector<double> make_ramp(std::size_t n) { throw std::logic_error("not implemented"); }

// Fill a vector<int> to exactly its capacity, remember data() as an integer,
// push_back one more element, and return true if the storage moved.
bool reallocation_moves_storage() { throw std::logic_error("not implemented"); }

// Make a shared_ptr<Tracked>, take a weak_ptr to it, reset the shared_ptr,
// and return whether the weak_ptr is now expired.
bool weak_expires_after_reset() { throw std::logic_error("not implemented"); }
```

### Kiểm thử
Dán đoạn này bên dưới code khởi đầu (cùng một file) rồi chạy. Mọi kiểm tra đều là `assert` thuần; lần thất bại đầu tiên sẽ dừng chương trình.

```cpp
int main() {
    assert(Tracked::live == 0);
    {   // moving ownership does not create or destroy objects
        auto a = make_tracked(5);
        assert(Tracked::live == 1);
        auto b = transfer(std::move(a));
        assert(a == nullptr && b != nullptr && b->id == 5 && Tracked::live == 1);
    }
    assert(Tracked::live == 0);                         // destroyed at scope end
    {   // the loser is destroyed inside pick_larger
        auto big = pick_larger(make_tracked(3), make_tracked(9));
        assert(big->id == 9 && Tracked::live == 1);
        auto tie = pick_larger(make_tracked(4), make_tracked(4));
        assert(Tracked::live == 2);
    }
    assert(Tracked::live == 0);
    {   // elements of a vector of unique_ptr are owned by the vector
        std::vector<std::unique_ptr<Tracked>> v;
        for (int i = 0; i < 3; ++i) v.push_back(make_tracked(i));
        assert(Tracked::live == 3);
        v.erase(v.begin());
        assert(Tracked::live == 2);
    }
    assert(Tracked::live == 0);
    auto r = make_ramp(4);
    assert(r.size() == 4 && r[0] == 0.0 && r[3] == 3.0 && make_ramp(0).empty());
    assert(reallocation_moves_storage());               // old pointers would dangle
    assert(weak_expires_after_reset() && Tracked::live == 0);
    std::cout << "ramp size " << r.size() << ", live objects at end " << Tracked::live << "\n";
    std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi
Một lời giải đúng sẽ in ra kết quả sau; với sanitizer, đầu ra giống hệt và không có báo cáo nào xuất hiện.

```text
ramp size 4, live objects at end 0
all tests passed
```

### Thử thách mở rộng
Viết `class SampleBuffer` sở hữu một `std::vector<double>`, cung cấp `const std::vector<double>& samples() const`, và có `void push(double)`. Hãy chứng minh bằng một bài kiểm thử rằng một tham chiếu đã lưu từ `samples()` chỉ còn hợp lệ qua `push` nếu bạn `reserve` trước, và ghi tài liệu hợp đồng đó trong một comment.

## Kiểm chứng

Hãy kiểm tra mọi khẳng định về vòng đời bằng hai đường độc lập. Tĩnh: build với `-Wall -Wextra` (các cảnh báo như `-Wreturn-local-addr`) và đọc từng tham chiếu hay con trỏ thoát ra khỏi một hàm. Động: build với `-fsanitize=address,undefined -g` và chạy một bài kiểm thử thực thi đường nghi ngờ; nêu loại báo cáo của sanitizer (`heap-use-after-free`, `stack-use-after-scope`, `heap-buffer-overflow`) và so với loại đã dự đoán. Kiểm tra các khẳng định về bố cục bằng `static_assert(sizeof(S) == 16)` và `offsetof`, để một thay đổi thứ tự thành viên hay nền tảng làm hỏng build thay vì một giao thức trên dây. Kiểm tra quyền sở hữu bằng một kiểu đếm như `Tracked` của bài lab: khẳng định số đối tượng đang sống sau một phép di chuyển, sau khi hủy một phần tử vector và sau một lần cấp phát lại. Nhớ điều mỗi công cụ không cho thấy: một lần chạy sanitizer sạch chỉ bao phủ các đường đã thực thi, và `p == v.data()` không phải phép thử hiệu lực.

## Lỗi thường gặp

- **Tham chiếu treo tới biến cục bộ:** trả về `const T&` tới một biến khối, hoặc lưu `&s` của một tham số mà bên gọi sẽ hủy (bộ logger của Bài tập 3). GCC có thể biến nó thành tham chiếu null, nên triệu chứng có thể là một crash xa nguyên nhân.
- **Con trỏ vào vector bị vô hiệu:** `push_back`, `insert` hay `erase` sau khi lấy `&v[0]`; khối cũ bị giải phóng, và địa chỉ cũ vẫn có thể bằng một địa chỉ mới.
- **Đối tượng tạm chết tại dấu chấm phẩy:** `const auto& r = id(make());`, `std::string_view sv = make();`, hay `for (auto x : f().items())` trước C++23.
- **Rò rỉ ở đường thoát sớm:** một `new` thô với `delete` ở cuối (Bài tập 6), hoặc một chu trình `shared_ptr` (Bài tập 7).
- **Tham chiếu lấy từ một con trỏ thông minh có bí danh:** một hàm được gọi reset `shared_ptr` toàn cục trong khi bên gọi vẫn dùng `*g_p` (Bài tập 14).
- **Giả định về bố cục:** `memcpy` một struct ra định dạng trên dây, hoặc đọc từng byte một struct có padding; các byte padding không có giá trị có nghĩa, và bố cục có thể khác nhau giữa các nền tảng và trình biên dịch.
- **Sở hữu chung không phải an toàn đa luồng:** số đếm của control block là nguyên tử, còn đối tượng được trỏ tới thì không.

## Phương án khác và đánh đổi

- **Ngữ nghĩa giá trị trước.** Trả về một `std::vector` theo giá trị là rẻ (move hoặc copy elision) và không có câu hỏi về vòng đời; cái giá là một bản sao ở chỗ ý định là chia sẻ.
- **`unique_ptr` so với `shared_ptr` so với con trỏ hay tham chiếu thô không sở hữu.** `unique_ptr` có kích thước của một con trỏ và không tốn chi phí lúc chạy; `shared_ptr` thêm control block, một bộ đếm nguyên tử và sự ràng buộc vòng đời; con trỏ hay tham chiếu thô chỉ đúng khi một chủ sở hữu sống lâu hơn được bảo đảm ở nơi khác (R.3, R.30).
- **Chỉ số hay handle thay cho con trỏ.** Một chỉ số vào vector sống qua lần cấp phát lại (nhưng không qua việc erase các phần tử trước nó); một handle có thế hệ (generational) còn phát hiện được việc dùng sau khi xóa, với cái giá là một lần tra cứu.
- **`reserve` so với `std::deque` hay `std::list`.** `reserve` giữ một khối liên tục và dùng được khi biết kích thước tối đa; `std::deque` không bao giờ chuyển chỗ các phần tử đã có khi `push_back` (tham chiếu còn hợp lệ, iterator thì không) với giá là không liên tục; `std::list` giữ địa chỉ mọi nút ổn định nhưng tốn một lần cấp phát mỗi phần tử.
- **Sắp xếp lại thành viên so với bố cục có tài liệu.** Sắp thành viên theo alignment giảm dần tiết kiệm bộ nhớ; một định dạng trên dây tường minh với số nguyên độ rộng cố định và các hàm tuần tự hóa an toàn hơn khi các byte rời khỏi tiến trình.

## Vận dụng và ghi nhớ

Một callback lưu một con trỏ tới một buffer cảm biến tạm thời. Hãy mô tả một kịch bản thất bại và thiết kế lại hợp đồng sở hữu để callback có thể sống lâu hơn lời gọi của bên sản xuất một cách an toàn.

Hãy đóng tài liệu tham khảo trước khi thử. Không nhìn tài liệu, hãy vẽ ra giấy hình của từng thứ sau: một `std::vector<double>` 6 phần tử với một con trỏ tới phần tử 2 trước và sau một lần `push_back` cấp phát lại; bản đồ byte của `struct { char a; short b; int c; }` cùng kích thước của nó; và chủ sở hữu, các bên quan sát yếu và control block của một `shared_ptr` trao cho hai bên tiêu thụ. Nêu với mỗi cái handle nào mất hiệu lực khi nào. Quay lại sau ít nhất một tuần và dựng lại từ một trang giấy trắng các thời gian lưu trữ, quy tắc bố cục và bảng vô hiệu hóa, rồi đối chiếu với bài.

## Đáp án bài tập

1. (a) hợp lệ: một bản sao của giá trị được trả về. (b) không hợp lệ: `x` cục bộ bị hủy khi return, nên người gọi giữ một **tham chiếu treo (dangling reference)**. (c) hợp lệ trong suốt thời gian chương trình chạy vì `x` có thời gian lưu trữ tĩnh (static storage) (nhưng đó là trạng thái toàn cục dùng chung, không thread-safe).
2. Đầu ra `1 7`: sau khi move, `a` là null và `b` sở hữu giá trị; tồn tại một `int`. `unique_ptr` không sao chép được vì phải có đúng một chủ sở hữu; với một device handle, điều này ngăn hai chủ sở hữu cùng đóng nó.
3. `last` trỏ vào `scan` cục bộ, vốn bị hủy khi `tick` return, nên mọi lần dùng sau đó là hành vi không xác định. Cách sửa 1: `std::vector<double> last;` và `last = s;` (sao chép). Cách sửa 2: truyền `std::shared_ptr<const std::vector<double>>` và lưu nó. Chi phí sao chép là $360\times8=2880$ B, ở 10 Hz khoảng $29$ kB/s: không đáng kể.
4. `p` không hợp lệ ngay khi `push_back` vượt quá capacity hiện tại, vì các phần tử chuyển sang một khối mới. Các capacity $1,2,4,\dots,128$ cho **8** lần cấp phát với 100 phần tử. `v.reserve(100)` trước vòng lặp chỉ còn một lần cấp phát và giữ các con trỏ hợp lệ đến kích thước đó.
5. Tốt nhất: `std::shared_ptr<const Map>` (chỉ đọc, vòng đời gắn với người dùng cuối cùng) hoặc, nếu cả hai bên tiêu thụ nằm cùng scope và không sống lâu hơn, một `const Map&`. Sao chép giá trị nhân đôi một bản đồ lớn; `unique_ptr` không chia sẻ được; con trỏ thô không nói gì về quyền sở hữu. Chi phí: một bộ đếm tham chiếu atomic và vòng đời chia sẻ khó lập luận hơn.
6. `return` sớm làm rò rỉ `c` (`delete` bị bỏ qua; một exception từ `apply` cũng rò rỉ). $2\ \text{MB}\times5\times600=6000$ MB, 6 GB. Sửa: `auto c = std::make_unique<Config>();` (hoặc chỉ `Config c;`), không có `delete`.
7. Sau `a->peer = b; b->peer = a;` mỗi node có số đếm 2 (handle cục bộ cộng peer). Bỏ các handle cục bộ để lại số đếm 1, do nhau giữ, nên không cái nào về 0: một sự rò rỉ. Làm một chiều thành `std::weak_ptr<Node> peer;` (không sở hữu) để số đếm về 0.
8. Một con trỏ/tham chiếu/iterator vào vector (có thể được lưu trong `record`) được dùng trong `update` sau khi `push_back` cấp phát lại và giải phóng khối cũ. Xác nhận bằng cách chạy kịch bản lỗi với ASan, tìm địa chỉ đã lưu, và kiểm tra `capacity()` trước/sau; sửa bằng cách lưu một chỉ số, dùng `reserve`, hoặc sao chép. Một lần chạy sạch ở chỗ khác chứng minh rất ít vì sanitizer chỉ báo các đường đã được thực thi.
9. Một thiết kế tốt: frame là `std::shared_ptr<const Frame>` lấy từ một pool; mỗi consumer có một hàng đợi có giới hạn (hoặc một slot "chỉ mới nhất") để recorder chậm bỏ hoặc nhảy qua frame thay vì ghim bộ nhớ; driver sở hữu pool và tái sử dụng các buffer có use count đã giảm về một. Nó nêu điều gì xảy ra khi tràn và rằng các consumer không bao giờ sửa các frame dùng chung.
10. Một câu trả lời tốt assert: di chuyển một `unique_ptr` không đổi số đếm còn sống; hủy một phần tử vector giảm đi một; cấp phát lại một vector gồm các đối tượng di chuyển được giữ số đếm còn sống bằng số phần tử sau khi move (các bản sao, nếu có, bị hủy). Thí nghiệm tham chiếu treo cho thấy `heap-use-after-free` cùng stack trace cấp phát và giải phóng. Thí nghiệm này được giữ ngoài code điều khiển.

11. (a) Các lần cấp phát lại xảy ra ở kích thước $1,g,\dots,g^{m-1}$ với $g^{m-1}<n$, và mỗi lần di chuyển số phần tử bằng kích thước hiện tại, nên số move $\le\sum_{i<m}g^i<n(1+g^{-1}+g^{-2}+\cdots)=\frac{g}{g-1}n$. Với $n=1000$: $2000$ cho $g=2$ và $3000$ cho $g=1.5$. (b) Kết quả từ g++ 11.4.0 (libstdc++, hệ số tăng 2) với $n=1000$: move noexcept, copy được: 11 lần cấp phát lại, 0 copy, **1023 move**; move có thể ném, copy được: 11 lần cấp phát lại, **1023 copy**, 0 move; move có thể ném, chỉ-move: 11 lần cấp phát lại, 0 copy, 1023 move; sau `reserve(1000)`: 0 lần cấp phát lại, 0 copy, 0 move. Các capacity là $1,2,4,\dots,1024$, nên số move là $1+2+\dots+512=1023<2n$, phù hợp với (a). (c) `push_back` và `emplace_back` phải để vector không đổi nếu có gì ném exception (strong guarantee). Chuyển phần tử sang khối mới bằng một move có thể ném sẽ để khối cũ bị rút ruột dở dang, nên `move_if_noexcept` chọn copy khi move có thể ném *và* copy tồn tại; khi kiểu chỉ-move không có lựa chọn an toàn nào, nó vẫn move và đảm bảo bị từ bỏ (cppreference). `reserve` loại bỏ mọi việc chuyển chỗ. (d) Sau `reserve(N)`, pointer `p` tới phần tử 0 vẫn hợp lệ qua bất kỳ số lần `push_back`/`emplace_back` nào miễn `size()` không bao giờ vượt $N$ (capacity khi đó không đổi), và qua `pop_back` (chỉ vô hiệu hóa phần tử bị xóa và `end()`) miễn phần tử 0 không phải cái bị xóa. Nó bị vô hiệu hóa bởi: `push_back` quá $N$ (capacity đổi, tất cả mất hiệu lực); `insert` ở đầu (mọi thứ từ vị trí chèn trở đi, kể cả phần tử 0, dù không cấp phát lại); `erase(begin())`; `clear()` và `operator=`/`assign` (luôn vô hiệu hóa); `shrink_to_fit` (có thể cấp phát lại); và `reserve` với đối số lớn hơn (capacity đổi). Vì vậy "tôi gọi `reserve` trước" là một lời hứa về *bao nhiêu* phần tử sẽ được thêm, nên được kiểm tra (`assert(v.size() < v.capacity())` trước mỗi lần chèn) hoặc mã hóa bằng cách dùng chỉ số thay vì pointer.
12. Đã kiểm chứng với g++ 11.4.0, `-std=c++20`, ASan+UBSan. Hợp lệ: (A) temporary được bind trực tiếp vào reference nên thời gian sống được kéo dài (chương trình in `x`); (D1) khởi tạo aggregate bằng ngoặc nhọn kéo dài member reference (in `x`); (F) một data member của temporary, bind trực tiếp, nằm trong quy tắc kéo dài (in `y`). Dangling: (B) temporary được bind vào *tham số* của `id`, nên nó chết ở cuối biểu thức đầy đủ và `r` trỏ vào nó (ASan: `stack-use-after-scope`); (C) temporary `std::string` bị hủy, để view trỏ vào vùng heap đã giải phóng (`heap-use-after-free`, vì 64 ký tự vượt bộ đệm small-string); (D2) khởi tạo aggregate bằng ngoặc tròn, mới có từ C++20, không kéo dài (`stack-use-after-scope`); (E) range được bind vào reference do `items()` trả về, temporary `H` chết trước thân vòng lặp (`stack-use-after-scope`); (G) giống (B): tham số reference chấm dứt việc kéo dài (`stack-use-after-scope`). (E) được sửa trong C++23: trang range-based `for` nói rằng từ C++23, thời gian sống của mọi temporary trong range-initialiser được kéo dài đến hết vòng lặp (trước đó là hành vi không xác định); trong C++20 cách vòng là một init-statement, `for (H h = mk(); int x : h.items())`. (B) và (G) không phải vòng range-based `for`, nên quy tắc đó không áp dụng: temporary được bind vào một *tham số* reference, và theo quy tắc tham số nó chỉ tồn tại đến hết biểu thức đầy đủ chứa lời gọi. Sửa bất kỳ cái nào bằng cách copy giá trị: `std::string s = id(make());`.
13. (a) Với `head`, `tail` và `n = 3`: node 1 có count $1$ (chỉ `head`), node 2 có $1$ (chỉ `node1.next`), node 3 có $2$ (`node2.next` và `tail`); các con trỏ `prev` là yếu và không thêm gì vào count mạnh (đã kiểm tra khi chạy: `use(head)=1 use(2nd)=1 use(tail)=2`). (b) `tail.reset()` chỉ hạ count của node 3 từ 2 xuống 1; không gì bị hủy. `head.reset()` hạ count của node 1 xuống 0, nên thân destructor của nó chạy (`~Node(1)`), rồi các member của nó bị hủy, giải phóng `next` và hủy node 2 (`~Node(2)`), và cứ thế: đầu ra là `~Node(1) ~Node(2) ~Node(3)`. (c) Việc hủy là đệ quy: `next` của mỗi node hủy node kế tiếp bên trong destructor của node trước. Đo với `ulimit -s` $=8192$ kB ở `-O0`: $n=10^5$ hoàn tất, $n=10^6$ bị crash với exit status 139 (SIGSEGV do tràn stack). Ngưỡng chính xác phụ thuộc kích thước frame và mức tối ưu. (d) `while (head && head.use_count() == 1) head = std::move(head->next);` tách node kế tiếp ra trước khi node hiện tại bị hủy, nên mỗi node bị hủy ở độ sâu một; khi đó $n=10^6$ hoàn tất với cùng thứ tự destructor. (e) Nếu `prev` mạnh, mỗi cặp kề nhau sẽ sở hữu lẫn nhau: count bằng 2 cho mỗi node ở giữa, không cái nào về không sau `head.reset()` (cycle của Bài tập 7) và cả danh sách sẽ bị rò rỉ.
14. (a) `f` nhận một reference tới widget do `g_p` sở hữu. `g()` gán một widget mới cho `g_p`, bỏ chủ sở hữu duy nhất của widget cũ và hủy nó; `w.x` trong `f` khi đó đọc bộ nhớ đã giải phóng. ASan báo `heap-use-after-free` trên một lần READ cỡ 4 trong `f`, với stack trace giải phóng nằm dưới `g` (đã tái hiện với g++ 11.4.0; phiên bản có pin không báo lỗi và in `42`). (b) Cách 1: `auto pin = g_p; f(*pin);` ở bên gọi, chi phí một lần tăng reference count (atomic) cho cả cây gọi (R.37). Cách 2: đổi `f` nhận `std::shared_ptr<Widget>` theo giá trị (R.34), giữ count riêng với cùng chi phí nhưng làm cho sự phụ thuộc thời gian sống hiện ra trong chữ ký. Cách 3: tái cấu trúc để không có gì được `f` gọi có thể reset `g_p` (ví dụ biến global thành bất biến sau khi khởi động, hoặc truyền widget xuống từ một owner sống lâu hơn lời gọi); không tốn chi phí lúc chạy nhưng cần kỷ luật và review thiết kế. (c) `a`: dùng đối tượng, không null, không có vai trò về thời gian sống; `b`: dùng nó, có thể null; `c`: nhận quyền sở hữu (sink), bên gọi phải `std::move`; `d`: có thể reseat hoặc reset pointer của bên gọi (R.33); `e`: chia sẻ quyền sở hữu (R.34); `h`: có thể giữ lại một count hoặc không, nên là lời hứa yếu hơn và smart pointer chỉ có đó vì thời gian sống (R.36). Các hàm chỉ dùng đối tượng nên ưu tiên `a` hoặc `b` (R.30). (d) Không: không thể copy pin vì `unique_ptr` là chủ sở hữu duy nhất; nếu `g()` reset `unique_ptr` toàn cục thì đối tượng bị hủy bất kể. Cách chữa là về cấu trúc: đừng để hàm được gọi với tới pointer sở hữu, hoặc chuyển quyền sở hữu vào một biến cục bộ trong suốt cây gọi.

## Đọc thêm

[LearnCpp](https://www.learncpp.com/) — khóa học chính, tài liệu, hoặc bộ tham khảo được cung cấp. Hãy theo mục chủ đề liên quan; đây là các liên kết đọc thêm, không phải các chương sách được sao chép lại.

- [C++ working draft](https://eel.is/c++draft/) - [basic.stc.general], [basic.stc.auto], [basic.stc.dynamic], [basic.align], [class.temporary].
- [cppreference: Storage duration](https://en.cppreference.com/w/cpp/language/storage_duration), [Object](https://en.cppreference.com/w/cpp/language/object) (alignment), [sizeof](https://en.cppreference.com/w/cpp/language/sizeof), [offsetof](https://en.cppreference.com/w/cpp/types/offsetof), [std::unique_ptr](https://en.cppreference.com/w/cpp/memory/unique_ptr) và [operator new](https://en.cppreference.com/w/cpp/memory/new/operator_new).
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector) (iterator invalidation) và [std::move_if_noexcept](https://en.cppreference.com/w/cpp/utility/move_if_noexcept).
- [cppreference: Reference initialization](https://en.cppreference.com/w/cpp/language/reference_initialization) (lifetime of a temporary) và [Range-based for loop](https://en.cppreference.com/w/cpp/language/range-for).
- [cppreference: std::shared_ptr](https://en.cppreference.com/w/cpp/memory/shared_ptr) và các quy tắc Core Guidelines C.66, R.22 đến R.24 và R.30 đến R.37.

**Thực hành thêm:** [LearnCpp chapter 22 quiz](https://www.learncpp.com/cpp-tutorial/chapter-22-summary-and-quiz/) (move semantics và smart pointer), các bài [LearnCpp std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) và [std::shared_ptr](https://www.learncpp.com/cpp-tutorial/stdshared_ptr/), các [C++ Core Guidelines resource-management rules](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management), và [AddressSanitizer use-after-free example](https://github.com/google/sanitizers/wiki/AddressSanitizerExampleUseAfterFree).
