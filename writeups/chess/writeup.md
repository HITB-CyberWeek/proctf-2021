# Chess

## Description

The service allows playing chess. Users enter moves like e2-e4, the program
checks the rules and writes the board after the move. The service is written
in C language.


```
Enter your name: test
Enter your password: pass
Ok, let's play the game
   A B C D E F G H
8  R N B Q K B N R  8
7  P P P P P P P P  7
6  . . . . . . . .  6
5  . . . . . . . .  5
4  . . . . . . . .  4
3  . . . . . . . .  3
2  p p p p p p p p  2
1  r n b q k b n r  1
   A B C D E F G H

White turn. Enter your move (e.g. e2-e4):e2-e4
   A B C D E F G H
8  R N B Q K B N R  8
7  P P P P P P P P  7
6  . . . . . . . .  6
5  . . . . . . . .  5
4  . . . . p . . .  4
3  . . . . . . . .  3
2  p p p p . p p p  2
1  r n b q k b n r  1
   A B C D E F G H

Black turn. Enter your move (e.g. e2-e4):
```

## Flags

Before the game, the program asks for user and password and adds them in
append-only file flags.txt. If the user is new, it is registered, otherwise,
the user is allowed to enter the game if his password is valid.

## The vuln

The bug is in the move parsing code. The move is checked if it contains only
one '-' character and every move component is less than the board
dimensions.

The actual coordinates in memory are computed as Y\*8 + X, so if the big number
is passed, the coordinate is overflowed and can become negative. This allows
makeing moves outside of the board, in the stack memory.

The game logic is made in such a way that all unknown figures move like knights.
So we can move the bytes on the stack by these rules.

To create a piece with some value the input buffer can be used.
The value of stack bytes can be revealed by transporting them as the knights
on the chessboard - it is printed after every move.

# Exploitation

The service has several solutions, let's describe one of them.

To exploit the service, the attacker should restore the libc base address by
transporting corresponding bytes from the stack on the chessboard and looking
at their values. Of course, the leaking bytes should refer to some location
in libc.

Then the return address on a stack should be overwritten to the one-gadget
address in the libc, giving the attacker a shell. When transporting bytes as
knights some stack areas should be avoided, like cannaries, or values that are
changed.

The last step is to make the current function return. It can be done by finishing
the game on the board with a checkmate.

The full sploit can be found at [/sploits/chess/spl.py](../../sploits/chess/spl.py).
