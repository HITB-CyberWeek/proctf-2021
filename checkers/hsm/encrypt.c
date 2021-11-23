#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "bearssl.h"

static void
print_int_text(const char *name, const unsigned char *buf, size_t len) {
    size_t u;
    for (u = 0; u < len; u ++) {
        printf("%02X", buf[u]);
    }
    printf("\n");
}


static void
print_rsa_key(br_rsa_private_key *sk) {
    print_int_text("p ", sk->p, sk->plen);
    print_int_text("q ", sk->q, sk->qlen);
    print_int_text("dp", sk->dp, sk->plen);
    print_int_text("dq", sk->dq, sk->dqlen);
    print_int_text("iq", sk->iq, sk->iqlen);
}


static size_t
hextobin(unsigned char *dst, const char *src, int dst_size) {
    size_t num;
    unsigned acc;
    int z;

    num = 0;
    z = 0;
    acc = 0;
    while (*src != 0) {
        int c = *src ++;
        if (c >= '0' && c <= '9') {
            c -= '0';
        } else if (c >= 'A' && c <= 'F') {
            c -= ('A' - 10);
        } else if (c >= 'a' && c <= 'f') {
            c -= ('a' - 10);
        } else {
            continue;
        }
        if (z) {
            *dst ++ = (acc << 4) + c;
            num ++;
            if (num > dst_size) {
                break;
            }
        } else {
            acc = c;
        }
        z = !z;
    }
    return num;
}

unsigned long mix(unsigned long a, unsigned long b, unsigned long c) {
    a=a-b;  a=a-c;  a=a^(c >> 13);
    b=b-c;  b=b-a;  b=b^(a << 8);
    c=c-a;  c=c-b;  c=c^(b >> 13);
    a=a-b;  a=a-c;  a=a^(c >> 12);
    b=b-c;  b=b-a;  b=b^(a << 16);
    c=c-a;  c=c-b;  c=c^(b >> 5);
    a=a-b;  a=a-c;  a=a^(c >> 3);
    b=b-c;  b=b-a;  b=b^(a << 10);
    c=c-a;  c=c-b;  c=c^(b >> 15);
    return c;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s PUBKEY_HEX PLAINTEXT\n", argv[0]);
        return -1;
    }

    unsigned char pubkey[1024];
    unsigned char buf[1024];
    br_hmac_drbg_context rng;
    br_hmac_drbg_init(&rng, &br_sha256_vtable, "abcdef", strlen("abcdef"));

    memset((void *) pubkey, 0, sizeof(pubkey));
    hextobin(pubkey, argv[1], sizeof(pubkey));

    memset((void *) buf, 0, sizeof(buf));

    br_rsa_public_key pk;
    pk.n = pubkey;
    pk.nlen = 64;
    pk.e = pubkey + 64;
    pk.elen = 4;        // Note, 64 + 4 == 64 (PUBKEY_SIZE)

    char gamma[16];
    unsigned long seed = mix(clock(), time(NULL), getpid());
    srand(seed);
    size_t i;
    for (i = 0; i < sizeof(gamma); i++) {
        gamma[i] = rand() % 256;
    }

    br_rsa_oaep_encrypt menc = br_rsa_oaep_encrypt_get_default();
    int len = menc(&rng.vtable, &br_sha1_vtable, NULL, 0, &pk, buf, sizeof(buf), gamma, sizeof(gamma));

    char *plaintext = argv[2];

    for (i = 0; i <= strlen(plaintext); i++) {
      buf[len + i] = plaintext[i] ^ gamma[i % sizeof(gamma)];
    }
    print_int_text("", (unsigned char *)buf, len + strlen(plaintext) + 1);

/*    br_hmac_drbg_context rng;
    br_rsa_private_key sk;
    br_rsa_public_key pk;
    br_rsa_keygen kg;

    char seed[] = "seed for RSA keygen2";

    unsigned char kbuf_priv[BR_RSA_KBUF_PRIV_SIZE(2048)];
    unsigned char kbuf_pub[BR_RSA_KBUF_PUB_SIZE(2048)];

    unsigned size = 1024;
    uint32_t pubexp = 17;

    br_hmac_drbg_init(&rng, &br_sha256_vtable, seed, strlen(seed));
    kg = br_rsa_keygen_get_default();

    if (!kg(&rng.vtable, &sk, kbuf_priv, &pk, kbuf_pub, size, pubexp)) {
        printf("ERROR: RSA key generation failed\n");
        return -1;
    }
    print_rsa_key(&sk);

    if (!kg(&rng.vtable, &sk, kbuf_priv, &pk, kbuf_pub, size, pubexp)) {
        printf("ERROR: RSA key generation failed\n");
        return -1;
    }
    print_rsa_key(&sk);*/

    return 0;
}
