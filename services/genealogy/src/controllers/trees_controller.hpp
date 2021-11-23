#ifndef _CONTROLLERS_TREES_CONTROLLER_HPP_

#define _CONTROLLERS_TREES_CONTROLLER_HPP_

#include <memory>

#include "base_controller.hpp"
#include "../server/http_request.hpp"
#include "../server/http_response.hpp"
#include "../database/trees_database.hpp"
#include "../database/persons_database.hpp"
#include "../brotobuf/person.hpp"
#include "../security/signer.hpp"


class TreesController: public BaseController {
public:
    TreesController();

    HttpResponse get_tree(const HttpRequest & request);
    HttpResponse create_tree(const HttpRequest & request);
    HttpResponse update_tree(const HttpRequest & request);
    HttpResponse update_owners(const HttpRequest & request);
    HttpResponse export_tree_archive(const HttpRequest & request);
    HttpResponse check_tree_achive(const HttpRequest & request);

private:
    HttpResponse _return_tree_json(const Tree & tree);
    brotobuf::Person _build_brotobuf_person(unsigned long long person_id);
    tao::json::value _restore_brotobuf_person(const std::optional<brotobuf::Person> & person);

    std::shared_ptr<TreesDatabase> _trees_database;
    std::shared_ptr<PersonsDatabase> _persons_database;
    std::shared_ptr<Signer> _signer;
};

#endif