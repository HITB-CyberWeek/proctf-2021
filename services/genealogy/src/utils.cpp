#include "utils.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <sstream>
#include <vector>
 

const std::string WHITESPACE = " \n\r\t\f\v";
 
std::string ltrim(const std::string & s)
{
    size_t start = s.find_first_not_of(WHITESPACE);
    return (start == std::string::npos) ? "" : s.substr(start);
}
 
std::string rtrim(const std::string & s)
{
    size_t end = s.find_last_not_of(WHITESPACE);
    return (end == std::string::npos) ? "" : s.substr(0, end + 1);
}
 
std::string trim(const std::string & s) {
    return rtrim(ltrim(s));
}

void to_lower_case(std::string & s) {
    std::transform(
        s.begin(), s.end(), s.begin(), [](unsigned char c){ return std::tolower(c); }
    );
}

int guard(int n, const char * err) {
    if (n == -1) {
        perror(err);
        exit(1);
    }
    return n;
}

std::vector<std::string> string_split(const std::string & s, char delim) {
    std::vector<std::string> result;
    std::stringstream ss(s);
    std::string item;

    while (getline(ss, item, delim)) {
        result.push_back(item);
    }

    return result;
}
