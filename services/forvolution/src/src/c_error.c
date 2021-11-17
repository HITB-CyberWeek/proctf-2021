#include <stdbool.h>
#include <errno.h>
#include <string.h>

int c_get_errno() {
	return errno;
}

const char* c_get_error_message() {
	return strerror(errno);
}
