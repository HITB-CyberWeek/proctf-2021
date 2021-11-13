#ifndef _HTTP_REQUEST_HPP_

#define _HTTP_REQUEST_HPP_

#include <map>
#include <string>

#include "tao/json.hpp"

#include "http_method.hpp"


class HttpRequest {
public:
    typedef std::map<std::string, std::string> Headers;
    typedef std::map<std::string, std::string> Cookies;

    HttpRequest(HttpMethod method, const std::string & path, size_t id, const Headers & headers);

    const HttpMethod method;
    const std::string path;
    size_t id;
    const Headers headers;
    const Cookies cookies;

    std::string content;

    tao::json::value get_json() const;

private:
    static Cookies get_cookies_by_headers(const Headers & headers);
};

#endif