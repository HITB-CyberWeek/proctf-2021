#ifndef _DATABASE_TREES_HPP_

#define _DATABASE_TREES_HPP_

#include <vector>

#include "tao/pq/transaction.hpp"
#include "tao/pq/result.hpp"

#include "common.hpp"
#include "persons.hpp"

struct Tree {
    unsigned long long id;
    unsigned long long user_id;
    std::optional<unsigned long long> person_id;
    std::string title;
    std::string description;
};

class TreesDatabase {
public:
    TreesDatabase(std::shared_ptr<tao::pq::transaction> tx);
    std::shared_ptr<tao::pq::transaction> transaction();

    std::optional<Tree> find_tree(unsigned long long id);
    std::optional<Tree> find_tree_by_user(unsigned long long user_id);
    Tree create_tree(
        unsigned long long user_id, const std::string & title, const std::string & description,
        std::optional<unsigned long long> person_id
    );
    Tree update_tree(
        unsigned long long user_id, const std::string & title, const std::string & description,
        std::optional<unsigned long long> person_id
    );

    std::vector<unsigned long long> get_owners(unsigned long long tree_id);
    void set_owners(unsigned long long tree_id, const std::vector<unsigned long long> & owners);

private:
    std::optional<Tree> _find_tree(const tao::pq::result & result);

    std::shared_ptr<tao::pq::transaction> _tx;
};

#endif