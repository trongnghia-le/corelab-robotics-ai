---
{"title": "Cơ bản C++: kiểu dữ liệu, phạm vi và giá trị có thể dự đoán", "summary": "Viết một chương trình biên dịch nhỏ và hiểu phép tính số học của nó.", "objectives": ["Biên dịch và chạy một chương trình C++17.", "Dự đoán phép tính số nguyên và số thực dấu phẩy động.", "Dùng vector và tham chiếu const một cách an toàn."]}
---

## Vì sao điều này quan trọng

Viết một chương trình biên dịch nhỏ và hiểu phép tính số học của nó. Bài học này phát triển phép tính cốt lõi trước khi yêu cầu bạn áp dụng nó vào một bối cảnh mới. Hãy làm bài chẩn đoán trước nếu bạn nghĩ mình đã biết rồi; việc từng dùng công cụ không phải là bằng chứng của sự hiểu.

## Trực giác

C++ làm cho cách biểu diễn dữ liệu và vòng đời đối tượng (lifetime) trở nên hiển hiện. Một kiểu (type) cho trình biên dịch biết phép toán nào hợp lệ, nhưng cũng quyết định số học và bố cục bộ nhớ. Biên dịch bắt được một số lỗi trước khi chạy; các bài kiểm thử phải bắt những hành vi sai mà vẫn là C++ hợp lệ.

Hãy hình dung bộ nhớ là một hàng dài các byte được đánh số, và mỗi biến là một đoạn của hàng đó có đóng dấu một kiểu. Kiểu quyết định cùng lúc ba việc: đối tượng chiếm bao nhiêu byte, các bit trong những byte đó được đọc ra sao (số nguyên bù hai, số dấu phẩy động nhị phân IEEE 754, một địa chỉ), và trình biên dịch chấp nhận những phép toán nào. Bốn byte `00 00 80 3f` là số nguyên 1065353216 khi đọc như `int` và là số 1.0 khi đọc như `float`; bản thân các byte không nói điều đó, chỉ có khai báo mới nói. Đây là khác biệt cốt lõi so với Python, nơi mỗi đối tượng mang kiểu của nó lúc chạy và số nguyên không bao giờ tràn. Trong C++ kiểu được cố định lúc biên dịch và phép tính được thực hiện trong kiểu mà trình biên dịch suy ra từ các toán hạng, không phải kiểu mà lập trình viên nghĩ tới.

Một tình huống cụ thể. Một robot đi được 9 m trong 4 s. Chương trình dưới đây lưu tốc độ trung bình theo hai cách, rồi lấy kích thước của một vector ba số đọc trừ đi 4. Nó được biên dịch bằng g++ 11.4.0 (`-std=c++20 -Wall -Wextra`) mà không có cảnh báo nào. Hãy dự đoán ba số được in ra trước khi đọc tiếp.

```cpp
#include <iostream>
#include <vector>

int main() {
    int meters{9};
    int seconds{4};
    double v1 = meters / seconds;
    double v2 = static_cast<double>(meters) / seconds;
    std::vector<int> w{10, 20, 30};
    std::cout << v1 << ' ' << v2 << ' ' << w.size() - 4 << '\n';
}
```

![Sơ đồ bộ nhớ kiểu stack: một vector double có kích thước 3 với chỉ số hợp lệ từ 0 đến 2, cùng phép chia số nguyên so với số thực của 5 cho 2.](/lesson-figures/CPP01.svg)

*Hình: kiểu quyết định số học. Phép chia nguyên `5 / 2` bị cắt cụt thành 2 trong khi `5.0 / 2` giữ 2.5, và chỉ số hợp lệ của vector dừng ở `size() - 1`; ô nhớ sau phần tử cuối vẫn tồn tại nhưng không thuộc vector.*

**Kiểm tra dự đoán.** Chương trình in `2 2.25 18446744073709551615`. Số đầu là `2`, không phải `2.25`: cả hai toán hạng của `meters / seconds` đều là `int` nên phép chia là chia nguyên và trả về 2; chỉ sau đó số 2 mới được đổi thành `2.0` để gán cho `double` bên trái dấu `=`. Dòng thứ hai ép kiểu một toán hạng trước, nên phép chia thực hiện bằng số thực và cho 2.25. Số thứ ba không âm và cũng không phải lỗi: `w.size()` có kiểu không dấu `std::size_t` (64 bit trên máy này), nên `3 - 4` quay vòng modulo $2^{64}$ thành $2^{64}-1 = 18446744073709551615$.

Hai trực giác sai nằm sau phần lớn lỗi C++ của người mới. Thứ nhất là "kiểu ở bên trái dấu `=` quyết định phép tính": kiểu của kết quả theo các toán hạng, còn đích chỉ nhận giá trị đã tính xong. Thứ hai là "biên dịch không cảnh báo nghĩa là đã được kiểm tra": trình biên dịch chỉ xác nhận các phép toán hợp lệ với các kiểu, không xác nhận các con số mang đúng ý của tác giả. Các phần sau biến hai bức tranh này thành quy tắc: mỗi biểu thức có kiểu gì (chuyển đổi), kết quả dấu phẩy động mang bao nhiêu sai số, một đối tượng sống bao lâu, và chương trình được phép làm gì ở mép của một vector.

## Lý thuyết và suy dẫn

Một khai báo biến đưa vào một đối tượng có kiểu: `int count{3};` lưu một số nguyên, còn `double dt{0.01};` lưu một giá trị thực xấp xỉ. Hãy khởi tạo mọi biến vô hướng cục bộ trước khi đọc. Phép chia nguyên cắt cụt về phía không: `5/2` là 2, trong khi `5.0/2` là 2.5. Chuyển kết quả đã bị cắt cụt sang double sau đó không khôi phục được phần thập phân đã mất.

Hàm khai báo kiểu trả về và các tham số có kiểu. Truyền vector theo giá trị (by value) sẽ sao chép nó; `const std::vector<double>&` cho phép hàm xem vector hiện có mà không sửa. Đối tượng được tham chiếu phải còn sống trong suốt lời gọi. Phạm vi cục bộ (scope) quyết định tên nào nhìn thấy được ở đâu và khi nào các đối tượng tự động thông thường bị hủy.

Dùng `std::vector` cho một dãy có kích thước xác định lúc chạy. `size()` của nó là một số đếm, còn chỉ số hợp lệ chạy từ không đến kích thước trừ một. `operator[]` không kiểm tra biên; `.at()` thì có. Ưu tiên vòng lặp range-based khi chỉ số không có ý nghĩa riêng. Biên dịch với cảnh báo được bật và coi mỗi cảnh báo là một câu hỏi cần giải quyết, không phải đồ trang trí.

### Đối tượng, kiểu và khởi tạo bằng danh sách

Một *đối tượng* (object) là một vùng lưu trữ có kiểu; khai báo như `T x{init};` tạo ra nó và cố định cách đọc các bit. Có ba dạng khởi tạo quan trọng trong thực tế. Khởi tạo *mặc định* (default) một biến vô hướng cục bộ (`int n;`) để lại giá trị bất định, và đọc nó là hành vi không xác định (cppreference, "Default-initialization", mục "Indeterminate and erroneous values"). Khởi tạo *giá trị* (value) (`int n{};`, `double d{};`) cho số không. Khởi tạo *bằng danh sách* (ngoặc nhọn) `T x{v};` hoạt động như khởi tạo trực tiếp cộng thêm một quy tắc: các phép chuyển đổi thu hẹp (narrowing) là ill-formed (cppreference, "List-initialization", mục "Narrowing conversions"; tiêu chuẩn [dcl.init.list], đoạn 7 trong bản nháp làm việc hiện hành tại eel.is/c++draft). Một phép chuyển đổi là thu hẹp khi nó có thể làm đổi giá trị: số thực sang số nguyên, số nguyên sang số thực (trừ khi nguồn là hằng số lưu chính xác được), hoặc số nguyên sang kiểu nguyên không chứa hết mọi giá trị của nguồn (trừ khi là hằng số vừa khít). Dạng dấu bằng `int c = 9.99;` thực hiện cùng phép chuyển đổi đó một cách âm thầm; `-Wconversion` cảnh báo về nó, còn `-Wall -Wextra` thì không.

Quy tắc làm việc là khởi tạo mọi đối tượng bằng ngoặc nhọn (C++ Core Guidelines ES.20 và ES.23) và viết `static_cast` ở bất cứ chỗ nào chủ ý thu hẹp (ES.46), để bước mất mát hiện ra với người đọc và với trình biên dịch. Ngoặc nhọn còn loại bỏ một cái bẫy kinh điển: với `int count{3.0 * 2}` trình biên dịch từ chối bộ khởi tạo thay vì âm thầm đổi một `double` rồi lưu 6.

**Ví dụ.** Biên dịch bằng g++ 11.4.0, `-std=c++20 -Wall -Wextra`, chương trình dưới đây in ra gì, và trình biên dịch nói gì nếu thay phép khởi tạo cuối bằng `int d{9.99};`, hoặc nếu thêm `-Wconversion` vào chương trình đầu?

```cpp
#include <iostream>

int main() {
    int a{};
    double b{};
    int c = 9.99;
    std::cout << a << ' ' << b << ' ' << c << '\n';
}
```

**Lời giải.** `{}` khởi tạo giá trị `a` và `b` về không, và `int c = 9.99;` chỉ giữ phần nguyên, 9, không có chẩn đoán nào, nên đầu ra là `0 0 9`. Thay phép khởi tạo cuối bằng `int d{9.99};` thì thành một phép chuyển đổi thu hẹp (narrowing) trong ngoặc nhọn, và quá trình build dừng với `error: narrowing conversion of '9.9900000000000002e+0' from 'double' to 'int' [-Wnarrowing]`. Thêm `-Wconversion` vào chương trình đầu cho `warning: conversion from 'double' to 'int' changes value from '9.9900000000000002e+0' to '9'`. Các chữ số phía sau là giá trị nhị phân thực sự được lưu của 9.99.

### Tham chiếu, `const` và cách truyền đối số

Tham chiếu (reference) là một tên khác của một đối tượng đã có. Trong `double mean(const std::vector<double>& v)` tên `v` gắn với vector của nơi gọi và không có bản sao nào được tạo (cppreference, "Reference declaration"). Tham chiếu phải được khởi tạo ngay tại chỗ khai báo và không thể gắn lại sau đó; tham chiếu tới `const` từ chối ghi qua tên đó, biến câu "hàm này chỉ đọc" thành một khẳng định được trình biên dịch kiểm tra (Core Guidelines Con.1, F.16). Truyền theo giá trị (by value) khởi tạo bằng sao chép tham số từ đối số, nên một vector $n$ phần tử, mỗi phần tử $s$ byte, tốn một lần cấp phát và $ns$ byte sao chép, $O(n)$ mỗi lần gọi; còn tham chiếu tốn một địa chỉ (8 byte trên nền tảng 64 bit) bất kể $n$. Hướng dẫn F.16 rút thành quy tắc ngón tay cái: truyền các kiểu rẻ để sao chép như `int`, `double` hay `std::string_view` theo giá trị và mọi thứ lớn hơn theo `const&`; F.17 dùng tham chiếu không const cho tham số vào-ra, và F.20 ưu tiên giá trị trả về hơn tham số đầu ra.

Cái giá của tham chiếu là vòng đời. Nó không sở hữu đối tượng mà nó gọi tên; nếu đối tượng đó kết thúc trước, tham chiếu bị *treo* (dangle) và dùng nó là hành vi không xác định (cppreference, "Reference declaration", mục "Dangling references"; Core Guidelines F.43 cấm trả về tham chiếu tới đối tượng cục bộ). Trong một lời gọi, đối số luôn sống lâu hơn tham số, nên tham số `const&` là an toàn; nguy hiểm bắt đầu khi tham chiếu được lưu lại hoặc trả về.

**Ví dụ.** Một đám mây điểm gồm 250 000 giá trị `double` được một hàm đọc năm lần, một lần theo giá trị và một lần theo `const&` (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Kiểu này tự đếm số lần sao chép. Mỗi trường hợp xảy ra bao nhiêu lần sao chép, một lần gọi theo giá trị chuyển bao nhiêu byte, và đó là lưu lượng bao nhiêu ở 60 Hz?

```cpp
#include <iostream>
#include <vector>

struct Cloud {
    std::vector<double> p;
    static inline int copies = 0;
    explicit Cloud(std::size_t n) : p(n, 1.0) {}
    Cloud(const Cloud& o) : p(o.p) { ++copies; }
};

double first_by_value(Cloud c) { return c.p[0]; }
double first_by_ref(const Cloud& c) { return c.p[0]; }

int main() {
    Cloud cloud(250000);
    for (int i = 0; i < 5; ++i) first_by_value(cloud);
    std::cout << "after 5 by-value calls: copies = " << Cloud::copies << '\n';
    Cloud::copies = 0;
    for (int i = 0; i < 5; ++i) first_by_ref(cloud);
    std::cout << "after 5 by-reference calls: copies = " << Cloud::copies << '\n';
    std::cout << "bytes per by-value call: " << cloud.p.size() * sizeof(double) << '\n';
}
```

**Lời giải.** Tham số theo giá trị được khởi tạo sao chép ở mỗi lần gọi, nên 5 lần gọi cho `copies = 5`; tham số `const&` gắn vào đối tượng có sẵn và `copies = 0`. Đầu ra là `after 5 by-value calls: copies = 5`, `after 5 by-reference calls: copies = 0`, `bytes per by-value call: 2000000`. Mỗi lần gọi theo giá trị cấp phát và điền $250\,000\times8\text{ B}=2\,000\,000$ B $=2$ MB; với tần số 60 Hz đó là $2\times10^6\times60=1.2\times10^{8}$ B/s $=120$ MB/s lưu lượng mà phiên bản `const&` không tạo ra.

### Phạm vi và vòng đời của đối tượng tự động

*Phạm vi* (scope) của một tên là phần chương trình nơi tên đó dùng được; với biến khai báo trong một khối, nó chạy từ chỗ khai báo đến dấu ngoặc đóng (cppreference, "Scope"). *Vòng đời* (lifetime) của một đối tượng là khái niệm lúc chạy. Đối tượng có thời gian lưu trữ tự động (automatic storage duration), tức là biến cục bộ không `static`, được tạo khi luồng thực thi đi qua định nghĩa của nó và bị hủy khi luồng thực thi rời khối, theo thứ tự ngược với thứ tự khởi tạo (cppreference, "Storage duration", mục "Automatic storage duration"; tiêu chuẩn [basic.stc.auto]). Vùng nhớ lấy từ call stack, nên tạo và hủy một đối tượng như vậy chỉ tốn một phép dịch con trỏ, không cấp phát. Bảo đảm thứ tự ngược này là nền tảng cho các quy tắc quản lý tài nguyên ở bài sau.

Với biến cục bộ, phạm vi và vòng đời trùng nhau, nhưng đó là hai ý niệm khác nhau: tham chiếu hay con trỏ mở rộng *quyền truy cập* tới một đối tượng, không bao giờ mở rộng *vòng đời* của nó. Dùng lại một tên trong phạm vi lồng nhau sẽ che tên ngoài và không được khuyến khích (Core Guidelines ES.12). Hệ quả thứ hai là một hàm không được đưa ra địa chỉ của biến cục bộ của chính nó, vì biến đó đã mất khi hàm trả về.

**Ví dụ.** Một kiểu in ra khi được tạo và khi bị hủy làm cho thứ tự hiện rõ (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Chương trình dưới đây tạo và hủy `a`, `b`, `c`, `d` theo thứ tự nào?

```cpp
#include <iostream>

struct Probe {
    const char* name;
    explicit Probe(const char* n) : name(n) { std::cout << "make " << name << '\n'; }
    ~Probe() { std::cout << "drop " << name << '\n'; }
};

int main() {
    Probe a("a");
    {
        Probe b("b");
        Probe c("c");
        std::cout << "inner block ends\n";
    }
    Probe d("d");
    std::cout << "main ends\n";
}
```

**Lời giải.** Đối tượng được dựng tại chỗ khai báo được chạy tới và bị hủy theo thứ tự ngược lại ở cuối phạm vi của chúng. Đầu ra theo thứ tự là `make a`, `make b`, `make c`, `inner block ends`, `drop c`, `drop b`, `make d`, `main ends`, `drop d`, `drop a`. `c` được tạo sau cùng trong khối trong và bị hủy đầu tiên; `a` được tạo đầu tiên và bị hủy cuối cùng.

### `std::vector`, `size()` và giới hạn chỉ số

Một `std::vector<T>` sở hữu một mảng liên tục gồm `size()` phần tử. `size()` trả về `std::size_t`, một kiểu không dấu, và các chỉ số hợp lệ là $0\le i<\texttt{size()}$. `v[i]` có tiền điều kiện $i<\texttt{size()}$ và không kiểm tra gì: nếu tiền điều kiện sai thì "hành vi là không xác định" (cppreference, "std::vector::operator[]"). `v.at(i)` có kiểm tra và ném `std::out_of_range` (cppreference, "std::vector::at"). Dạng không kiểm tra là mặc định vì nó không tốn gì, nên kỷ luật phải đến từ chỗ khác: vòng lặp `for` theo phạm vi khi chỉ số không có ý nghĩa riêng (Core Guidelines ES.71), truy cập có kiểm tra trong kiểm thử, và bản build có sanitizer (SL.con.3 yêu cầu tránh lỗi biên).

Hành vi không xác định nghĩa là tiêu chuẩn không đặt yêu cầu nào lên chương trình, không phải là nó sẽ crash. Đọc qua cuối mảng một phần tử có thể trả về dữ liệu cũ, dữ liệu của ô lân cận, crash muộn hơn hoặc dường như chạy đúng, và một cờ biên dịch khác có thể đổi kết quả. AddressSanitizer (`-fsanitize=address`) gắn công cụ vào các truy cập heap và stack và dừng ngay ở truy cập ngoài biên đầu tiên bằng một báo cáo nêu rõ dòng sai và kích thước khối nhớ; UndefinedBehaviorSanitizer (`-fsanitize=undefined`) báo cáo các vi phạm khác như tràn số có dấu. Cả hai chỉ xét những đường thực sự được chạy, nên một lần chạy sạch là bằng chứng cho những đầu vào đó chứ không phải chứng minh.

**Ví dụ.** Một vector ba giá trị `int` được đọc ở chỉ số 3 (g++ 11.4.0, `-std=c++20 -Wall -Wextra -g -fsanitize=address,undefined`). Trình biên dịch và lần chạy báo gì, và truy cập nằm chính xác ở đâu?

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{10, 20, 30};
    int i = 3;
    std::cout << v[i] << '\n';
}
```

**Lời giải.** Chương trình biên dịch không cảnh báo, và lúc chạy bị dừng với `AddressSanitizer: heap-buffer-overflow ... READ of size 4 ... t4.cpp:7` cùng `located 0 bytes to the right of 12-byte region`. Các con số khớp với bố cục: cấp phát $3\times4=12$ byte, và chỉ số 3 bắt đầu ở độ lệch byte $3\times4=12$, byte đầu tiên sau khối, nên lần đọc 4 byte bắt đầu cách vùng 0 byte về bên phải. Nếu không có sanitizer, chính chương trình đó sẽ chỉ in ra bất cứ thứ gì nằm sau mảng.

### Chuyển đổi số nguyên, số học modulo và tràn số không xác định

Phép chia nguyên chỉ là một chỗ mà kiểu làm thay đổi con số. Chỗ còn lại là *chuyển đổi trước khi tính*. Với một toán tử nhị phân built-in, các toán hạng trước tiên được promote rồi đưa về một kiểu chung $C$ bằng các phép chuyển đổi số học thông thường (usual arithmetic conversions; cppreference, "Usual arithmetic conversions", Stage 5). Nếu cả hai cùng có dấu hoặc cùng không dấu, $C$ là kiểu có rank lớn hơn. Nếu một bên có dấu ($S$) và một bên không dấu ($U$): khi rank của $U$ không nhỏ hơn rank của $S$, $C$ là $U$; nếu không, khi $S$ biểu diễn được mọi giá trị của $U$ thì $C$ là $S$; còn lại $C$ là kiểu không dấu tương ứng với $S$. Vì vậy, trên nền tảng có `int` và `unsigned int` 32 bit cùng rank, `-3 < 7u` chuyển $-3$ thành $2^{32}-3$ và cho kết quả sai (false).

Sau đó hai quy tắc khác nhau áp dụng cho kết quả. Số học *không dấu* được định nghĩa theo modulo $2^n$ với $n$ bit (cppreference, "Arithmetic operators", Overflows), nên với `int x = -3; unsigned y = 7;`
$$x-y \equiv (2^{32}-3)-7 = 2^{32}-10 = 4294967286 \pmod{2^{32}},$$
đúng bằng giá trị trong ví dụ của C++ Core Guidelines (ES.100). Tràn số *có dấu* không phải là quay vòng: hành vi là không xác định (undefined), và trình biên dịch được phép giả định nó không bao giờ xảy ra (ES.103; cppreference liệt kê quay vòng, bẫy (trap), bão hòa hoặc bị tối ưu bỏ đi là các biểu hiện có thể có). Đó là lý do "dùng `unsigned` để một số đếm không bao giờ âm" (một cách sửa hấp dẫn cho `v.size() - 1`) bị các guidelines bác bỏ (ES.106): giá trị không bị ngăn khỏi âm, nó âm thầm trở thành một số dương rất lớn, và mở cửa cho các tổ hợp signed/unsigned ở trên. Tóm tắt của guidelines: làm toán bằng kiểu có dấu (ES.102), đánh chỉ số bằng kiểu chỉ số có dấu hoặc chuyển đổi một lần ở biên (ES.107), và làm cho việc thu hẹp (narrowing) tường minh (ES.46).

![Một vòng gồm 2^32 giá trị unsigned với 0 ở đỉnh, cách đọc có dấu ở nửa trên, và các mũi tên cho -20 đổi sang unsigned và cho phép trừ 30.](/lesson-figures/CPP01-2.svg)

*Hình: các giá trị unsigned 32 bit nằm trên một vòng. Đổi $-20$ sang `unsigned` đặt nó tại $2^{32}-20$, tức lùi 20 bước từ 0, và trừ 30 lùi thêm 30 bước tới $2^{32}-50 = 4294967246$.*

```explore
{
  "title": "Wrap-around of an n-bit unsigned type",
  "title_vi": "Tràn vòng của kiểu unsigned n bit",
  "prompt": "Predict first: with a 6-bit type (modulus 64) what unsigned value does a true difference of -50 become, and what does the same bit pattern mean when read as a signed number? Then move d across 0 and across the modulus.",
  "prompt_vi": "Dự đoán trước: với kiểu 6 bit (modulo 64), hiệu thật bằng -50 trở thành giá trị unsigned nào, và cùng dãy bit đó có nghĩa gì khi đọc như số có dấu? Sau đó kéo d qua 0 và qua giá trị modulo.",
  "params": [
    { "name": "n", "label": "bits n", "label_vi": "số bit n", "min": 3, "max": 8, "step": 1, "value": 6, "unit": "" },
    { "name": "d", "label": "true value x - y", "label_vi": "giá trị thật x - y", "min": -100, "max": 100, "step": 1, "value": -50, "unit": "" }
  ],
  "let": [
    { "name": "m", "expr": "2^n" },
    { "name": "w", "expr": "d - m*floor(d/m)" },
    { "name": "s", "expr": "w - m*step(w - m/2)" }
  ],
  "plot": {
    "x": { "name": "t", "min": -100, "max": 100, "label": "true value t = x - y", "label_vi": "giá trị thật t = x - y" },
    "y": { "label": "stored value", "label_vi": "giá trị lưu", "min": -110, "max": 260 },
    "series": [
      { "expr": "t", "label": "true value", "label_vi": "giá trị thật", "color": "grey" },
      { "expr": "t - m*floor(t/m)", "label": "unsigned result (t mod 2^n)", "label_vi": "kết quả unsigned (t mod 2^n)", "color": "orange" }
    ],
    "points": [
      { "x": "d", "y": "w", "label": "unsigned result", "label_vi": "kết quả unsigned", "color": "orange" }
    ]
  },
  "readouts": [
    { "label": "modulus 2^n", "label_vi": "modulo 2^n", "expr": "m", "unit": "", "digits": 0 },
    { "label": "unsigned result", "label_vi": "kết quả unsigned", "expr": "w", "unit": "", "digits": 0 },
    { "label": "same bits read as signed", "label_vi": "cùng dãy bit đọc như số có dấu", "expr": "s", "unit": "", "digits": 0 }
  ]
}
```

*Thanh trượt dùng ít bit để quy luật dễ thấy; với `unsigned` 32 bit của bài, modulo là 4294967296 và hình răng cưa có cùng dạng.* Đáp án của câu dự đoán: $-50\bmod 64=14$, và dãy bit 14 có bit cao nhất bằng 0 nên cũng đọc ra $+14$ khi dùng kiểu có dấu; kéo $d$ về $-20$ cho $44$, được đọc là $-20$ vì $44\ge32$.

**Ví dụ.** Trên máy Linux 64 bit với g++ 11.4.0 (`int` 32 bit), một giá trị có dấu $-20$ gặp một giá trị không dấu 30 trong chương trình dưới đây. `a - b`, `a < b`, `c < b` (với `long long c = -20`) và phép ép `a - b` trở lại `int` in ra gì, và lời gọi liên quan `square(50000)` của `int square(int x) { return x * x; }` làm gì?

```cpp
#include <iostream>

int main() {
    int a = -20;
    unsigned b = 30;
    std::cout << a - b << '\n';
    std::cout << (a < b) << '\n';
    long long c = -20;
    std::cout << (c < b) << '\n';
    std::cout << static_cast<int>(a - b) << '\n';
}
```

**Lời giải.** `int` và `unsigned int` có cùng hạng (rank), nên $a$ thành $2^{32}-20=4294967276$ và hiệu là $4294967276-30=4294967246=2^{32}-50$. Phép so sánh `a < b` do đó là $4294967276<30$, sai (`0`), và `-Wall -Wextra` báo điều này (`-Wsign-compare`). Với `long long c`, kiểu chung là `long long`, chứa được mọi `unsigned int`, nên phép so sánh là $-20<30$ và đúng (`1`). Ép kết quả không dấu trở lại `int` cho $-50$, vì phép chuyển đổi trả về giá trị đồng dư modulo $2^{32}$ ([conv.integral], đoạn 3). Đầu ra là `4294967246`, `0`, `1`, `-50`. Lời gọi `square(50000)` là hành vi không xác định vì $2\,500\,000\,000>2^{31}-1$: GCC với `-fsanitize=undefined` báo `signed integer overflow: 50000 * 50000 cannot be represented in type 'int'`, còn không có nó thì in giá trị đã quay vòng $-1794967296=2\,500\,000\,000-2^{32}$, chỉ là một trong các kết quả được phép.

### Mô hình sai số dấu phẩy động và giá của một phép cộng dồn

Dấu phẩy động nhị phân làm tròn mọi phép toán. Với IEEE double làm tròn về số gần nhất, mỗi phép toán cơ bản trả về $\mathrm{fl}(a\circ b)=(a\circ b)(1+\delta)$ với $|\delta|\le u=2^{-53}\approx1.1\times10^{-16}$ (với `float`, $u=2^{-24}\approx6\times10^{-8}$). Đây là mô hình sai số tương đối của Goldberg (Goldberg, *What Every Computer Scientist Should Know About Floating-Point Arithmetic*, mục "Errors In Summation").

Áp dụng vào tổng đệ quy $s_1=x_1$, $s_i=\mathrm{fl}(s_{i-1}+x_i)=(s_{i-1}+x_i)(1+\delta_i)$. Khai triển và bỏ các số hạng bậc hai cho
$$s_n=\sum_{j=1}^{n}x_j\,(1+\theta_j),\qquad |\theta_j|\lesssim (n-j+1)\,u,$$
vì $x_j$ đi qua các phép cộng thứ $j,\dots,n$ và mỗi phép làm nhiễu nó một hệ số $(1+\delta_i)$ (số hạng đầu bị nhiễu khoảng $nu$, số hạng cuối chỉ $u$). Do đó
$$\Bigl|s_n-\sum x_j\Bigr|\;\lesssim\;u\sum_{j}(n-j+1)|x_j|\;\le\;\frac{n(n+1)}{2}\,u\,\max_j|x_j|.$$
Trường hợp xấu nhất tăng như $n^2u$, còn các sai số làm tròn ngẫu nhiên điển hình tăng giống $\sqrt n\,u$, nhưng một độ lệch có hệ thống (cộng $0.1$ lặp đi lặp lại) có thể tiến gần trường hợp xấu nhất. Phép cộng bù của Kahan (compensated summation) giữ các bit thấp bị mất trong một số hiệu chỉnh $c$ và, theo Định lý 8 của Goldberg (mục "Optimizers"), chỉ làm nhiễu mỗi số hạng khoảng $2u+O(nu^2)$ thay vì $(n-j+1)u$. Chứng minh dựa vào việc $(t-s)-y$ khác không: một trình tối ưu coi dấu phẩy động như đại số thực sẽ viết lại nó thành $0$ và phá hỏng thuật toán, đó là lý do không được dùng `-ffast-math` cho code như vậy.

![Hai đường bậc thang của khoảng cách giữa các số dấu phẩy động liền kề theo độ lớn, cho float và double, với các điểm 1e8 và 1e14 được đánh dấu.](/lesson-figures/CPP01-3.svg)

*Hình: khoảng cách giữa hai số liền kề ($\mathrm{ulp}$) tăng gấp đôi mỗi khi độ lớn tăng gấp đôi. Một double gần $10^8$ phân giải được $1.5\times10^{-8}$, gần $10^{14}$ chỉ còn $1.6\times10^{-2}$; một `float` gần $1.7\times10^{7}$ đã nhảy từng bước 2.*

**Ví dụ.** Mô hình làm tròn dự đoán ba điều có thể thấy trong 8 dòng (g++ 11.4.0, `-std=c++20 -Wall -Wextra`). Chương trình dưới đây in ra gì cho `f + 1.0f == f` và `d + 1.0 == d` ở $2^{24}$ và $10^{16}$, cho `0.1 + 0.2` và phép so sánh nó với `0.3`, và cho khoảng cách giữa các số dấu phẩy động ở hai độ lớn đó?

```cpp
#include <cmath>
#include <iomanip>
#include <iostream>

int main() {
    float f = 16777216.0f;                       // 2^24
    double d = 1.0e16;
    std::cout << std::setprecision(17);
    std::cout << (f + 1.0f == f) << ' ' << (d + 1.0 == d) << '\n';
    std::cout << 0.1 + 0.2 << ' ' << (0.1 + 0.2 == 0.3) << '\n';
    std::cout << std::nextafter(f, 1e30f) - f << ' ' << std::nextafter(d, 1e30) - d << '\n';
}
```

**Lời giải.** Đầu ra là `1 1`, `0.30000000000000004 0`, `2 2`. Trên $2^{24}=16\,777\,216$ một `float` không còn biểu diễn được mọi số nguyên, nên cộng 1 không đổi gì (tổng đúng nằm đúng giữa hai số float và làm tròn về lân cận chẵn); một `double` cho kết quả tương tự ở $10^{16}$, nơi khoảng cách là 2, điều mà dòng cuối xác nhận bằng `nextafter`. `0.1 + 0.2` khác `0.3` vì mỗi hằng số trong ba hằng số thập phân được lưu với sai số tương đối tới $u=2^{-53}$, đó là lý do đẳng thức của các double đã tính phải được kiểm tra bằng một dung sai chọn theo thang của dữ liệu.

### Ba cách tính trung bình trượt và nguồn gốc sai số của chúng

Bài học đưa ra trung bình cửa sổ trực tiếp, cập nhật streaming $S_{k+1}=S_k-x_k+x_{k+w}$ và dạng tổng tiền tố (prefix sum) $y_k=(P_{k+w}-P_k)/w$. Sai số dấu phẩy động của chúng tăng theo các cách khác nhau.

- *Trực tiếp*: áp dụng cận ở trên cho $w$ số hạng của một cửa sổ rồi chia cho $w$: sai số của trung bình nhiều nhất khoảng $\tfrac{w+1}{2}\,u\max|x|$, bất kể tín hiệu dài bao nhiêu.
- *Streaming*: sai số trong $S_k$ tích lũy qua mọi cập nhật trước đó và không bao giờ được loại bỏ, nên sau $k$ bước nó có thể tới khoảng $k\,u\,\max|S|$ trong trường hợp xấu nhất và $\sqrt{k}\,u\,\max|S|$ điển hình (sự trôi của Bài tập 9).
- *Tổng tiền tố*: $P_n$ có thể lớn hơn nhiều so với tổng của bất kỳ cửa sổ nào, nên $P_{k+w}$ và $P_k$ đều bị làm tròn ở thang $\mathrm{ulp}(P_n)/2$, và hiệu của chúng, vốn nhỏ, là một *triệt tiêu thảm họa* (catastrophic cancellation) theo nghĩa của Goldberg (mục "Cancellation": trừ hai đại lượng vốn đã chịu sai số làm tròn). Sai số của $y_k$ do đó vào khoảng $\mathrm{ulp}(P_n)/w$, dù cửa sổ ngắn đến đâu.

Biện pháp gần như không tốn kém là trừ trước một giá trị tham chiếu, ví dụ $x_0$ hoặc một ước lượng trung bình chạy, cộng dồn $x_i-x_0$, rồi cộng lại ở cuối: khi đó các tổng có độ lớn của *phần biến thiên*, không phải của *độ lệch nền* (offset). Bài tập 14 đo hiệu ứng này.

**Ví dụ.** Một tín hiệu nhỏ nằm trên một độ lệch (offset) rất lớn làm lộ ra ba biến thể của trung bình trượt (g++ 11.4.0, `-std=c++20 -Wall -Wextra`): trung bình trực tiếp, tổng cửa sổ streaming và tổng tiền tố. Với $x=\{10^{16},1,1,1,1\}$ và $w=2$ các trung bình cửa sổ đúng là $5\times10^{15}+0.5$, rồi 1, 1, 1. Mỗi biến thể in ra gì, và vì sao?

```cpp
#include <iostream>
#include <vector>

int main() {
    const std::vector<double> x{1e16, 1, 1, 1, 1};
    const std::size_t w = 2;
    std::vector<double> p(x.size() + 1, 0.0);
    for (std::size_t i = 0; i < x.size(); ++i) p[i + 1] = p[i] + x[i];
    double s = x[0] + x[1];                       // streaming window sum
    for (std::size_t k = 0; k + w <= x.size(); ++k) {
        double direct = (x[k] + x[k + 1]) / 2.0;
        double prefix = (p[k + w] - p[k]) / 2.0;
        double stream = s / 2.0;
        std::cout << "k=" << k << " direct=" << direct << " streaming=" << stream
                  << " prefix=" << prefix << '\n';
        if (k + w < x.size()) s = s - x[k] + x[k + w];
    }
}
```

**Lời giải.** Đầu ra có bốn dòng: `k=0 direct=5e+15 streaming=5e+15 prefix=5e+15`, rồi với $k=1,2,3$ cùng một bộ ba `direct=1 streaming=0.5 prefix=0`. Trung bình trực tiếp đúng cho ba cửa sổ nhỏ ($(1+1)/2=1$). Tổng streaming bắt đầu bằng $10^{16}+1$, bị làm tròn về $10^{16}$ (khoảng cách ở đó là 2), nên sau khi trừ $x_0=10^{16}$ nó chứa 0 thay vì 1 và sai 1 mãi mãi, cho $s/2=0.5$. Tổng tiền tố (prefix sums) không bao giờ "thấy" các số 1, vì mỗi phép cộng vào $P\approx10^{16}$ làm tròn về lại $P$, nên $P_{k+w}-P_k=0$. Cách chữa trong bài, trừ $x_0$ trước, đưa dữ liệu về $\{0,1,1,1,1\}$, với dữ liệu đó cả ba biến thể đều chính xác.

## Ví dụ có lời giải

### Trường hợp 1: phép chia nguyên giấu mất phần thập phân

**Đề bài.** Một chương trình khai báo `int steps{5};` và `int total{2};` và phải lưu tỉ số của hai số này dưới dạng `double`. Phiên bản đầu là `double ratio = steps / total;`. Hãy nêu giá trị nó lưu và cần đổi gì để được 2.5.

**Lời giải.**

1. *Tìm kiểu của các toán hạng.* Cả hai toán hạng của `/` đều là `int` (khai báo ở trên).
2. *Áp dụng các phép chuyển đổi số học thông thường* (cppreference, "Usual arithmetic conversions"; [expr.arith.conv]). Hai toán hạng đã cùng kiểu nên không có chuyển đổi nào, và phép `/` dựng sẵn cho `int` trả về một `int` là thương bị cắt cụt về phía không: $5=2\cdot2+1$, nên kết quả là 2 dư 1.
3. *Thực hiện phép gán.* Giá trị `int` 2 được đổi sang `double` và lưu chính xác là 2.0. Kiểu `double` ở bên trái không đóng vai trò nào ở bước 2: nó chỉ nhận giá trị đã tính xong.
4. *Chuyển đổi trước khi chia.* Viết `static_cast<double>(steps) / total`. Lúc này các toán hạng là `double` và `int`, `int` được đổi sang `double` (lại là các phép chuyển đổi số học thông thường), và phép chia là $5.0/2.0=2.5$.
5. *Chạy thử.* Biên dịch bằng g++ 11.4.0 (`-std=c++20 -Wall -Wextra`), chương trình

```cpp
#include <iostream>

int main() {
    int steps{5};
    int total{2};
    double ratio_int = steps / total;
    double ratio_fp = static_cast<double>(steps) / total;
    std::cout << ratio_int << ' ' << ratio_fp << '\n';
}
```

in ra `2 2.5`.

**Kiểm tra.** Python cho `5 // 2 = 2` với `5 % 2 = 1`, và `5 / 2 = 2.5`. Đẳng thức $\text{steps}=\text{total}\cdot q+r$ xác nhận cách tách: $2\cdot2+1=5$. Một trường hợp giới hạn cho thấy khi nào lỗi vô hình: với `steps = 4` cả hai phiên bản cùng cho 2, nên một bài kiểm thử mà mọi đầu vào đều chia hết sẽ cho mã hỏng đi qua.

**Rút ra.** Kiểu của các toán hạng chọn phép tính; kiểu của đích chỉ nhận kết quả. Cùng sự cẩn thận đó áp dụng cho `mean` của một vector rỗng, phải bị từ chối trước mọi phép chia.

### Trường hợp 2: tốc độ encoder qua chỗ timer quay vòng

**Đề bài.** Một encoder 4096 xung mỗi vòng tiến thêm 37 xung giữa hai lần đọc một timer 32 bit chạy tự do tính bằng micro giây (`std::uint32_t`). Lần đọc đầu là $t_0=4\,294\,967\,000$ µs, lần thứ hai là $t_1=1200$ µs: timer đã quay vòng đúng một lần ở giữa (nó quay vòng mỗi $2^{32}\,\mu s\approx71.6$ phút). Tính tốc độ trục theo rad/s và rpm, và cho thấy hai lỗi viết mã điển hình sẽ trả về gì.

**Lời giải.**

1. *Thời gian trôi qua.* Hai lần đọc có kiểu `std::uint32_t` (ở đây là `unsigned int`), nên `t1 - t0` là số học không dấu, được định nghĩa modulo $2^{32}$ ([basic.fundamental], đoạn 2; cppreference, "Arithmetic operators", Overflows). Thay số: $\Delta t=(1200-4\,294\,967\,000)\bmod 2^{32}=1200+(4\,294\,967\,296-4\,294\,967\,000)=1200+296=1496\ \mu s$. Điều này đúng miễn là khoảng thời gian thật ngắn hơn $2^{32}$ µs.
2. *Góc đã quay.* Một xung là $2\pi/4096$ rad. Trong mã, số xung và số xung mỗi vòng đều là `int`, nên phân số phải được lập bằng số thực: `static_cast<double>(37) / 4096`, rồi $\Delta\theta=37\cdot\frac{2\pi}{4096}=0.056757$ rad. Nếu viết `37 / 4096 * 2.0 * pi` thì phép chia nguyên cho 0 trước tiên.
3. *Tốc độ.* $\omega=\Delta\theta/\Delta t=0.056757\ \text{rad}/(1.496\times10^{-3}\ \text{s})=37.9394$ rad/s.
4. *Đổi đơn vị.* $37.9394\ \text{rad/s}\times\dfrac{60}{2\pi}=362.29$ rpm.
5. *Chạy thử.* Chương trình dưới đây (g++ 11.4.0, `-std=c++20 -Wall -Wextra`) cũng tính hai phiên bản sai:

```cpp
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>

constexpr double kPi = 3.14159265358979323846;

int main() {
    const int counts_per_rev = 4096;
    const int delta_counts = 37;
    const std::uint32_t t0 = 4294967000u;   // microseconds, just before the 32-bit timer wraps
    const std::uint32_t t1 = 1200u;         // microseconds, just after

    const std::uint32_t dt_us = t1 - t0;    // modulo 2^32
    const double dt_wrong = static_cast<double>(t1) - static_cast<double>(t0);
    const double w_int = delta_counts / counts_per_rev * 2.0 * kPi / (dt_us * 1e-6);
    const double w = static_cast<double>(delta_counts) / counts_per_rev * 2.0 * kPi / (dt_us * 1e-6);

    std::cout << std::fixed << std::setprecision(4);
    std::cout << "dt_us = " << dt_us << "\n";
    std::cout << "dt from doubles = " << dt_wrong << "\n";
    std::cout << "w (int division) = " << w_int << " rad/s\n";
    std::cout << "w = " << w << " rad/s\n";
}
```

Đầu ra: `dt_us = 1496`, `dt from doubles = -4294965800.0000`, `w (int division) = 0.0000 rad/s`, `w = 37.9394 rad/s`.

![Timer micro giây 2^32 vẽ như một vòng với lần đọc t0 ngay trước chỗ quay vòng và t1 ngay sau đó, hai cung 296 và 1200 micro giây, và ba kết quả đã tính.](/lesson-figures/CPP01-4.svg)

*Hình: khoảng thời gian là cung đi từ $t_0$ qua chỗ quay vòng đến $t_1$: $296+1200=1496$ µs. Đổi sang `double` trước khi trừ cho khoảng thời gian âm; chia nguyên cho tốc độ bằng không; thứ tự đúng cho 37.94 rad/s.*

**Kiểm tra.** Một cách thứ hai là "mở vòng" bằng tay: $t_1+2^{32}=4\,294\,968\,496$, và $4\,294\,968\,496-4\,294\,967\,000=1496$ µs. Kiểm tra bậc độ lớn: $37/4096=0.00903$ vòng trong 1.496 ms là 6.04 vòng/s, tức 362 rpm, khớp với bước 4. Python tái hiện $\omega=37.93936$ rad/s.

**Rút ra.** Quay vòng không dấu là một tính năng khi dùng có chủ ý cho hiệu hai mốc timer (trừ trước, trong kiểu không dấu), và là lỗi khi cùng các giá trị đó bị mở rộng trước hoặc trộn với đại lượng có dấu.

## Bài tập

1. **(Dễ)** Một encoder báo `int ticks = 7;` trong `int rev = 2;` vòng quay. Hãy dự đoán giá trị của `double a = ticks / rev;` và của `double b = static_cast<double>(ticks) / rev;`. Phần thập phân bị mất chính xác ở đâu trong `a`? *(Phỏng theo: LearnCpp, the chapter on arithmetic operators and integer division)*
2. **(Dễ)** Một vòng điều khiển chứa `double dt = 1 / 100;` với ý định là chu kỳ 100 Hz. `dt` nhận giá trị nào, bộ điều khiển sau đó làm gì, và có hai cách nào để viết đúng? *(Phỏng theo: C++ Core Guidelines, ES.20 and ES.46 on initialisation and narrowing)*
3. **(Vừa)** **Tìm lỗi.** Đoạn này in một vector theo thứ tự ngược:
   ```cpp
   void print_reversed(const std::vector<double>& v) {
       for (std::size_t i = v.size() - 1; i >= 0; --i)
           std::cout << v[i] << ' ';
   }
   ```
   Hãy giải thích hai thất bại riêng biệt (đầu vào không rỗng và rỗng) và đưa ra một vòng lặp đúng. *(Phỏng theo: C++ Core Guidelines, ES.100 on mixing signed and unsigned)*
4. **(Vừa)** **Dự đoán đầu ra** (suy luận từng câu lệnh trước khi biên dịch):
   ```cpp
   std::vector<int> v{4, 8, 15};
   std::cout << v.size() - 1 << ' ';
   try { std::cout << v.at(3); }
   catch (const std::out_of_range&) { std::cout << "caught"; }
   ```
   `v[3]` sẽ làm gì thay vào đó, và vì sao điều đó tệ hơn đối với robot?
5. **(Vừa)** Một node perception truyền một point cloud (`std::vector<double>` gồm $10^6$ phần tử) tới một bộ lọc ở 30 Hz. Hãy ước lượng lưu lượng bộ nhớ gây ra khi truyền theo giá trị so với `const&`. Đưa ra một signature tránh việc sao chép và ngăn việc sửa đổi.
6. **(Vừa)** Một sinh viên viết `double s = 0; for (int i = 0; i < 10; ++i) s += 0.1; if (s == 1.0) arm_motor();`. Hãy dự đoán motor có được kích hoạt hay không, cho sai số xấp xỉ $1-s$, và viết một phép so sánh an toàn. Giải thích vì sao `double` vẫn tốt hơn `float` ở đây.
7. **(Khó)** **Tìm lỗi.** Một trung bình trượt (moving average) cửa sổ `w` trên `x`:
   ```cpp
   std::vector<double> y;
   for (std::size_t i = 0; i + w < x.size(); ++i) {
       double s = 0;
       for (std::size_t j = i; j < i + w; ++j) s += x[j];
       y.push_back(s / w);
   }
   ```
   Với `x = {1,2,3,4}`, `w = 2` hãy liệt kê nó trả về gì và đáng ra phải trả về gì. Nêu cách sửa và hai đầu vào khác mà hàm phải từ chối.
8. **(Khó)** Bạn làm mượt vận tốc motor đo ở 1 kHz bằng trung bình trượt 11 mẫu. Hãy đặc tả hợp đồng của hàm (kiểu, tiền điều kiện, độ dài đầu ra, ý nghĩa của các đầu ra đầu tiên). Tính độ trễ mà bộ lọc thêm vào cho đầu vào dốc (ramp), và nói khi nào độ trễ đó không chấp nhận được trong một vòng điều khiển.
9. **(Khó)** **Suy dẫn.** Chứng minh rằng cập nhật streaming $y_{k+1}=y_k+(x_{k+w}-x_k)/w$ bằng việc tính lại tổng cửa sổ. Sau đó giải thích vì sao việc dùng lặp lại qua hàng triệu mẫu có thể gây trôi (drift) trong dấu phẩy động, và gợi ý một biện pháp khắc phục.
10. **(Dự án)** Viết `stats.hpp`/`main.cpp` với `mean`, `variance` và `moving_average`, một `main` kiểm thử để kiểm tra các trường hợp tính tay và các đường lỗi, biên dịch với `-std=c++17 -Wall -Wextra -Wpedantic`, rồi dựng lại với `-fsanitize=address,undefined -g` và báo cáo đầu ra của cả hai bản build.

11. **(Thử thách)** **Chuyển đổi quyết định phép so sánh.** Trên máy Linux 64 bit (`int` 32 bit, `long` và `std::size_t` 64 bit), hãy dự đoán từng kết quả và nêu kiểu chung được chọn bởi các phép chuyển đổi số học thông thường: (a) `-3 - 7u` in ra dưới dạng số không dấu; (b) `-3 < 7u`; (c) `int i = -1; std::vector<int> v{1,2,3}; i < v.size()`; (d) `-1LL < 3u`; (e) `short s = -1; unsigned short us = 1; s < us`; (f) `-1L < 1UL`. Suy ra (a) bằng số học modulo. Sau đó viết lại (c) theo hai cách không thể cho kết quả bất ngờ, và nói Core Guidelines ưu tiên cách nào cho chỉ số. Biên dịch với `-Wall -Wextra` và báo cáo trình biên dịch cảnh báo ở dòng nào trong sáu dòng. (adapted from C++ Core Guidelines, ES.100 and ES.106; cppreference, "Usual arithmetic conversions", Stage 5)
12. **(Thử thách)** **Tràn số không phải là quay vòng.** Xét `int area(int h, int w) { return h * w; }` được gọi là `area(10'000'000, 100'000'000)`. (a) Tính tích thật và phần dư của nó theo modulo $2^{32}$, và giá trị `int` mà một máy bù hai sẽ hiện nếu nó quay vòng. (b) Phát biểu chính xác tiêu chuẩn C++ nói gì về lời gọi này, đối chiếu với cùng phép tính trên `unsigned`. (c) Với `bool f(int x) { return x + 1 > x; }` và `f(INT_MAX)`, nói bạn kỳ vọng gì từ trình tối ưu, rồi biên dịch bằng GCC ở `-O0`, `-O2`, `-O2 -fsanitize=undefined` và `-O2 -fwrapv` và báo cáo bốn đáp án. (d) Đưa ra một phiên bản `area` có hợp đồng kiểm tra được và không thể tràn với các đầu vào bạn chấp nhận, cùng cạnh hình vuông lớn nhất mà `int` chứa được. (adapted from C++ Core Guidelines, ES.103; cppreference, "Arithmetic operators", Overflows)
13. **(Thử thách)** **Cộng $10^7$ lần số 0.1.** (a) Suy ra, đến bậc một, cận $\bigl|s_n-\sum x_j\bigr|\lesssim u\sum_j (n-j+1)|x_j|$ cho phép cộng dồn đệ quy. (b) Tính nó với $n=10^7$, $x_j=0.1$ trong `float` ($u=2^{-24}$) và trong `double` ($u=2^{-53}$). (c) Viết các vòng lặp bằng `float`, bằng `double`, và một phiên bản `float` dùng Kahan, rồi báo cáo ba kết quả và sai số của chúng so với $10^7\cdot$`0.1f` (tích chính xác của giá trị đã lưu). (d) Dựng lại với `-O2 -ffast-math` và giải thích chuyện gì xảy ra với kết quả Kahan, dùng đẳng thức $C=((S+Y)-S)-Y$. (adapted from Goldberg, *What Every Computer Scientist Should Know About Floating-Point Arithmetic*, sections "Errors In Summation" and "Optimizers", Theorem 8)
14. **(Thử thách)** **Tổng tiền tố với độ lệch nền.** Cho $x_i = 10^8 + k_i/100$ với $k_i=(37i)\bmod 101$ cho $i<n=10^6$, và cửa sổ $w=10$. (a) Trước khi chạy, hãy dự đoán bậc độ lớn của sai số của trung bình trượt tổng tiền tố $y_k=(P_{k+w}-P_k)/w$ trong `double`, dùng $\mathrm{ulp}(P_n)$, và giải thích nó như một triệt tiêu thảm họa. (b) Tính một tham chiếu chính xác bằng số nguyên 64 bit theo đơn vị $0.01$. (c) Đo sai số tuyệt đối lớn nhất của các phiên bản tổng tiền tố, tổng streaming và tổng trực tiếp, và của một phiên bản tổng tiền tố cộng dồn $x_i-x_0$. (d) Nói bạn sẽ đưa phiên bản nào vào sản phẩm cho tín hiệu vận tốc 1 kHz nằm trên một độ lệch nền lớn, và bài kiểm thử nào đã phát hiện được vấn đề. (adapted from Goldberg, section "Cancellation" (catastrophic versus benign cancellation); the signal is constructed for this exercise)

## Cài đặt tham khảo

Hãy đọc hợp đồng (contract) trước. Dự đoán đầu ra trước khi chạy code ở máy bạn. Phần này dùng để học; bài nộp sao chép từ đây là thực hành có hỗ trợ, không phải bằng chứng độc lập.

```cpp
#include <vector>
#include <stdexcept>
#include <cassert>
double mean(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    double sum{0.0};
    for (double v : x) sum += v;
    return sum / static_cast<double>(x.size());
}
int main() { assert(mean({2.,4.,6.}) == 4.); }
// g++ -std=c++17 -Wall -Wextra -Wpedantic main.cpp -o demo
```

## Thực hành độc lập

### Mục tiêu
Viết một thư viện số nhỏ có kiểm thử bằng C++17: mean, variance, một moving average với hợp đồng chặt chẽ, và một phép chia không thể cắt cụt một cách âm thầm. Quan sát từng đường lỗi được kích hoạt và từng bất biến được giữ.

### Chuẩn bị
Một trình biên dịch C++17 (`g++` hoặc `clang++`). Lưu code khởi đầu và các bài kiểm thử chung thành `lab.cpp`, rồi biên dịch bằng `g++ -std=c++17 -Wall -Wextra -Wpedantic lab.cpp -o lab && ./lab`. Sau đó, dựng lại với `-fsanitize=address,undefined -g`.

### Nhiệm vụ
1. Cài đặt `mean` và `safe_ratio`. Dự đoán bằng tay `safe_ratio(5, 2)` trả về gì và vì sao `5 / 2` đơn thuần sẽ không như vậy.
2. Cài đặt `variance` dùng `mean` (hai lượt). Hãy tính tay `{2, 4, 6}` trước.
3. Cài đặt `moving_average` với độ dài đầu ra chính xác $n-w+1$ và hai phép kiểm tra tiền điều kiện.
4. Biên dịch với cảnh báo bật. Sửa mọi cảnh báo (thường là signed/unsigned) thay vì dập tắt chúng.
5. Dựng lại với sanitizer, rồi tạm thời đổi một cận vòng lặp thành `<` thay vì `<=` và xem bài kiểm thử nào bắt được.

### Code khởi đầu
```cpp
#include <cassert>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <stdexcept>
#include <vector>

// Mean of x. Throw std::invalid_argument if x is empty.
double mean(const std::vector<double>& x) { throw std::logic_error("not implemented"); }

// Population variance (divide by n) using mean(); throw on empty input.
double variance(const std::vector<double>& x) { throw std::logic_error("not implemented"); }

// Window means: output length n-w+1, y[k] = mean of x[k..k+w-1].
// Throw std::invalid_argument if w == 0 or w > x.size().
std::vector<double> moving_average(const std::vector<double>& x, std::size_t w) { throw std::logic_error("not implemented"); }

// Return a/b as a double (no truncation). Throw std::domain_error if b == 0.
double safe_ratio(int a, int b) { throw std::logic_error("not implemented"); }
```

### Kiểm thử
Dán đoạn này bên dưới code khởi đầu (cùng một file) rồi chạy. Mọi kiểm tra đều là `assert` thuần; lần thất bại đầu tiên sẽ dừng chương trình.

```cpp
static bool near(double a, double b) { return std::abs(a - b) < 1e-12; }
template <class E, class F> static bool throws(F f) { try { f(); } catch (const E&) { return true; } catch (...) { return false; } return false; }

int main() {
    // hand-computed cases
    assert(near(mean({2., 4., 6.}), 4.));
    assert(near(mean({-3., 3.}), 0.));
    assert(near(mean({5.}), 5.));                       // singleton
    assert(near(variance({2., 4., 6.}), 8. / 3.));      // (4+0+4)/3
    assert(near(safe_ratio(5, 2), 2.5));
    auto y = moving_average({1, 2, 3, 4}, 2);
    assert(y.size() == 3 && near(y[0], 1.5) && near(y[1], 2.5) && near(y[2], 3.5));
    // error paths
    assert(throws<std::invalid_argument>([] { mean({}); }));
    assert(throws<std::invalid_argument>([] { moving_average({1, 2}, 0); }));
    assert(throws<std::invalid_argument>([] { moving_average({1, 2}, 3); }));
    assert(throws<std::domain_error>([] { safe_ratio(1, 0); }));
    // invariants: w == 1 returns the input; w == n returns the mean; shift invariance of variance
    std::vector<double> x{3, -1, 4, 1, -5, 9};
    auto id = moving_average(x, 1);
    for (std::size_t i = 0; i < x.size(); ++i) assert(near(id[i], x[i]));
    auto full = moving_average(x, x.size());
    assert(full.size() == 1 && near(full[0], mean(x)));
    std::vector<double> shifted;
    for (double v : x) shifted.push_back(v + 100.0);
    assert(std::abs(variance(shifted) - variance(x)) < 1e-9);
    std::cout << "mean = " << mean(x) << ", variance = " << variance(x) << ", ma size = " << moving_average(x, 3).size() << "\n";
    std::cout << "all tests passed\n";
}
```

### Kết quả mong đợi
Một lời giải đúng sẽ in ra kết quả sau; một `assert` thất bại sẽ dừng cùng với tên file và dòng.

```text
mean = 1.83333, variance = 18.8056, ma size = 4
all tests passed
```

### Thử thách mở rộng
Thêm `class MovingAverage` với `double push(double v)` giữ một ring buffer và tổng chạy với độ phức tạp O(1) mỗi mẫu, và kiểm thử rằng nó khớp với `moving_average` trên dữ liệu ngẫu nhiên đến 1e-9. Giải thích cách bạn sẽ ngăn trôi dấu phẩy động.

### Thực hành với thư viện
Làm lại bài lab bằng thư viện chuẩn C++17 thay vì các vòng lặp tự viết: `std::accumulate` cho mean, `std::transform_reduce` cho variance, và `std::partial_sum` (tổng tiền tố) cho moving average, trong đó $y_k=(P_{k+w}-P_k)/w$. Biên dịch bằng `g++ -std=c++17 -Wall -Wextra -Wpedantic lib.cpp -o lib && ./lib`. Sau đó chạy các bài kiểm thử của bạn trên các phiên bản này: chúng phải khớp đến $10^{-12}$.

```cpp
#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

double mean_std(const std::vector<double>& x) {
    if (x.empty()) throw std::invalid_argument("empty");
    return std::accumulate(x.begin(), x.end(), 0.0) / static_cast<double>(x.size());
}
double variance_std(const std::vector<double>& x) {
    const double m = mean_std(x);
    return std::transform_reduce(x.begin(), x.end(), 0.0, std::plus<>{},
                                 [m](double v) { return (v - m) * (v - m); }) / static_cast<double>(x.size());
}
// Moving average through prefix sums: y[k] = (P[k+w] - P[k]) / w
std::vector<double> moving_average_std(const std::vector<double>& x, std::size_t w) {
    if (w == 0 || w > x.size()) throw std::invalid_argument("window");
    std::vector<double> p(x.size() + 1, 0.0);
    std::partial_sum(x.begin(), x.end(), p.begin() + 1);
    std::vector<double> y(x.size() - w + 1);
    for (std::size_t k = 0; k < y.size(); ++k) y[k] = (p[k + w] - p[k]) / static_cast<double>(w);
    return y;
}

int main() {
    std::vector<double> x{3, -1, 4, 1, -5, 9};
    assert(std::abs(mean_std(x) - 11.0 / 6.0) < 1e-12);
    const auto y = moving_average_std(x, 3);
    const std::vector<double> want{2.0, 4.0 / 3.0, 0.0, 5.0 / 3.0};
    assert(y.size() == want.size() && std::equal(y.begin(), y.end(), want.begin(),
           [](double a, double b) { return std::abs(a - b) < 1e-12; }));
    std::cout << "variance = " << variance_std(x) << "\n";   // matches the hand-written lab
    std::cout << "library track ok\n";
}
```

Đầu ra kỳ vọng: `variance = 18.8056` rồi `library track ok`. Lưu ý rằng `std::accumulate(x.begin(), x.end(), 0)` với giá trị khởi đầu kiểu `int` sẽ cắt cụt âm thầm mọi tổng riêng; chữ `0.0` là quan trọng.

## Kiểm chứng

Hãy kiểm tra mỗi khẳng định số của bài này hai lần, bằng hai đường. Với một phép chuyển đổi, dự đoán kiểu chung từ các quy tắc rồi in `typeid(a + b).name()` hoặc dùng `static_assert(std::is_same_v<decltype(a + b), unsigned>)`. Với một tổng dấu phẩy động, so với một tham chiếu chính xác tính bằng số nguyên 64 bit (chẳng hạn đơn vị 0.01) hoặc bằng `fractions.Fraction` của Python, và nêu dung sai như một bội của $u\cdot|x|$, không phải một số cố định. Với trung bình trượt, kiểm thử bốn trường hợp biên (`w == 1`, `w == n`, `w == 0`, `w > n`) và các bất biến của bài lab: độ dài đầu ra $n-w+1$, `w == 1` trả về chính đầu vào, `w == n` trả về trung bình, và cộng một hằng số vào đầu vào thì cộng cùng hằng số đó vào đầu ra. Build lại với `-Wall -Wextra -Wpedantic` rồi với `-fsanitize=address,undefined -g`; cố ý đổi `<=` thành `<` trong một cận vòng lặp và xác nhận một bài kiểm thử thất bại. Một sanitizer im lặng chỉ chứng tỏ các đường đã chạy là sạch.

## Lỗi thường gặp

- **Chia nguyên trước khi chuyển đổi:** `double r = a / b;` với hai toán hạng `int` bị cắt cụt; triệu chứng là vận tốc hay tỉ số luôn là số nguyên, và các bài kiểm thử mà mọi đầu vào đều chia hết sẽ không thấy lỗi.
- **Quay vòng không dấu trong điều kiện vòng lặp:** `for (std::size_t i = n - 1; i >= 0; --i)` không bao giờ kết thúc, và `v.size() - 1` trên vector rỗng là $2^{64}-1$. Với g++ 11.4.0, `-Wextra` đánh dấu `>= 0` (`-Wtype-limits`) nhưng không nói gì về phép trừ bị quay vòng.
- **Coi tràn số có dấu là quay vòng:** `x + 1 > x` có thể bị trình tối ưu gấp thành `true`, nên một "kiểm tra quay vòng" biến mất ở `-O2` trong khi chạy được ở `-O0`; sanitizer có thể im lặng khi phép so sánh đã bị gấp.
- **Biến cục bộ chưa khởi tạo:** `int n;` rồi đọc là không xác định; `-Wall` chỉ cảnh báo ở các trường hợp đơn giản.
- **`operator[]` ngoài phạm vi:** hành vi không xác định không có ngoại lệ; dùng `.at()` trong kiểm thử hoặc chạy bản build có sanitizer.
- **So sánh bằng và trôi dấu phẩy động:** `sum == 1.0` sau nhiều phép cộng lặp, tổng cửa sổ streaming không bao giờ hồi phục sau một lỗi làm tròn, và tổng tiền tố của dữ liệu nằm trên một offset lớn.
- **Tham chiếu treo:** một hàm trả về `const&` tới biến cục bộ, hoặc một tham chiếu được lưu lâu hơn đối tượng mà nó gọi tên.

## Phương án khác và đánh đổi

- **Số nguyên có độ rộng cố định hay double.** Số xung encoder, timestamp và giá trị thanh ghi cảm biến là số nguyên có độ rộng biết trước: `std::int32_t` và `std::uint32_t` làm modulo hiện rõ và giữ phép tính chính xác; `double` là kiểu đúng cho các đại lượng vật lý sau khi chuyển đổi. Trộn hai loại này là nơi các lỗi của bài sinh ra.
- **Kích thước có dấu.** `std::ssize(v)` (C++20) hoặc chỉ số `std::ptrdiff_t` tránh được việc trộn signed/unsigned với cái giá là một phép chuyển đổi ở biên thư viện (Core Guidelines ES.100 đến ES.107).
- **`operator[]` so với `.at()` so với `for` theo phạm vi.** Truy cập không kiểm tra là nhanh nhất, `.at()` báo lỗi bằng ngoại lệ, và `for` theo phạm vi loại bỏ hoàn toàn chỉ số.
- **Ba cách tính trung bình trượt.** Tổng trực tiếp tốn $O(nw)$ nhưng chính xác; streaming tốn $O(n)$ và tích lũy độ trôi; tổng tiền tố tốn $O(n)$ với hiểm họa offset lớn. Cộng Kahan hay trừ một giá trị tham chiếu khôi phục độ chính xác với chi phí nhỏ, còn `long double` hoặc bộ cộng dồn số nguyên là các phương án hạng nặng.
- **Python so với C++ cho cùng một việc.** Số nguyên Python không bao giờ tràn và số thực của nó là cùng các double IEEE; C++ cho quyền kiểm soát kiểu và bộ nhớ với cái giá là các quy tắc hành vi không xác định của bài này.

## Vận dụng và ghi nhớ

Tính một moving average cho vận tốc motor được lấy mẫu. Nêu kiểu số của bạn, hợp đồng đầu vào, hành vi ở biên, và một bài kiểm thử bắt được lỗi cắt cụt số nguyên.

Hãy đóng tài liệu tham khảo trước khi thử. Không nhìn tài liệu, hãy viết kiểu và giá trị của từng biểu thức sau trên máy Linux 64 bit: `7 / 2`, `7 / 2.0`, `-1 < 1u`, `std::vector<int>{}.size() - 1`, `1e16 + 1 == 1e16`. Giải thích một cách mà mỗi đáp án có thể đổi trên nền tảng khác (chẳng hạn `std::size_t` hay `long` 32 bit). Quay lại sau ít nhất một tuần và dựng lại từ một trang giấy trắng các quy tắc chuyển đổi, mô hình làm tròn và ba cách tính trung bình trượt, rồi đối chiếu với bài.

## Đáp án bài tập

1. `a` là `3` (in ra 3) vì `ticks / rev` được tính dưới dạng `int / int` (cắt cụt) trước khi kết quả được chuyển đổi; `b` là `3.5`. Phần thập phân mất ở phép chia, không phải ở phép gán.
2. `1 / 100` là phép chia nguyên, nên `dt` là `0`. Một bộ điều khiển với `dt = 0` không bao giờ tích phân (hoặc chia cho không trong đạo hàm). Hãy viết `1.0 / 100` hoặc `0.01` (hoặc `constexpr double dt{1.0/100.0};`).
3. `size_t` không dấu, nên `i >= 0` luôn đúng: sau khi `i == 0` phép giảm quay vòng thành một giá trị rất lớn và `v[i]` đọc ngoài biên (hành vi không xác định, undefined behaviour). Với vector rỗng, `v.size() - 1` đã quay vòng thành giá trị rất lớn. Đúng: `for (std::size_t i = v.size(); i-- > 0; ) std::cout << v[i] << ' ';`
4. `v.size() - 1` là `2`; `v.at(3)` ném `std::out_of_range`, nên đầu ra là `2 caught`. `v[3]` là hành vi không xác định không kiểm tra: nó có thể đọc rác, sập về sau, hoặc có vẻ chạy được, điều này tệ hơn đối với robot so với một exception rõ ràng.
5. Theo giá trị: $10^6\times8$ B $=8$ MB được sao chép mỗi lần gọi; ở 30 Hz là khoảng $240$ MB/s lưu lượng thêm cộng một lần cấp phát mỗi lần. Theo tham chiếu: không sao chép. Signature `void filter(const std::vector<double>& cloud);`.
6. Tổng là $0.9999999999999999$, nên `s == 1.0` sai và motor không được kích hoạt; $1-s\approx1.1\times10^{-16}$. Dùng `std::abs(s - 1.0) < 1e-9`. `double` có khoảng 16 chữ số so với khoảng 7 của `float`, nên sai số làm tròn tích lũy nhỏ hơn nhiều.
7. Nó trả về 2 giá trị `{1.5, 2.5}`; đáng ra phải trả về 3 giá trị `{1.5, 2.5, 3.5}`. Điều kiện vòng lặp nên là `i + w <= x.size()`. Cũng cần từ chối `w == 0` (chia cho không) và `w > x.size()` (không có cửa sổ đầy đủ; `i + w` sẽ không bao giờ hợp lệ).
8. Hợp đồng: `x` là một vector các double hữu hạn, `1 <= w <= x.size()`, độ dài đầu ra `x.size() - w + 1`, phần tử `k` là trung bình của `x[k..k+w-1]` (nên không có đầu ra cho `w-1` mẫu khởi động đầu tiên). Với đầu vào dốc, trung bình trễ $(w-1)/2=5$ mẫu $=5$ ms ở 1 kHz. Không chấp nhận được khi biên pha (phase margin) hoặc ngân sách độ trễ của vòng chặt hơn mức đó, hoặc khi dùng đạo hàm của giá trị đã lọc.
9. Tổng cửa sổ $S_{k+1}=S_k-x_k+x_{k+w}$ vì các cửa sổ chỉ khác nhau ở việc bỏ $x_k$ và thêm $x_{k+w}$; chia cho $w$ cho ra cập nhật. Mỗi lần cập nhật thêm một sai số làm tròn không bao giờ được sửa, nên sai số đi lang thang ngẫu nhiên (random walk). Cách khắc phục: tính lại tổng từ đầu mỗi N bước, dùng cộng bù (Kahan/compensated summation), hoặc bộ tích lũy số nguyên cho số đếm cảm biến nguyên.
10. Một câu trả lời tốt cho thấy cả hai bản build in cùng kết quả kiểm thử, có các bài kiểm thử đường lỗi (rỗng, `w == 0`, `w > n`), báo cáo rằng sanitizer không đưa ra chẩn đoán nào cho các đường đã chạy, và nêu rằng một lần chạy sạch không phải là bằng chứng của sự đúng đắn.

11. (Kết quả từ một lần chạy g++ 11.4.0 trên Linux 64 bit.) (a) Kiểu chung là `unsigned int` (rank bằng nhau, nên $U$ thắng): $-3\mapsto 2^{32}-3$, và $(2^{32}-3)-7=2^{32}-10=4294967286$. (b) `-3 < 7u` là **false** (0), vì $-3$ trở thành $4294967293$. (c) **false**: kiểu chung là `unsigned long` (`std::size_t`), và $-1$ trở thành $2^{64}-1$. (d) **true**: `long long` có rank cao hơn `unsigned int` và biểu diễn được mọi giá trị `unsigned int`, nên kiểu chung là `long long` và $-1<3$. (e) **true**: cả hai kiểu `short` được promote lên `int` trước, nên phép so sánh là $-1<1$ trong `int`. (f) **false**: `long` và `unsigned long` có rank bằng nhau, nên kiểu chung là `unsigned long` và $-1\mapsto 2^{64}-1$. Cách viết lại an toàn cho (c): `i < static_cast<int>(v.size())` (chuyển đổi một lần, ở biên, chấp nhận được khi `size` vừa trong `int`), hoặc dùng kiểu chỉ số/kích thước có dấu như `std::ptrdiff_t n = std::ssize(v)` (C++20) hoặc `gsl::index`, đó là điều ES.107 khuyến nghị cho chỉ số. Với g++ 11.4.0 và `-Wall -Wextra` (`-Wsign-compare`), cảnh báo chỉ xuất hiện cho (b), (c) và (f); (a) là phép trừ không dấu thông thường, (d) trộn các kiểu mà kiểu có dấu chứa được mọi giá trị, và ở (e) cả hai toán hạng được promote lên `int`. Vậy trình biên dịch không bắt được mọi bất ngờ: (a) sai một cách âm thầm với người đọc kỳ vọng $-10$.
12. (a) Tích thật là $10^{15}$. Theo modulo $2^{32}$ nó là $2764472320$, đọc như `int` bù hai là $2764472320-2^{32}=-1530494976$ (tính bằng Python, và cùng các bit đó được tạo ra bởi một phép ép kiểu trong C++). (b) Với `int`, tràn số có dấu là **hành vi không xác định**: tiêu chuẩn không áp đặt yêu cầu nào, và quay vòng về $-1530494976$ chỉ là một biểu hiện có thể (cppreference liệt kê quay vòng, bẫy, bão hòa và bị tối ưu bỏ đi). Với `unsigned`, cùng tích đó là xác định: nó là phần dư $2764472320$. (c) Một trình tối ưu tuân chuẩn được phép giả định `x + 1` không tràn và gập phép so sánh thành `true`. Với GCC 11.4.0 trên `f(INT_MAX)` kết quả quan sát được là: `-O0` cho 1, `-O2` cho 1, `-O2 -fsanitize=undefined` cho 1 mà không có chẩn đoán nào (phép so sánh đã bị gập thành `true` nên không có tràn nào được thực thi), và `-O2 -fwrapv` cho 0 (quay vòng giờ là hành vi được định nghĩa). Bài học: một sanitizer im lặng không chứng minh rằng tràn số không có. (d) Ví dụ `std::int64_t area(std::int32_t h, std::int32_t w) { if (h < 0 || w < 0) throw std::invalid_argument("negative"); return static_cast<std::int64_t>(h) * w; }`: tích đã mở rộng của hai số 32 bit không âm nhỏ hơn $2^{62}$, nên không thể tràn. Nếu kết quả buộc phải là `int`, hãy kiểm tra `h <= INT_MAX / w` (với `w > 0`) trước khi nhân. Cạnh hình vuông lớn nhất vừa là $\lfloor\sqrt{2^{31}-1}\rfloor=46340$ (Python `math.isqrt`).
13. (a) Với $s_i=(s_{i-1}+x_i)(1+\delta_i)$, $|\delta_i|\le u$, quy nạp cho $s_n=\sum_j x_j\prod_{i=\max(j,2)}^{n}(1+\delta_i)$. Tích của $m$ thừa số $(1+\delta_i)$ bằng $1+\theta$ với $|\theta|\le mu+O(u^2)$, và $x_j$ gặp $n-j+1$ thừa số (với $j\ge2$; $x_1$ gặp $n-1$), nên $|\theta_j|\lesssim(n-j+1)u$; cộng $|x_j\theta_j|$ cho ra cận. (b) Với các số hạng bằng nhau $\sum_j(n-j+1)=n(n+1)/2$, nên cận là $0.1\cdot\frac{n(n+1)}{2}\,u$. Với $n=10^7$ nó là $298023.25$ cho `float` và $5.55\times10^{-4}$ cho `double` (Python). (c) Đo được: `float` cộng thường $=1087937.0$, sai số $+87936.99$ so với $10^7\cdot$`0.1f` $=1000000.0149$ (nằm trong cận $2.98\times10^5$ nhưng còn xa mới nhỏ); `float` Kahan $=1000000.0$, sai số $-0.0149$ (kết quả `float` được làm tròn tới số biểu diễn được gần nhất); `double` cộng thường $=999999.999839$, sai số $-1.61\times10^{-4}$ so với $10^6$ (nằm trong $5.55\times10^{-4}$). Vậy Kahan trong `float` tốt hơn cộng thường trong `double` ở đây, phù hợp với việc cận $2u$ tốt hơn $(n-j+1)u$. (d) Với `-O2 -ffast-math` vòng Kahan trả về $1087937.0$, giống phép cộng thường: trình biên dịch được dùng đại số số thực, viết lại $C=((S+Y)-S)-Y$ thành $0$, và phần hiệu chỉnh biến mất (Goldberg, mục "Optimizers"). Hoặc giữ phép cộng bù ra khỏi các translation unit dùng `-ffast-math`, hoặc thêm `-fno-associative-math` (với nó, cùng bản build GCC 11.4.0 lại cho Kahan $=1000000.0$).
14. (a) $P_n\approx10^{14}$ (đo được $P_n=100000000499999.9$), có ulp là $2^{46-52}=0.015625$. Mỗi $P_k$ được làm tròn trong khoảng nửa ulp (và các sai số tích lũy qua các phép cộng trước đó), và $y_k$ trừ hai giá trị như vậy để được một tổng cửa sổ gần $10^9$ rồi chia cho $w=10$, nên sai số kỳ vọng vào khoảng $\mathrm{ulp}(P_n)/w\approx1.6\times10^{-3}$, lớn hơn nhiều so với độ phân giải $\mathrm{ulp}(10^8)=1.5\times10^{-8}$ của dữ liệu. Đây là triệt tiêu thảm họa: các toán hạng đã mang sai số làm tròn lớn hơn nhiều so với độ phân giải của chính hiệu. (b) Lưu $c_i=10^{10}+k_i$ (đơn vị $0.01$) trong `std::int64_t`; tổng cửa sổ chính xác là tổng của $w$ giá trị đó (dưới $10^{12}$), rồi $y_k=\text{sum}/(100w)$. (c) Các cực đại đo được trên mọi cửa sổ: tổng tiền tố $2.41\times10^{-3}$, tổng streaming $3.66\times10^{-3}$, tổng trực tiếp (lấy mẫu mỗi cửa sổ thứ 1000) $2.98\times10^{-8}$, tổng tiền tố của $x_i-x_0$ $1.49\times10^{-8}$. Hai giá trị cuối ở mức sai số biểu diễn của chính đầu vào (nửa ulp của $10^8$ là $7.5\times10^{-9}$). Phiên bản streaming chịu thiệt vì $S_k\approx10^9$ và sai số làm tròn của nó không bao giờ rời đi; phiên bản tiền tố vì $P_n$ lớn hơn một tổng cửa sổ $10^5$ lần. (d) Đưa tổng trực tiếp vào sản phẩm khi $w$ nhỏ (chi phí $O(nw)$ không đáng kể ở 1 kHz) hoặc tổng tiền tố đã dịch khi $w$ lớn, và thêm một bài kiểm thử hồi quy có độ lệch nền lớn và biến thiên nhỏ (so với tham chiếu số nguyên hoặc `long double` với dung sai tỷ lệ với $u\cdot|x|$, không phải với $\max|y|$); một bài kiểm thử trên dữ liệu trung bình bằng không sẽ không bao giờ lộ ra vấn đề.

## Đọc thêm

[LearnCpp](https://www.learncpp.com/) — khóa học chính, tài liệu, hoặc bộ tham khảo được cung cấp. Hãy theo mục chủ đề liên quan; đây là các liên kết đọc thêm, không phải các chương sách được sao chép lại.

- [C++ Core Guidelines, các quy tắc số học ES.100 đến ES.107](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#es100-dont-mix-signed-and-unsigned-arithmetic) - trộn signed/unsigned, tràn số và thu hẹp.
- [C++ working draft](https://eel.is/c++draft/) - [basic.fundamental], [expr.pre], [conv.integral], [expr.arith.conv], [dcl.init.list], [basic.stc.auto].
- [cppreference: List-initialization](https://en.cppreference.com/w/cpp/language/list_initialization), [Default-initialization](https://en.cppreference.com/w/cpp/language/default_initialization), [Reference declaration](https://en.cppreference.com/w/cpp/language/reference), [Storage duration](https://en.cppreference.com/w/cpp/language/storage_duration) và [std::vector::operator[]](https://en.cppreference.com/w/cpp/container/vector/operator_at).
- [cppreference: Arithmetic operators](https://en.cppreference.com/w/cpp/language/operator_arithmetic) và [usual arithmetic conversions](https://en.cppreference.com/w/cpp/language/usual_arithmetic_conversions).
- [Goldberg, What Every Computer Scientist Should Know About Floating-Point Arithmetic](https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html) - sai số làm tròn, triệt tiêu và phép cộng Kahan.

**Thực hành thêm:** [LearnCpp chapter 4 quiz](https://www.learncpp.com/cpp-tutorial/chapter-4-summary-and-quiz/) (kiểu cơ bản và phép chia nguyên), [LearnCpp chapter 12 quiz](https://www.learncpp.com/cpp-tutorial/chapter-12-summary-and-quiz/) (kiểu hợp thành và tham chiếu), [LearnCpp on the std::vector unsigned subscript problem](https://www.learncpp.com/cpp-tutorial/stdvector-and-the-unsigned-length-and-subscript-problem/), và [Exercism C++ track](https://exercism.org/tracks/cpp/exercises).
