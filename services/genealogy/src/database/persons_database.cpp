#include "persons_database.hpp"

#include <memory>
#include <optional>

#include "tao/pq/transaction.hpp"
#include "tao/json/value.hpp"

PersonsDatabase::PersonsDatabase(std::shared_ptr<tao::pq::transaction> tx): Database(tx) {
    this->_tx->connection()->prepare(
        "create_person",
        "INSERT INTO genealogy_tree_persons" 
        "(owner_id, birth_date, death_date, title, first_name, middle_name, last_name, photo_url) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id"
    );
    this->_tx->connection()->prepare(
        "get_person", "SELECT * FROM genealogy_tree_persons WHERE id = $1"
    );
    this->_tx->connection()->prepare(
        "mark_as_parent", "INSERT INTO genealogy_tree_person_parents (child_id, parent_id) VALUES ($1, $2)"
    );
    this->_tx->connection()->prepare(
        "delete_parents", "DELETE FROM genealogy_tree_person_parents WHERE child_id = $1"
    );
    this->_tx->connection()->prepare(
        "delete_children", "DELETE FROM genealogy_tree_person_parents WHERE parent_id = $1"
    );
    this->_tx->connection()->prepare(
        "delete_person", "DELETE FROM genealogy_tree_persons WHERE id = $1"
    );    
    this->_tx->connection()->prepare(
        "get_parents", "SELECT parent_id FROM genealogy_tree_person_parents WHERE child_id = $1"
    );
}

std::optional<Person> PersonsDatabase::find_person(unsigned long long id) {
    const auto result = this->_tx->execute("get_person", id);
    if (result.size() == 0) {
        return {};
    }
    const auto tree = result[0];
    return Person {
        tree["id"].as<unsigned long long>(),
        tree["owner_id"].as<unsigned long long>(),
        tree["birth_date"].as<unsigned long long>(),
        tree["death_date"].as<unsigned long long>(),
        tree["title"].as<std::string>(),
        tree["first_name"].as<std::string>(),
        tree["middle_name"].as<std::string>(),
        tree["last_name"].as<std::string>(),
        tree["photo_url"].as<std::string>()
    };
}

Person PersonsDatabase::create_person(
    unsigned long long owner_id,
    unsigned long long birth_date, unsigned long long death_date,
    const std::string & title,
    const std::string & first_name,
    const std::string & middle_name,
    const std::string & last_name,
    const std::string & photo_url
) {
    const auto result = this->_tx->execute(
        "create_person",
        owner_id, birth_date, death_date, 
        title, first_name, middle_name, last_name, photo_url
    );
    assert(result.size() > 0);
    const auto person_id = result[0]["id"].as<unsigned long>();

    return this->find_person(person_id).value();
}

void PersonsDatabase::delete_person(unsigned long long person_id) {
    this->delete_parents(person_id);
    this->delete_children(person_id);
    this->_tx->execute("delete_person", person_id);
}

void PersonsDatabase::mark_as_parent(unsigned long long child_id, unsigned long long parent_id) {
    this->_tx->execute("mark_as_parent", child_id, parent_id);
}

void PersonsDatabase::delete_parents(unsigned long long child_id) {
    this->_tx->execute("delete_parents", child_id);
}

void PersonsDatabase::delete_children(unsigned long long parent_id) {
    this->_tx->execute("delete_children", parent_id);
}

std::vector<unsigned long long> PersonsDatabase::get_parents(unsigned long long person_id) {
    const auto result = this->_tx->execute("get_parents", person_id);
    std::vector<unsigned long long> parents;
    for (const auto& row: result) {
        parents.push_back(row["parent_id"].as<unsigned long long>());
    }
    return parents;
}

tao::json::value PersonsDatabase::build_person_json(unsigned long long person_id) {
    const auto found_person = this->find_person(person_id);
    if (!found_person.has_value()) {
        return tao::json::null;
    }
    const auto person = found_person.value();

    std::vector<tao::json::value> parents;
    for (auto parent_id: this->get_parents(person_id)) {
        parents.push_back(this->build_person_json(parent_id));
    }

    return {
        {"id", person.id},
        {"title", person.title},
        {"first_name", person.first_name},        
        {"middle_name", person.middle_name},
        {"last_name", person.last_name},
        {"photo_url", person.photo_url},
        {"birth_date", person.birth_date},
        {"death_date", person.death_date},
        {"parents", parents}
    };
}