'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, session, redirect, jsonify
from flask_socketio import SocketIO
import db
import secrets
from string import ascii_letters, digits, punctuation
import bcrypt
import datetime
import bleach

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_SECURE=True, #limits cookies to HTTPS traffic only
    SESSION_COOKIE_HTTPONLY=True, #prevents contents of cookies from being read with JavaScript
    SESSION_COOKIE_SAMESITE='Lax', #prevents CSRF (unless web browser contains external link/GET request)
    SESSION_PERMANENT_LIFETIME=datetime.timedelta(hours=1), #session token expiry time
    )

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes
from socket_routes import public_keys, session_ids

attempts = db.Attempts()


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

    data = request.json

    username = bleach.clean(data.get('username'))
    
    if attempts.is_blocked(username):
        return "Error: Your account has been blocked due to too many failed login attempts"
    


    val = session_ids.get(username)
    if val != None:
        if session.get('id'):
            if session.get('id') != val:
                return "The username's session id is different from yours"
        else:
            return "The username already has a session id, while you dont even have one"


    if data.get('requestType') == 'password':
        user = db.get_user(username)
        if user == -1:
            attempts.set_failed(username)
            if attempts.is_blocked(username):
                return "Too many failed login attempts, your account has been blocked"
            else:
                return "Error: User does not exist!"
            
        #password verification
        password = data.get("password").encode('utf-8')
        verify = bcrypt.kdf(password=password, salt=user.salt, desired_key_bytes=60, rounds=200)
        if verify != user.password:
            attempts.set_failed(username)
            if attempts.is_blocked(username):
                return "Too many failed login attempts, your account has been blocked"
            return "Error: Password does not match!"
        
        attempts.reset(username)

        return 'pass'
            
        
    elif data.get('requestType') == 'key':
            public = bleach.clean(data.get("public"))

            print('__________________')
            print(f"\n\nUSER {username}'s public key:\n\n {public}\n\n")
            print('__________________')

            public_keys.add_key(username, public)

            if val == None:
                session['id'] = secrets.token_hex(120) #120 bytes -> 240 hexadecimal characters -> 10^145 permutations
                session_ids[username] = session.get('id')

                print(f"\n\nLOGINNN SESSION ID {session.get('id')}\n\n")

            return url_for('home', username=username, friends=db.get_friends(username), received=db.get_received(username), pending=db.get_sent(username), session_id=session.get('id'))
    
    else:
        return 'requestType aint valid bruh'
    

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)

    data = request.json
    username = bleach.clean(data.get('username'))

    if data.get('requestType') == 'password':
        if db.get_user(username) == -1:        
            return 'pass'
        else:
            return 'Error: User already exists!'
        
    elif data.get('requestType') == 'key':
            password = data.get("password").encode('ascii')
            public = bleach.clean(data.get("public"))

            print('__________________')
            print(f"\n\nUSER {username}'s public key:\n\n {public}\n\n")
            print('__________________')

            salt = bcrypt.gensalt()
            hash = bcrypt.kdf(password=password, salt=salt, desired_key_bytes=60, rounds=200)

            db.insert_user(username, hash, salt)
            public_keys.add_key(username, public)
            attempts.reset(username)

            session['id'] = secrets.token_hex(120) #120 bytes -> 240 hexadecimal characters -> 10^145 permutations
            session_ids[username] = session.get('id')

            return url_for('home', username=username, friends=db.get_friends(username), received=db.get_received(username), pending=db.get_sent(username), session_id=session.get('id'))
    else:
        return 'requestType aint valid bruh'


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    username = request.args.get("username")
    session_id = request.args.get("session_id")

    if request.args.get("username") is None:
        abort(404)
    if request.args.get("session_id") is None:
        return 'NO SESSION ID'


    #a = request.cookies.get("username")
    #if a != request.args.get("username") or a == None:


    username=request.args.get("username")
    print('\n\n')
    print(session_ids)
    print('\n \n')

    if session.get('id') == None:
        return 'YOU DONT EVEN HAVE A SESSION ID'

    val = session_ids.get(username)

    if val != None:
        if session.get('id') != val:
            return 'SID stored in server NOT EQUAL to your SESSION SID'
        elif val != session_id:
            return 'SID stored in server NOT EQUAL to your URL SID'
        # elif val != request.cookies.get('room_id'):
        #     return 'HUH'
    else:
        return 'relogin'


    return render_template("home.jinja", username=username, friends=db.get_friends(username), received=db.get_received(username), pending=db.get_sent(username), session_id=session.get('id'))

if __name__ == '__main__':
    socketio.run(app, host="localhost", port=5000 ,debug=True, ssl_context=('localhost.crt', 'localhost.key'))
