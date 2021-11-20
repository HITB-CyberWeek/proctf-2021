CC = gcc

all: authme client

authme: authme.c 
	$(CC) -W -O2 -o authme authme.c
	strip authme

client: client.c 
	$(CC) -W -O2 -o client client.c
	strip client
	
