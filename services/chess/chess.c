#include <stdlib.h>
#include <stdio.h>


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
                    return 1;
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
                if (start_x < end_y) {
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

    if (*start_y < 0 || *start_y > 7) {
        return 0;
    }
    if (*end_y < 0 || *end_y > 7) {
        return 0;
    }
    if (*start_x > 7 || *end_x > 7) {
        return 0;
    }

    return 1;
}




int make_move(char* board, int *is_white_turn, char *move) {
    int start_x, start_y, end_x, end_y;

    if (!parse_move(move, &start_x, &start_y, &end_x, &end_y)) {
        return 0;
    }

    // printf("%d %d %d %d\n", start_x, start_y, end_x, end_y);


    if (!is_move_valid(board, *is_white_turn, start_x, start_y, end_x, end_y)) {
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
            if (board[8*y + x] % 8 == 6 && (board[8*y + x] / 8) % 2 == !is_white_turn) {
                king_x = x;
                king_y = y;
            }
        }
    }

    if (king_x == -1 || king_y == -1) {
        return 0;
    }

    for (int y = 0; y < 8; y += 1) {
        for (int x = 0; x < 8; x += 1) {
            if (is_move_valid(board, *is_white_turn, x, y, king_x, king_y)) {
                printf("king on check %d %d\n", x, y);
                // revert move
                board[8*start_y + start_x] = start_figure;
                board[8*end_y + end_x] = end_figure;
                *is_white_turn ^= 1;
                return 0;
            }
        }
    }

    return 1;
}


// figures empty, pawn, rook, knight, bishop, queen, king
//         0 X    1 P   2 R   3 N     4 B     5 Q    6 K


int main() {
    char board[64] = {};
    int is_white_turn = 1;



    // ASK NAME
    init_board(board);
    print_board(board);


    int ok = make_move(board, &is_white_turn, "e2-e4");
    if (!ok) {
        printf("Bad move\n");
    }

    print_board(board);

    if (!make_move(board, &is_white_turn, "e7-e5")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "f2-f4")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "e5-f4")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "g2-g3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "f4-f3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "e1-f2")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "h7-h5")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "a2-a4")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "h8-h7")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "a1-a3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "h7-h6")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "a3-f3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "h6-f6")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "b2-b3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "f6-f3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "f2-f3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "a7-a6")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "d1-e1")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "f8-a3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "f1-h3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "d8-h4")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "b1-c3")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "b8-c6")) { printf("Bad move\n"); }
    print_board(board);
    if (!make_move(board, &is_white_turn, "g1-e2")) { printf("Bad move\n"); }
    print_board(board);

    return 0;

}