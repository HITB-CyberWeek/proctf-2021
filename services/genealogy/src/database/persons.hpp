#ifndef _DATABASE_PERSONS_HPP

#define _DATABASE_PERSONS_HPP

#include <optional>
#include <memory>
#include <string>
#include <vector>

#include "tao/pq.hpp"
#include "tao/json/value.hpp"

#include "common.hpp"

struct Person {
    unsigned long long id;
    unsigned long long owner_id;
    unsigned long long birth_date;
    std::optional<unsigned long long> death_date;
    std::string name;
};

class PersonsDatabase {
public:
    PersonsDatabase(std::shared_ptr<tao::pq::transaction> tx);
    std::shared_ptr<tao::pq::transaction> transaction();
    tao::json::value build_person_json(unsigned long long person_id);

    std::optional<Person> find_person(unsigned long long id);
    Person create_person(
        unsigned long long owner_id, 
        unsigned long long birth_date, std::optional<unsigned long long> death_date,
        const std::string & name
    );
    void update_person(
        unsigned long long person_id,
        unsigned long long birth_date, std::optional<unsigned long long> death_date,
        const std::string & name
    );
    void delete_person(unsigned long long person_id);
    void mark_as_parent(unsigned long long child_id, unsigned long long parent_id);
    void delete_parents(unsigned long long child_id);
    void delete_children(unsigned long long parent_id);
    std::vector<unsigned long long> get_parents(unsigned long long person_id);

private:
    std::shared_ptr<tao::pq::transaction> _tx;
};

#endif