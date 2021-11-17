#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

enum Command {
    COMMAND_NONE,
    COMMAND_ADD,COMMAND_SUB,COMMAND_MUL,COMMAND_DIV,COMMAND_REM,
    COMMAND_XOR,COMMAND_OR,COMMAND_AND,
    COMMAND_COPY,COMMAND_INPUT,COMMAND_OUTPUT,
    COMMAND_IFZERO,COMMAND_IFGT,COMMAND_IFLS,
    COMMAND_SKIP,COMMAND_SKIPREF
};

typedef struct _COMMAND {
    int type;
    bool is_reload;
    bool is_remove;
    union {
        struct {
            int k;
            int l;
        } arith;
        struct {
            int k;
        } copy;
        struct {
            int p;
            int j;
            int k;
        } if_cond;
        struct {
            int k;
        } skip;
    } args;
} COMMAND,*PCOMMAND;
bool Command2TWord (PCOMMAND cmd, unsigned int *word){
    unsigned int val=0;
    int ret = 1;
    if (cmd->is_reload){
        val = val | (0b1 << 23);
    }
    if (cmd->is_remove){
        val = val | (0b1 << 22);
    }
    val = val | (cmd->type << 18);
    // 24 бита одна команда
    if (cmd->type ==  COMMAND_ADD){
        // 2 bit - атрибут      
        // 4 bit - операция     
        // 8 bit - k            
        // 8 bit - l 
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_SUB){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_MUL){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_DIV){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_REM){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_XOR){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_OR){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
     else if (cmd->type ==  COMMAND_AND){
        int k=cmd->args.arith.k & 0b11111111;
        int l=cmd->args.arith.l & 0b11111111;
        val = val | (k << 10);
        val = val | (l << 2);
    }
    else if (cmd->type ==  COMMAND_COPY){
        // 2 bit - атрибут      
        // 4 bit - операция     
        // 16 bit - k           
        int k=cmd->args.copy.k & 0b1111111111111111;
        val = val | (k << 2);
    }
    else if (cmd->type ==  COMMAND_INPUT){
        int k=cmd->args.copy.k & 0b1111111111111111;
        val = val | (k << 2);
    }
    else if (cmd->type ==  COMMAND_OUTPUT){
        int k=cmd->args.copy.k & 0b1111111111111111;
        val = val | (k << 2);
    }
    else if (cmd->type ==  COMMAND_IFZERO){
        // 2 bit - атрибут
        // 4 bit - операция 
        //  4 bit - p           6
        //  4 bit - j           6
        //  4 bit - k           6
        int p = cmd->args.if_cond.p & 0b111111;
        int j = cmd->args.if_cond.j & 0b111111;
        int k = cmd->args.if_cond.k & 0b111111;
        val = val | (p << 12);
        val = val | (j << 6);
        val = val | (k << 0);
    }
    else if (cmd->type ==  COMMAND_IFGT){
        int p = cmd->args.if_cond.p & 0b111111;
        int j = cmd->args.if_cond.j & 0b111111;
        int k = cmd->args.if_cond.k & 0b111111;
        val = val | (p << 12);
        val = val | (j << 6);
        val = val | (k << 0);
    }
    else if (cmd->type ==  COMMAND_IFLS){
        int p = cmd->args.if_cond.p & 0b111111;
        int j = cmd->args.if_cond.j & 0b111111;
        int k = cmd->args.if_cond.k & 0b111111;
        val = val | (p << 12);
        val = val | (j << 6);
        val = val | (k << 0);
    }
    else if (cmd->type ==  COMMAND_SKIP){
        // 2 bit - атрибут
        // 4 bit - операция
        // 18 bit - на сколько прыгать
        int k = cmd->args.skip.k & 0b111111111111111111;
        val = val | (k << 0);
    }
    else if (cmd->type ==  COMMAND_SKIPREF){
        // 2 bit - атрибут
        // 4 bit - операция
        // 18 bit - номер ячейки
        int k = cmd->args.skip.k & 0b111111111111111111;
        val = val | (k << 0);
    }
    else{
        printf("Unknown command type\n");
        ret = 0;
    }
    *word = val;
    return ret;
}
int TWord2Command (PCOMMAND cmd, unsigned int val){
    cmd->type = (val >> 18) & 0b1111;
    unsigned int attrib = (val >> 22) & 0b11;
    if ((attrib & 0b10) !=0){
        cmd->is_reload = 1;
    }
    if ((attrib & 0b01) !=0){
        cmd->is_remove = 1;
    }
	int ret = 1;
    // 24 бита одна команда
    if (cmd->type ==  COMMAND_ADD){
        // 2 bit - атрибут      
        // 4 bit - операция     
        // 8 bit - k            
        // 8 bit - l
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_SUB){
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_MUL){
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_DIV){
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_REM){
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_XOR){
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_OR){
        cmd->args.arith.k = (val >> 10) & 0b11111111;
        cmd->args.arith.l = (val >> 2) & 0b11111111;
    }
    else if (cmd->type ==  COMMAND_COPY){
        cmd->args.copy.k = (val >> 2) & 0b1111111111111111;
		if ((cmd->args.copy.k & 0b1000000000000000) != 0) {
			cmd->args.copy.k = cmd->args.copy.k | 0b11111111111111110000000000000000;
		}
    }
    else if (cmd->type ==  COMMAND_INPUT){
        cmd->args.copy.k = (val >> 2) & 0b1111111111111111;
    }
    else if (cmd->type ==  COMMAND_OUTPUT){
        cmd->args.copy.k = (val >> 2) & 0b1111111111111111;
		if ((cmd->args.copy.k & 0b1000000000000000) != 0) {
			cmd->args.copy.k = cmd->args.copy.k | 0b11111111111111110000000000000000;
		}
    }
    else if (cmd->type ==  COMMAND_IFZERO){
        cmd->args.if_cond.p = (val >> 12) & 0b111111;
        cmd->args.if_cond.j = (val >> 6) & 0b111111;
        cmd->args.if_cond.k = (val >> 0) & 0b111111;
    }
    else if (cmd->type ==  COMMAND_IFGT){
        cmd->args.if_cond.p = (val >> 12) & 0b111111;
        cmd->args.if_cond.j = (val >> 6) & 0b111111;
        cmd->args.if_cond.k = (val >> 0) & 0b111111;
    }
    else if (cmd->type ==  COMMAND_IFLS){
        cmd->args.if_cond.p = (val >> 12) & 0b111111;
        cmd->args.if_cond.j = (val >> 6) & 0b111111;
        cmd->args.if_cond.k = (val >> 0) & 0b111111;
    }
    else if (cmd->type ==  COMMAND_SKIP){
        cmd->args.skip.k = val & 0b111111111111111111;
    }
    else if (cmd->type ==  COMMAND_SKIPREF){
        cmd->args.skip.k = val & 0b111111111111111111;
    }
    else{
		ret = 0;
    }
	return ret;
}
int Text2Command(char *text, PCOMMAND cmd){
    if (isdigit(text[0]) || text[0] == '-'){
        cmd->type = COMMAND_NONE;
        return 0;
    }
	memset(cmd, 0, sizeof(COMMAND));
    char * res = strtok(text," \t");
    if (res == NULL)
        return 0;
    if (!strcmp(res,"add")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_ADD;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"sub")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_SUB;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"mul")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_MUL;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);        
    }
    else if (!strcmp(res,"div")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_DIV;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"rem")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_REM;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"xor")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_XOR;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"or")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_OR;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"and")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        cmd->type = COMMAND_AND;
        cmd->args.arith.k = strtol(op1,0,10);
        cmd->args.arith.l = strtol(op2,0,10);
    }
    else if (!strcmp(res,"copy")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        cmd->type = COMMAND_COPY;
        cmd->args.copy.k = strtol(op1,0,10);
    }
    else if (!strcmp(res,"input")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        cmd->type = COMMAND_INPUT;
        cmd->args.copy.k = strtol(op1,0,10);
    }
    else if (!strcmp(res,"output")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        cmd->type = COMMAND_OUTPUT;
        cmd->args.copy.k = strtol(op1,0,10);        
    }
    else if (!strcmp(res,"ifzero")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        char * op3 = strtok(NULL," \t");
        if (op3 == NULL)
            return 0;
        cmd->type = COMMAND_IFZERO;
        cmd->args.if_cond.p = strtol(op1,0,10);
        cmd->args.if_cond.j = strtol(op2,0,10);
        cmd->args.if_cond.k = strtol(op3,0,10);
    }
    else if (!strcmp(res,"ifgt")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        char * op3 = strtok(NULL," \t");
        if (op3 == NULL)
            return 0;
        cmd->type = COMMAND_IFGT;
        cmd->args.if_cond.p = strtol(op1,0,10);
        cmd->args.if_cond.j = strtol(op2,0,10);
        cmd->args.if_cond.k = strtol(op3,0,10);
    }
    else if (!strcmp(res,"ifls")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        char * op2 = strtok(NULL," \t");
        if (op2 == NULL)
            return 0;
        char * op3 = strtok(NULL," \t");
        if (op3 == NULL)
            return 0;
        cmd->type = COMMAND_IFLS;
        cmd->args.if_cond.p = strtol(op1,0,10);
        cmd->args.if_cond.j = strtol(op2,0,10);
        cmd->args.if_cond.k = strtol(op3,0,10);
    }
    else if (!strcmp(res,"skip")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        cmd->type = COMMAND_SKIP;
        cmd->args.skip.k = strtol(op1,0,10);
    }
    else if (!strcmp(res,"skipref")){
        char * op1 = strtok(NULL," \t");
        if (op1 == NULL)
            return 0;
        cmd->type = COMMAND_SKIPREF;
        cmd->args.skip.k = strtol(op1,0,10);
    }
    else {
        printf("Unknown command\n");
        return 0;
    }
    char * is_reload = strtok(NULL," \t\n");
    if (is_reload == NULL)
        return 1;
    if (!strcmp(is_reload,"reload")){
        cmd->is_reload = 1;
    }
    if (!strcmp(is_reload,"remove")){
        cmd->is_remove = 1;
    }
    char * is_remove = strtok(NULL," \t\n");
    if (is_remove == NULL)
        return 1;
    if (!strcmp(is_remove,"reload")){
        cmd->is_reload = 1;
    }
    if (!strcmp(is_remove,"remove")){
        cmd->is_remove = 1;
    }
    return 1;
}
int Command2Text(char *text, PCOMMAND cmd){
    /*
     COMMAND_ADD,COMMAND_SUB,COMMAND_MUL,COMMAND_DIV,COMMAND_REM
    COMMAND_XOR,COMMAND_OR,COMMAND_AND,
    COMMAND_COPY,COMMAND_INPUT,COMMAND_OUTPUT,
    COMMAND_IFZERO,COMMAND_IFGT,COMMAND_IFLS,
    COMMAND_SKIP,COMMAND_SKIPREF
     */
    if (cmd->type == COMMAND_ADD){
        sprintf(text,"add %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_SUB){
        sprintf(text,"sub %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_MUL){
        sprintf(text,"mul %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_DIV){
        sprintf(text,"div %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_REM){
        sprintf(text,"rem %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_XOR){
        sprintf(text,"xor %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_OR){
        sprintf(text,"or %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_AND){
        sprintf(text,"and %d %d",cmd->args.arith.k,cmd->args.arith.l);
    }
    else if (cmd->type == COMMAND_COPY){
        sprintf(text,"copy %d",cmd->args.copy.k);
    }
    else if (cmd->type == COMMAND_INPUT){
        sprintf(text,"input %d",cmd->args.copy.k);
    }
    else if (cmd->type == COMMAND_OUTPUT){
        sprintf(text,"output %d",cmd->args.copy.k);
    }
    else if (cmd->type == COMMAND_IFZERO){
        sprintf(text,"ifzero %d %d %d",cmd->args.if_cond.p,cmd->args.if_cond.j,cmd->args.if_cond.k);
    }
    else if (cmd->type == COMMAND_IFGT){
        sprintf(text,"ifgt %d %d %d",cmd->args.if_cond.p,cmd->args.if_cond.j,cmd->args.if_cond.k);
    }
    else if (cmd->type == COMMAND_IFLS){
        sprintf(text,"ifls %d %d %d",cmd->args.if_cond.p,cmd->args.if_cond.j,cmd->args.if_cond.k);
    }
    else if (cmd->type == COMMAND_SKIP){
        sprintf(text,"skip %d",cmd->args.skip.k);
    }
    else if (cmd->type == COMMAND_SKIPREF){
        sprintf(text,"skipref %d",cmd->args.skip.k);
    }
    else {
        printf("Unknown opcode");
        return 0;
    }
    if (cmd->is_reload){
        strcat(text," reload");
    }
    if (cmd->is_remove){
        strcat(text," remove");
    }
    return 1;
}
typedef struct _CELL {
    int cell_value;
    COMMAND cmd;
} CELL,*PCELL;
typedef struct _MEM {
    PCELL cells;
    int size;
} MEMORY,*PMEMORY;
char * INPUT="";
int input_pos = 0;
int input_size = 0;
int GetInput(){
	char c = INPUT[input_pos];
	if (input_pos < input_size) {
		input_pos += 1;
	}
    return c;
}
void PutOutput(int val){
	printf("%c", val);
    return ;
}
bool ExecuteCommand(PMEMORY memory, int * position){
    unsigned int pos = *position;
    pos = pos % memory->size;
    PCOMMAND cmd = &(memory->cells[pos].cmd);
    int result = memory->cells[pos].cell_value;
    bool is_renew = 1;
	int is_finish = 0;
    if (cmd->type == COMMAND_ADD){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
        result = (memory->cells[cell1_num].cell_value +
                    memory->cells[cell2_num].cell_value) & 0xFFFFFF;
    }
    else if (cmd->type == COMMAND_SUB){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = (memory->cells[cell1_num].cell_value -
			memory->cells[cell2_num].cell_value) & 0xFFFFFF;
    }
    else if (cmd->type == COMMAND_MUL){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = (memory->cells[cell1_num].cell_value *
			memory->cells[cell2_num].cell_value) & 0xFFFFFF;
    }
    else if (cmd->type == COMMAND_DIV){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = (memory->cells[cell1_num].cell_value /
			memory->cells[cell2_num].cell_value) & 0xFFFFFF;
    }
    else if (cmd->type == COMMAND_REM){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = (memory->cells[cell1_num].cell_value %
			memory->cells[cell2_num].cell_value) & 0xFFFFFF;
    }
    else if (cmd->type == COMMAND_XOR){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = memory->cells[cell1_num].cell_value ^
			memory->cells[cell2_num].cell_value;
    }
    else if (cmd->type == COMMAND_OR){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = memory->cells[cell1_num].cell_value |
			memory->cells[cell2_num].cell_value;
    }
    else if (cmd->type == COMMAND_AND){
		unsigned int cell1_num = (pos + cmd->args.arith.k) % memory->size;	// или тут
		unsigned int cell2_num = (pos + cmd->args.arith.l) % memory->size;	// или тут
		result = memory->cells[cell1_num].cell_value &
			memory->cells[cell2_num].cell_value;
    }
    else if (cmd->type == COMMAND_COPY){
        cmd->args.copy.k = cmd->args.copy.k % memory->size;
        result = memory->cells[cmd->args.copy.k].cell_value; // можно оставить тут багу, типа случайно не тот юнион оставили
    }
    else if (cmd->type == COMMAND_INPUT){
		unsigned int cell_num = (pos + cmd->args.copy.k) % memory->size;	// или тут
        memory->cells[cell_num].cell_value = GetInput();
        memset(&(memory->cells[cell_num].cmd),0,sizeof(COMMAND));
        TWord2Command(&(memory->cells[cell_num].cmd),memory->cells[cell_num].cell_value);
        is_renew = 0;
    }
    else if (cmd->type == COMMAND_OUTPUT){
		unsigned int cell_num = (pos + cmd->args.copy.k) % memory->size;
        PutOutput(memory->cells[cell_num].cell_value);
        is_renew = 0;
    }
    else if (cmd->type == COMMAND_IFZERO){
        cmd->args.if_cond.p = cmd->args.if_cond.p % memory->size;
        cmd->args.if_cond.j = cmd->args.if_cond.p % memory->size;
        cmd->args.if_cond.k = cmd->args.if_cond.p % memory->size;
        if (memory->cells[cmd->args.if_cond.p].cell_value == 0){
            result = memory->cells[cmd->args.if_cond.j].cell_value;
        }
        else{
            result = memory->cells[cmd->args.if_cond.k].cell_value;
        }
    }
    else if (cmd->type == COMMAND_IFGT){
        cmd->args.if_cond.p = cmd->args.if_cond.p % memory->size;
        cmd->args.if_cond.j = cmd->args.if_cond.p % memory->size;
        cmd->args.if_cond.k = cmd->args.if_cond.p % memory->size;
        if (memory->cells[cmd->args.if_cond.p].cell_value > 0){
            result = memory->cells[cmd->args.if_cond.j].cell_value;
        }
        else{
            result = memory->cells[cmd->args.if_cond.k].cell_value;
        }
    }
    else if (cmd->type == COMMAND_IFLS){
        cmd->args.if_cond.p = cmd->args.if_cond.p % memory->size;
        cmd->args.if_cond.j = cmd->args.if_cond.p % memory->size;
        cmd->args.if_cond.k = cmd->args.if_cond.p % memory->size;
        if (memory->cells[cmd->args.if_cond.p].cell_value < 0){
            result = memory->cells[cmd->args.if_cond.j].cell_value;
        }
        else{
            result = memory->cells[cmd->args.if_cond.k].cell_value;
        }
    }
    else if (cmd->type == COMMAND_SKIP){
        unsigned int newpos= *position;
        newpos = (newpos + cmd->args.skip.k) % memory->size;
        if (newpos < *position && cmd->is_remove){
            newpos+=1;
        }
        *position = newpos;
        is_renew = 0;
		if (cmd->args.skip.k == 0) {
			is_finish = 1;
		}
    }
    else if (cmd->type == COMMAND_SKIPREF){
        unsigned int newpos= *position;
        newpos = (newpos + memory->cells[cmd->args.skip.k].cell_value) % memory->size;
        *position = newpos;
        is_renew = 0;
    }
    else {
        printf("Unknown opcode\n");
        return 2;
    }
	if (cmd->type != COMMAND_SKIP && cmd->type != COMMAND_SKIPREF) {
		*position = pos + 1;
	}
	bool is_reload = cmd->is_reload;
    if (cmd->is_remove){
        PCELL new_mem = (PCELL)malloc(sizeof(CELL) * (memory->size-1));
        memcpy(new_mem,memory->cells,pos * sizeof(CELL));
        memcpy(&(new_mem[pos]),&(memory->cells[pos+1]),(memory->size-pos-1) * sizeof(CELL));
        free(memory->cells);
        memory->cells = new_mem;
		memory->size -= 1;
		*position = *position - 1;
    }
	if (is_renew) {
		memory->cells[pos].cell_value = result;
		memset(&(memory->cells[pos].cmd), 0, sizeof(COMMAND));
		TWord2Command(&(memory->cells[pos].cmd), result);
	}
    if (is_reload){
        *position = 0;
    }
	return is_finish;
}
PMEMORY CreateMemory(int size){
    PMEMORY mem = (PMEMORY) malloc(sizeof(MEMORY));
    mem->size = size;
    mem->cells = (PCELL) malloc(sizeof(CELL) * size);
    for (int i=0; i<size; i++){
        mem->cells[i].cmd.type = COMMAND_SKIP;
        mem->cells[i].cmd.args.skip.k = 1;
    }
    return mem;
}
bool Test1(){
    COMMAND cmd;
    char text []= "add 1 2";
    char buf[32];
    Text2Command(text,&cmd);
    Command2Text(buf,&cmd);
    printf(buf);
    if (!strcmp(buf, text)){
        return 1;
    }
    return 0;
}
void Test2(){
    PMEMORY mem = CreateMemory(20);
    char buf1[32];
    char buf2[32];
    FILE * f = fopen("1.obf","r");
    for (int i=0; i<8; i++){
        fgets(buf1,32,f);
        Text2Command(buf1,&(mem->cells[i].cmd));
        Command2Text(buf2,&(mem->cells[i].cmd));
        printf("%s\n",buf2);
    }
}
int Compile(char * in_fname, char * out_filename){
    char buf1[128];
    FILE * fin = fopen(in_fname,"r");
    if (!fin){
        printf("no such file %s\n",in_fname);
        return 1;
    }
    FILE * fout = fopen(out_filename,"wb+");
    if (!fout){
        printf("no such file %s\n",in_fname);
        return 1;
    }
    COMMAND cmd;
    int status;
    while(!feof(fin)){
        char * res = fgets(buf1,128,fin);
        int val;
        if (isdigit(buf1[0]) || buf1[0] == '-'){
            val = strtol(buf1,0,10);
			printf("%d\n", val);
        }
        else {
            status = Text2Command(buf1,&cmd);
            if (status ==0)
                return 1;
            status = Command2TWord(&cmd, (unsigned int *)&val);
            if (status == 0)
                return 2;
			Command2Text(buf1, &cmd);
			printf("%s\n",buf1);
        }
        fwrite(&val,3,1,fout);
    }
    fclose(fout);
    fclose(fin);
    return 0;
}
void PrintCell(PMEMORY memory, int position) {
	char buf_deb[128];
	if (memory->cells[position].cmd.type != COMMAND_NONE) {
		int res = Command2Text(buf_deb, &(memory->cells[position].cmd));
		if (res == 1) {
			printf("%3d) %s\n", position, buf_deb);
		}
		else {
			printf("%3d) %d\n", position, memory->cells[position].cell_value);
		}
	}
	else {
		printf("%3d) %d\n", position, memory->cells[position].cell_value);
	}
}
int Execute(char * filename, int max_steps,int is_debug) {
	FILE * fin = fopen(filename, "rb");
 	if (!fin) {
		printf("no such file %s\n", filename);
		return 1;
	}
	fseek(fin, 0, SEEK_END);
	int size = ftell(fin);
	fseek(fin, 0, SEEK_SET);
	int memory_size = size / 3;

	PMEMORY memory = CreateMemory(memory_size);
	int val=0;
	COMMAND cmd;
	for (int i = 0; i < memory_size; i++) {
		int n = fread(&val, 1, 3, fin);
		if (n != 3) {
			break;
		}
		memset(&cmd, 0, sizeof(COMMAND));
		memory->cells[i].cell_value = val;
		if (TWord2Command(&cmd, val)) {
			memcpy(&(memory->cells[i].cmd), &cmd, sizeof(COMMAND));
		}
		else {
			memory->cells[i].cmd.type = COMMAND_NONE;
		}
	}
	int position = 0;
	int is_finish = 0;
	while (is_finish == 0) {
		if (is_debug==1) {
			printf("---\n");
			PrintCell(memory, position);
		}
		else if (is_debug == 2) {
			printf("---\n");
			for (int k = 0; k < 10; k++) {
				if (position + k < memory->size)
					PrintCell(memory, position+k);
			}
		}
		else if (is_debug == 3) {
			printf("---\n");
			for (int k = 0; k < memory->size; k++) {
				if (k == position)
					printf(">");
				printf(" %06x ", memory->cells[k].cell_value);
				PrintCell(memory, k);
			}
		}
		is_finish = ExecuteCommand(memory, &position);
		max_steps--;
		if (max_steps == 0)
			break;
	}
	return 0;
}
int Decompile(char * in_fname, char * out_filename){
    char buf1[128];
    FILE * fin = fopen(in_fname,"r");
    if (!fin){
        printf("no such file %s\n",in_fname);
        return 1;
    }
    FILE * fout = fopen(out_filename,"wb+");
    if (!fout){
        printf("no such file %s\n",in_fname);
        return 1;
    }
    COMMAND cmd;
    int status;
}
int main (int argc, char * argv[]){
    int operation = 0;
    if (argc >= 2){
        if (!strcmp(argv[1],"compile")){
            // Превратить текст в байт-код
            if (argc >= 4){
                if (Compile(argv[2],argv[3]) !=0){
                    return 1;
                }
            }
            else{
                printf("No filenames\n");
            }
        }
        else if (!strcmp(argv[1],"decompile")){
            // Превратить байт-код в текстoperation
        }
        else if (!strcmp(argv[1],"execute")){
            // Исполнить байт-код, input берется как числа из stdin
            // output выводится на экран.
			int debug = 2;
			if (argc >= 3) {
				int max_steps = 50000;
				if (argc >= 4) {
					INPUT = argv[3];
					input_size = strlen(INPUT);
					if (argc >= 5) {
						debug = strtol(argv[4], 0, 10);
						if (argc >= 6) {
							max_steps = strtol(argv[5], 0, 10);
							if (max_steps < 10) {
								max_steps = 50000;
							}

						}
					}
				}
				if (Execute(argv[2],max_steps,debug) != 0) {
					return 1;
				}
			}
			else {
				printf("No filename\n");
			}
        }
    }
    return 0;
}
