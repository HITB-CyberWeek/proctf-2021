#include <memory>
#include <string>

#include "server/http_request.hpp"
#include "server/http_status_code.hpp"

#include "server/http_response.hpp"
#include "server/http_server.hpp"
#include "utils.hpp"
#include "brotobuf/tree.hpp"
#include "database/common.hpp"
#include "database/users.hpp"
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

HttpResponse create_user(const HttpRequest & request) {
    return UsersController().create_user(request);
}

HttpResponse login(const HttpRequest & request) {
    return UsersController().login(request);
}

HttpResponse get_me(const HttpRequest & request) {
    return UsersController().get_me(request);
}

HttpResponse get_tree(const HttpRequest & request) {
    return TreesController().get_tree(request);
}

HttpResponse create_tree(const HttpRequest & request) {
    return TreesController().create_tree(request);
}

HttpResponse update_tree(const HttpRequest & request) {
    return TreesController().update_tree(request);
}

HttpResponse create_person(const HttpRequest & request) {
    return PersonsController().create_person(request);
}

HttpResponse update_person(const HttpRequest & request) {
    return PersonsController().update_person(request);
}

HttpResponse delete_person(const HttpRequest & request) {
    return PersonsController().delete_person(request);
}

HttpResponse update_links(const HttpRequest & request) {
    return TreesController().update_links(request);
}

HttpResponse update_owners(const HttpRequest & request) {
    return TreesController().update_owners(request);
}

HttpResponse export_tree_archive(const HttpRequest & request) {
    return TreesController().export_tree_archive(request);
}

HttpResponse check_tree_archive(const HttpRequest & request) {
    return TreesController().check_tree_achive(request);
}

int main() {
    ensure_keys_exist();

    auto server = std::make_unique<HttpServer>(8888);

    server->add_route({HttpMethod::POST, "/users", false}, create_user);
    server->add_route({HttpMethod::POST, "/login", false}, login);
    server->add_route({HttpMethod::GET, "/users/me", false}, get_me);

    server->add_route({HttpMethod::GET, "/tree", false}, get_tree);
    server->add_route({HttpMethod::POST, "/tree", false}, create_tree);
    server->add_route({HttpMethod::PUT, "/tree", false}, update_tree);

    server->add_route({HttpMethod::POST, "/tree/persons", false}, create_person);
    server->add_route({HttpMethod::PUT, "/tree/persons", true}, update_person);
    server->add_route({HttpMethod::DELETE, "/tree/persons", true}, delete_person);

    server->add_route({HttpMethod::PUT, "/tree/links", false}, update_links);

    server->add_route({HttpMethod::PUT, "/tree/owners", false}, update_owners);

    server->add_route({HttpMethod::GET, "/tree/archive", false}, export_tree_archive);
    server->add_route({HttpMethod::POST, "/tree/archive", false}, check_tree_archive);

    server->start();
    return 0;
}