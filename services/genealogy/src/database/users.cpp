#include "users.hpp"

#include "tao/pq.hpp"

#include "common.hpp"
#include "tao/pq/transaction.hpp"

UsersDatabase::UsersDatabase(std::shared_ptr<tao::pq::transaction> tx): _tx(tx) {
    this->_tx->connection()->prepare(
        "insert_user", "INSERT INTO users (login, password_hash) VALUES ($1, $2)" 
    );
    this->_tx->connection()->prepare(
        "find_user_by_id", "SELECT id, login, password_hash FROM users WHERE id = $1" 
    );    
    this->_tx->connection()->prepare(
        "find_user_by_login", "SELECT id, login, password_hash FROM users WHERE login = $1" 
    );
}

std::shared_ptr<tao::pq::transaction> UsersDatabase::transaction() {
    return this->_tx;
}

std::optional<User> UsersDatabase::find_user(int user_id) const {
    const auto result = this->_tx->execute("find_user_by_id", user_id);
    return this->_find_user(result);
}

std::optional<User> UsersDatabase::find_user(const std::string & login) const {
    const auto result = this->_tx->execute("find_user_by_login", login);
    return this->_find_user(result);
}

std::optional<User> UsersDatabase::_find_user(const tao::pq::result & result) const {
    if (result.size() == 0) {
        return {};
    }
    const auto user = result[0];
    return User {
        user["id"].as<unsigned long long>(),
        user["login"].as<std::string>(),
        user["password_hash"].as<std::string>()
    };
}

User UsersDatabase::create_user(const std::string & login, const std::string & password_hash) const {
    this->_tx->execute("insert_user", login, password_hash);
    return this->find_user(login).value();
}