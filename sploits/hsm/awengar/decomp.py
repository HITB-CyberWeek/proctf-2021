import re
scmds = """40006f2c <get_meta>:
40006f2c:	37 9c ff fc 	addi sp,sp,-4
40006f30:	5b 9d 00 04 	sw (sp+4),ra
40006f34:	37 81 00 0c 	addi r1,sp,12
40006f38:	f8 00 50 38 	calli 4001b018 <printf>
40006f3c:	34 01 00 01 	mvi r1,1
40006f40:	2b 9d 00 04 	lw ra,(sp+4)
40006f44:	37 9c 00 04 	addi sp,sp,4
40006f48:	c3 a0 00 00 	ret
40006e6c <set_meta>:
40006e6c:	37 9c ff fc 	addi sp,sp,-4
40006e70:	5b 9d 00 04 	sw (sp+4),ra
40006e74:	40 44 00 00 	lbu r4,(r2+0)
40006e78:	44 80 00 1f 	be r4,r0,40006ef4 <set_meta+0x88>
40006e7c:	78 06 40 02 	mvhi r6,0x4002
40006e80:	20 83 00 ef 	andi r3,r4,0xef
40006e84:	38 c6 b2 c0 	ori r6,r6,0xb2c0
40006e88:	7c 65 00 2d 	cmpnei r5,r3,45
40006e8c:	28 c3 00 00 	lw r3,(r6+0)
40006e90:	28 68 00 00 	lw r8,(r3+0)
40006e94:	7c 83 00 20 	cmpnei r3,r4,32
40006e98:	b5 04 20 00 	add r4,r8,r4
40006e9c:	40 8a 00 01 	lbu r10,(r4+1)
40006ea0:	a0 a3 18 00 	and r3,r5,r3
40006ea4:	21 4a 00 07 	andi r10,r10,0x7
40006ea8:	e4 0a 50 00 	cmpe r10,r0,r10
40006eac:	a1 43 50 00 	and r10,r10,r3
40006eb0:	5d 40 00 1d 	bne r10,r0,40006f24 <set_meta+0xb8>
40006eb4:	b8 40 30 00 	mv r6,r2
40006eb8:	34 09 ff ef 	mvi r9,-17
40006ebc:	e0 00 00 07 	bi 40006ed8 <set_meta+0x6c>
40006ec0:	40 e4 00 01 	lbu r4,(r7+1)
40006ec4:	a0 a3 18 00 	and r3,r5,r3
40006ec8:	20 84 00 07 	andi r4,r4,0x7
40006ecc:	e4 04 20 00 	cmpe r4,r0,r4
40006ed0:	a0 83 18 00 	and r3,r4,r3
40006ed4:	5c 60 00 10 	bne r3,r0,40006f14 <set_meta+0xa8>
40006ed8:	34 c6 00 01 	addi r6,r6,1
40006edc:	40 c4 00 00 	lbu r4,(r6+0)
40006ee0:	a0 89 18 00 	and r3,r4,r9
40006ee4:	7c 65 00 2d 	cmpnei r5,r3,45
40006ee8:	b5 04 38 00 	add r7,r8,r4
40006eec:	7c 83 00 20 	cmpnei r3,r4,32
40006ef0:	5c 80 ff f4 	bne r4,r0,40006ec0 <set_meta+0x54>
40006ef4:	34 03 00 21 	mvi r3,33
40006ef8:	34 21 00 04 	addi r1,r1,4
40006efc:	f8 00 52 81 	calli 4001b900 <strncpy>
40006f00:	78 02 40 02 	mvhi r2,0x4002
40006f04:	38 42 b2 c4 	ori r2,r2,0xb2c4
40006f08:	28 41 00 00 	lw r1,(r2+0)
40006f0c:	f8 00 50 43 	calli 4001b018 <printf>
40006f10:	34 0a 00 01 	mvi r10,1
40006f14:	b9 40 08 00 	mv r1,r10
40006f18:	2b 9d 00 04 	lw ra,(sp+4)
40006f1c:	37 9c 00 04 	addi sp,sp,4
40006f20:	c3 a0 00 00 	ret
40006f24:	34 0a 00 00 	mvi r10,0
40006f28:	e3 ff ff fb 	bi 40006f14 <set_meta+0xa8>
"""
cmds = scmds.split("\n")
regs = [('r10',"r13"),('ra',"rax"),('r1',"rdi"),('r2',"rbx"),('r3',"rcx"),('r4',"rdx"),('r5',"r8"),('r6',"r9"),('r7',"r10"),('r8',"r11"),('r9',"r12"),('sp',"rsp"),('r0','0')]

for i in range(len(cmds)):
    for kreg in range(len(regs)):
        a=regs[kreg][0]
        b=regs[kreg][1]
        rr = re.sub(a+"([,\s+])",b+r"\1",cmds[i])
        rr = re.sub(a+"$",b,rr)
        cmds[i]=rr

repl = [(r'addi\s+(\w+),(\w+),([0-9-]+)',r'mov \1, \2\n\t\t add \1, \3'),\
    #(r'addi\s+r1,sp,(.+)',r'mov rdi, [rsp+\1]'),\
    (r'calli\s+[0-9a-f]+\s\<(\w+)\>',r'call \1'),\
    (r'mvi\s(\w+),([0-9-]+)',r'mov \1, \2'),\
    (r'lw\s(\w+),\((\w+)\+(\d+)\)',r'mov \1, [\2+\3]'),\
    #(r'lw\sr3,\(r6\+(\d+)\)',r'mov rcx, [r9+\1]'),\
    #(r'lw\sr8,\(r3\+(\d+)\)',r'mov r11, [rcx+\1]'),\
    (r'lbu\s(\w+),\((\w+)\+(\d+)\)',r'movzx \1, byte[\2+\3]'),\
    (r'be\s(\w+),(\w+),([0-9a-f]+)\s.+',r'cmp \1,\2\n\t\tjz lab_\3'),\
    (r'bne\s(\w+),(\w+),([0-9a-f]+)\s.+',r'cmp \1,\2\n\t\tjnz lab_\3'),\
    (r'bi\s([0-9a-f]+)\s.+',r'jmp lab_\1'),\
    (r'mvhi\s(\w+),0x([0-9a-f]+)',r'ror (\1), 16\n\t\tmov \1w,\2h\n\t\trol \1, 16'),\
    (r'andi\s(\w+),(\w+),0x([0-9a-f]+)',r'mov \1,\2\n\t\tand \1,0\3h'),\
    (r'ori\s(\w+),(\w+),0x([0-9a-f]+)',r'mov \1,\2\n\t\tor \1,0\3h'),\
    (r'cmpnei (\w+),(\w+),(\d+)',r'mov r14,1\n\t\tcmp \2,\3\n\t\tcmovne \1,r14'),\
    (r'cmpe (\w+),(\w+),(\w+)',r'mov r14,1\n\t\tcmp \2,\3\n\t\tcmovne \1,r14'),\
    (r'sw\s\((\w+)\+(\d+)\),(\w+)',r'mov [\1+\2],\3'),\
    (r'and\s(\w+),(\w+),(\w+)',r'mov \1,\2\n\t\tand \1,\3'),\
    (r'add\s(\w+),(\w+),(\w+)',r'mov \1,\2\n\t\tadd \1,\3'),\
    (r'mv (\w+),(\w+)',r'mov \1, \2')
]
print("global _start")
print("[BITS 64]")
print("section   .text")
print("extern printf,strncpy")
for cmd in cmds:
    res1 = re.findall(r'[0-9a-f]+ <([A-Za-z0-9_]+)>:',cmd)
    if len(res1)>0:
        print(res1[0]+":")
    res2 = re.findall(r'([0-9a-f]+)\:\s+[0-9a-f]{2}\s[0-9a-f]{2}\s[0-9a-f]{2}\s[0-9a-f]{2}\s+(.+)',cmd)
    if len(res2)>0:
        #print(res2[0])
        tmp = res2[0][1]
        for rr in repl:
            tmp = re.sub(rr[0],rr[1],tmp)
        tmp = re.sub("rbxw","bx",tmp)
        tmp = re.sub(r"cmp 0,(\w+)",r"cmp \1,0",tmp)
        print("lab_"+res2[0][0]+":","\t",tmp)

"""

    ra to rax
    r1 to rdi
    r2 to rbx
    r3 to rcx
    r4 to rdx
    r5 to r8
    r6 to r9
    r7 to r10
    r8 to r11
    r9 to r12
    r10 to r13
    
    sp to rsp
    
    """
    
