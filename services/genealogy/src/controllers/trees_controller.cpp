#include "trees_controller.hpp"

#include <algorithm>
#include <iterator>
#include <openssl/aes.h>
#include <vector>
#include <memory>

#include "tao/json/forward.hpp"
#include "tao/json/type.hpp"
#include "tao/json/value.hpp"

#include "../database/trees_database.hpp"
#include "../brotobuf/tree.hpp"


TreesController::TreesController() {
    this->_persons_database = std::make_shared<PersonsDatabase>(this->_tx);
    this->_trees_database = std::make_shared<TreesDatabase>(this->_tx);
    this->_signer = std::make_shared<Signer>(this->_keys->get_signing_key());
}

HttpResponse TreesController::get_tree(const HttpRequest & request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto tree = this->_trees_database->find_tree_by_user(user_id.value());
    if (!tree) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Your genealogy tree doesn't exist, create it first"}
        }, HttpStatusCode::NOT_FOUND);
    }

    return this->_return_tree_json(tree.value());
}

HttpResponse TreesController::create_tree(const HttpRequest & request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto found_tree = this->_trees_database->find_tree_by_user(user_id.value());
    if (found_tree) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Your genealogy tree already exists, you may have only one"}
        }, HttpStatusCode::CONFLICT);
    }

    const auto json = request.get_json();
    const auto title = json.at("title").get_string();
    const auto description = json.at("description").get_string();
    const auto person_id = json.at("person").optional<unsigned long long>();

    const auto tree = this->_trees_database->create_tree(
        user_id.value(), title, description, person_id
    );

    const auto response = this->_return_tree_json(tree);
    this->_trees_database->transaction()->commit();
    return response;
}

HttpResponse TreesController::update_tree(const HttpRequest & request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto tree = this->_trees_database->find_tree_by_user(user_id.value());
    if (!tree) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Your genealogy tree doesn't exist, create it first"}
        }, HttpStatusCode::NOT_FOUND);
    }

    const auto json = request.get_json();
    const auto title = json.at("title").get_string();
    const auto description = json.at("description").get_string();
    const auto person_id = json.at("person").optional<unsigned long long>();

    const auto updated_tree = this->_trees_database->update_tree(
        tree->id, title, description, person_id
    );

    const auto response = this->_return_tree_json(updated_tree);
    this->_trees_database->transaction()->commit();
    return response;
}

HttpResponse TreesController::update_owners(const HttpRequest &request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto tree = this->_trees_database->find_tree_by_user(user_id.value());
    if (!tree) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Your genealogy tree doesn't exist, create it first"}
        }, HttpStatusCode::NOT_FOUND);
    }

    const auto json = request.get_json();
    if (!json.is_array() || json.get_array().size() > 60) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Invalid content: should be array of owners not more than 60 elements"}
        }, HttpStatusCode::BAD_REQUEST);
    }    

    std::vector<unsigned long long> owners;
    for (const auto& element: json.get_array()) {
        owners.push_back(element.as<unsigned long long>());
    }

    this->_trees_database->set_owners(tree->id, owners);

    const auto response = this->_return_tree_json(tree.value());
    this->_trees_database->transaction()->commit();
    return response;    
}


HttpResponse TreesController::export_tree_archive(const HttpRequest & request) {
    const auto user_id = this->_current_user_id(request);
    if (!user_id) {
        return HttpResponse({
            {"status", "error"},
            {"message", "You're not authenticated"}
        }, HttpStatusCode::UNAUTHORIZED);
    };

    const auto tree = this->_trees_database->find_tree_by_user(user_id.value());
    if (!tree) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Your genealogy tree doesn't exist, create it first"}
        }, HttpStatusCode::NOT_FOUND);
    }

    brotobuf::GenealogyTree tree_message;
    tree_message.id = tree->id;
    tree_message.title = tree->title;
    tree_message.description = tree->description;
    tree_message.owners = this->_trees_database->get_owners(tree->id);
    if (tree->person_id) {
        tree_message.person = this->_build_brotobuf_person(tree->person_id.value());
    }

    brotobuf::OutputStream stream;
    tree_message.serialize(stream);
    const auto serialized_data = stream.get();

    std::string serialized_data_str;
    serialized_data_str.assign(serialized_data.begin(), serialized_data.end());

    // Add signature to our archive
    auto response = HttpResponse(serialized_data_str + this->_signer->sign(serialized_data));
    response.set_header("content-type", "application/octet-stream");
    return response;
}

HttpResponse TreesController::check_tree_achive(const HttpRequest & request) {
    if (!this->_signer->check_sign(request.content)) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Invalid signature under your archive"}
        }, HttpStatusCode::I_M_A_TEAPOT);
    }

    // Truncate signature
    std::vector<unsigned char> serialized_data;
    std::copy(
        request.content.begin(),
        request.content.begin() + request.content.size() - AES_BLOCK_SIZE,
        std::back_inserter(serialized_data)
    );

    brotobuf::InputStream stream(serialized_data.begin(), serialized_data.end());
    brotobuf::GenealogyTree tree_message;
    tree_message.deserialize(stream);

    std::vector<tao::json::value> owners;
    for (auto owner: tree_message.owners) {
        owners.push_back(owner);
    }

    return HttpResponse({
        {"status", "ok"},
        {"message", "Your archive is correct"},
        {"tree", {
            {"id", tree_message.id},
            {"title", tree_message.title},
            {"description", tree_message.description},
            {"owners", owners},
            {"person", this->_restore_brotobuf_person(tree_message.person)}
        }}
    });
}

brotobuf::Person TreesController::_build_brotobuf_person(unsigned long long person_id) {
    brotobuf::Person result;

    const auto person = this->_persons_database->find_person(person_id);
    if (!person) {
        return result;
    }
    result.title = person->title;
    result.first_name = person->first_name;
    result.middle_name = person->middle_name;
    result.last_name = person->last_name;
    result.photo_url = person->photo_url;
    result.birth_date = person->birth_date;
    result.death_date = person->death_date.value_or(NO_DEATH_DATE);
    for (auto parent_id: this->_persons_database->get_parents(person_id)) {
        result.parents.push_back(this->_build_brotobuf_person(parent_id));
    }
    return result;
}

tao::json::value TreesController::_restore_brotobuf_person(const std::optional<brotobuf::Person> & person) {
    if (! person) {
        return tao::json::null;
    }
    std::vector<tao::json::value> parents;
    for (const auto& parent: person->parents) {
        parents.push_back(this->_restore_brotobuf_person(parent));
    }
    return {
        {"title", person->title},
        {"first_name", person->first_name},
        {"middle_name", person->middle_name},
        {"last_name", person->last_name},
        {"photo_url", person->photo_url},
        {"birth_date", person->birth_date},
        {"death_date", person->death_date == NO_DEATH_DATE ? tao::json::null : tao::json::value(person->death_date)},
        {"parents", parents}
    };
}

HttpResponse TreesController::_return_tree_json(const Tree & tree) {
    std::vector<tao::json::value> owners;
    for (auto owner: this->_trees_database->get_owners(tree.id)) {
        owners.push_back(owner);
    }

    tao::json::value person_json = tao::json::null;
    if (tree.person_id) {
        person_json = this->_persons_database->build_person_json(tree.person_id.value());
    }

    return HttpResponse({
        {"status", "ok"},
        {"tree", {
            {"id", tree.id},
            {"person", person_json},
            {"title", tree.title},
            {"description", tree.description},
            {"owners", owners}
        }}
    });
}