#include "trees_database.hpp"

#include <memory>
#include <optional>

#include "tao/pq/null.hpp"
#include "tao/pq/transaction.hpp"

#include "persons_database.hpp"


TreesDatabase::TreesDatabase(std::shared_ptr<tao::pq::transaction> tx) : Database(tx) {
    this->_tx->connection()->prepare(
        "create_tree", "INSERT INTO genealogy_trees (user_id, person_id, title, description) VALUES ($1, $2, $3, $4) RETURNING id"
    );
    this->_tx->connection()->prepare(
        "update_tree", "UPDATE genealogy_trees SET person_id = $2, title = $3, description = $4 WHERE id = $1"
    );    
    this->_tx->connection()->prepare(
        "get_tree_by_id", "SELECT * FROM genealogy_trees WHERE id = $1"
    );
    this->_tx->connection()->prepare(
        "get_tree_by_user_id", "SELECT * FROM genealogy_trees WHERE user_id = $1"
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
        tree["id"].as<unsigned long long>(),
        tree["user_id"].as<unsigned long long>(),
        tree["person_id"].optional<unsigned long long>(),
        tree["title"].as<std::string>(),
        tree["description"].as<std::string>()
    };
}

Tree TreesDatabase::create_tree(
    unsigned long long user_id,
    const std::string & title, const std::string & description, std::optional<unsigned long long> person_id
) {
    const auto result = this->_tx->execute("create_tree", user_id, person_id, title, description);
    assert(result.size() > 0);
    const auto tree_id = result[0]["id"].as<unsigned long long>();

    return this->find_tree(tree_id).value();    
}

Tree TreesDatabase::update_tree(
    unsigned long long tree_id,
    const std::string & title, const std::string & description, std::optional<unsigned long long> person_id
) {
    this->_tx->execute("update_tree", tree_id, person_id, title, description);

    return this->find_tree(tree_id).value();
}

std::vector<unsigned long long> TreesDatabase::get_owners(unsigned long long tree_id) {
    const auto result = this->_tx->execute("get_owners", tree_id);
    std::vector<unsigned long long> owners;
    for (const auto& row: result) {
        owners.push_back(row["user_id"].as<unsigned long long>());
    }
    return owners;
}

void TreesDatabase::set_owners(unsigned long long tree_id, const std::vector<unsigned long long> &owners) {
    this->_tx->execute("delete_owners", tree_id);
    for (auto& owner: owners) {
        this->_tx->execute("create_owner", tree_id, owner);
    }
}