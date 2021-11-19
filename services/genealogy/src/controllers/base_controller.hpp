#ifndef _CONTROLLERS_BASE_CONTROLLER_HPP_

#define _CONTROLLERS_BASE_CONTROLLER_HPP_

#include <optional>
#include <memory>

#include "tao/pq/transaction.hpp"

#include "../server/http_request.hpp"
#include "../security/hasher.hpp"
#include "../security/key_storage.hpp"

class BaseController {
public:
    BaseController();

protected:
    std::optional<unsigned long long> _current_user_id(const HttpRequest & request);
    std::string _get_user_cookie_hash(int user_id);

    std::unique_ptr<Hasher> _hasher;
    std::unique_ptr<KeyStorage> _keys;
    std::shared_ptr<tao::pq::transaction> _tx;
};

#endif