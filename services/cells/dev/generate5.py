import re
import random
import binascii
import z3
random.seed(10)
def csum(s):
    res = 0
    for i in range(len(s)//4):
        val = ord(s[4*i]) | (ord(s[4*i+1])<<8)  | (ord(s[4*i+2])<<16)  | (ord(s[4*i+3])<<24)
        res ^=val
    restsize = len(s)%4
    if restsize == 0:
        return res
    elif restsize == 1:
        return res ^ ord(s[-1])
    elif restsize == 2:
        return res ^ (ord(s[-2]) | (ord(s[-1]) << 8) )
    elif restsize == 3:
        return res ^ (ord(s[-3]) | (ord(s[-2]) << 8) | (ord(s[-1]) << 16))
    
a=[]
flag = "0102030405060708090a0b0c0d0f000="
flag = flag + "," + hex(csum(flag))[2:]
password="12345678"
solv = z3.Solver()
def GenerateFormula(password,to_size):
    ops = [("^","xor"),("-","sub"),("+","add")]
    modified_password = []
    commands = []
    takes = [i for i in range(len(password))]
    ops_taken = [random.choice(ops)  for i in range( len(password))]
    random.shuffle(takes)
    
    cells_z3 = []
    password_z3 = []
    for i in range(len(password)):
        password_z3.append(z3.BitVec('p%d' % i,7))
        solv.add(z3.Or(\
                    z3.And(password_z3[-1] >= ord('0'),password_z3[-1] <= ord('9')),\
                    z3.And(password_z3[-1] >= ord('A'),password_z3[-1] <= ord('Z')),\
                    z3.And(password_z3[-1] >= ord('a'),password_z3[-1] <= ord('z'))))
    
    for i in range(len(password)):
        a=ord(password[takes[i]])
        b=ord(password[takes[len(password)-i-1]])
        op = ops_taken[i]
        modified_password.append(eval("%d %s %d" % (a,op[0],b)))
        commands.append("$P%d:%s $N%d $N%d" %(i,op[1],takes[i],takes[len(password)-i-1]))
        cells_z3.append(eval("password_z3[%d] %s password_z3[%d]" % (takes[i],op[0],takes[len(password)-i-1])))
    
    for i in range(to_size):
        op1_idx = random.randint(0,len(commands)-1)
        op2_idx = random.randint(0,len(commands)-1)
        if op1_idx == op2_idx:
            op2_idx = random.randint(0,len(commands)-1)
        for i in range(len(modified_password)):
            print(i,modified_password[i])
        print("!",op2_idx,op1_idx)
        a=modified_password[op1_idx]
        b=modified_password[op2_idx]
        op = random.choice(ops)
        modified_password.append(eval("%d %s %d" % (a,op[0],b)))
        commands.append("$P%d:%s $P%d $P%d" %(i+len(password),op[1],op1_idx,op2_idx))
        cells_z3.append(eval("cells_z3[%d] %s cells_z3[%d]" % (op1_idx,op[0],op2_idx)))
    return modified_password,commands,password_z3,cells_z3

mpassword,commands,password_z3,cells_z3 = GenerateFormula(password,len(flag))
flag2 = []
flag2_z3 = []
start_idx = len(mpassword) - len(flag)
for i in range(len(flag)):
	print('idx',start_idx+i,len(mpassword),len(flag))
	val = ord(flag[i]) ^  mpassword[start_idx+i]
	#if val >0:
	flag2.append(val)
	flag2_z3.append(val ^ cells_z3[start_idx+i])
	#else:
	#	flag2.append(256+val)
# $N - номер ячейки буффера
#for i in range(len(flag2_z3)):
print(flag,"!",flag[32],flag[33])
for i in range(len(flag)):
    if i < 31:
        solv.add(\
            z3.Or(\
                    z3.And(flag2_z3[i] >= ord('0'),flag2_z3[i] <= ord('9')),\
                    z3.And(flag2_z3[i] >= ord('A'),flag2_z3[i] <= ord('Z')),\
                    z3.And(flag2_z3[i] >= ord('a'),flag2_z3[i] <= ord('z'))))
    elif i == 31:
        solv.add(flag2_z3[i] == ord('='))
    elif i == 32:
        solv.add(flag2_z3[i] == ord(','))
    elif i > 32:
        solv.add(\
            z3.Or(\
                z3.And(flag2_z3[i] >= ord('0'),flag2_z3[i] <= ord('9')),\
                z3.And(flag2_z3[i] >= ord('a'),flag2_z3[i] <= ord('h'))\
                ))

print(solv)
print(solv.check())
for i in range(8):
    print(chr(solv.model()[password_z3[i]].as_long()))

for i in range(8):
	a.append("input $N%d remove" % i)
# Тут можно вводить различные упаковки флага
a.append("skip $P0 remove")
flag = flag2
for i in range(len(flag)):
	a.append("$XX%d:xor $F%d $P%d" %(i,i,i))
for i in range(len(flag)):
	a.append("output $XX%d" % i)
a.append("skip 0")	
commands[-1] += " reload"
a = a + commands

for i in range(8):
	a.append("$N%d:0" % i)

for i in range(len(flag)):
	c = flag[i]
	a.append("$F%d:%d" % (i,c))
	
labels={}

for i in range(len(a)):
	ff=re.findall(r'\$(\w+)',a[i])
	if len(ff)>0:
		for f in ff:
			labels[f]=-1
for i in range(len(a)):
	ff=re.findall(r'\$(\w+):',a[i])
	if len(ff)>0:
		labels[ff[0]]=i
for i in range(len(a)):
	ff2=re.findall(r'\$(\w+):',a[i])
	ff1=re.findall(r'\$(\w+)',a[i])
	if len(ff2)>0:
		if labels[ff2[0]] != -1:
			a[i] = a[i].replace("$"+ff2[0]+":","")

	if len(ff1)>0:
		for f in ff1:
			if labels[f] != -1:
				if i < labels[f]:
					a[i] = a[i].replace("$"+f,str(labels[f]-i))
				else:
					a[i] = a[i].replace("$"+f,str(labels[f]-i))
			
#print("!\n".join(a))
open("4.txt","w+").write("\n".join(a))
quit()
import subprocess,struct
subprocess.Popen(["sh","-c","./cells.elf compile 4.txt 4.cells > /dev/null"])
data = open("4.cells","rb").read()
#print(data)
cmds = []
for i in range(len(data)//3):
    cmds.append(data[i*3:i*3+3])
print("CMDS",cmds[0:10])
for i in range(len(cmds)):
    cmds[i] = cmds[i][0] | (cmds[i][1] << 8) | (cmds[i][2] << 16)

bts = {}
k=0
ep = 0
num=0
while k<len(cmds):
    if k not in bts:
        for i in range(k+1,len(cmds)):
            if i==k:
                continue
            for j in range(k+1,len(cmds)):
                if j==k:
                    continue
                if cmds[i] ^ cmds[j] == cmds[k]:
                    print(("%d=%d ^ %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                    bts[k]=(i,j,"^")
                    break
                if cmds[i] + cmds[j] == cmds[k]:
                    print(("%d=%d + %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                    bts[k]=(i,j,"+")
                    break
                if cmds[i] - cmds[j] == cmds[k]:
                    print(("%d=%d - %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                    bts[k]=(i,j,"-")
                    break
                if cmds[i] * cmds[j] == cmds[k]:
                    print(("%d=%d - %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                    bts[k]=(i,j,"-")
                    break
            if k in bts:
                break
    if k in bts:
        print("---")
        if bts[k][2] == "^":
            op1 = bts[k][0] - k +1
            op2 = bts[k][1] - k +1
            print("Result:",hex(cmds[k]),"Op1:",op1,"Op2",op2,'val',cmds[bts[k][0]],cmds[bts[k][1]])
            cmds[k] = (6 << 18) | ((op1 & 0xFF) << 10 ) | ((op2&0xFF) << 2)
            print(hex(cmds[k]))
            print ("changing %d =%d ^ %d" % (k,bts[k][0],bts[k][1]))
            #print(cmds[0:30])
        if bts[k][2] == "+":
            op1 = k-bts[k][0]
            op2 = k-bts[k][1]
            cmds[k] = (1 << 18) | (op1 << 10 ) | (op2 << 2)
            print ("changing %d =%d + %d" % (k,bts[k][0],bts[k][1]))
        if bts[k][2] == "-":
            op1 = k-bts[k][0]
            op2 = k-bts[k][1]
            cmds[k] = (2 << 18) | (op1 << 10 ) | (op2 << 2)
            print ("changing %d =%d - %d" % (k,bts[k][0],bts[k][1]))
        if bts[k][2] == "*":
            op1 = k-bts[k][0]
            op2 = k-bts[k][1]
            cmds[k] = (3 << 18) | (op1 << 10 ) | (op2 << 2)
            print ("changing %d =%d * %d" % (k,bts[k][0],bts[k][1]))
        
        if ep > k:
            offset = (ep - k) % len(cmds)
            cmds = cmds[0:k+1] + [(1 << 22)| (15<<18) | (offset & 0xFFFF)] + cmds[k+1:]
        elif ep == k:
            offset = len(cmds)
            cmds = cmds[0:k+1] + [(1 << 22)| (15<<18) | (offset & 0xFFFF)] + cmds[k+1:]
        elif ep < k:
            offset = len(cmds) - (k - ep)
            print("offset neg",offset)
            cmds = cmds[0:k+1] + [(1 << 22)| (15<<18) | (offset & 0xFFFF)] + cmds[k+1:]
        ep=k
        print("ep=",ep)
        num+=1
        bts = {}
        if num ==50:
            break
    k+=1;
print("ep=",ep)
cmds=[(1 << 22)| (15<<18) | ((ep+1) & 0xFF)] + cmds
res=b""
#0b110110000010101010100
#  43210fedcba9876543210
#       0x680308 -1 -194
#       -0x308
#
for c in cmds:
    res+= (c & 0xff).to_bytes(1, byteorder='little')
    res+= (c>>8 & 0xff).to_bytes(1, byteorder='little')
    res+= (c>>16 & 0xff).to_bytes(1, byteorder='little')

open("4.cells.pk","wb+").write(res)
        
