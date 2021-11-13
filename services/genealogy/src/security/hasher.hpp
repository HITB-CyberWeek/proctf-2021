#ifndef _SECURITY_PASSWORD_HASHER_

#define _SECURITY_PASSWORD_HASHER_

#include <string>

class Hasher {
public:
    std::string md5(const std::string & value);
};

#endif