#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

void make_dir_recurcivly(const char* filename) {
	const char* p;
	char* tmp;

	tmp = calloc(1, strlen(filename) + 1);
	p = filename;

	while((p = strchr(p, '/')) != NULL) {
		memcpy(tmp, filename, p - filename);
		tmp[filename - p] = 0;
		++p;
		if (mkdir(tmp, 0755) && errno != EEXIST)
			break;
	}

	free(tmp);
}

void* c_db_write(void* buffer, void* data, int size) {
	memcpy(buffer, data, size);
	return buffer + size;
}

int c_db_store(void* start, void* end, char* filename) {
	FILE* file;
	int size;
	int writed;

	size = end - start;

	make_dir_recurcivly(filename);
	file = fopen(filename, "w");
	if (file == NULL) {
		perror("open: ");
		return 0;
	}

	writed = fwrite(start, 1, size, file);

	if (fclose(file)) {
		perror("close: ");
		return 0;
	}

	if (writed < size)
		return 0;

	return writed;
}

void* c_db_shift(void* buffer, int size) {
	return buffer + size;
}

int c_db_load(void* buffer, int size, char* filename) {
	FILE* file;
	int readed;

	file = fopen(filename, "r");
	if (file == NULL)
		return 0;

	readed = fread(buffer, 1, size, file);

	if (fclose(file))
		return 0;

	return readed;
}
