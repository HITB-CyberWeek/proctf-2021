#include "hasher.hpp"

#include <string>

#include "openssl/md5.h"
#include "../utils.hpp"

std::string Hasher::md5(const std::string & value) {
    // Just a wrapper for openssl's MD5()
    unsigned char hash[MD5_DIGEST_LENGTH];
    MD5((unsigned char*) value.data(), value.size(), hash);

    std::string result;
    result.reserve(2 * MD5_DIGEST_LENGTH);
    for (size_t idx = 0; idx < MD5_DIGEST_LENGTH; idx++) {
        result += string_format("%02x", hash[idx]);
    }

    return result;
}