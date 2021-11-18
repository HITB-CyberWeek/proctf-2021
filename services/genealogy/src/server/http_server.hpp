#ifndef _HTTP_SERVER_HPP_

#define _HTTP_SERVER_HPP_

#include <map>
#include <string>
#include <functional>

#include "tcp_server.hpp"
#include "http_request.hpp"
#include "http_response.hpp"
#include "http_status_code.hpp"
#include "http_method.hpp"


class HttpServer: public TcpServer {
public:
    typedef std::function<HttpResponse(const HttpRequest &)> RouteHandler;

    const int MAX_CONTENT_LENGTH = 100 * 1024;

    struct RouteKey {
        RouteKey(HttpMethod method, const std::string & path, bool with_id);

        HttpMethod method;
        std::string path;
        bool with_id;

        bool operator<(const RouteKey & other) const;
        bool operator==(const RouteKey & other) const;
    };

    HttpServer(unsigned short port);
    void add_route(RouteKey key, RouteHandler handler);

protected:
    void _handle_client(int client_socket) override;
    void _send_headers(int client_socket, HttpStatusCode status_code, const HttpResponse::Headers & headers);
    void _send_body(int client_socket, const std::string & body);
    static RouteKey _get_route_key(HttpMethod method, const std::string & path);

private:
    HttpMethod _parse_http_method(const std::string & method);
    void _return_http_error(int client_socket, HttpStatusCode status_code);
    static int _extract_id_from_path(const std::string & path);

    std::map<RouteKey, RouteHandler> routes;
};

#endif