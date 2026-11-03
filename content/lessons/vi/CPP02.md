---
{"title": "Bộ nhớ, tham chiếu và vòng đời đối tượng", "summary": "Giải thích ai sở hữu một đối tượng và một tham chiếu còn hợp lệ trong bao lâu.", "objectives": ["Phân biệt giá trị, địa chỉ, con trỏ và tham chiếu.", "Nhận diện tham chiếu treo (dangling) và vùng lưu trữ bị vô hiệu hóa.", "Dùng RAII và các container chuẩn để quản lý quyền sở hữu."]}
---

## Vì sao điều này quan trọng

Giải thích ai sở hữu một đối tượng và một tham chiếu còn hợp lệ trong bao lâu. Bài học này phát triển phép tính cốt lõi trước khi yêu cầu bạn áp dụng nó vào một bối cảnh mới. Hãy làm bài chẩn đoán trước nếu bạn nghĩ mình đã biết rồi; việc từng dùng công cụ không phải là bằng chứng của sự hiểu.

## Trực giác

Con trỏ là một giá trị có thể trỏ tới một đối tượng trong bộ nhớ; bản thân nó không phải là quyền sở hữu. Tham chiếu là một bí danh (alias). Tính đúng đắn phụ thuộc vào việc đối tượng còn tồn tại hay không và một thao tác có di chuyển vùng lưu trữ của nó hay không. Vẽ ra vòng đời của các đối tượng thường hữu ích hơn việc nhìn chằm chằm vào địa chỉ.

![Dòng thời gian của một lần cấp phát lại vector: con trỏ tới phần tử 0 trong khối cũ trở thành treo sau khi các phần tử chuyển sang khối lớn hơn, trong khi unique_ptr chuyển giao một mũi tên sở hữu duy nhất.](/lesson-figures/CPP02.svg)

*Một con trỏ chỉ hợp lệ chừng nào đối tượng nó trỏ tới còn hợp lệ; cấp phát lại và thoát khỏi scope đều kết thúc vòng đời.*

## Lý thuyết và suy dẫn

Một đối tượng cục bộ tự động bị hủy khi scope của nó kết thúc. Trả về con trỏ hoặc tham chiếu tới nó để lại một handle treo. Sao chép một giá trị tạo ra một đối tượng khác với vòng đời riêng; sao chép một con trỏ chỉ tạo ra một giá trị địa chỉ khác.

`std::vector` sở hữu vùng lưu trữ phần tử liên tục (contiguous). Tăng quá dung lượng (capacity) có thể cấp phát một khối mới, di chuyển các phần tử, và vô hiệu hóa con trỏ, tham chiếu và iterator trỏ tới vùng lưu trữ cũ. Một đối tượng vector có thể vẫn còn sống trong khi con trỏ tới một phần tử cũ của nó trở nên không hợp lệ. Đừng dựa vào việc quan sát thấy địa chỉ ổn định trong một lần chạy.

RAII gắn việc giải phóng tài nguyên với việc hủy đối tượng. `std::unique_ptr<T>` sở hữu một đối tượng cấp phát động và không thể sao chép; di chuyển (move) sẽ chuyển giao quyền sở hữu. `std::shared_ptr<T>` chia sẻ quyền sở hữu bằng bộ đếm tham chiếu và có thêm chi phí. Cả hai đều không tự động làm cho việc truy cập an toàn với luồng (thread-safe). Hãy ưu tiên giá trị và container cho đến khi thật sự cần sở hữu động.

Để kiểm tra các lỗi bộ nhớ nghi ngờ, hãy biên dịch code của chính bạn với `-fsanitize=address,undefined -g`. Sanitizer phát hiện nhiều thao tác không hợp lệ được thực thi; vượt qua một lần chạy không phải là bằng chứng rằng mọi vòng đời đều đúng.

## Ví dụ có lời giải

Hàm `const int& bad(){ int x=3; return x; }` trả về một tham chiếu sau khi x đã bị hủy. Ngược lại, `int good(){ int x=3; return x; }` trả về một giá trị. Với vector v, lấy &v[0] rồi gây ra một lần cấp phát lại có thể vô hiệu hóa con trỏ đó dù v vẫn còn tồn tại.

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

Hãy kiểm tra ví dụ số đã giải một cách độc lập, sau đó thử một trường hợp biên và một bất biến từ phần suy dẫn. Giữ kết quả mong đợi tách biệt với phần cài đặt. Cố ý đổi một dấu hoặc bỏ một số hạng: các bài kiểm thử của bạn phải loại bỏ phiên bản bị hỏng đó. Dùng bài chẩn đoán để kiểm tra khái niệm và lập luận bằng số; các câu trả lời ngắn vẫn là thực hành được hướng dẫn bằng rubric.

## Lỗi thường gặp

“Địa chỉ đó vẫn chứa 3” không làm cho một đối tượng đã bị hủy trở nên hợp lệ. Sở hữu chia sẻ ngăn được một số việc hủy sớm nhưng có thể đưa vào chu trình (cycle) và không sửa được data race.

## Phương án khác và đánh đổi

Ngữ nghĩa giá trị (value semantics) đơn giản hóa việc lập luận về vòng đời. unique_ptr biểu đạt quyền sở hữu độc quyền. shared_ptr hữu ích cho các vòng đời thực sự được chia sẻ nhưng thêm sự ràng buộc và chi phí; tham chiếu không sở hữu vẫn phù hợp khi vòng đời được đảm bảo ở nơi khác.

## Vận dụng và ghi nhớ

Một callback lưu con trỏ tới một buffer cảm biến tạm thời. Hãy mô tả một kịch bản thất bại và thiết kế lại hợp đồng sở hữu để callback có thể sống lâu hơn lời gọi của producer một cách an toàn.

Hãy đóng tài liệu tham khảo trước khi thử. Giải thích các giả định của bạn và một cách mà câu trả lời của bạn có thể sai. Quay lại sau ít nhất một tuần và dựng lại lập luận chính từ một trang giấy trắng. Một bài quiz đơn thuần không kiểm chứng được khả năng vận dụng vào tình huống lạ hay năng lực ở mức nghiên cứu.

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

## Đọc thêm

[LearnCpp](https://www.learncpp.com/) — khóa học chính, tài liệu, hoặc bộ tham khảo được cung cấp. Hãy theo mục chủ đề liên quan; đây là các liên kết đọc thêm, không phải các chương sách được sao chép lại.

**Thực hành thêm:** [LearnCpp chapter 22 quiz](https://www.learncpp.com/cpp-tutorial/chapter-22-summary-and-quiz/) (move semantics và smart pointer), các bài [LearnCpp std::unique_ptr](https://www.learncpp.com/cpp-tutorial/stdunique_ptr/) và [std::shared_ptr](https://www.learncpp.com/cpp-tutorial/stdshared_ptr/), các [C++ Core Guidelines resource-management rules](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#r-resource-management), và [AddressSanitizer use-after-free example](https://github.com/google/sanitizers/wiki/AddressSanitizerExampleUseAfterFree).
