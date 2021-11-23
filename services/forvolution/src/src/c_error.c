#include <errno.h>
#include <string.h>

const char* c_get_error_message() {
	return strerror(errno);
}
