
## Description

Service consists of site (frontend) and binary file (virtual machine on C).
Logic of site looks like next:
1. User registers on site and log in 
2. User goes to form and points password and secret message
3. Site generates a program for virtual machine (CellsVM) and allows user to 
verify that password fits for this programand returns the secret message.
4. User may logout and try to find another users in search form. He must enter
almost 1 symbol to search
5. When he found some user he can download his program, run it and verify 
password to get secret.

## Virtual Machine

CellsVM was specialy developed and implemented for contest.
Cell is a 3 byte memory region. It contains 24-bit number which may be interpreted
as number or as command.
Memory is a sequence of cells. Each program has its own memory size.
Program for CellsVM is a sequence of 3-byte numbers in little endian.

Each command in VM stores its result in he same cell where it is located so that
it overwrites itself. Cell addresses in commands are relative from the current position.
If address exceeds memory size then machine takes address % memorysize. Let pc be a current
number of memory cell.

VM supports next commands:
1. ADD k l  
SUB k l  
MUL k l  
DIV k l  
REM k l  
XOR k l  
OR k l  
AND k l    
Executes arithmetic operation with numbers on pc+k and pc+l cells and sores result in pc cell.
2. COPY k  
copies value into cells[pc+k] to current cell

INPUT k
takes number from queue of input numbers and put in to pc+k cell

OUTPUT k
puts number from cells[pc+k]  to output queue

3. IFZERO p j k  
IFGT p j k  
IFLS p j k  

Verifies that value in pc+p cell equal/greater/less zero and if it is true copies value from
pc+j cell else copies value from pc+k cell.

4. SKIP k  
Increments pc on k cells.

   SKIPREF k  
Increments pc on cells[k] cells  
  Special case - if skip 0 then finish program

Also commands supports next attributes  
* remove - removes current cell from memory. All tailed cells shifts by one, their addresses decremets to 1  
* reload - assigns pc to 0

cells.cpp file contains implementation of virtual machine. It supports compiling and execution.
Execution may restrict number of commands executed (by default it executes less than 50000 commands). Also
it supports tracing modes (in participant's vms this part was cut for the sake of complication).

So in this VM you may write some command, which modifies current command and changes it to another.
Also cell addresses changes on remove attributes. Password comes from input queue and flag goes to output queue.

## Program packing
    
Program for this machine is intended to decrypt flag using password. It worsk by next algorithm
1. At python-site compute xor of 4-byte pieces of flag, at end of flag place ',' and hex of this csum.
    So now flag has checksum to verify that it was properly decrypted
2. User enters 8-symbol password, it stores to some memory in program
3. Program generates 32+1+8 numbers (key_flow) using some binary operation (ADD,XOR,MUL)
4. Decrypt Flag with csum and output
5. At python-side split flag by ',' and veryfy csum. If it is valid then flag is valid

Also some self-modifying instructions was inserted. So encoded flag was not fully accessible from static analysis.
    
## Hacking

There was no intended bugs on site, all values were filtered.
Intended way of solution is next
1. Inter any random symbol on search field. Download all user's cell-programs
2. Run cell-program in virtual machine. Build execution trace of 
    Participants must reverse their cells.elf file to find, how to build execution trace of 
    cell-program. As I have tracing mode, so I use it to get sequence of commands which 
    receives key_flow from password. Also extrace bytes of encoded_flag. It lies right after our password
    in memory of program and continues till end of program
3. We will use z3py to compute password.  
3.1 Make symbols with each byte of password (p0,p1,..,p7)  
3.2 Take formulas which computes key_flow from password and create new symbols with appropriate operations 
    between password symbols (p0 ^ p1 and so on)  
3.3 Create symbols for decoded_flag by xoring key_flow symbols with bytes of encoded_flag (encoded_flag[i] ^ key_flow and so on)  
3.4 Add next rules to solver:  
                  * Each symbol of password is alphanumeric  
                  * Each symbol of decrypted_flag is alphanumeric  
3.5 Solve this and print result  

After 3 step we extracts flag and we can verify that it is right. Using csum to add more conditions we can decrease time 
of modeling.
    
## Protection

It is impossible to protect any program perfectly because reverser always able to build trace and reverse your program 
manually. So we must prevent automatic flag extraction. To do this we may create more complex formulas for key_flow. 
For example:
1. Compute key_flow using formulas with binary operations. 
2. Add N bytes into key_flow so that i byte depends on some pair of i-1 bytes. Let's call it key_flow2
3. Take 32+1+8 bytes of key_flow2 and decode flag.

By this way we can make dependencies more complex and inrease tim of modeling in z3.

Also it was supposed that participants may try to implement their own encryption algorithms, for example RC4. 

## Checker

Checker verifies that service is able to build program for CellsVM and may return correct flag on password.
Checker verifies that service returns newly added user and his program, it downloads program and verifies that 
password fits for it.
    
## Files
    
* exploit.py - exploit for service which uses z3
* cells.cpp,cells.elf - source code and binary of virtual machine
    




