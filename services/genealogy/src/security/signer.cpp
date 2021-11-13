#include "signer.hpp"

#include <cstring>
#include <memory>

#include "openssl/aes.h"

Signer::Signer(const std::string & key) : _key(key), _iv(new unsigned char[AES_BLOCK_SIZE]) {    
    memset(this->_iv.get(), 0, AES_BLOCK_SIZE);
}

std::string Signer::sign(const Signer::Data & data) const {
    auto plaintext = data;

    // Append two bytes with the length
    this->_append_length(plaintext);

    // Pad our data
    this->_append_padding(plaintext, AES_BLOCK_SIZE);

    // Encrypt it with AES-128
    auto encrypted = this->_encrypt(plaintext);

    // Last block is our signature
    std::string result;
    result.assign(
        encrypted.data() + encrypted.size() - AES_BLOCK_SIZE,
        encrypted.data() + encrypted.size()
    );
    return result;
}

bool Signer::check_sign(const std::string & data) const {
    printf("data.length() = %zu\n", data.length());
    if (data.length() < AES_BLOCK_SIZE) {
        return false;    
    }

    auto data_without_signature = data.substr(0, data.length() - AES_BLOCK_SIZE);
    auto signature = data.substr(data.length() - AES_BLOCK_SIZE);
    Data plaintext;
    plaintext.assign(data_without_signature.begin(), data_without_signature.end());

    return this->sign(plaintext) == signature;
}

void Signer::_append_length(Data & data) const {
    size_t data_size = data.size();

    data.resize(data_size + 2);

    data[data_size + 1] = data_size / 256;
    data[data_size + 2] = data_size % 256;
}

void Signer::_append_padding(Data & data, unsigned long long block_size) const {
    const size_t data_size = data.size();
    const size_t padded_length = ((data_size + block_size) / block_size) * block_size;    
    data.resize(padded_length);
    unsigned char padding = padded_length - data.size();
    for (size_t idx = data_size; idx < padded_length; idx++) {
        data[idx] = padding;
    }
}

Signer::Data Signer::_encrypt(const Data & data) const {
    std::shared_ptr<unsigned char[]> output(new unsigned char[data.size()]);

    AES_KEY enc_key;
    AES_set_encrypt_key((const unsigned char*) this->_key.data(), 128, &enc_key);
    AES_cbc_encrypt(data.data(), output.get(), data.size(), &enc_key, this->_iv.get(), AES_ENCRYPT);

    Data result;
    result.assign(output.get(), output.get() + data.size());

    return result;
}
