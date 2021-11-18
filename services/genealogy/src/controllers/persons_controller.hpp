#ifndef _CONTROLLER_PERSONS_CONTROLLER_HPP_

#define _CONTROLLER_PERSONS_CONTROLLER_HPP_

#include <memory>

#include "base_controller.hpp"
#include "../database/persons_database.hpp"
#include "../server/http_request.hpp"
#include "../server/http_response.hpp"


class PersonsController: public BaseController {
public:
    PersonsController();

    HttpResponse create_person(const HttpRequest & request);
    HttpResponse update_person(const HttpRequest & request);
    HttpResponse delete_person(const HttpRequest & request);

private:
    std::shared_ptr<PersonsDatabase> _persons_database;    
};

#endif