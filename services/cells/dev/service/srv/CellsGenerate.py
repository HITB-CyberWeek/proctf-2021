import re,random,os,subprocess

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
def csum_b(s):
    res = 0
    for i in range(len(s)//4):
        val = (s[4*i]) | ((s[4*i+1])<<8)  | ((s[4*i+2])<<16)  | ((s[4*i+3])<<24)
        res ^=val
    restsize = len(s)%4
    if restsize == 0:
        return res
    elif restsize == 1:
        return res ^ (s[-1])
    elif restsize == 2:
        return res ^ ((s[-2]) | ((s[-1]) << 8) )
    elif restsize == 3:
        return res ^ ((s[-3]) | ((s[-2]) << 8) | ((s[-1]) << 16))

def GenRS(flen=31):
    s=''
    for i in range(flen):
        s+=random.choice("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return s

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
        ridx = takes[to_size-i-1]
        if takes[i] == takes[to_size-i-1]:
            ridx = random.choice(range(len(password)))
            b=ord(password[ridx])
        op = ops_taken[i]
        modified_password.append(eval("%d %s %d" % (a,op[0],b)))
        commands.append("$P%d:%s $N%d $N%d" %(i,op[1],takes[i],ridx))
    return modified_password,commands

def GenerateCells(password,flag,output_path,name):
    result=[]
    init_flag = flag
    flag = flag + "," + hex(csum(flag))[2:]
    mpassword,commands = GenerateFormula(password,len(flag))
    flag2 = []
    for i in range(len(flag)):
        val = ord(flag[i]) ^  mpassword[i]
        flag2.append(val)
    for i in range(8):
        result.append("input $N%d remove" % i)
    result.append("skip $P0 remove")
    flag = flag2
    for i in range(len(flag)):
        result.append("$XX%d:xor $F%d $P%d" %(i,i,i))
    for i in range(len(flag)):
        result.append("output $XX%d" % i)
    result.append("skip 0")	
    commands[-1] += " reload"
    result = result + commands
    for i in range(8):
        result.append("$N%d:0" % i)
    for i in range(len(flag)):
        c = flag[i]
        result.append("$F%d:%d" % (i,c))
    labels={}
    for i in range(len(result)):
        ff=re.findall(r'\$(\w+)',result[i])
        if len(ff)>0:
            for f in ff:
                labels[f]=-1
    for i in range(len(result)):
        ff=re.findall(r'\$(\w+):',result[i])
        if len(ff)>0:
            labels[ff[0]]=i
    for i in range(len(result)):
        ff2=re.findall(r'\$(\w+):',result[i])
        ff1=re.findall(r'\$(\w+)',result[i])
        if len(ff2)>0:
            if labels[ff2[0]] != -1:
                result[i] = result[i].replace("$"+ff2[0]+":","")
        if len(ff1)>0:
            for f in ff1:
                if labels[f] != -1:
                    if i < labels[f]:
                        result[i] = result[i].replace("$"+f,str(labels[f]-i))
                    else:
                        result[i] = result[i].replace("$"+f,str(labels[f]-i))
    
    tmp_prog_path = os.path.join(output_path,name+".tmp.txt")
    tmp_prog_bin  = os.path.join(output_path,name+".tmp.cells")
    open(tmp_prog_path,"w+").write("\n".join(result))
    res = subprocess.Popen(["sh","-c","./cells.elf compile %s %s > /dev/null" % (tmp_prog_path,tmp_prog_bin)])
    res.communicate()
    data = open(tmp_prog_bin,"rb").read()
    cmds = []
    for i in range(len(data)//3):
        cmds.append(data[i*3:i*3+3])
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
                        #print(("%d=%d ^ %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                        bts[k]=(i,j,"^")
                        break
                    """if cmds[i] + cmds[j] == cmds[k]:
                        #print(("%d=%d + %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                        bts[k]=(i,j,"+")
                        break
                    if cmds[i] - cmds[j] == cmds[k]:
                        #print(("%d=%d - %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                        bts[k]=(i,j,"-")
                        break
                    if cmds[i] * cmds[j] == cmds[k]:
                        #print(("%d=%d - %d" %(k,i,j)),cmds[k],cmds[i], cmds[j])
                        bts[k]=(i,j,"-")
                        break"""
                if k in bts:
                    break
        if k in bts:
            if bts[k][2] == "^":
                op1 = bts[k][0] - k +1
                op2 = bts[k][1] - k +1
    #            print("Result:",hex(cmds[k]),"Op1:",op1,"Op2",op2,'val',cmds[bts[k][0]],cmds[bts[k][1]])
                cmds[k] = (6 << 18) | ((op1 & 0xFF) << 10 ) | ((op2&0xFF) << 2)
    #            print(hex(cmds[k]))
    #            print ("changing %d =%d ^ %d" % (k,bts[k][0],bts[k][1]))
    #            print(cmds[0:30])
            if bts[k][2] == "+":
                op1 = k-bts[k][0]
                op2 = k-bts[k][1]
                cmds[k] = (1 << 18) | (op1 << 10 ) | (op2 << 2)
                #print ("changing %d =%d + %d" % (k,bts[k][0],bts[k][1]))
            if bts[k][2] == "-":
                op1 = k-bts[k][0]
                op2 = k-bts[k][1]
                cmds[k] = (2 << 18) | (op1 << 10 ) | (op2 << 2)
                #print ("changing %d =%d - %d" % (k,bts[k][0],bts[k][1]))
            if bts[k][2] == "*":
                op1 = k-bts[k][0]
                op2 = k-bts[k][1]
                cmds[k] = (3 << 18) | (op1 << 10 ) | (op2 << 2)
                #print ("changing %d =%d * %d" % (k,bts[k][0],bts[k][1]))
            
            if ep > k:
                offset = (ep - k) % len(cmds)
                cmds = cmds[0:k+1] + [(1 << 22)| (15<<18) | (offset & 0xFFFF)] + cmds[k+1:]
            elif ep == k:
                offset = len(cmds)
                cmds = cmds[0:k+1] + [(1 << 22)| (15<<18) | (offset & 0xFFFF)] + cmds[k+1:]
            elif ep < k:
                offset = len(cmds) - (k - ep)
    #            print("offset neg",offset)
                cmds = cmds[0:k+1] + [(1 << 22)| (15<<18) | (offset & 0xFFFF)] + cmds[k+1:]
            ep=k
    #        print("ep=",ep)
            num+=1
            bts = {}
            if num ==1005:
                break
        k+=1
        
    #print("Final ep=",ep)
    cmds=[(1 << 22)| (15<<18) | ((ep+1) & 0b111111111111111111)] + cmds
    #print(hex(cmds[0]))
    res=b""
    for c in cmds:
        res+= (c & 0xff).to_bytes(1, byteorder='little')
        res+= (c>>8 & 0xff).to_bytes(1, byteorder='little')
        res+= (c>>16 & 0xff).to_bytes(1, byteorder='little')
    os.unlink(tmp_prog_path)
    os.unlink(tmp_prog_bin)
    tmp_prog_bin2  = os.path.join(output_path,name+".pk.cell")
    open(tmp_prog_bin2,"wb+").write(res)
    return res,tmp_prog_bin2
