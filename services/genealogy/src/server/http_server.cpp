#include "http_server.hpp"

#include <cassert>
#include <cstdlib>
#include <map>
#include <sstream>
#include <stdexcept>

#include "http_response.hpp"
#include "http_status_code.hpp"
#include "http_method.hpp"
#include "../utils.hpp"


auto HttpStatusCodeMessages = std::map<HttpStatusCode, std::string> {
    {HttpStatusCode::OK, "OK"},
    {HttpStatusCode::CREATED, "Created"},
    {HttpStatusCode::MOVED_PERMANENTLY, "Moved Permanently"},
    {HttpStatusCode::FOUND, "Found"},
    {HttpStatusCode::NOT_MODIFIED, "Not Modified"},
    {HttpStatusCode::BAD_REQUEST, "Bad Request"},
    {HttpStatusCode::UNAUTHORIZED, "Unauthorized"},
    {HttpStatusCode::FORBIDDEN, "Forbidden"},
    {HttpStatusCode::NOT_FOUND, "Not Found"},
    {HttpStatusCode::METHOD_NOT_ALLOWED, "Method Not Allowed"},
    {HttpStatusCode::REQUEST_TIMEOUT, "Request Timeout"},
    {HttpStatusCode::CONFLICT, "Conflict"},
    {HttpStatusCode::LENGTH_REQUIRED, "Length Required"},
    {HttpStatusCode::PRECONDITION_FAILED, "Precondition Failed"},
    {HttpStatusCode::I_M_A_TEAPOT, "I'm A Teapot"},
    {HttpStatusCode::TOO_MANY_REQUESTS, "Too Many Requests"},
    {HttpStatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error"},
};

bool HttpServer::RouteKey::operator<(const RouteKey & other) const {
    if (this->method != other.method) {
        return this->method < other.method;
    }
    if (this->path != other.path) {
        return this->path < other.path;
    }
    return this->with_id < other.with_id;
}

bool HttpServer::RouteKey::operator==(const RouteKey & other) const {
    return this->method == other.method && this->path == other.path && this->with_id == other.with_id;
}

HttpServer::RouteKey::RouteKey(HttpMethod method, const std::string & path, bool with_id) :
    method(method), path(path), with_id(with_id) {
}

HttpServer::HttpServer(unsigned short port) : TcpServer(port) {
}

void HttpServer::_handle_client(int client_socket) {
    // Read first line of the request: GET /index.html HTTP/1.1
    auto request_line = this->_read_line(client_socket);

    if (request_line.size() > 1000) {
        this->_return_http_error(client_socket, HttpStatusCode::BAD_REQUEST);
        return;
    }
    
    std::istringstream request_line_stream(request_line);
    std::string method_str;
    std::string path;
    request_line_stream >> method_str >> path;

    auto method = this->_parse_http_method(method_str);
    if (method == HttpMethod::UNKNOWN || path.empty() || !path.starts_with("/")) {
        this->_return_http_error(client_socket, HttpStatusCode::BAD_REQUEST);
        return;
    }

    if (!path.ends_with("/")) {
        path.append("/");
    }

    printf("%s %s\n", method_str.c_str(), path.c_str());
    
    // Read headers from the request: one per line
    auto headers = HttpRequest::Headers();
    std::string header = this->_read_line(client_socket);
    while (trim(header) != "") {
        auto colon = header.find_first_of(':');
        if (colon != std::string::npos) {
            auto header_name = trim(header.substr(0, colon));
            auto header_value = trim(header.substr(colon + 1));
            to_lower_case(header_name);
            headers[header_name] = header_value;
        }
        header = this->_read_line(client_socket);
    }

    auto request = HttpRequest(method, path, 0, headers);

    // Read body of the request
    if (method == HttpMethod::POST || method == HttpMethod::PUT ||
        headers.find("content-length") != headers.end()) {
        if (headers.find("content-length") == headers.end()) {
            this->_return_http_error(client_socket, HttpStatusCode::LENGTH_REQUIRED);
            return;
        }

        int content_length;
        try {
            content_length = stoi(headers["content-length"]);
        } catch (std::exception &) {
            this->_return_http_error(client_socket, HttpStatusCode::LENGTH_REQUIRED);
            return;
        }
        if (content_length < 0 || content_length > MAX_CONTENT_LENGTH) {
            this->_return_http_error(client_socket, HttpStatusCode::BAD_REQUEST);
            return;
        }
        auto content = this->_read(client_socket, content_length);
        request.content = content;
    }

    // Find appropriate RouteKey for this path
    auto route_key = this->_get_route_key(method, path);
    if (route_key.with_id) {
        request.id = this->_extract_id_from_path(path);
    }

    // Find handler by RouteKey, if not found, return 404
    if (this->routes.find(route_key) == this->routes.end()) {
        this->_return_http_error(client_socket, HttpStatusCode::NOT_FOUND);
        return;
    }

    // Call handler!
    auto handler = this->routes[route_key];
    HttpResponse response;
    try {
        response = handler(request);    
    } catch (std::exception & e) {
        printf("%s\n", e.what());
        this->_return_http_error(client_socket, HttpStatusCode::INTERNAL_SERVER_ERROR);
        return;
    }    

    printf("%s %s → %d\n", method_str.c_str(), path.c_str(), response.status_code);

    // Send response to the client
    this->_send_headers(client_socket, response.status_code, response.get_all_headers());
    this->_send_body(client_socket, response.content);
    this->_close(client_socket);
}

void HttpServer::_send_headers(
    int client_socket, HttpStatusCode status_code, const HttpResponse::Headers & headers
) {
    std::string status_code_message = "Unknown";
    if (HttpStatusCodeMessages.find(status_code) != HttpStatusCodeMessages.end()) {
        status_code_message = HttpStatusCodeMessages[status_code];
    }
    // Send status line: HTTP/1.1 200 OK
    this->_send(client_socket, string_format("HTTP/1.1 %d %s\n", (int) status_code, status_code_message.c_str()));

    bool has_content_type = false;
    for (auto& [name, value]: headers) {
        auto header_name = name;
        to_lower_case(header_name);
        if (header_name == "content-type") {
            has_content_type = true;
        }
        this->_send(client_socket, string_format("%s: %s\n", name.c_str(), value.c_str()));
    }
    if (!has_content_type) {
        this->_send(client_socket, "Content-Type: application/json\n");
    }
}

void HttpServer::_send_body(int client_socket, const std::string & body) {
    size_t content_length = body.length();
    this->_send(client_socket, string_format("Content-Length: %zu\n", content_length));
    this->_send(client_socket, "Connection: Close\n");
    this->_send(client_socket, "\n");
    if (content_length) {
        this->_send(client_socket, body);
    }
}

HttpMethod HttpServer::_parse_http_method(const std::string & method) {
    if (method == "GET") {
        return HttpMethod::GET;
    }
    if (method == "POST") {
        return HttpMethod::POST;
    }
    if (method == "PUT") {
        return HttpMethod::PUT;
    }
    if (method == "DELETE") {
        return HttpMethod::DELETE;
    }
    return HttpMethod::UNKNOWN;
}

void HttpServer::_return_http_error(int client_socket, HttpStatusCode status_code) {
    this->_send_headers(client_socket, status_code, {});
    this->_send_body(client_socket, "");
    this->_close(client_socket);    
}

void HttpServer::add_route(RouteKey key, RouteHandler handler) {
    if (!key.path.ends_with('/')) {
        key.path.append("/");
    }
    this->routes[key] = handler;
}

HttpServer::RouteKey HttpServer::_get_route_key(HttpMethod method, const std::string & path) {
    assert(path.length() != 0);
    assert(path.starts_with("/"));
    assert(path.ends_with("/"));
    if (path == "/") {
        return RouteKey(method, path, false);
    }

    auto id = _extract_id_from_path(path);
    if (id == -1) {
        return RouteKey(method, path, false);
    }

    auto last_slash = path.find_last_of("/", path.length() - 2);
    return RouteKey(method, path.substr(0, last_slash + 1), true);
}

int HttpServer::_extract_id_from_path(const std::string & path) {
    assert(path.length() != 0);
    assert(path.starts_with("/"));
    assert(path.ends_with("/"));
    if (path == "/") {
        return -1;
    }
    
    // Id is always the last part of the path
    auto last_slash = path.find_last_of("/", path.length() - 2);
    assert(last_slash != std::string::npos);

    try {
        auto id = std::stoi(path.substr(last_slash + 1, path.length()));
        if (id >= 0) {
            return id;
        }
    } catch (std::invalid_argument &) {
    } catch (std::out_of_range &) {
    }

    return -1;
}

void HttpServer::add_static_routes(const std::filesystem::path & path) {
    // Adds routes for files in some directory (i.e. static/)
    for (const auto & entry : std::filesystem::directory_iterator(path)) {
        if (!entry.is_regular_file()) {
            continue;
        }

        auto path = std::string("/") + entry.path().filename().string();
        if (path == "/index.html") {
            path = "/";
        }

        this->add_route(
            {HttpMethod::GET, path, false}, 
            [entry](const auto & request) {
                auto response = HttpResponse(get_file_content(entry.path()), HttpStatusCode::OK);
                if (entry.path().string().ends_with(".html")) {
                    response.set_header("Content-Type", "text/html");
                } else if (entry.path().string().ends_with(".css")) {
                    response.set_header("Content-Type", "text/css");
                } else if (entry.path().string().ends_with(".js")) {
                    response.set_header("Content-Type", "text/javascript");
                } else {
                    response.set_header("Content-Type", "application/octet-stream");
                }
                return response;
            }
        );
    }
}