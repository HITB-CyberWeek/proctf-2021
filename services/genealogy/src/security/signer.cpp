#include "signer.hpp"

#include <cassert>
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
    size_t data_length = data.size();

    assert(data_length <= 65535);

    data.resize(data_length + 2);

    data[data_length] = data_length / 256;
    data[data_length + 1] = data_length % 256;
}

void Signer::_append_padding(Data & data, unsigned long long block_size) const {
    // Add padding to the data
    const size_t data_length = data.size();
    const size_t padded_length = ((data_length + block_size) / block_size) * block_size;
    data.resize(padded_length);
    unsigned char padding = padded_length - data_length;
    for (size_t idx = data_length; idx < padded_length; idx++) {
        data[idx] = padding;
    }
}

Signer::Data Signer::_encrypt(const Data & data) const {
    // Call openssl's AES_cbc_encrypt()
    std::shared_ptr<unsigned char[]> output(new unsigned char[data.size()]);

    AES_KEY enc_key;
    AES_set_encrypt_key((const unsigned char*) this->_key.data(), 128, &enc_key);

    AES_cbc_encrypt(data.data(), output.get(), data.size(), &enc_key, this->_iv.get(), AES_ENCRYPT);

    Data result;
    result.assign(output.get(), output.get() + data.size());

    return result;
}
