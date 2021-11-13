#include "trees_controller.hpp"

#include <algorithm>
#include <iterator>
#include <openssl/aes.h>
#include <vector>
#include <memory>

#include "tao/json/forward.hpp"
#include "tao/json/type.hpp"
#include "tao/json/value.hpp"

#include "../database/common.hpp"
#include "../database/trees.hpp"
#include "../brotobuf/tree.hpp"


TreesController::TreesController() {
    const auto database = Database().connection();
    const auto transaction = database->transaction();
    this->_persons_database = std::make_shared<PersonsDatabase>(transaction);
    this->_trees_database = std::make_shared<TreesDatabase>(transaction, this->_persons_database);
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

    const auto found_tree = this->_trees_database->find_tree_by_user(user_id.value());
    if (!found_tree) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Your genealogy tree doesn't exist, create it first"}
        }, HttpStatusCode::NOT_FOUND);
    }

    return this->_return_tree_json(found_tree.value());
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
    const auto name = json.at("name").get_string();
    const auto birth_date = json.at("birth_date").get_unsigned();

    const auto tree = this->_trees_database->create_tree(
        user_id.value(), name, birth_date, title, description
    );

    const auto response = this->_return_tree_json(tree);
    this->_trees_database->transaction()->commit();
    return response;
}

HttpResponse TreesController::update_links(const HttpRequest & request) {
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

    this->_trees_database->delete_links(tree->id);

    const auto json = request.get_json();
    if (!json.is_array() || json.get_array().size() > 10) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Invalid content: should be array of links not more than 10 elements"}
        }, HttpStatusCode::BAD_REQUEST);
    }

    for (const auto link: json.get_array()) {
        const auto type = link.at("type").get_unsigned();
        const auto value = link.at("value").get_string();
        this->_trees_database->create_link(tree->id, (LinkType) type, value);
    }

    const auto response = this->_return_tree_json(tree.value());
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
    if (!json.is_array() || json.get_array().size() > 10) {
        return HttpResponse({
            {"status", "error"},
            {"message", "Invalid content: should be array of owners not more than 10 elements"}
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
    for (const auto& link: this->_trees_database->get_links(tree->id)) {
        brotobuf::Link link_message;
        link_message.type = link.type;
        link_message.value = link.value;
        tree_message.links.push_back(link_message);
    }
    tree_message.person = this->_build_brotobuf_person(tree->person_id);

    brotobuf::OutputStream stream;
    tree_message.serialize(stream);
    const auto serialized_data = stream.get();

    std::string serialized_data_str;
    serialized_data_str.assign(serialized_data.begin(), serialized_data.end());

    // Add sign to our archive
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

    std::vector<tao::json::value> links;
    for (auto link: tree_message.links) {
        links.push_back({{"type", link.type}, {"value", link.value}});
    }

    return HttpResponse({
        {"status", "ok"},
        {"message", "Your archive is correct"},
        {"tree", {
            {"id", tree_message.id},
            {"title", tree_message.title},
            {"description", tree_message.description},
            {"owners", owners},
            {"links", links},
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
    result.name = person->name;
    result.birth_date = person->birth_date;
    result.death_date = person->death_date.value_or(0);
    for (auto parent_id: this->_persons_database->get_parents(person_id)) {
        result.parents.push_back(this->_build_brotobuf_person(parent_id));
    }
    return result;
}

tao::json::value TreesController::_restore_brotobuf_person(const brotobuf::Person & person) {
    std::vector<tao::json::value> parents;
    for (const auto& parent: person.parents) {
        parents.push_back(this->_restore_brotobuf_person(parent));
    }
    return {
        {"name", person.name},
        {"birth_date", person.birth_date},
        {"death_date", person.death_date},
        {"parents", parents}
    };
}

HttpResponse TreesController::_return_tree_json(const Tree & tree) {
    std::vector<tao::json::value> links;
    for (const auto& link: this->_trees_database->get_links(tree.id)) {
        links.push_back({
            {"type", (unsigned long long) link.type},
            {"value", link.value}
        });
    }

    std::vector<tao::json::value> owners;
    for (auto owner: this->_trees_database->get_owners(tree.id)) {
        owners.push_back(owner);
    }

    return HttpResponse({
        {"status", "ok"},
        {"tree", {
            {"id", tree.id},
            {"person", this->_persons_database->build_person_object(tree.person_id)},
            {"title", tree.title},
            {"description", tree.description},
            {"links", links},
            {"owners", owners}
        }}
    });
}