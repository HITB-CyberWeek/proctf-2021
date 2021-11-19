#include <signal.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <byteswap.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netinet/in.h>


static const uint32_t SHA256_K[256] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static uint32_t rotr(uint32_t num, int count) {
    return num >> count | (num << (32 - count));
}

void print_hex(uint8_t* msg, int msglen) {
    for (int i = 0; i < msglen; i += 1) {
        printf("%02x", (uint8_t)msg[i]);
    }
    printf("\n");
}

static int div_like_in_python(int a, int b) {
    return ((a % b) + b) % b;
}

static void sha256(const uint8_t* msg, int msglen, uint8_t *out) {
    uint32_t ss[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};

    uint8_t chunk[64];
    uint8_t padding[64] = {0x80, 0};

    int padding_len = 1 + div_like_in_python((64 - (msglen + 1 + 8) ), 64 ) + 8;

    *(uint64_t *)(&padding[padding_len - 8]) = __bswap_64(msglen*8);

    int padding_ptr = 0;
    for (int chunk_num = 0; chunk_num < (msglen+padding_len) / 64 ; chunk_num += 1) {
        int copied = chunk_num * 64;
        int left = msglen - copied;

        if (left >= 64) {
            memcpy(chunk, &msg[64*chunk_num], 64);
        } else {
            if(left < 0) {
                left = 0;
            }
            memcpy(chunk, &msg[64*chunk_num], left);
            int space_in_block = 64 - left;

            memcpy(chunk+left, padding+padding_ptr, 64 - left);
            padding_ptr += (64 - left);
        }

        uint32_t w[64];
        for (int i = 0; i < 16; i += 1) {
            w[i] = __bswap_32(*(uint32_t *)(&chunk[i*4]));
        }

        for (int i = 16; i < 64; i += 1) {
            uint32_t a = rotr(w[i-15], 7) ^ rotr(w[i-15], 18) ^ (w[i-15] >> 3);
            uint32_t b = rotr(w[i-2], 17) ^ rotr(w[i-2], 19) ^ (w[i-2] >> 10);
            w[i] = a + b + w[i-16] + w[i-7];

        }

        uint32_t s[8];
        for (int i = 0; i < 8; i+=1) {
            s[i] = ss[i];
        }

        for (int i = 0; i < 64; i+= 1) {
            uint32_t c = (s[4] & s[5]) ^ ((s[4] ^ 0xffffffff) & s[6]);
            uint32_t t = SHA256_K[i] + s[7] + c + w[i] +
                         (rotr(s[4], 6) ^ rotr(s[4], 11) ^ rotr(s[4], 25));
            uint32_t q = rotr(s[0], 2) ^ rotr(s[0], 13) ^ rotr(s[0], 22);
            uint32_t m = (s[0] & s[1]) ^ (s[0] & s[2]) ^ (s[1] & s[2]);

            s[7] = s[6];
            s[6] = s[5];
            s[5] = s[4];
            s[4] = s[3] + t;
            s[3] = s[2];
            s[2] = s[1];
            s[1] = s[0];
            s[0] = q + m + t;
        }

        for (int i = 0; i < 8; i += 1) {
            ss[i] += s[i];
        }
    }

    for (int i = 0; i < 8; i += 1) {
        *(uint32_t*)(&out[i*4]) = __bswap_32(ss[i]);
    }
}


static int read_packet_or_die(int client_socket, uint8_t* buf) {
    uint8_t got_bytes = 0;

    uint8_t pkt_len;

    if (recv(client_socket, &pkt_len, 1, 0) != 1) {
        return 0;
    }

    while (got_bytes < pkt_len) {
        int got_this_time = recv(client_socket, &buf[got_bytes], pkt_len-got_bytes, 0);
        if (got_this_time <= 0) {
            exit(1);
        }
        got_bytes += got_this_time;
    }

    return pkt_len;
}

static int write_packet_or_die(int client_socket, uint8_t* buf, uint8_t len) {
    uint8_t sent_bytes = 0;

    if (send(client_socket, &len, 1, 0) != 1) {
        return 0;
    }

    while (sent_bytes < len) {
        int sent_this_time = send(client_socket, &buf[sent_bytes], len-sent_bytes, 0);
        if (sent_this_time <= 0) {
            exit(1);
        }
        sent_bytes += sent_this_time;
    }
    return sent_bytes;
}


static void hash_to_hex(uint8_t* hash, char *hex) {
    for(int i = 0; i < 32; i += 1) {
        sprintf(&hex[i*2], "%02x", hash[i]);
    }
    hex[64] = 0;
}

static int send_error_or_die(int client_socket) {
    uint8_t error_code = 0xff;
    return write_packet_or_die(client_socket, &error_code, 1) > 0;
}

static int send_ok_or_die(int client_socket) {
    uint8_t error_code = 0x0;
    return write_packet_or_die(client_socket, &error_code, 1) > 0;
}


static int get_random(uint8_t* buf, uint8_t num) {
    int fd = open("/dev/urandom", O_RDONLY);

    if(fd == -1) {
        fprintf(stderr, "Bad open\n");
        exit(1);
    }

    if (read(fd, buf, num) != num) {
        fprintf(stderr, "Bad read\n");
        exit(1);
    }
    close(fd);
}

int validate_string(uint8_t* buf) {
    for (int i = 0; buf[i]; i += 1) {
        int good = 0;

        if (buf[i] >= 'a' && buf[i] <= 'z') {
            good = 1;
        } else if (buf[i] >= 'A' && buf[i] <= 'Z') {
            good = 1;
        } else if (buf[i] >= '0' && buf[i] <= '9') {
            good = 1;
        } else if (buf[i] == '_' || buf[i] == '-' || buf[i] == '=') {
            good = 1;
        }

        if (!good) {
            return 0;
        }
    }
    return 1;
}


static void get_valid_string_or_die(int client_socket, uint8_t *str) {
    uint8_t str_len = read_packet_or_die(client_socket, str);
    str[str_len] = 0;

    if(str_len < 1 || str_len >= 64 || !validate_string(str)) {
        send_error_or_die(client_socket);
        exit(1);
    }
}


uint64_t fastpow(uint64_t base, uint64_t exp)
{
    uint64_t result = 1;
    for (;;)
    {
        if (exp & 1)
            result *= base;
        exp >>= 1;
        if (!exp) {
            break;
        }
        base *= base;
    }

    return result;
}


void register_and_put(int client_socket) {
    uint8_t login[256];
    uint8_t password[256];
    uint8_t flag[256];

    get_valid_string_or_die(client_socket, login);
    get_valid_string_or_die(client_socket, password);
    get_valid_string_or_die(client_socket, flag);

    FILE* file = fopen("flags.txt", "a+");
    if (file == NULL) {
        fprintf(stderr, "failed to open flags.txt\n");
        send_error_or_die(client_socket);
        exit(1);
    }

    int success = fprintf(file, "%s %s %s\n", login, password, flag);
    fflush(file);

    if (!success) {
        send_error_or_die(client_socket);
        exit(1);
    }

    send_ok_or_die(client_socket);
}

void login_and_get(int client_socket) {
    uint8_t login[256];
    uint8_t random[512];
    uint8_t response_buf[256];

    uint8_t login_buf[64] = {0};
    uint8_t pass_buf[64] = {0};
    uint8_t flag_buf[64] = {0};

    uint8_t password_hash[32];
    uint8_t random_hash[32];

    char *line = NULL;
    size_t len = 0;

    get_valid_string_or_die(client_socket, login);

    get_random(random, 2);
    write_packet_or_die(client_socket, random, 2);

    uint8_t rand_len = read_packet_or_die(client_socket, random+2);
    rand_len += 2;
    if (rand_len < 4) {
        send_error_or_die(client_socket);
        exit(1);
    }

    FILE* file = fopen("flags.txt", "a+");
    if (file == NULL) {
        fprintf(stderr, "failed to open flags.txt\n");
        send_error_or_die(client_socket);
        exit(1);
    }

    while (getline(&line, &len, file) != -1) {
        if (sscanf(line, "%63s %63s %63s\n", login_buf, pass_buf, flag_buf) == 3) {
            if (!strcmp(login, login_buf)) {
                break;
            }
        }
    }

    if(line) {
        free(line);
    }

    if (strcmp(login, login_buf)) {
        send_error_or_die(client_socket);
        exit(1);
    }

    sha256(pass_buf, strlen(pass_buf), password_hash);
    sha256(random, rand_len, random_hash);

    uint64_t last_pass = *((uint64_t *)(&password_hash[24]));
    uint64_t last_random = *((uint64_t *)(&random_hash[24]));

    // print_hex(password_hash, 32);
    // print_hex(random_hash, 32);

    uint64_t expected_response = fastpow(last_pass, last_random);

    uint8_t response_len = read_packet_or_die(client_socket, response_buf);
    if (response_len != 8) {
        send_error_or_die(client_socket);
        exit(1);
    }

    if (expected_response != *((uint64_t *)response_buf)) {
        send_error_or_die(client_socket);
        exit(1);
    }

    write_packet_or_die(client_socket, flag_buf, strlen(flag_buf));
}

void list_users(int client_socket) {
    uint8_t login_buf[64] = {0};
    uint8_t pass_buf[64] = {0};
    uint8_t flag_buf[64] = {0};

    FILE* file = fopen("flags.txt", "a+");
    if (file == NULL) {
        fprintf(stderr, "failed to open flags.txt\n");
        send_error_or_die(client_socket);
        exit(1);
    }

    const int max_file_size_to_look = 500000;

    fseek(file, 0, SEEK_END);
    int size = ftell(file);
    int start_offset = size - max_file_size_to_look;
    if (start_offset < 0) {
        start_offset = 0;
    }

    fseek(file, start_offset, SEEK_SET);

    char *line = NULL;
    size_t len = 0;

    if (start_offset > 0) {
        // skip one line
        if (getline(&line, &len, file) == -1) {
            send_error_or_die(client_socket);
            exit(1);
        }
    }

    while (getline(&line, &len, file) != -1) {
        if (sscanf(line, "%63s", login_buf) == 1) {
            write_packet_or_die(client_socket, login_buf, strlen(login_buf));
        }
    }

    if(line) {
        free(line);
    }
}

int handle_client(int client_socket) {
    uint8_t start_pkt[256];


    if (read_packet_or_die(client_socket, start_pkt) != 1) {
        send_error_or_die(client_socket);
        exit(1);
    }

    if(start_pkt[0] == 0) {
        register_and_put(client_socket);
    } else if (start_pkt[0] == 1) {
        login_and_get(client_socket);
    } else if (start_pkt[0] == 2) {
        list_users(client_socket);
    } else {
        send_error_or_die(client_socket);
        exit(1);
    }

    return 0;
}


void sigchld_handler(int signo) {
    while (1) {
        int wstatus;
        pid_t pid = waitpid(-1, &wstatus, WNOHANG);
        if (pid == 0 || pid == -1) {
            break;
        }
    }
}

int main(int argc, char ** argv) {
    if (chdir("data") == -1) {
        fprintf(stderr, "Bad chdir\n");
        exit(1);
    }

    struct sigaction sa;
    sa.sa_handler = sigchld_handler;
    sa.sa_flags = SA_RESTART;
    sigfillset(&sa.sa_mask);
    sigaction(SIGCHLD, &sa, NULL);

    int serv_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (serv_socket == -1) {
        fprintf(stderr, "Bad server socket\n");
        exit(1);
    }

    int one = 1;
    if (setsockopt(serv_socket, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one)) == -1) {
        fprintf(stderr, "Bad setsockopt\n");
        exit(1);
    }

    struct sockaddr_in my_addr = {};
    my_addr.sin_family = AF_INET;
    my_addr.sin_port = __bswap_16(3256);

    if (bind(serv_socket, (struct sockaddr *) &my_addr, sizeof(my_addr)) == -1) {
        fprintf(stderr, "Bad bind\n");
        exit(1);
    }

    const int LISTEN_BACKLOG = 256;
    if (listen(serv_socket, LISTEN_BACKLOG) == -1) {
        fprintf(stderr, "Bad listen\n");
        exit(1);
    }

    struct sockaddr_in peer_addr = {};
    socklen_t peer_addr_size = sizeof(peer_addr);

    while(1) {
        int client_socket = accept(serv_socket, (struct sockaddr*) &peer_addr, &peer_addr_size);

        if (client_socket == -1) {
            continue;
        }

        int fork_result = fork();

        if (fork_result == -1) {
            fprintf(stderr, "Bad fork\n");
            sleep(1);
            continue;
        }

        if (fork_result == 0) {
            // child
            alarm(10);
            close(serv_socket);
            handle_client(client_socket);
            exit(0);
        } else {
            // parent
            close(client_socket);
        }
    }

    return 0;
}
