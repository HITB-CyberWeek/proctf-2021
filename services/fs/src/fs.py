from flask import Flask, Response, request, abort, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
import ujson as json
import re
import pathlib
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from Crypto.Signature import pkcs1_15
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA

import base64


class ShareRequest:
    def __init__(self, u, l, m):
        self.username = u
        self.location = l
        self.message = m


class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

    def is_active(self):
        return True

class UsersRepository:
    def get_user(self, username):
        return User(username)
    
    def get_or_create_user(self, username, password):
        if not re.match(r'^\w+$', username):
            return None

        userDir = pathlib.Path(f"users/{username}/")
        password_hash_path = userDir / ".pass_hash"
        if not userDir.exists():
            print(f"user not exists. creating")
            userDir.mkdir()

            password_hash = generate_password_hash(password)
            password_hash_path.write_text(password_hash)
            return self.get_user(username)
        else:
            print(f"user exists")
            if not check_password_hash(password_hash_path.read_text(), password):
                print(f"hash mismatch")
                return None
            return self.get_user(username)



app = Flask(__name__)
app.config['SECRET_KEY'] = '############### AUTOGENERATE IT #################'

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

users_repository = UsersRepository()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        registeredUser = users_repository.get_or_create_user(username, password)
        if registeredUser != None:
            print(f'Proceeding to login {registeredUser.get_id()}')
            login_user(registeredUser)
            return redirect(url_for('whoami'))
        else:
            return abort(401)
    else:
        return Response('''
            <form action="" method="post">
                <p><input type=text name=username>
                <p><input type=password name=password>
                <p><input type=submit value=Login>
            </form>
        ''')



def is_safe_path(basedir, path):
    abs_basedir = os.path.abspath(basedir)    
    abs_path = os.path.abspath(path)
    return abs_basedir == os.path.commonpath([abs_basedir, abs_path])


@app.route('/share', methods=['POST'])
@login_required
def share():
    len = int(request.headers["Content-Length"])
    if len > 1024:
        return "Request data is too big", 400

    data = request.get_data()
    share_request = ShareRequest(**loads(data))

    if not is_safe_path(current_user.username, share_request.location):
        return f"You don't own the location '{share_request.location}' requested to share", 403

    key = RSA.import_key(open('key.pem').read())
    h = MD5.new(data)
    print(h.hexdigest())
    signature = pkcs1_15.new(key).sign(h)
    print(signature)
    result = url_for('get_access', request = base64.urlsafe_b64encode(data), signature = base64.urlsafe_b64encode(signature))

    return f'\n<a href="{result}">click here</a>\n';


@app.route('/get_access', methods=['POST'])
@login_required
def get_access():
    data = base64.urlsafe_b64decode(request.args["request"])
    h = MD5.new(data)
    print(h.hexdigest())

    signature = base64.urlsafe_b64decode(request.args["signature"])
    print(signature)

    key = RSA.import_key(open('key.pem').read())    
    try:
        pkcs1_15.new(key).verify(h, signature)
    except:
        return f"Signature invalid", 403

    share_request = ShareRequest(**loads(data))
    print(f"sharing location {share_request.location} to user {share_request.username} with message {share_request.message}")

    return f"access granted"



@app.errorhandler(401)
def unauthorized(e):
    return Response('<p>Login failed</p>')

# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return users_repository.get_user(userid)


@app.route('/')
def index():
    return "<h2>This is a next-gen file sharing service</h2>"

@app.route('/whoami')
@login_required
def whoami():
    return "<h1>'" + current_user.username + "' logged in</h1>"


def bytes_to_str(b: bytes) -> str:
    return b.decode("iso-8859-1")

def str_to_bytes(s: str) -> bytes:
    return s.encode("iso-8859-1")

def loads(b: bytes):
    return json.loads(bytes_to_str(b))

def dumps(o):
    return str_to_bytes(json.dumps(o, ensure_ascii=False))

@app.route("/get")
def get():
    print(dumps(request.args))
    return "<p>Hello, World!</p>\n"

@app.route("/post", methods=["POST"])
def post():
    data = request.data
    print(data)
    print(loads(data))
    
    return "\n<p>Hello, World!</p>\n"


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=7777, debug = True)