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
    unsigned long long person_id;
    std::string title;
    std::string description;
};

enum LinkType {
    URL = 1,
    EMAIL = 2,
    PHONE = 3,
    TELEGRAM = 4,    
};

struct Link {
    LinkType type;
    std::string value;
};

class TreesDatabase {
public:
    TreesDatabase(std::shared_ptr<tao::pq::transaction> tx, std::shared_ptr<PersonsDatabase> persons);
    std::shared_ptr<tao::pq::transaction> transaction();

    std::optional<Tree> find_tree(unsigned long long id);
    std::optional<Tree> find_tree_by_user(unsigned long long user_id);
    Tree create_tree(
        unsigned long long user_id, const std::string person_name, unsigned long long person_birth_date,
        const std::string & title, const std::string & description
    );

    std::vector<Link> get_links(unsigned long long tree_id);
    void delete_links(unsigned long long tree_id);
    void create_link(unsigned long long tree_id, LinkType type, const std::string & value);

    std::vector<unsigned long long> get_owners(unsigned long long tree_id);
    void set_owners(unsigned long long tree_id, const std::vector<unsigned long long> & owners);

private:
    std::optional<Tree> _find_tree(const tao::pq::result & result);

    std::shared_ptr<tao::pq::transaction> _tx;
    std::shared_ptr<PersonsDatabase> _persons;
};

#endif