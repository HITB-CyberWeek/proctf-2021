#include "trees.hpp"

#include <memory>
#include <optional>

#include "tao/pq/null.hpp"
#include "tao/pq/transaction.hpp"

#include "persons.hpp"


TreesDatabase::TreesDatabase(
    std::shared_ptr<tao::pq::transaction> tx,
    std::shared_ptr<PersonsDatabase> persons
) : _tx(tx), _persons(persons) {
    this->_tx->connection()->prepare(
        "create_tree", "INSERT INTO genealogy_trees (user_id, person_id, title, description) VALUES ($1, $2, $3, $4) RETURNING id"
    );
    this->_tx->connection()->prepare(
        "set_tree_person", "UPDATE genealogy_trees SET person_id = $2 WHERE id = $1"
    );    
    this->_tx->connection()->prepare(
        "get_tree_by_id", "SELECT * FROM genealogy_trees WHERE id = $1"
    );
    this->_tx->connection()->prepare(
        "get_tree_by_user_id", "SELECT * FROM genealogy_trees WHERE user_id = $1"
    );

    this->_tx->connection()->prepare(
        "get_links", "SELECT * FROM genealogy_tree_links WHERE tree_id = $1"
    );
    this->_tx->connection()->prepare(
        "delete_links", "DELETE FROM genealogy_tree_links WHERE tree_id = $1"
    );
    this->_tx->connection()->prepare(
        "create_link", "INSERT INTO genealogy_tree_links (tree_id, type, value) VALUES ($1, $2, $3)"
    );

    this->_tx->connection()->prepare(
        "get_owners", "SELECT user_id FROM genealogy_tree_owners WHERE tree_id = $1"
    );
    this->_tx->connection()->prepare(
        "delete_owners", "DELETE FROM genealogy_tree_owners WHERE tree_id = $1"
    );
    this->_tx->connection()->prepare(
        "create_owner", "INSERT INTO genealogy_tree_owners (tree_id, user_id) VALUES ($1, $2)"
    );
}

std::shared_ptr<tao::pq::transaction> TreesDatabase::transaction() {
    return this->_tx;
}

std::optional<Tree> TreesDatabase::find_tree(unsigned long long id) {
    const auto result = this->_tx->execute("get_tree_by_id", id);
    return this->_find_tree(result);
}

std::optional<Tree> TreesDatabase::find_tree_by_user(unsigned long long user_id) {
    const auto result = this->_tx->execute("get_tree_by_user_id", user_id);
    return this->_find_tree(result);
}

std::optional<Tree> TreesDatabase::_find_tree(const tao::pq::result & result) {
    if (result.size() == 0) {
        return {};
    }
    const auto tree = result[0];
    return Tree {
        tree["id"].as<unsigned>(),
        tree["user_id"].as<unsigned>(),
        tree["person_id"].as<unsigned>(),
        tree["title"].as<std::string>(),
        tree["description"].as<std::string>()
    };
}

Tree TreesDatabase::create_tree(
    unsigned long long user_id, const std::string person_name, unsigned long long person_birth_date,
    const std::string & title, const std::string & description
) {
    const auto result = this->_tx->execute("create_tree", user_id, tao::pq::null, title, description);
    assert(result.size() > 0);
    const auto tree_id = result[0]["id"].as<unsigned>();

    const auto person = this->_persons->create_person(user_id, person_birth_date, {}, person_name);
    this->_tx->execute("set_tree_person", tree_id, person.id);

    return this->find_tree(tree_id).value();
}

std::vector<Link> TreesDatabase::get_links(unsigned long long tree_id) {
    const auto result = this->_tx->execute("get_links", tree_id);

    std::vector<Link> links;
    for (const auto& row: result) {
        links.push_back(Link {
            (LinkType) row["type"].as<unsigned>(),
            row["value"].as<std::string>()
        });
    }
    return links;
}

void TreesDatabase::delete_links(unsigned long long tree_id) {
    this->_tx->execute("delete_links", tree_id);
}

void TreesDatabase::create_link(unsigned long long tree_id, LinkType type, const std::string & value) {
    this->_tx->execute("create_link", tree_id, (unsigned long long) type, value);
}

std::vector<unsigned long long> TreesDatabase::get_owners(unsigned long long tree_id) {
    const auto result = this->_tx->execute("get_owners", tree_id);
    std::vector<unsigned long long> owners;
    for (const auto& row: result) {
        owners.push_back(row["user_id"].as<unsigned>());
    }
    return owners;
}

void TreesDatabase::set_owners(unsigned long long tree_id, const std::vector<unsigned long long> &owners) {
    this->_tx->execute("delete_owners", tree_id);
    for (auto& owner: owners) {
        this->_tx->execute("create_owner", tree_id, owner);
    }
}