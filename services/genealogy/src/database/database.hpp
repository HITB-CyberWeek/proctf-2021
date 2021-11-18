#ifndef _DATABASE_COMMON_HPP

#define _DATABASE_COMMON_HPP

#include <memory>

#include "tao/pq/connection.hpp"
#include "tao/pq/transaction.hpp"

class Database {
public:
    Database(std::shared_ptr<tao::pq::transaction> tx);

    std::shared_ptr<tao::pq::transaction> transaction();

protected:
    std::shared_ptr<tao::pq::transaction> _tx;
};

#endif