#ifndef _TCP_SERVER_HPP_

#define _TCP_SERVER_HPP_

#include <memory>
#include <string>

class TcpServer {
public:
    TcpServer(unsigned short port);
    void start();

protected:
    std::string _read_line(int socket);
    std::string _read(int socket, size_t bytes_count);
    virtual void _handle_client(int client_socket) = 0;
    void _send(int socket, const std::string & data);
    void _close(int socket);

private:
    const size_t BUFFER_SIZE = 100 * 1024;
    const unsigned short TIMEOUT_SECONDS = 60;
    unsigned short _port;
    std::unique_ptr<char[]> _buffer;
    size_t _buffer_length;

    int _create_socket();
    std::string _read_from_buffer(size_t length);
    void _fill_up_buffer(int socket);
};

#endif