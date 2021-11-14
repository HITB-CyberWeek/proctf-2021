#include "http_request.hpp"

#include "tao/json.hpp"

#include "http_method.hpp"
#include "tao/json/from_stream.hpp"
#include "../utils.hpp"


HttpRequest::HttpRequest(HttpMethod method, const std::string & path, size_t id, const Headers & headers): 
    method(method), path(path), id(id),
    headers(headers), cookies(HttpRequest::get_cookies_by_headers(headers)) {
}

HttpRequest::Cookies HttpRequest::get_cookies_by_headers(const Headers & headers) {
    Cookies result;
    for (auto& [name, value]: headers) {
        if (name == "cookie") {
            for (auto& cookie: string_split(value, ';')) {
                auto splitted_cookie = string_split(cookie, '=');
                if (splitted_cookie.size() < 2) {
                    continue;
                }
                auto cookie_name = trim(splitted_cookie[0]);
                auto cookie_value = splitted_cookie[1];
                result[cookie_name] = cookie_value;
            }   
        }
    }
    return result;
}

tao::json::value HttpRequest::get_json() const {
    return tao::json::from_string(this->content);
}