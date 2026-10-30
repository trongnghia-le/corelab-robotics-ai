// Intentionally broken starter: identify, explain, test, then fix.
#include <vector>
#include <iostream>
double mean(const std::vector<int>& values) {
    int total = 0;
    for (int value : values) total += value;
    return total / values.size();
}
int main() { std::cout << mean({1, 2}) << '\n'; }
