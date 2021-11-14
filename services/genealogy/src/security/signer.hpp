#ifndef _SECURITY_SIGNER_HPP_

#define _SECURITY_SIGNER_HPP_

#include <string>
#include <memory>
#include <vector>

class Signer {
public:
    typedef std::vector<unsigned char> Data;

    Signer(const std::string & key);
    std::string sign(const Data & data) const;
    bool check_sign(const std::string & data) const;

private:
    void _append_length(Data & data) const;
    void _append_padding(Data & data, unsigned long long block_size) const;
    Data _encrypt(const Data & data) const;

    const std::string _key;
    std::shared_ptr<unsigned char[]> _iv;
};

#endif