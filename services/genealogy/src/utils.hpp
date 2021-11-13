#ifndef _UTILS_HPP_

#define _UTILS_HPP_

#include <string>
#include <stdexcept>
#include <memory>
#include <vector>

std::string ltrim(const std::string & s); 
std::string rtrim(const std::string & s); 
std::string trim(const std::string & s);
void to_lower_case(std::string & s);

int guard(int n, const char * err);

std::vector<std::string> string_split(const std::string & s, char delim);

// Are you waiting for std::format() as much as I do?
template<typename ... Args>
std::string string_format(const std::string & format, Args ... args)
{
    int size_s = std::snprintf(nullptr, 0, format.c_str(), args ...) + 1; // Extra space for '\0'
    if (size_s <= 0) {
        throw std::runtime_error("Error during formatting.");
    }
    auto size = static_cast<size_t>(size_s);
    auto buf = std::make_unique<char[]>(size);
    std::snprintf(buf.get(), size, format.c_str(), args ...);
    return std::string(buf.get(), buf.get() + size - 1); // We don't want the '\0' inside
}

#endif