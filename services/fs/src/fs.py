#!/usr/bin/env python3

from flask import Flask, Response, request, abort, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
import ujson as json
import re
import pathlib
import os
import secrets
import itertools
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
    def append_acl(self, username, path):
        acl_path = f"users/{username}/.acl"

        with open(acl_path, "a", encoding="ascii") as f:
            f.write(f"{path}\n")

    def is_phys_subpath(self, basedir, path):
        abs_basedir = os.path.abspath(basedir)
        abs_path = os.path.abspath(path)
        return abs_basedir == os.path.commonpath([abs_basedir, abs_path])

    def validate_access(self, username, path):
        acl_path = f"users/{username}/.acl"
        with open(acl_path, encoding="ascii") as f:
            acl = itertools.islice([x.rstrip("\n") for x in f if x.strip()], 0, 256)
        for allowed_path in acl:
            if self.is_phys_subpath(f"data/{allowed_path}", path):
                return True
        return False

    def get_user(self, username):
        return User(username)

    def get_or_create_user(self, username, password):
        if not re.fullmatch(r"[a-zA-Z0-9_]+", username):
            return None

        user_dir = pathlib.Path("users") / username
        os.makedirs(os.path.dirname(user_dir), exist_ok=True)

        password_hash_path = user_dir / ".pass_hash"

        if not user_dir.exists():
            user_dir.mkdir()

            password_hash = generate_password_hash(password)
            password_hash_path.write_text(password_hash)

            self.append_acl(username, f"{username}")

            return self.get_user(username)
        else:
            if not check_password_hash(password_hash_path.read_text(), password):
                return None
            return self.get_user(username)


def load_or_gen_rsa_key():
    key_path = pathlib.Path("secret") / "key.pem"
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    try:
        key = RSA.import_key(key_path.read_text())
    except FileNotFoundError:
        key = RSA.generate(2048)
        try:
            with open(key_path, "wb") as key_file:
                key_file.write(key.exportKey("PEM"))
        except:
            key = RSA.import_key(key_path.read_text())
    return key


def load_or_gen_secret_key():
    key_path = pathlib.Path("secret") / "key.secret"
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    try:
        key = key_path.read_text()
    except FileNotFoundError:
        key = secrets.token_hex()
        try:
            with open(key_path, "w") as key_file:
                key_file.write(key)
        except Exception as e:
            key = key_path.read_text()
    return key


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
app.config["SECRET_KEY"] = load_or_gen_secret_key()
app.config["signing_key"] = load_or_gen_rsa_key()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

users_repository = UsersRepository()


@app.route('/publickey', methods=['GET'])
def publickey():
    return app.config["signing_key"].publickey().exportKey('PEM'), {"Content-Type": "application/x-pem-file"}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        registeredUser = users_repository.get_or_create_user(username, password)
        if registeredUser != None:
            login_user(registeredUser)
            return redirect(url_for("whoami"))
        else:
            return abort(401)
    else:
        return Response('''
            Register or Login
            <form action="" method="post">
                <p><input type=text name=username placeholder=login>
                <p><input type=password name=password placeholder=password>
                <p><input type=submit value=Send>
            </form>
        ''')


@app.route("/share", methods=["GET", "POST"])
@login_required
def share():
    if request.method == "POST":
        len = int(request.headers["Content-Length"])

        data = request.get_data()
        share_request = ShareRequest(**loads(data))

        if not users_repository.is_phys_subpath(f"data/{current_user.username}", f"data/{share_request.location}"):
            return f"You don't own the location '{share_request.location}' requested to share", 403

        key = app.config["signing_key"]
        h = MD5.new(data)
        signature = pkcs1_15.new(key).sign(h)
        result = url_for("access", request = base64.urlsafe_b64encode(data), signature = base64.urlsafe_b64encode(signature))

        return f'\n<a href="{result}">click here to get access</a>\n'

    return '''
    <!doctype html>
    <h2>Come here POSTing someone's signed share request</h2>
    '''

@app.route("/access")
@login_required
def access():
    req = request.args.get("request")
    sign = request.args.get("signature")
    if not req and not sign:
        return '''
    <!doctype html>
    <h4>To get access to the shared path please specify 'request' and 'signature' params in query string</h4>
    '''

    data = base64.urlsafe_b64decode(req)

    h = MD5.new(data)
    signature = base64.urlsafe_b64decode(sign)

    key = app.config["signing_key"]
    try:
        pkcs1_15.new(key).verify(h, signature)
    except:
        return "Signature invalid", 403

    share_request = ShareRequest(**loads(data))
    if share_request.username != current_user.username:
        return f"Current user '{current_user.username}' is not equal to ticket user '{share_request.username}'", 403
    users_repository.append_acl(share_request.username, share_request.location)

    return f"Access to {share_request.location} granted with message: '{share_request.message}'"


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            print("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            print("No selected file")
            return redirect(request.url)
        if file:
            filepath = f"{current_user.username}/{file.filename}"
            real_path = f"data/{filepath}"
            if not users_repository.is_phys_subpath(f"data/{current_user.username}", real_path):
                return f"Can't upload not to user's folder", 403
            os.makedirs(os.path.dirname(real_path), exist_ok=True)
            file.save(real_path)
            return redirect(url_for("download_file", file=filepath))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route("/download")
@login_required
def download_file():
    file = request.args.get("file")
    if not file:
        return '''
    <!doctype html>
    <h4>To download a file please specify 'file' param in query string</h4>
    '''

    filepath = f"data/{file}"
    if not users_repository.validate_access(current_user.username, filepath):
        return f"Access denied", 403

    if os.path.isfile(filepath):
        return send_file(filepath)
    elif os.path.isdir(filepath):
        return dumps(os.listdir(filepath))
    else:
        return "File not found", 404


@app.errorhandler(401)
def unauthorized(e):
    return Response("<p>Login failed</p>")

# callback to reload the user object


@login_manager.user_loader
def load_user(userid):
    return users_repository.get_user(userid)


@app.route("/")
def index():
    return f"<h3>This is an old-school file upload and sharing service</h3>You can <a href='/login'>register or log in</a> here. Or just check <a href='/whoami'>who you are</a>"


@app.route("/whoami")
@login_required
def whoami():
    return f"<h1>'{current_user.username}' logged in</h1>" + '''
            Now you can:<br><br>
            <a href="/upload">Upload</a><br>
            <a href="/download">Download</a><br>
            <a href="/share">Share</a><br>
            <a href="/access">Get shared access</a><br>
            <a href="/publickey">Get public key</a><br>
        '''


def bytes_to_str(b: bytes) -> str:
    return b.decode("iso-8859-1")


def str_to_bytes(s: str) -> bytes:
    return s.encode("iso-8859-1")


def loads(b: bytes):
    return json.loads(bytes_to_str(b))


def dumps(o):
    return str_to_bytes(json.dumps(o, ensure_ascii=False))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7777)
