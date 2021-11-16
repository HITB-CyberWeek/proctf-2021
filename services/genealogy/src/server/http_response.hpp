#ifndef _HTTP_RESPONSE_HPP_

#define _HTTP_RESPONSE_HPP_

#include <map>
#include <vector>
#include <tuple>
#include <string>

#include "tao/json/value.hpp"

#include "http_status_code.hpp"

class HttpResponse {
public:
    typedef std::vector< std::tuple<std::string, std::string> > Headers;
    typedef std::map<std::string, std::string> Cookies;

    HttpResponse(HttpStatusCode status_code = HttpStatusCode::OK);
    HttpResponse(const std::string & content, HttpStatusCode status_code = HttpStatusCode::OK);
    HttpResponse(const tao::json::value & content, HttpStatusCode status_code = HttpStatusCode::OK);
    
    HttpStatusCode status_code;
    Headers headers;
    Cookies cookies;
    std::string content;

    Headers get_all_headers() const;
    void set_cookie(const std::string & name, const std::string & value);
    void set_header(const std::string & name, const std::string & value);
};

#endif