#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <bsp.h>
#include <ctype.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

// FIXME
#include "bearssl_rand.h"
#include "bearssl_rsa.h"
#include "rand/hmac_drbg.c"
#include "mac/hmac.c"
#include "rsa/rsa_default_keygen.c"
#include "rsa/rsa_i31_keygen.c"
#include "rsa/rsa_i31_keygen_inner.c"
#include "int/i31_ninv31.c"
#include "int/i31_decred.c"
#include "int/i31_moddiv.c"
#include "int/i31_add.c"
#include "int/i31_decode.c"
#include "int/i31_muladd.c"
#include "int/i31_rshift.c"
#include "int/i31_encode.c"
#include "int/i31_mulacc.c"
#include "int/i31_sub.c"
#include "int/i31_bitlen.c"
#include "int/i32_div32.c"
#include "int/i31_modpow2.c"
#include "int/i31_tmont.c"
#include "int/i31_montmul.c"
#include "codec/ccopy.c"
#include "int/i31_fmont.c"
#include "hash/sha2small.c"
#include "codec/dec32be.c"
#include "codec/enc32be.c"
#include "hash/sha1.c"
#include "rsa/rsa_default_oaep_encrypt.c"
#include "rsa/rsa_i31_oaep_encrypt.c"
#include "rsa/rsa_oaep_pad.c"
#include "hash/mgf1.c"
#include "rsa/rsa_i31_pub.c"
#include "int/i31_decmod.c"
#include "rsa/rsa_default_oaep_decrypt.c"
#include "rsa/rsa_i31_oaep_decrypt.c"
#include "rsa/rsa_i31_priv.c"
#include "rsa/rsa_oaep_unpad.c"
#include "int/i31_reduce.c"

/******************************** Macroses ************************************/

//#define DEBUG
//#define DEBUG_INPUT
#define MAX_SLOTS (17*30)
// 17 teams x 1 max register(generate) per round x 30 rounds = 510
#define RSA_KEY_SIZE_BITS   512
#define RSA_PUB_EXP          17
#define META_SIZE            33                                       // So we can store here 32-byte flag + '\0'
#define RSA_CIPHERTEXT_SIZE  BR_RSA_KBUF_PUB_SIZE(RSA_KEY_SIZE_BITS)  // 68
#define PLAINTEXT_SIZE       64
#define CIPHERTEXT_SIZE      (RSA_CIPHERTEXT_SIZE + PLAINTEXT_SIZE)   // 132
#define PUBKEY_SIZE          BR_RSA_KBUF_PUB_SIZE(RSA_KEY_SIZE_BITS)  // 68
#define PRIVKEY_SIZE         BR_RSA_KBUF_PRIV_SIZE(RSA_KEY_SIZE_BITS) // 160
#define IS_VALID_SLOT(slot)  (0 <= slot && slot < MAX_SLOTS)
#define MAX_CMD_LEN          16
#define MAX_ARG1_LEN         (2 * CIPHERTEXT_SIZE)                    // 264
#define MAX_ARG2_LEN         (2 * CIPHERTEXT_SIZE)                    // 264
#define MAX_ARG3_LEN         30
#define IS_COMMAND(input, check_name, check_args) (strcmp(input->command, check_name) == 0 && input->argc == check_args)

/******************************* Structures ***********************************/

typedef struct {
  int idx;                              //   4
  char meta[META_SIZE];                 //  33
  char buf[PLAINTEXT_SIZE + 1];         // 133
  br_rsa_private_key sk;
  unsigned char privkey[PRIVKEY_SIZE];  // 240
  br_rsa_public_key pk;
  unsigned char pubkey[PUBKEY_SIZE];    // 100
} Slot;                                 // TOTAL = 392 bytes

typedef struct {
  char command[MAX_CMD_LEN + 1];
  char argc;
  char arg1[MAX_ARG1_LEN + 1]; // 768 bits / 8 = 96 bytes, 96 bytes * 4/3 = 128 bytes (base64)
  char arg2[MAX_ARG2_LEN + 1];
  char arg3[MAX_ARG3_LEN + 1];
  bool error;
  bool eof;
} Input;

/****************** forward declarations to avoid warnings ********************/

rtems_task Init(rtems_task_argument argument);
bool handle_input(Input *input);
void parse_input_stdin(Input *input);
bool set_meta(Slot* slot, char new_meta[]);
bool get_meta(const Slot slot);
void rand_init(char seed[]);
void print_int_text(const char *name, const unsigned char *buf, size_t len);
void generate(Slot *slot);
void encrypt(char *pubkey_hex, char *plaintext);
void decrypt(Slot *slot, char *ciphertext_hex);
#ifdef DEBUG
void rsa_test(void);
#endif

/******************************************************************************/

Slot slots[MAX_SLOTS];
int free_slot_index = 0; // round-robin
int max_token_lengths[4] = {
  MAX_CMD_LEN, MAX_ARG1_LEN, MAX_ARG2_LEN, MAX_ARG3_LEN
};
br_hmac_drbg_context rng;

/////////////////////////////////////////////////////////////////////////////////////////

#ifdef DEBUG_INPUT
void print_input(Input *input) {
  printf("[DEBUG] input:\n");
  printf("   error     : %s\n", input->error ? "true" : "false");
  printf("   command   : '%s' (length %d, max %d)\n", input->command, strlen(input->command), MAX_CMD_LEN);
  printf("   argc      : %d\n", input->argc);
  printf("   arg1      : '%s' (length %d, max %d)\n", input->arg1, strlen(input->arg1), MAX_ARG1_LEN); 
  printf("   arg2      : '%s' (length %d, max %d)\n", input->arg2, strlen(input->arg2), MAX_ARG2_LEN); 
  printf("   arg3      : '%s' (length %d, max %d)\n", input->arg3, strlen(input->arg3), MAX_ARG3_LEN); 
}
#endif

/////////////////////////////////////////////////////////////////////////////////////////

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

/////////////////////////////////////////////////////////////////////////////////////////

void parse_input_stdin(Input *input) {
  int c;
  int token_number = 0;
  int token_idx = 0;
  char *dst = input->command;

  memset((void *) input, 0, sizeof(Input));

  while (true) {
    c = fgetc(stdin);
    if (c == EOF) {
      input->eof = true;
      break;
    }
    if (c == '\n') { // Buffers are already filled with zeroes, no need to write '\0'.
      break;
    }
    if (input->error) {
      continue; // Throw away all input, wait for newline.
    }
    if (c == ' ') {
      token_number++;
      token_idx = 0;
      switch (token_number) {
        case 1: dst = input->arg1; break;
        case 2: dst = input->arg2; break;
        case 3: dst = input->arg3; break;
        default: input->error = true;
      }
      continue;
    }
    if (token_idx < max_token_lengths[token_number]) {
      dst[token_idx++] = token_number == 0 ? toupper(c) : c;
    } else {
      input->error = true;
    }
  }
  input->argc = token_number;
#ifdef DEBUG_INPUT
  print_input(input);
#endif
}

/////////////////////////////////////////////////////////////////////////////////////////

bool set_meta(Slot* slot, char new_meta[]) {
  unsigned char *c;
  for (c = (unsigned char *) new_meta; *c != '\0'; c++) {
    if (!isalnum(*c) && *c != '=' && *c != '-' && *c != ' ') {
      return false;
    }
  }
  strncpy(slot->meta, new_meta, META_SIZE); // Bug 1! \0 is not written if len(arg2) >= META_SIZE
  printf("OK");
  return true;
}

/////////////////////////////////////////////////////////////////////////////////////////

bool get_meta(const Slot slot) { // Note: slot is copied to the stack. We need this for exploitation!
  printf(slot.meta); // Bug 2!
  return true;
}

/////////////////////////////////////////////////////////////////////////////////////////

void rand_init(char seed[]) {
  br_hmac_drbg_init(&rng, &br_sha256_vtable, seed, strlen(seed));
}

/////////////////////////////////////////////////////////////////////////////////////////

void print_int_text(const char *name, const unsigned char *buf, size_t len) {
  size_t u;
  if (strlen(name) > 0) {
    printf("%s = ", name);
  }
  for (u = 0; u < len; u ++) {
    printf("%02X", buf[u]);
  }
#ifdef DEBUG
  printf(" (%d bytes = %d bits)", len, len*8);
  printf("\n");
#endif
}

/////////////////////////////////////////////////////////////////////////////////////////

#ifdef DEBUG
void print_private_key(br_rsa_private_key *sk) {
  printf("[DEBUG] RSA private key:\n");
  print_int_text("[DEBUG] p ", sk->p, sk->plen);
  print_int_text("[DEBUG] q ", sk->q, sk->qlen);
  print_int_text("[DEBUG] dp", sk->dp, sk->plen);
  print_int_text("[DEBUG] dq", sk->dq, sk->dqlen);
  print_int_text("[DEBUG] iq", sk->iq, sk->iqlen);
}
#endif

/////////////////////////////////////////////////////////////////////////////////////////

#ifdef DEBUG
void print_public_key(br_rsa_public_key *pk) {
  printf("[DEBUG] RSA public key:\n");
  print_int_text("[DEBUG] n ", pk->n, pk->nlen);
  print_int_text("[DEBUG] e ", pk->e, pk->elen);
}
#endif

/////////////////////////////////////////////////////////////////////////////////////////

#ifdef DEBUG
void rsa_test() {
  br_rsa_private_key sk;
  br_rsa_public_key pk;
  br_rsa_keygen kg;

  unsigned char kbuf_priv[BR_RSA_KBUF_PRIV_SIZE(RSA_KEY_SIZE_BITS)];
  unsigned char kbuf_pub[BR_RSA_KBUF_PUB_SIZE(RSA_KEY_SIZE_BITS)];
  printf("kbuf_priv: %d bytes, kbuf_pub: %d bytes\n", sizeof(kbuf_priv), sizeof(kbuf_pub));

  kg = br_rsa_keygen_get_default();
  if (!kg(&rng.vtable, &sk, kbuf_priv, &pk, kbuf_pub, RSA_KEY_SIZE_BITS, RSA_PUB_EXP)) {
    printf("ERROR: RSA key generation failed\n");
    return;
  }
  print_private_key(&sk);
  print_public_key(&pk);

  char tmp[128];
  char plain[128] = "Hello World!";
  br_rsa_oaep_encrypt menc = br_rsa_oaep_encrypt_get_default();

  int len = menc(&rng.vtable, &br_sha1_vtable, NULL, 0, &pk, tmp, sizeof(tmp), plain, strlen(plain) + 1);
  if (!len) {
    printf("ERROR: RSA encryption failed\n");
    return;
  }
  printf("RSA ciphertext size: %d bytes\n", len);
  print_int_text("ciphertext ", tmp, len);

  br_rsa_oaep_decrypt mdec = br_rsa_oaep_decrypt_get_default();
  if (mdec(&br_sha1_vtable, NULL, 0, &sk, tmp, &len) != 1) {
    printf("ERROR: RSA decryption failed\n");
    return;
  }
  print_int_text("plaintext ", (unsigned char *)tmp, len);
  printf("%s\n", tmp);

  char rand[16];
  rng.vtable->generate(&rng.vtable, rand, sizeof(rand));
  print_int_text("rand", rand, sizeof(rand));
  rng.vtable->generate(&rng.vtable, rand, sizeof(rand));
  print_int_text("rand", rand, sizeof(rand));
  rng.vtable->generate(&rng.vtable, rand, sizeof(rand));
  print_int_text("rand", rand, sizeof(rand));
}
#endif

/////////////////////////////////////////////////////////////////////////////////////////

void generate(Slot *slot)
{
  char buf[16];
  memset(buf, 0, sizeof(buf));
  snprintf(buf, sizeof(buf), "%d", free_slot_index);

  br_rsa_keygen kg = br_rsa_keygen_get_default();
  if (!kg(&rng.vtable, &(slot->sk), slot->privkey, &(slot->pk), slot->pubkey, RSA_KEY_SIZE_BITS, RSA_PUB_EXP)) {
    printf("ERROR");
    return;
  }
#ifdef DEBUG
  print_private_key(&slot->sk);
  print_public_key(&slot->pk);
#endif
  print_int_text(buf, slot->pubkey, sizeof(slot->pubkey));
}

/////////////////////////////////////////////////////////////////////////////////////////

void encrypt(char *pubkey_hex, char *plaintext) {
  unsigned char pubkey[PUBKEY_SIZE + 1];
  unsigned char buf[CIPHERTEXT_SIZE + 1];

  if (strlen(pubkey_hex) > PUBKEY_SIZE*2) {
    printf("ERROR: too long public key (hex): %d > %d.", strlen(pubkey_hex), PUBKEY_SIZE*2);
    return;
  }
  memset((void *) pubkey, 0, sizeof(pubkey));
  hextobin(pubkey, pubkey_hex, sizeof(pubkey));

  if (strlen(plaintext) > PLAINTEXT_SIZE) {
    printf("ERROR: too long plaintext: %d > %d.", strlen(plaintext), PLAINTEXT_SIZE);
    return;
  }
  memset((void *) buf, 0, sizeof(buf));
  //strncpy((char *) buf, plaintext, sizeof(buf));

  br_rsa_public_key pk;
  pk.n = pubkey;
  pk.nlen = 64;
  pk.e = pubkey + PUBKEY_SIZE - 1;  // Last byte of pubkey
  pk.elen = 1;
#ifdef DEBUG
  print_public_key(&pk);
#endif

  char gamma[16];
  rng.vtable->generate(&rng.vtable, gamma, sizeof(gamma));

  br_rsa_oaep_encrypt menc = br_rsa_oaep_encrypt_get_default();
  int len = menc(&rng.vtable, &br_sha1_vtable, NULL, 0, &pk, buf, sizeof(buf), gamma, sizeof(gamma));

  /* br_rsa_oaep_encrypt()
   *     rnd           source of random bytes.
   *     dig           hash function to use with MGF1.
   *     label         label value (may be `NULL` if `label_len` is zero).
   *     label_len     label length, in bytes.
   *     pk            RSA public key.
   *     dst           destination buffer.
   *     dst_max_len   destination buffer length (maximum encrypted data size).
   *     src           message to encrypt.
   *     src_len       source message length (in bytes).
   *     return  encrypted message length (in bytes), or 0 on error. 
   */

  if (!len) {
    printf("ERROR: cryptography failed.");
    return;
  }
  size_t i;
  for (i = 0; i <= strlen(plaintext); i++) {
    buf[len + i] = plaintext[i] ^ gamma[i % sizeof(gamma)];
  }
  // Total max length: len (RSA_CIPHERTEXT_SIZE) + PLAINTEXT_SIZE + 1 == CIPHERTEXT_SIZE + 1
  print_int_text("", (unsigned char *)buf, len + strlen(plaintext) + 1);
}

/////////////////////////////////////////////////////////////////////////////////////////

void decrypt(Slot *slot, char *ciphertext_hex) {
  char ciphertext[CIPHERTEXT_SIZE + 1];

  if (strlen(ciphertext_hex) > CIPHERTEXT_SIZE*2) {
    printf("ERROR: too long ciphertext (hex): %d > %d", strlen(ciphertext_hex), CIPHERTEXT_SIZE*2);
    return;
  }

  memset(ciphertext, 0, sizeof(ciphertext));
  hextobin((unsigned char *)ciphertext, ciphertext_hex, sizeof(ciphertext));

  br_rsa_oaep_decrypt mdec = br_rsa_oaep_decrypt_get_default();
  /* \see br_rsa_oaep_decrypt
   * \brief RSA decryption helper, for SSL/TLS.
   * \param dig         hash function to use with MGF1.
   * \param label       label value (may be `NULL` if `label_len` is zero).
   * \param label_len   label length, in bytes.
   * \param sk          RSA private key.
   * \param data        input/output buffer.
   * \param len         encrypted/decrypted message length.
   * \return  1 on success, 0 on error.                                        */

  size_t len = 64;
  if (mdec(&br_sha1_vtable, NULL, 0, &slot->sk, ciphertext, &len) != 1) {
    printf("ERROR: decryption failed");
    return;
  }
  int i;
  for (i = 0; i < PLAINTEXT_SIZE; i++) {
    ciphertext[64 + i] ^= ciphertext[i % 16];
  }
  memset(slot->buf, 0, sizeof(slot->buf));
  for (i = 0; i < PLAINTEXT_SIZE; i++) {
    slot->buf[i] = ciphertext[64 + i];
  }
  slot->buf[sizeof(slot->buf)-1] = 0;
  printf("OK");
}

/////////////////////////////////////////////////////////////////////////////////////////

bool handle_input(Input *input)
{
  if (IS_COMMAND(input, "HELP", 0)) {
    printf("  SETSLOT <N>\n");
    printf("  RANDINIT <SEED>\n");
    printf("  GENERATE\n");
    printf("  SETMETA <SLOT> <META>\n");
    printf("  GETMETA <SLOT>\n");
    printf("  DECRYPT <SLOT> <CIPHERTEXT_HEX>\n");
    printf("  GETPLAINTEXT <SLOT>");
    // printf("  ENCRYPT <PUBKEY_HEX> <PLAINTEXT>\n"); // Private API, probably no user will need.
    return true;
  }
  else if (IS_COMMAND(input, "SETSLOT", 1)) {
    int slot = atoi(input->arg1);
    if (!IS_VALID_SLOT(slot)) {
      return false;
    }
    free_slot_index = (slot + 1) % MAX_SLOTS;
    printf("OK: FREE SLOT: %d", free_slot_index);
    return true;
  }
  else if (IS_COMMAND(input, "GENERATE", 0)) {
    int slot = free_slot_index;

    memset((void *) &slots[slot], 0, sizeof(Slot));
    slots->idx = slot;
    generate(&slots[slot]);

    free_slot_index = (free_slot_index + 1) % MAX_SLOTS;
    return true;
  }
  else if (IS_COMMAND(input, "SETMETA", 2)) {
    int slot = atoi(input->arg1);
    if (!IS_VALID_SLOT(slot)) {
      return false;
    }
    return set_meta(&slots[slot], input->arg2);
  }
  else if (IS_COMMAND(input, "GETMETA", 1)) {
    int slot = atoi(input->arg1);
    if (!IS_VALID_SLOT(slot)) {
      return false;
    }
    return get_meta(slots[slot]);
  }
  else if (IS_COMMAND(input, "DECRYPT", 2)) {
    int slot = atoi(input->arg1);
    if (!IS_VALID_SLOT(slot)) {
      return false;
    }
    decrypt(&slots[slot], input->arg2);
    return true;
  }
  else if (IS_COMMAND(input, "GETPLAINTEXT", 1)) {
    int slot = atoi(input->arg1);
    if (!IS_VALID_SLOT(slot)) {
      return false;
    }
    printf("%s", slots[slot].buf);
    return true;
  }
  else if (IS_COMMAND(input, "ENCRYPT", 2)) {
    encrypt(input->arg1, input->arg2);
    return true;
  }
#ifdef DEBUG
  else if (IS_COMMAND(input, "RSA", 0)) {
    rsa_test();
    return true;
  }
#endif
  else if (IS_COMMAND(input, "RANDINIT", 1)) {
    rand_init(input->arg1);
    printf("OK");
    return true;
  }
  return false;
}

/////////////////////////////////////////////////////////////////////////////////////////

rtems_task Init(rtems_task_argument ignored) {
  Input input;
  bool command_result;
#ifdef DEBUG
  printf("ATTENTION! DEBUG BUILD!\n\n");
  printf("BR_RSA_KBUF_PUB_SIZE(RSA_KEY_SIZE_BITS) = %d\n", BR_RSA_KBUF_PUB_SIZE(RSA_KEY_SIZE_BITS));
  printf("BR_RSA_KBUF_PRIV_SIZE(RSA_KEY_SIZE_BITS) = %d\n", BR_RSA_KBUF_PRIV_SIZE(RSA_KEY_SIZE_BITS));
  printf("MAX_ARG1_LEN = %d\n", MAX_ARG1_LEN);
  printf("CIPHERTEXT_SIZE = %d\n", CIPHERTEXT_SIZE);
  printf("sizeof(Slot) = %d\n", sizeof(Slot));
  printf("Slot %4d = %p\n", 0, &slots[0]);
  printf("Slot %4d = %p\n", 1, &slots[1]);
  printf("Slot %4d = %p\n", 2, &slots[2]);
  printf("Slot %4d = %p\n", MAX_SLOTS-1, &slots[MAX_SLOTS-1]);
  printf("Input     = %p\n", &input);
#endif

  rand_init("DEFAULT SEED");

  while (true) {
    parse_input_stdin(&input);
    if (input.eof) {
      break;
    }
    else if (input.error) {
      printf("INPUT ERROR");
    }
    else {
      command_result = handle_input(&input);
      if (!command_result) {
        printf("PROTOCOL ERROR");
      }
    }
    printf("\n");
    fflush(stdout);
  }

  printf("\nBYE\n");
  rtems_task_delete(RTEMS_SELF);
}

/////////////////////////////////////////////////////////////////////////////////////////

/* NOTICE: the clock driver is explicitly disabled */
#define CONFIGURE_APPLICATION_DOES_NOT_NEED_CLOCK_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_CONSOLE_DRIVER
//#define CONFIGURE_APPLICATION_NEEDS_LIBBLOCK

#define CONFIGURE_MAXIMUM_TASKS            1
//#define CONFIGURE_USE_DEVFS_AS_BASE_FILESYSTEM

#define CONFIGURE_RTEMS_INIT_TASKS_TABLE
#define CONFIGURE_INIT_TASK_STACK_SIZE (1024 * 1024)   // Very important! Otherwise memory corruption will occur if we use more stack.
//#define CONFIGURE_EXECUTIVE_RAM_SIZE (64*1024*1024)
//#define CONFIGURE_MINIMUM_STACK_SIZE (2*1024*1024)
//#define CONFIGURE_MAXIMUM_PTYS 4
//#define CONFIGURE_EXTRA_TASK_STACKS 1024

#define CONFIGURE_INIT
#include <rtems/confdefs.h>
