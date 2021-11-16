#ifndef _DATABASE_COMMON_HPP

#define _DATABASE_COMMON_HPP

#include <memory>

#include "tao/pq/connection.hpp"
#include "tao/pq/transaction.hpp"

class Database {
public:
    Database(const std::string & connection_string="host=172.19.0.3 port=6432 dbname=genealogy user=genealogy password=genealogy");

    std::shared_ptr<tao::pq::connection> connection();
    std::shared_ptr<tao::pq::transaction> transaction();

private:
    std::shared_ptr<tao::pq::connection> _connection;
};

#endif