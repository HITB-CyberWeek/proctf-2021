from flask import Flask, Response, request, abort, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
import ujson as json
import re
import pathlib
from werkzeug.security import generate_password_hash, check_password_hash

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

@app.route('/')
def index():
    return "<h2>Hello World</h2>"

@app.route('/whoami')
@login_required
def whoami():
    return "<h1>'" + current_user.username + "' logged in</h1>"

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

@app.errorhandler(401)
def unauthorized(e):
    return Response('<p>Login failed</p>')

# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return users_repository.get_user(userid)






def bytes_to_str(b: bytes) -> str:
    return b.decode("iso-8859-1")

def loads(b: bytes):
    return json.loads(bytes_to_str(b))

@app.route("/get")
def get():
    print(json.dumps(request.args).encode())
    return "<p>Hello, World!</p>\n"

@app.route("/post", methods=["POST"])
def post():
    #data = request.data
    data = request.get_data()
    print(data)
    print(loads(data))
    
    return "\n<p>Hello, World!</p>\n"


if __name__ == "__main__":
    app.run(debug = True)