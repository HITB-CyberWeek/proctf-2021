#define _GNU_SOURCE
#include <arpa/inet.h>
#include <netinet/in.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include <stdio.h>

int c_tcp_open(int port) {
	int sock;
	int reuseaddr;
	struct sockaddr_in6 servaddr;

	sock = socket(AF_INET6, SOCK_STREAM | SOCK_NONBLOCK, IPPROTO_TCP);
	if (sock < 0)
		return sock;

	reuseaddr = 1;
	if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuseaddr, sizeof(int)) < 0) {
		close(sock);
		return -1;
	}

	memset(&servaddr, 0, sizeof(servaddr));
	servaddr.sin6_family = AF_INET6;
	inet_pton(AF_INET6, "::", &servaddr.sin6_addr);
	servaddr.sin6_port = htons(port);

	if (bind(sock, (const struct sockaddr*)&servaddr, sizeof(servaddr)) < 0) {
		close(sock);
		return -1;
	}

	if (listen(sock, 100) < 0) {
		close(sock);
		return -1;
	}

	return sock;
}

int c_accept(int socket) {
	struct sockaddr_in6 client_addr;
	socklen_t client_addr_len;

	client_addr_len = sizeof(client_addr);
	return accept4(socket, (struct sockaddr*)&client_addr, &client_addr_len, SOCK_NONBLOCK);
}

int c_read(int socket, char* buffer, int count) {
	return read(socket, buffer, count);
}

int c_write(int socket, char* buffer, int count) {
	return write(socket, buffer, count);
}

int c_tcp_close(int socket) {
	return close(socket);
}
