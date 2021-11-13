#include "common.hpp"

#include <memory>

#include "tao/pq/notification.hpp"
#include "tao/pq/transaction.hpp"


Database::Database(const std::string & connection_string) {
    this->_connection = tao::pq::connection::create(connection_string);
}

std::shared_ptr<tao::pq::connection> Database::connection() {
    return this->_connection;
}

std::shared_ptr<tao::pq::transaction> Database::transaction() {
    return this->_connection->transaction();
}