#include "persons_controller.hpp"

#include "../database/persons_database.hpp"
#include "../utils.hpp"

PersonsController::PersonsController() {
    this->_persons_database = std::make_shared<PersonsDatabase>(this->_tx);
}

HttpResponse PersonsController::create_person(const HttpRequest &request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto json = request.get_json();
    const auto title = json.at("title").get_string();
    const auto first_name = json.at("first_name").get_string();
    const auto middle_name = json.at("middle_name").get_string();
    const auto last_name = json.at("last_name").get_string();
    const auto photo_url = json.at("photo_url").get_string();
    const auto birth_date = json.at("birth_date").get_unsigned();
    const auto death_date = json.at("death_date").get_unsigned();
    const auto first_parent_id = json.at("first_parent").optional<unsigned long long>();
    const auto second_parent_id = json.at("second_parent").optional<unsigned long long>();

    if (first_parent_id.has_value() && !this->_persons_database->find_person(first_parent_id.value())) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Invalid first parent id"}
        }, HttpStatusCode::PRECONDITION_FAILED);
    }
    if (second_parent_id.has_value() && !this->_persons_database->find_person(second_parent_id.value())) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Invalid second parent id"}
        }, HttpStatusCode::PRECONDITION_FAILED);
    }

    const auto person = this->_persons_database->create_person(
        user_id.value(), birth_date, death_date, 
        title, first_name, middle_name, last_name, photo_url
    );

    if (first_parent_id.has_value()) {
        this->_persons_database->mark_as_parent(person.id, first_parent_id.value());
    }
    if (second_parent_id.has_value()) {
        this->_persons_database->mark_as_parent(person.id, second_parent_id.value());
    }

    const auto person_object = this->_persons_database->build_person_json(person.id);

    this->_persons_database->transaction()->commit();

    return HttpResponse({
        {"status", "ok"},
        {"person", person_object}
    });
}

HttpResponse PersonsController::delete_person(const HttpRequest & request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto person = this->_persons_database->find_person(request.id);
    if (!person.has_value() || person->owner_id != user_id.value()) {
        return HttpResponse({
            {"status", "error"},
            {"message", string_format("Person %d not found or is owned not by you", request.id)}
        }, HttpStatusCode::NOT_FOUND);
    }

    this->_persons_database->delete_person(request.id);

    this->_persons_database->transaction()->commit();

    return HttpResponse({
        {"status", "ok"},
        {"message", "Person deleted"}
    });
}