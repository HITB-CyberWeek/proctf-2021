#!/usr/bin/env python3
import requests, traceback
import string,random,re,sys,json,os,shutil,stat
import subprocess as sp

#import pow
def id_gen(size=6, chars=string.ascii_uppercase+string.ascii_lowercase+ string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
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
tmp_dir = "tmp"
if not os.path.exists(tmp_dir):
    os.mkdir(tmp_dir)

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
"Mozilla/5.0 (Linux; Android 8.0.0; SM-G930F Build/R16NW; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/74.0.3729.157 Safari/537.36",
"Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36",
"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0",
"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0",
"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:66.0) Gecko/20100101 Firefox/66.0",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/6.0)",
"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)",
"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0; MASMJS)",
"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0; MDDCJS)",
"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)"]
ua = random.choice(USER_AGENTS)

cmd = sys.argv[1]
if cmd == "info":
    print("vulns: 1:1")
    exit(101)
ip=sys.argv[2]
url = "http://"+ip+":5000/"
try:
    if cmd == "check":
        r1 = requests.get(url)
        if not "CellMachine" in r1.text:
            print("Invalid start page")
            print(r1.text)
            exit(102)
        exit(101)
    elif cmd == "put":
        flag_id = sys.argv[3]
        flag = sys.argv[4]
        vuln = sys.argv[5]
        
        sess = requests.Session()
        r=sess.get(url)

        #challange = re.findall(r'md5\("([^"]+)"\+',r.text)
        #if len(challange) == 0:
            #sys.stderr.write("No challange found \n")
            #exit(102)
        #challange=challange[0]
        #pow_res = pow.generate_pow(challange)

        login = id_gen(8)
        password = id_gen(8)
        password_message = id_gen(8)
        
        resp = sess.post(url+"register",data=dict(login=login,password=password))
        if not "alert(\"Successfully registered\");" in resp.text:
            sys.stderr.write("Cannot register on site\n")
            print(resp.text)
            exit(102)
        resp = sess.post(url+"login",data=dict(login=login,password=password))
        if not "alert(\"Successfully logged in\");" in resp.text:
            sys.stderr.write("Cannot login site\n")
            print(resp.text)
            exit(102)
        
        resp = sess.post(url+"code",data=dict(name=flag_id,password=password_message,content=flag))
        
        if not "alert(\"Generated new cells\");" in resp.text:
            sys.stderr.write("Cannot submit flag\n")
            print(resp.text)
            exit(102)
        resp = sess.get(url+"/")
        if not flag_id in resp.text:
            sys.stderr.write("No flagid in page\n")
            print(resp.text)
            exit(102)
        resp = sess.get(url+"check/%s/%s" %(login,flag_id+".pk.cell"),params=dict(key=password_message))
        if not flag in resp.json()['status']:
            sys.stderr.write("No flag in check\n")
            print(resp.json)
            exit(102)
        
        print(",".join([login,password,password_message,flag_id]))
        exit(101)
    elif cmd == "get":
        (login,password,password_message,flag_id) = sys.argv[3].split(",")
        sess = requests.Session()
        r=sess.get(url)
        resp = sess.post(url+"login",data=dict(login=login,password=password))
        if not "alert(\"Successfully logged in\");" in resp.text:
            sys.stderr.write("Cannot login site\n")
            print(resp.text)
            exit(102)
        resp = sess.get(url+"/")
        if not flag_id in resp.text:
            sys.stderr.write("No flagid in page\n")
            print(resp.text)
            exit(102)
        
        local_filename = os.path.join(tmp_dir,flag_id)
        
        with requests.get(url+"data/"+login+"/"+flag_id+".pk.cell", stream=True) as r:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        
        #password_message = 'a'+password_message[1:]
        #res = sp.Popen(["./cells.elf","execute",local_filename,password_message,"0"],stdout=sp.PIPE)
        pwd = os.getcwd()
        dockercmd=["docker","run","-v",pwd+":/home/checker","cells_container","execute",local_filename,password_message,"0"]
        res = sp.Popen(dockercmd,stdout=sp.PIPE)
        
        out = res.communicate()
        
        toks = out[0].split(b",")
        if len(toks)!=2:
            os.unlink(local_filename)
            sys.stderr.write("Invalid password\n")
            print(out[0])
            exit(102)
        sm = csum_b(toks[0])
        if hex(sm)[2:].encode() != toks[1]:
            sys.stderr.write("Invalid password 2\n")
            os.unlink(local_filename)
            print(out[0])
            exit(102)
            
        sess2 = requests.Session()
        resp = sess2.get(url+"search",params=dict(template=login[:2]))
        if not login in resp.text:
            os.unlink(local_filename)
            sys.stderr.write("No login in search resp\n")
            print(resp.text)
            exit(102)
        ref = '<a href="/data/%s/%s.pk.cell">' % (login,flag_id)
        if not ref in resp.text:
            os.unlink(local_filename)
            sys.stderr.write("No flagid in search resp\n")
            print(resp.text)
            exit(102)
        local_filename2 = local_filename+"2"
        with requests.get(url+"data/"+login+"/"+flag_id+".pk.cell", stream=True) as r:
            with open(local_filename2, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        a1=open(local_filename,"rb").read()
        a2=open(local_filename2,"rb").read()
        for i in range(len(a1)):
            if a1[i] != a2[i]:
                sys.stderr.write("File in search page is different\n")
                exit(102)
        os.unlink(local_filename2)
        os.unlink(local_filename)
        exit(101)
    else:
        print("No command")
except Exception:
    print(traceback.format_exc())
    exit(104)
