#include "database.hpp"

#include <memory>

#include "tao/pq/notification.hpp"
#include "tao/pq/transaction.hpp"


Database::Database(std::shared_ptr<tao::pq::transaction> tx) :
 _tx(tx) {    
}

std::shared_ptr<tao::pq::transaction> Database::transaction() {
    return this->_tx;
}