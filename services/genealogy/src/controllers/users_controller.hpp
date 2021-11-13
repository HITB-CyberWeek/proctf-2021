#ifndef _CONTROLLERS_USERS_CONTROLLER_HPP_

#define _CONTROLLERS_USERS_CONTROLLER_HPP_

#include "../security/hasher.hpp"
#include "base_controller.hpp"
#include "../database/users.hpp"
#include "../database/trees.hpp"
#include "../server/http_request.hpp"
#include "../server/http_response.hpp"

class UsersController: public BaseController {
public:
    UsersController();
    HttpResponse create_user(const HttpRequest & request);
    HttpResponse login(const HttpRequest & request);
    HttpResponse get_me(const HttpRequest & request);

private:
    std::shared_ptr<UsersDatabase> _users_database;
};

#endif