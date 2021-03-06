#ifndef _DATABASE_USERS_HPP_

#define _DATABASE_USERS_HPP_

#include <memory>
#include <string>

#include "tao/pq/transaction.hpp"

#include "database.hpp"

struct User {
    unsigned long long id;
    std::string login;
    std::string password_hash;
};

class UsersDatabase: public Database {
public:
    UsersDatabase(std::shared_ptr<tao::pq::transaction> tx);

    std::optional<User> find_user(const std::string & login) const;
    std::optional<User> find_user(int user_id) const;
    User create_user(const std::string & login, const std::string & password_hash) const;

private:
    std::optional<User> _find_user(const tao::pq::result & result) const;
};

#endif