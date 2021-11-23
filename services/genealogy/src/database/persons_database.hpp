#ifndef _DATABASE_PERSONS_HPP

#define _DATABASE_PERSONS_HPP

#include <optional>
#include <memory>
#include <string>
#include <vector>

#include "tao/pq.hpp"
#include "tao/json/value.hpp"

#include "database.hpp"

struct Person {
    unsigned long long id;
    unsigned long long owner_id;
    unsigned long long birth_date;
    unsigned long long death_date;
    std::string title;
    std::string first_name;
    std::string middle_name;
    std::string last_name;
    std::string photo_url;
};

class PersonsDatabase: public Database {
public:
    PersonsDatabase(std::shared_ptr<tao::pq::transaction> tx);
    tao::json::value build_person_json(unsigned long long person_id);

    std::optional<Person> find_person(unsigned long long id);
    Person create_person(
        unsigned long long owner_id, 
        unsigned long long birth_date, unsigned long long death_date,
        const std::string & title,
        const std::string & first_name,
        const std::string & middle_name,
        const std::string & last_name,
        const std::string & photo_url
    );
    void delete_person(unsigned long long person_id);
    void mark_as_parent(unsigned long long child_id, unsigned long long parent_id);
    void delete_parents(unsigned long long child_id);
    void delete_children(unsigned long long parent_id);
    std::vector<unsigned long long> get_parents(unsigned long long person_id);
};

#endif