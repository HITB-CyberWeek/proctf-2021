#ifndef _SECURITY_KEY_STORAGE_HPP_

#define _SECURITY_KEY_STORAGE_HPP_

#include <string>
#include <filesystem>

class KeyStorage {
public:
    const std::string::size_type KEY_LENGTH = 32;

    std::string get_cookie_key() const;
    std::string get_signing_key() const;

private:
    std::string _generate_key(std::string::size_type length) const;
    std::string _get_key(std::filesystem::path path) const;
};

#endif