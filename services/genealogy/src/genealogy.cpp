#include <memory>
#include <string>

#include "server/http_request.hpp"
#include "server/http_status_code.hpp"

#include "server/http_response.hpp"
#include "server/http_server.hpp"
#include "utils.hpp"
#include "brotobuf/tree.hpp"
#include "database/users_database.hpp"
#include "security/hasher.hpp"
#include "security/key_storage.hpp"
#include "controllers/users_controller.hpp"
#include "controllers/trees_controller.hpp"
#include "controllers/persons_controller.hpp"

void ensure_keys_exist() {
    const static auto keys = KeyStorage();
    keys.get_cookie_key();
    keys.get_signing_key();
}

int main() {
    ensure_keys_exist();

    auto server = std::make_unique<HttpServer>(8888);

    // Users Controller
    server->add_route({HttpMethod::POST, "/users", false},
        [](auto const & request){ return UsersController().create_user(request); }
    );
    server->add_route({HttpMethod::POST, "/login", false}, 
        [](auto const & request){ return UsersController().login(request); }
    );
    server->add_route({HttpMethod::GET, "/users/me", false}, 
        [](auto const & request){ return UsersController().get_me(request); }
    );

    // Trees Controller
    server->add_route({HttpMethod::GET, "/tree", false}, 
        [](auto const & request){ return TreesController().get_tree(request); }
    );
    server->add_route({HttpMethod::POST, "/tree", false}, 
        [](auto const & request){ return TreesController().create_tree(request); }
    );
    server->add_route({HttpMethod::PUT, "/tree", false}, 
        [](auto const & request){ return TreesController().update_tree(request); }
    );
    server->add_route({HttpMethod::PUT, "/tree/owners", false}, 
        [](auto const & request){ return TreesController().update_owners(request); }
    );
    server->add_route({HttpMethod::GET, "/tree/archive", false}, 
        [](auto const & request){ return TreesController().export_tree_archive(request); }
    );
    server->add_route({HttpMethod::POST, "/tree/archive", false}, 
        [](auto const & request){ return TreesController().check_tree_achive(request); }
    );

    // Persons Controller
    server->add_route({HttpMethod::POST, "/tree/persons", false}, 
        [](auto const & request){ return PersonsController().create_person(request); }
    );
    server->add_route({HttpMethod::PUT, "/tree/persons", true}, 
        [](auto const & request){ return PersonsController().update_person(request); }
    );
    server->add_route({HttpMethod::DELETE, "/tree/persons", true}, 
        [](auto const & request){ return PersonsController().delete_person(request); }
    );

    server->start();
    return 0;
}