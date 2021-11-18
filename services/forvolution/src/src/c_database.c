#include <string.h>
#include <stdio.h>


void* c_db_write(void* buffer, void* data, int size) {
	memcpy(buffer, data, size);
	return buffer + size;
}

int c_db_store(void* start, void* end, char* filename) {
	FILE* file;
	int size;
	int writed;

	size = end - start;

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

void* c_db_read(void* buffer, void* data, int size) {
	data = buffer;
	return buffer + size;
}

int c_db_load(void* buffer, int size, char* filename) {
	FILE* file;
	int readed;

	file = fopen(filename, "r");
	if (file = NULL)
		return 0;

	readed = fread(buffer, 1, size, file);

	if (fclose(file))
		return 0;

	return readed;
}
