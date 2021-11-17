import re
import random
import binascii
random.seed(10)
a=[]
flag = "0102030405060708090a0b0c0d0f0001="
flag = flag + "," + hex(binascii.crc32(flag.encode()))[2:]
password="12345678"

def GenerateFormula(password,to_size):
    ops = [("^","xor"),("-","sub"),("+","add"),("*","mul")]
    modified_password = []
    commands = []
    takes = [i % len(password)  for i in range(to_size)]
    ops_taken = [random.choice(ops)  for i in range(to_size)]
    random.shuffle(takes)
    for i in range(to_size):
        a=ord(password[takes[i]])
        b=ord(password[takes[to_size-i-1]])
        op = ops_taken[i]
        modified_password.append(eval("%d %s %d" % (a,op[0],b)))
        commands.append("$P%d:%s $N%d $N%d" %(i,op[1],takes[i],takes[to_size-i-1]))
    return modified_password,commands
        
mpassword,commands = GenerateFormula(password,100)
#mpassword = [ord(password[0]) ^ ord(password[1]),\
#ord(password[2]) ^ ord(password[3]),\
#ord(password[4]) ^ ord(password[5]),\
#ord(password[6]) ^ ord(password[7]),\
#ord(password[0]) - ord(password[1]),\
#ord(password[2]) - ord(password[3]),\
#ord(password[4]) - ord(password[5]),\
#ord(password[6]) - ord(password[7])]
flag2 = []
for i in range(len(flag)):
	val = ord(flag[i]) ^  mpassword[i % 8]
	#if val >0:
	flag2.append(val)
	#else:
	#	flag2.append(256+val)
# $N - номер ячейки буффера
for i in range(8):
	a.append("input $N%d remove" % i)
# Тут можно вводить различные упаковки флага
a.append("skip $P0 remove")
flag = flag2
for i in range(len(flag)):
	a.append("$XX%d:xor $F%d $P%d" %(i,i,i%8))
for i in range(len(flag)):
	a.append("output $XX%d" % i)
a.append("skip 0")	
commands[-1] += " reload"
a = a + commands
#a.append("$P0:xor $N0 $N1")
#a.append("$P1:xor $N2 $N3")
#a.append("$P2:xor $N4 $N5")
#a.append("$P3:xor $N6 $N7")
#a.append("$P4:sub $N0 $N1")
#a.append("$P5:sub $N2 $N3")
#a.append("$P6:sub $N4 $N5")
#a.append("$P7:sub $N6 $N7 reload")

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
        
