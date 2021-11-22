#include <algorithm>
#include <iostream>
#include <vector>

size_t choose_row(const std::vector<std::vector<int>>& a, const std::vector<bool>& used_eq, size_t column) {
	for (size_t i = 0; i < used_eq.size(); ++i) {
		if (used_eq[i])
			continue;
		if (a[i][column])
			return i;
	}
	return -1;
}

int main() {
	std::ios_base::sync_with_stdio(false);

	size_t n, m;
	std::cin >> n >> m;
	std::vector<std::vector<int>> a(n, std::vector<int>(m + 1));

	for (auto& line : a)
		for (auto& x : line)
			std::cin >> x;

	std::vector<bool> used_eq(n);
	for (size_t column = 0; column < m; ++column) {
		size_t row = choose_row(a, used_eq, column);
		used_eq[row] = true;
		
		int base = a[row][column];
		
		for (size_t i = 0; i < n; ++i) {
			if (i == row)
				continue;
			int c = a[i][column];
			if (!c)
				continue;
			for (size_t j = 0; j < m + 1; ++j)
				a[i][j] = a[i][j] * base - a[row][j] * c;
		}
	}

	for (size_t j = 0; j < m; ++j) {
		for (size_t i = 0; i < n; ++i) {
			if (a[i][j]) {
				std::cout << a[i].back() / a[i][j] << '\n';
				break;
			}
		}
	}
}
