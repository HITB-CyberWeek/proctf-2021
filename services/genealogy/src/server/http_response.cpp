#include "http_response.hpp"

#include "http_server.hpp"
#include "tao/json/to_string.hpp"
#include "../utils.hpp"

HttpResponse::HttpResponse(HttpStatusCode status_code) : status_code(status_code) {
}

HttpResponse::HttpResponse(const std::string & content, HttpStatusCode status_code)
  : HttpResponse(status_code) {
    this->content = content;
}

HttpResponse::HttpResponse(const tao::json::value & content, HttpStatusCode status_code)
 : HttpResponse(tao::json::to_string(content) + "\n", status_code) {
}

HttpResponse::Headers HttpResponse::get_all_headers() const {
    auto headers = this->headers;
    for (auto& [cookie_name, cookie_value]: this->cookies) {
        auto set_cookie = string_format("%s=%s", cookie_name.c_str(), cookie_value.c_str());
        headers.push_back({"Set-Cookie", set_cookie});
    }
    return headers;
}

void HttpResponse::set_cookie(const std::string & name, const std::string & value) {
    this->cookies[name] = value;
}

void HttpResponse::set_header(const std::string &name, const std::string &value) {
    for (auto& [header_name, header_value]: this->headers) {
        if (header_name == name) {
            header_value = value;
            return;
        }
    }
    this->headers.push_back({name, value});
}