import os,json,glob,subprocess
import CellsGenerate
from flask import Flask
from flask import make_response,jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "qweqwe"

def check_creadentials(login, password):
    user_dir = os.path.join("data",login)
    if not os.path.isdir(user_dir):
        return False
    user_file = os.path.join("data",login,"info.json")
    if not os.path.isfile(user_file):
        return False
    info = json.load(open(user_file,'r'))
    if info['login'] != login or info['password'] != password:
        return False;
    return True
@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)

@app.route('/data/<user>/<name>')
def send_data(user,name):
    if name[-8:] != ".pk.cell":
        return redirect('/?m=No such program')
    p = os.path.join("data",user)
    return send_from_directory(p,name)

@app.route('/')
def index():
    login = None
    if 'login' in session:
        login = session['login']
    if "m" in request.values:
        return render_template('index.html',mes=request.values['m'],login=login)
    if login:
        user_dir = os.path.join("data",login)
        if not os.path.isdir(user_dir):
            return render_template('index.html',mes="User dir not available",login=login)
        progs = []
        for fl in glob.glob(user_dir+"/info_*"):
            info = json.load(open(fl,'r'))
            progs.append(info)
        print(progs)
        return render_template('index.html',login=login,progs=progs)
    return render_template('index.html',login=login)

@app.route('/login', methods=['POST'])
def login():
    login, password = request.values['login'], request.values['password']
    if check_creadentials(login, password):
        session['login'] = login
        return redirect('/?m=Successfully logged in')
    else:
        return redirect('/?m=Invalid login or password')

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    session.pop("login",None)
    return resp

@app.route('/register', methods=['POST'])
def register():
    login,password  = request.values['login'], request.values['password']
    if check_creadentials(login,password):
        return redirect('/?m=User already exists')
    user_dir = os.path.join("data",login)
    os.mkdir(user_dir)
    user_file = os.path.join("data",login,"info.json")
    info = {"login":login,"password":password}
    json.dump(info,open(user_file,'w+'))
    return redirect('/?m=Successfully registered')

@app.route('/code', methods=['POST'])
def code():
    if not "login" in session:
        return redirect('/?m=Not logged in')
    
    login = session['login']
    name = request.values["name"]
    password = request.values["password"]
    content= request.values["name"]
    #pay = request.values("pay")
    user_dir = os.path.join("data",login)
    if not os.path.isdir(user_dir):
        return redirect('/?m=user dir removed')
    secret_path = os.path.join("data",login,"info_"+name+".json")
    res,resfile = CellsGenerate.GenerateCells(password,content,user_dir,name)
    info = {"name":name,"password":password,"content":content,"file":resfile}
    json.dump(info,open(secret_path,"w"))
    return redirect('/?m=Generated new cells')

@app.route('/check/<user>/<name>', methods=['GET'])
def check(user,name):
    if name[-8:] != ".pk.cell":
        return redirect('/?m=No such program')
    if not 'key' in request.values:
        return redirect('/?m=No key provided')
    p = os.path.join("data",user,name)
    proc = subprocess.Popen(["./cells.elf","execute",p,request.values['key'],"0"],stdout=subprocess.PIPE)
    res,_ = proc.communicate()
    print(res)
    toks = res.split(b",")
    if len(toks)!=2:
        return jsonify({'status':"Invalid password"})
    sm = CellsGenerate.csum_b(toks[0])
    if hex(sm)[2:].encode() != toks[1]:
        return jsonify({'status':"Invalid password"})
    return jsonify({'status':"OK"})

@app.route('/search', methods=['GET'])
def search():
    tmpl = request.values["template"]
    if len(tmpl)<2:
        return redirect('/?m=Too short template')
    users = []
    for fl in glob.glob("data"):
        if tmpl in fl:
          users.append(dict(name=fl))  
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
