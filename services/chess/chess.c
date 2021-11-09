#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>

#include <sys/stat.h>


void print_board(char* board) {
    char mapping[16] = ".prnbqkX.PRNBQKX";

    printf("   A B C D E F G H\n");
    for (int y = 7; y >= 0; y -= 1) {
        printf("%d  ", y+1);

        for (int x = 0; x < 8; x += 1) {
            printf("%c ", mapping[board[y*8 + x] % 16]);
        }
        printf(" %d\n", y+1);
    }
    printf("   A B C D E F G H\n\n");

}

void init_board(char* board) {
    for (int x = 0; x < 64; x += 1) {
        board[x] = 0;
    }

    for (int x = 0; x < 8; x += 1) {
        board[1*8 + x] = 1;
        board[6*8 + x] = 1 + 8;
    }

    board[0*8 + 0] = 2;
    board[0*8 + 1] = 3;
    board[0*8 + 2] = 4;
    board[0*8 + 3] = 5;
    board[0*8 + 4] = 6;
    board[0*8 + 5] = 4;
    board[0*8 + 6] = 3;
    board[0*8 + 7] = 2;

    board[7*8 + 0] = 2 + 8;
    board[7*8 + 1] = 3 + 8;
    board[7*8 + 2] = 4 + 8;
    board[7*8 + 3] = 5 + 8;
    board[7*8 + 4] = 6 + 8;
    board[7*8 + 5] = 4 + 8;
    board[7*8 + 6] = 3 + 8;
    board[7*8 + 7] = 2 + 8;

}

int is_move_valid(char* board, int is_white_turn, int start_x, int start_y, int end_x, int end_y) {
    char start_figure = board[8*start_y + start_x];
    char start_fig_color = (start_figure / 8) % 2;
    char start_fig_type = start_figure % 8;

    if  (start_fig_color == is_white_turn) {
        // wrong turn
        return 0;
    }

    char end_figure = board[8*end_y + end_x];
    char end_fig_color = (end_figure / 8) % 2;
    char end_fig_type = end_figure % 8;

    int is_usual_move = (end_fig_type == 0);

    if (!is_usual_move && start_fig_color == end_fig_color) {
        // don't allow to attack own pieces
        return 0;
    }

    int dx, dy;

    switch(start_fig_type) {
        case 0:
            // EMPTY SPACE
            return 0;
        case 1:
            // PAWN
            if (is_usual_move) {
                if (start_x != end_x) {
                    return 0;
                }
                if (is_white_turn) {
                    if (end_y - start_y == 1) {
                        return 1;
                    }
                    if (end_y - start_y == 2 && start_y == 1 && board[(start_y+1)*8+start_x] % 8 == 0) {
                        return 1;
                    }
                } else {
                    if (start_y - end_y == 1) {
                        return 1;
                    }
                    if (start_y - end_y == 2 && start_y == 6 && board[(start_y-1)*8+start_x] % 8 == 0) {
                        return 1;
                    }
                }
            } else {
                if (is_white_turn) {
                    if (end_y - start_y == 1) {
                        if (abs(end_x - start_x) == 1) {
                            return 1;
                        }
                    }
                } else {
                    if (start_y - end_y == 1) {
                        if (abs(end_x - start_x) == 1) {
                            return 1;
                        }
                    }
                }
            }
            return 0;
        case 5:
            // QUEEN
        case 2:
            // ROOK
            // dx = end_x - start_x > 0 ? 1: -1;
            // dy = end_y - start_y > 0 ? 1: -1;

            if(end_x == start_x) {
                int all_ok = 1;
                if (start_y < end_y) {
                    for (int y = start_y+1; y < end_y; y += 1) {
                        if (board[8*y + start_x] % 8 != 0) {
                            all_ok = 0;
                            break;
                        }
                    }
                } else {
                    for (int y = start_y-1; y > end_y; y -= 1) {
                        if (board[8*y + start_x] % 8 != 0) {
                            all_ok = 0;
                            break;
                        }
                    }
                }
                if (all_ok) {
                    return 1;
                }
            }
            if(end_y == start_y) {
                int all_ok = 1;
                if (start_x < end_x) {
                    for (int x = start_x+1; x < end_x; x += 1) {
                        if (board[8*start_y + x] % 8 != 0) {
                            all_ok = 0;
                            break;
                        }
                    }
                } else {
                    for (int x = start_x-1; x > end_x; x -= 1) {
                        if (board[8*start_y + x] % 8 != 0) {
                            all_ok = 0;
                            break;
                        }
                    }
                }
                if (all_ok) {
                    return 1;
                }
            }

            if (start_fig_type == 2) {
                // ROOK
                return 0;
            }
            [[fallthrough]];
        case 4:
            // bishop
            if (abs(end_x - start_x) != abs(end_y - start_y)) {
                return 0;
            }


            if (start_x < end_x && start_y < end_y) {
                for (int x = start_x + 1, y = start_y + 1; x < end_x && y < end_y; x += 1, y += 1) {
                    if (board[8*y + x] % 8 != 0) {
                        return 0;
                    }
                }
            } else if (start_x < end_x && start_y > end_y) {
                for (int x = start_x + 1, y = start_y - 1; x < end_x && y > end_y; x += 1, y -= 1) {
                    if (board[8*y + x] % 8 != 0) {
                        return 0;
                    }
                }
            } else if (start_x > end_x && start_y > end_y) {
                for (int x = start_x - 1, y = start_y - 1; x > end_x && y > end_y; x -= 1, y -= 1) {
                    if (board[8*y + x] % 8 != 0) {
                        return 0;
                    }
                }
            } else if (start_x > end_x && start_y < end_y) {
                for (int x = start_x - 1, y = start_y + 1; x > end_x && y < end_y; x -= 1, y += 1) {
                    if (board[8*y + x] % 8 != 0) {
                        return 0;
                    }
                }
            }

            return 1;
        case 3:
            // KNIGHT
            if (abs(end_x - start_x) == 1) {
                if (abs(end_y - start_y) == 2) {
                    return 1;
                }
            }
            if (abs(end_x - start_x) == 2) {
                if (abs(end_y - start_y) == 1) {
                    return 1;
                }
            }
            return 0;

        case 6:
            // KING
            return (abs(end_y - start_y) <= 1) && (abs(end_x - start_x) <= 1);
    }

    //
    return 0;

}

int parse_move(char *move, int *start_x, int *start_y, int *end_x, int *end_y) {
    char start_x_letter, end_x_letter;

    int minus_signs = 0;

    for (int i = 0; move[i]; i+=1) {
        if (move[i] == '-') {
            minus_signs += 1;
        }
    }

    if (minus_signs != 1) {
        return 0;
    }

    int result = sscanf(move, "%c%u-%c%u", &start_x_letter, start_y, &end_x_letter, end_y);
    *start_y -= 1;
    *end_y -= 1;

    if (result != 4) {
        return 0;
    }

    *start_x = start_x_letter - 'a';
    *end_x = end_x_letter - 'a';

    if (*start_x > 7 || *end_x > 7) {
        return 0;
    }
    if (*start_y > 7 || *end_y > 7) {
        return 0;
    }

    return 1;
}




int make_raw_move(char* board, int *is_white_turn, int start_x, int start_y, int end_x, int end_y, int pretend) {
    // printf("%d %d %d %d\n", start_x, start_y, end_x, end_y);

    if (!is_move_valid(board, *is_white_turn, start_x, start_y, end_x, end_y)) {
        // printf("BAD %d %d %d %d\n", start_x, start_y, end_x, end_y);
        return 0;
    }

    // make move
    char start_figure = board[8*start_y + start_x];
    char end_figure = board[8*end_y + end_x];

    board[8*start_y + start_x] = 0;
    board[8*end_y + end_x] = start_figure;

    *is_white_turn ^= 1;

    int king_x = -1;
    int king_y = -1;

    // check for check
    for (int y = 0; y < 8; y += 1) {
        for (int x = 0; x < 8; x += 1) {
            if (board[8*y + x] % 8 == 6 && ((board[8*y + x] / 8) % 2 == (*is_white_turn))) {
                king_x = x;
                king_y = y;
            }
        }
    }

    // printf("king_x %d king_y %d is_white_turn %d\n", king_x, king_y, *is_white_turn);

    if (king_x == -1 || king_y == -1) {
        return 0;
    }

    for (int y = 0; y < 8; y += 1) {
        for (int x = 0; x < 8; x += 1) {
            if (is_move_valid(board, *is_white_turn, x, y, king_x, king_y)) {
                // printf("king on check %d %d\n", x, y);
                // revert move
                board[8*start_y + start_x] = start_figure;
                board[8*end_y + end_x] = end_figure;
                *is_white_turn ^= 1;
                return 0;
            }
        }
    }

    char figure;
    if (pretend) {
        // rollback
        board[8*start_y + start_x] = start_figure;
        board[8*end_y + end_x] = end_figure;
        *is_white_turn ^= 1;
    } else {
        for (int x = 0; x < 8; x += 1) {
            // promote
            if (board[8*0 + x] % 8 == 1) {
                board[8*0 + x] = 13;
            }
            if (board[8*7 + x] % 8 == 1) {
                board[8*7 + x] = 5;
            }
        }
    }

    return 1;
}

int make_move(char* board, int *is_white_turn, char *move, int pretend) {
    int start_x, start_y, end_x, end_y;

    if (!parse_move(move, &start_x, &start_y, &end_x, &end_y)) {
        return 0;
    }

    return make_raw_move(board, is_white_turn, start_x, start_y, end_x, end_y, pretend);
}

int is_checkmate(char *board, int is_white_turn) {
    for (int start_y = 0; start_y < 8; start_y += 1) {
        for (int start_x = 0; start_x < 8; start_x += 1) {
            if ((board[8*start_y + start_x] / 8) % 2 == (is_white_turn)) {
                continue;
            }

            // printf("start_x %d start_y %d\n", start_x, start_y);

            for (int end_x = 0; end_x < 8; end_x += 1) {
                for (int end_y = 0; end_y < 8; end_y += 1) {
                    // printf("end_x %d end_y %d\n", end_x, end_y);
                    if (make_raw_move(board, &is_white_turn, start_x, start_y, end_x, end_y, 1)) {
                        // printf("good %d %d %d %d!\n", start_x, start_y, end_x, end_y);
                        return 0;
                    }
                }
            }
        }
    }
    return 1;
}


int try_to_login(char* name, char *pass) {
    FILE* file = fopen("data/flags.txt", "a+");
    if (file == NULL) {
        fprintf(stderr, "failed to open data/flags.txt\n");
        return 0;
    }

    char name_buf[64] = {0};
    char pass_buf[64] = {0};

    while (fscanf(file, "%63s %63s\n", name_buf, pass_buf) == 2) {
        if (!strcmp(name, name_buf)) {
            return strcmp(pass, pass_buf) == 0;
        }
    }

    return fprintf(file, "%s %s\n", name, pass) >= 0;
}

// figures empty, pawn, rook, knight, bishop, queen, king
//         0 X    1 P   2 R   3 N     4 B     5 Q    6 K


int main() {
    umask(0077);
    alarm(60);

    // ASK NAME
    char name_buf[64] = {0};
    char pass_buf[64] = {0};
    char move_buf[64] = {0};

    char board[64] = {};
    int is_white_turn = 1;

    printf("Enter your name: ");
    if (scanf("%63s", name_buf) != 1) {
        return 1;
    }

    printf("Enter your password: ");
    if (scanf("%63s", pass_buf) != 1) {
        return 1;
    }

    if(!try_to_login(name_buf, pass_buf)) {
        printf("Bad auth\n");
        return 1;
    }

    printf("Ok, let's play the game\n");
    init_board(board);

    for(;;) {
        print_board(board);
        printf("%s turn. Enter your move (e.g. e2-e4):", is_white_turn ? "White": "Black");

        if (scanf("%63s", move_buf) != 1) {
            exit(1);
        }

        if (!make_move(board, &is_white_turn, move_buf, 0)) {
            printf("Bad move\n");
            continue;
        }

        if (is_checkmate(board, is_white_turn)) {
            printf("Checkmate! %s wins\n", is_white_turn ? "Black": "White");
            return 0;
        }

    }

     // __asm__("int3");

    return 0;

}