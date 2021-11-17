import re
import random
import binascii
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
			
print("\n".join(a))
