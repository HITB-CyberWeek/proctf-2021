#include "key_storage.hpp"

#include <string>
#include <filesystem>
#include <fstream>
#include <random>

#include "../utils.hpp"


std::string KeyStorage::get_cookie_key() const {
    return this->_get_key("./keys/cookie.key");
}

std::string KeyStorage::get_signing_key() const {
    return this->_get_key("./keys/signing.key");
}

std::string KeyStorage::_get_key(const std::filesystem::path & path) const {
    if (!std::filesystem::exists(path)) {
        const auto key = this->_generate_key(this->KEY_LENGTH);
        std::ofstream f(path, std::ios::out | std::ios::binary);
        f.write(key.data(), key.length());
        f.close();
        return this->_get_key(path);
    }

    return get_file_content(path);
}

std::string KeyStorage::_generate_key(std::string::size_type length) const {
    static auto& chrs = "0123456789"
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    thread_local static std::mt19937 rg{std::random_device{}()};
    thread_local static std::uniform_int_distribution<std::string::size_type> pick(
        0, sizeof(chrs) - 2
    );

    std::string s;
    s.reserve(length);

    while (length--)
        s += chrs[pick(rg)];

    return s;    
}