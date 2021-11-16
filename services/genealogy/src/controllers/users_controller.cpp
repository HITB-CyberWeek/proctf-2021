#include "users_controller.hpp"

#include <memory>

#include "../security/hasher.hpp"
#include "../database/common.hpp"
#include "../database/users.hpp"
#include "../database/trees.hpp"
#include "../utils.hpp"

UsersController::UsersController() {
    const auto database = Database().connection();
    const auto transaction = database->transaction();
    this->_users_database = std::make_shared<UsersDatabase>(transaction);
}

HttpResponse UsersController::create_user(const HttpRequest & request) {
    const auto json = request.get_json();
    const auto login = json.at("login").get_string();
    const auto password = json.at("password").get_string();

    const auto password_hash = this->_hasher->md5(password);

    if (this->_users_database->find_user(login)) {
        this->_users_database->transaction()->rollback();
        return HttpResponse({
            {"status", "error"},
            {"message", string_format("User with login %s already exists", login.c_str())}
        }, HttpStatusCode::CONFLICT);
    }
    const auto user = this->_users_database->create_user(login, password_hash);
    this->_users_database->transaction()->commit();

    auto response = HttpResponse({
        {"status", "ok"},
        {"user", {
            {"id", user.id},
            {"login", user.login}
        }}
    });

    response.set_cookie("user_id", std::to_string(user.id));
    response.set_cookie("user_hash", this->_get_user_cookie_hash(user.id));

    return response;
}

HttpResponse UsersController::login(const HttpRequest & request) {
    const auto json = request.get_json();
    const auto login = json.at("login").get_string();
    const auto password = json.at("password").get_string();

    const auto password_hash = this->_hasher->md5(password);

    const auto user = this->_users_database->find_user(login);
    if (!user) {
        return HttpResponse({
            {"status", "error"},
            {"message", string_format("User with login %s doesn't exist", login.c_str())}
        }, HttpStatusCode::PRECONDITION_FAILED);
    }
    if (user->password_hash != password_hash) {
        return HttpResponse({
            {"status", "error"},
            {"message", string_format("Invalid password for user %s", login.c_str())}
        }, HttpStatusCode::PRECONDITION_FAILED);
    }    

    auto response = HttpResponse({
        {"status", "ok"},
        {"user", {
            {"id", user->id},
            {"login", user->login}
        }}
    });
    
    response.set_cookie("user_id", std::to_string(user->id));
    response.set_cookie("user_hash", this->_get_user_cookie_hash(user->id));

    return response;
}

HttpResponse UsersController::get_me(const HttpRequest & request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    }

    const auto user = this->_users_database->find_user(user_id.value());
    if (!user) {
        return HttpResponse({
            {"status", "error"},
            {"message", string_format("User has been deleted", user_id.value())}
        }, HttpStatusCode::UNAUTHORIZED);
    }

    return HttpResponse({
        {"status", "ok"},
        {"user", {
            {"id", user->id},
            {"login", user->login}
        }}
    });  
}