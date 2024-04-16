'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for
from flask_socketio import SocketIO
import db
import secrets
from string import ascii_letters, digits, punctuation
import bcrypt

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

attempts = db.Attempts()
public_keys = db.Public()

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user = db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if attempts.is_blocked(username):
        return "Error: Your account has been blocked due to too many failed login attempts"

    #password verification
    password = request.json.get("password").encode('utf-8')
    verify = bcrypt.kdf(password=password, salt=user.salt, desired_key_bytes=60, rounds=200)
    if verify != user.password:
        attempts.set_failed(username)
        if attempts.is_blocked(username):
            return "Too many failed login attempts, your account has been blocked"
        
        return "Error: Password does not match!"
    attempts.reset(username)

    return url_for('home', username=request.json.get("username"), friends=request.json.get("friends"), received=db.get_received(username), pending=db.get_pending(username))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")
    public = request.json.get("public")
    print(username)
    print(password)
    print(public)

    #hash received password
    password = password.encode('ascii')

    salt = bcrypt.gensalt()
    hash = bcrypt.kdf(password=password, salt=salt, desired_key_bytes=60, rounds=200)

    if db.get_user(username) is None:
        db.insert_user(username, hash, salt, public)
        # public_keys.add_key(username, public)
        attempts.reset(username)
        return url_for('home', username=username, friends=request.json.get("friends"), received=db.get_received(username), pending=db.get_pending(username))
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    if request.args.get("username") is None:
        abort(404)

    username=request.args.get("username")

    return render_template("home.jinja", username=username, friends=request.args.get("friends"), received=db.get_received(username), pending=db.get_pending(username))

if __name__ == '__main__':
    socketio.run(app, host="localhost", port=5000 ,debug=True, ssl_context=('localhost.crt', 'localhost.key'))

