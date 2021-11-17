#include <stdlib.h>
#include <sys/epoll.h>

#include <stdio.h>

struct c_epoll_event {
	int socket;
	int mode;
};

int buffer_size;
struct epoll_event* events_buffer;
const uint32_t EPOLLDEAD = EPOLLRDHUP | EPOLLERR | EPOLLHUP;

uint32_t get_event_type(int mode) {
	if (mode == 1)
		return EPOLLIN;
	if (mode == 2)
		return EPOLLOUT;
	return 0;
}

int get_mode(uint32_t events) {
	if (events & EPOLLDEAD)
		return 0;
	if (events & EPOLLIN)
		return 1;
	if (events & EPOLLOUT)
		return 2;
	return 0;
}

int c_epoll_create(int size) {
	int epfd;

	epfd = epoll_create(size);
	if (epfd < 0)
		return epfd;

	buffer_size = size;
	events_buffer = (struct epoll_event*)calloc(size, sizeof(struct epoll_event));
	if (events_buffer == NULL)
		return -1;

	return epfd;
}

int c_epoll_add(int epfd, int socket, int mode) {
	struct epoll_event ev;
	ev.events = get_event_type(mode);
	ev.data.fd = socket;
	return epoll_ctl(epfd, EPOLL_CTL_ADD, socket, &ev);
}

int c_epoll_update(int epfd, int socket, int mode) {
	struct epoll_event ev;

	uint32_t events = get_event_type(mode);
	if (!events)
		return epoll_ctl(epfd, EPOLL_CTL_DEL, socket, NULL);

	ev.events = events;
	ev.data.fd = socket;
	return epoll_ctl(epfd, EPOLL_CTL_MOD, socket, &ev);
}

int c_epoll_wait(int epfd, struct c_epoll_event* events) {
	int count;
	int i;

	count = epoll_wait(epfd, events_buffer, buffer_size, -1);
	if (count <= 0)
		return count;

	for (i = 0; i < count; ++i) {
		events[i].socket = events_buffer[i].data.fd;
		events[i].mode = get_mode(events_buffer[i].events);
	}

	return count;
}
