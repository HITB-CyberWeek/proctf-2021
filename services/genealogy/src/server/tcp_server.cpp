#include "tcp_server.hpp"

#include <cassert>
#include <malloc.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <cstring>
#include <algorithm>

#include "../utils.hpp"


TcpServer::TcpServer(unsigned short port): _port(port) {
    this->_buffer = std::unique_ptr<char[]>(new char[this->BUFFER_SIZE]);
    this->_buffer_length = 0;
}

void TcpServer::start() {
    int server_socket = this->_create_socket();
    for (;;) {
        int conn_fd = accept(server_socket, NULL, NULL);
        if (guard(fork(), "Could not fork") == 0) {
            this->_handle_client(conn_fd);
        } else {
            close(conn_fd);
        }
    }
}

std::string TcpServer::_read_line(int socket) {
    auto buffer_begin = this->_buffer.get();
    auto buffer_end = this->_buffer.get() + this->_buffer_length;
    auto newline = std::find(buffer_begin, buffer_end, '\n');
    if (newline != buffer_end) {
        return this->_read_from_buffer(newline - buffer_begin + 1);
    }

    this->_fill_up_buffer(socket);

    return this->_read_line(socket);
}

std::string TcpServer::_read_from_buffer(size_t length) {
    assert(length <= this->_buffer_length);

    auto buffer = this->_buffer.get();

    std::string result;
    result.assign(buffer, length);
    std::memmove(buffer, buffer + length, this->_buffer_length - length);

    this->_buffer_length -= length;

    return result;
}

void TcpServer::_fill_up_buffer(int socket) {
    size_t length = this->BUFFER_SIZE - this->_buffer_length;
    auto buffer = this->_buffer.get() + this->_buffer_length;

    ssize_t num_bytes_received = guard(recv(socket, buffer, length - 1, 0), "Could not recv on TCP connection");
    if (num_bytes_received == 0) {
        guard(shutdown(socket, SHUT_WR), "Could not shutdown TCP connection");
        guard(close(socket), "Could not close TCP connection");
        exit(0);
    }

    this->_buffer_length += num_bytes_received;
}

std::string TcpServer::_read(int socket, size_t bytes_count) {
    assert(bytes_count <= BUFFER_SIZE);

    while (bytes_count > this->_buffer_length) {
        this->_fill_up_buffer(socket);
    }
    return this->_read_from_buffer(bytes_count);
}

void TcpServer::_handle_client(int client_socket) {
    pid_t my_pid = getpid();
    char buf[100];
    for (;;) {
        ssize_t num_bytes_received = guard(recv(client_socket, buf, sizeof(buf) - 1, 0), "Could not recv on TCP connection");
        if (num_bytes_received == 0) {
            printf("%d: received end-of-connection; closing connection and exiting\n", my_pid);
            guard(shutdown(client_socket, SHUT_WR), "Could not shutdown TCP connection");
            guard(close(client_socket), "Could not close TCP connection");
            exit(0);
        }
        printf("%d: received %zu, bytes; echoing\n", my_pid, strlen(buf));

        guard(send(client_socket, buf, num_bytes_received, 0), "Could not send to TCP connection");
        printf("%d: echoed %zu bytes; receiving more\n", my_pid, strlen(buf));
    }
}

void TcpServer::_send(int client_socket, const std::string & data) {
    size_t sent = 0;
    while (sent != data.length()) {
        sent += guard(
            send(client_socket, data.data() + sent, data.length() - sent, 0),
            "Could not send to TCP connection"
        );
    }
}

void TcpServer::_close(int client_socket) {
    guard(shutdown(client_socket, SHUT_WR), "Could not shutdown TCP connection");
    guard(close(client_socket), "Could not close TCP connection");
    exit(0);
}

int TcpServer::_create_socket() {
    int server_socket = guard(socket(PF_INET, SOCK_STREAM, 0), "Could not create TCP socket");

    int opt = 1;
    guard(
        setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt)),
        "Cound not set socket option"
        );

    struct sockaddr_in listen_addr;
    listen_addr.sin_family = AF_INET;
    listen_addr.sin_addr.s_addr = INADDR_ANY;
    listen_addr.sin_port = htons(this->_port);

    guard(
        bind(server_socket, (struct sockaddr*) &listen_addr, sizeof(listen_addr)),
        "Cound not bind to port"
    );

    guard(listen(server_socket, 100), "Could not listen on TCP socket");

    printf("Listening for connections on port %d\n", this->_port);

    return server_socket;
}