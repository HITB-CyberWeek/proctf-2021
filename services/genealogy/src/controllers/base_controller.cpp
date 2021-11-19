#include "base_controller.hpp"

#include <cstdlib>
#include <optional>
#include <string>
#include <memory>

#include "tao/pq/connection.hpp"

#include "../server/http_request.hpp"
#include "../security/key_storage.hpp"

BaseController::BaseController() {
    this->_hasher = std::make_unique<Hasher>();
    this->_keys = std::make_unique<KeyStorage>();

    std::string connection_string = "host=database port=6432 dbname=genealogy user=genealogy password=genealogy";
    const char* db_env = std::getenv("DATABASE");
    if (db_env) {
        connection_string = db_env;
    }

    const auto connection = tao::pq::connection::create(connection_string);
    this->_tx = connection->transaction();
}

std::optional<unsigned long long> BaseController::_current_user_id(const HttpRequest & request) {
    const auto user_id_iterator = request.cookies.find("user_id");
    const auto user_hash_iterator = request.cookies.find("user_hash");
    if (user_id_iterator == request.cookies.end() || user_hash_iterator == request.cookies.end()) {
        return {};
    }

    int user_id = -1;
    try {
        user_id = std::stoi(user_id_iterator->second);
    } catch (std::exception & e) {
        printf("Invalid user_id cookie: %s\n", e.what());
        return {};
    }

    if (user_hash_iterator->second != this->_get_user_cookie_hash(user_id) || user_id < 0) {
        printf("Invalid cookie for user %d: %s\n", user_id, user_hash_iterator->second.c_str());
        return {};
    }

    return user_id;
}

std::string BaseController::_get_user_cookie_hash(int user_id) {
    const auto salt = this->_keys->get_cookie_key();
    return this->_hasher->md5(salt + std::to_string(user_id) + salt);
}