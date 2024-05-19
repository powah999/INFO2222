'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, session, redirect, send_from_directory
from flask_socketio import SocketIO
import db
import secrets
from string import ascii_letters, digits, punctuation
import bcrypt
import datetime
import bleach
import os
from flask_session import Session

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
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_PATH'] = 'uploads'
socketio = SocketIO(app)


server_session = Session(app)

# don't remove this!!
import socket_routes
from socket_routes import public_keys, session_ids, session_tokens

attempts = db.Attempts()

def comparestrings(string_a, string_b):
    li = []
    string_a = set(string_a)

    for char in string_a:
        if char not in string_b:
            li.append(char)
    if len(li) > 0:
        return f'Your username should only contain alphanumeric ("a" or "1"), underscore ("_"), period ("."), and space " " characters! '
    return True

# index page
@app.route("/")
def index():
    return render_template("login.jinja")

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


    #input validation against xss
    username = data.get('username')
    string_b = bleach.clean(data.get('username'))
    check = comparestrings(username, string_b)
    if check != True:
        return check
    
    if data.get('requestType') == 'salt':
        user = db.get_user(username)
        if type(user) == int:
            return 'User does not exist'
        return user.salt2

    
    if attempts.is_blocked(username):
        return "Error: Your account has been blocked due to too many failed login attempts"
    
    if username in session_ids.keys() and session_ids.get(username) != None:
        return 'Username already has a session'

    if data.get('requestType') == 'password' or data.get('requestType') == 'key':
        #user verification
        user = db.get_user(username)
        if user == -1:
            attempts.set_failed(username)
            if attempts.is_blocked(username):
                return "Too many failed login attempts, your account has been blocked"
            else:
                return "Error: User does not exist!"
            
        #password verification
        password = data.get("password").encode('utf-8')
        print(f'password = {password}')
        verify = bcrypt.kdf(password=password, salt=user.salt, desired_key_bytes=60, rounds=200)
        if verify != user.password:
            attempts.set_failed(username)
            if attempts.is_blocked(username):
                return "Too many failed login attempts, your account has been blocked"
            return "Error: Password does not match!"
        
        attempts.reset(username)

        print("\n\nHHHHHHHHHHHHHHHHHHHHHHHHH\n\n")

        #if request is 'password',only verifies user and password
        #if request 'key', server gets public key and sets a session
        if data.get('requestType') == 'key':
                public = data.get('public')
                public_b = bleach.clean(data.get("public"))
                check = comparestrings(public, public_b)
                if check != True:
                    return check
                

                print('__________________')
                print(f"\n\nUSER {username}'s public key:\n\n {public}\n\n")
                print('__________________')

                public_keys.add_key(username, public)

                session['username'] = username
                session['token'] = secrets.token_hex(60)
                session_tokens[username] = session.get('token')
                session_ids[username] = None

                #return url_for('home', username=username, friends=db.get_friends(username), received=db.get_received(username), pending=db.get_sent(username))
                return url_for('articles', username=username)
        else:
            return "pass"
    
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
    #input validation against xss
    username = data.get('username')
    string_b = bleach.clean(data.get('username'))

    print(f"username: {username}")
    print(f'string_b: {string_b}')
    check = comparestrings(username, string_b)
    if check != True:
        return check

    if data.get('requestType') == 'password' or data.get('requestType') == 'key':
        if db.get_user(username) == -1:
            if data.get('requestType') == 'key':
                password = data.get("password").encode('ascii')
                print(f'password  SIGNUP= {password}')
                salt2 = data.get("salt")
                print(f'\nsalt: {salt2}\n')
                public = data.get('public')
                print(f"public: {public}")

                account = data.get('account')
                print(f"account: {account}")
                if account != "student":
                    staff_role = account
                    
                    account = "staff"
                else:
                    staff_role = "N/A"

                print(f"staff_role")
                print(f"account")

                public_b = bleach.clean(data.get("public"))
                print(f'string_b: {string_b}')
                check = comparestrings(public, public_b)
                if check != True:
                    return check
                
                print('__________________')
                print(f"\n\nUSER {username}'s public key:\n\n {public}\n\n")
                print('__________________')

                salt = bcrypt.gensalt()
                hash = bcrypt.kdf(password=password, salt=salt, desired_key_bytes=60, rounds=200)

                db.insert_user(username, hash, salt, salt2, account, staff_role)
                public_keys.add_key(username, public)

                attempts.reset(username)

                session['token'] = secrets.token_hex(60)
                session_tokens[username] = session.get('token')

                session['username'] = username
                session_ids[username] = None

                #return url_for('home', username=username, friends=db.get_friends(username), received=db.get_received(username), pending=db.get_sent(username))
                return url_for('articles', username=username)
            else:
                return 'pass'
        else:
            return 'Error: User already exists!'
    else:
        return 'requestType aint valid bruh'


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# messages page
@app.route("/home")
def home():
    username = request.args.get("username")

    if request.args.get("username") is None:
        abort(404)
    
    if 'username' not in session or ('token' not in session):
        print('\nusername or token not in session\n')
        return redirect(url_for('login'))

    if session.get('username') != username:
        print('\n your session is not equal to the users actual session\n')
        return redirect(url_for('login'))    
    # uncomment once final
    # if session.get('username') not in session_tokens.keys() or (session.get('token') != session_tokens.get(session.get('username'))):
    #     return redirect(url_for('login'))    

    username = session.get("username")
    friends = db.get_friends(username)
    
    friend_status = {}
    for friend in friends:
        if friend.username not in session_ids.keys():
            friend_status[friend.username] = 'offline'
        else:
            friend_status[friend.username] = 'online'

    friend_roles = {}
    for friend in friends:
        friend_info = db.get_user(friend.username)
        account = friend_info.account
        if account == "staff":
            friend_roles[friend.username] = friend_info.staff_role
        else:
            friend_roles[friend.username] = account

    return render_template("home.jinja", 
                           username=username, 
                           friends=friends, 
                           received=db.get_received(username), 
                           pending=db.get_sent(username), 
                           friend_status=friend_status, 
                           friend_roles=friend_roles,
                           account = db.get_user(username).account
                           )


#home page, contains all posts
@app.route("/articles")
def articles():
    username = request.args.get("username")

    if request.args.get("username") is None:
        abort(404)
        
    if 'username' not in session or ('token' not in session):
        print('\nusername or token not in session\n')
        return redirect(url_for('login'))

    if session.get('username') != username:
        print('\n your session is not equal to the users actual session\n')
        return redirect(url_for('login'))

    friends = db.get_friends(username)
    
    friend_status = {}
    for friend in friends:
        if friend.username not in session_ids.keys():
            friend_status[friend.username] = 'offline'
        else:
            friend_status[friend.username] = 'online'

    friend_roles = {}
    for friend in friends:
        friend_info = db.get_user(friend.username)
        account = friend_info.account
        if account == "staff":
            friend_roles[friend.username] = friend_info.staff_role
        else:
            friend_roles[friend.username] = account
    
    articles = db.get_all_articles()

    return render_template("articles.jinja", 
                           articles=articles, 
                           username=username, 
                           account=db.get_user(username).account, 
                           can_post=db.get_user(username).can_post,
                           can_chat=db.get_user(username).can_message, 
                           role=db.get_user(username).staff_role
                           )

@app.route("/navbar")
def navbar():
    articles = db.get_all_articles()
    user = db.get_user(session['username'])

    return render_template("navbar.jinja", username=session["username"], articles=articles, account=user.account)

@app.route("/newarticle")
def new_article():
    user = db.get_user(session["username"])

    if user.can_post:
        return render_template("newarticle.jinja", username=session["username"])
    
    print("User cannot make posts")
    return "User cannot make posts"


@app.route("/logout")
def logout():
    if (session["username"]):
        username = session["username"]
        session_ids.pop(username, None)
        public_keys.keys.pop(username, None)
        session_tokens.pop(username, None)
        session.clear()

    return redirect(url_for("login"))


@app.route("/upload", methods=["POST"])
def upload():
    title = request.form.get('title')
    content = request.form.get('content')
    file = request.files.get('file')

    user = db.get_user(session["username"])

    if not title or not content:
        print("Cannot have empty text fields")
        return "Fail"
    
    if title == "" or content == "":
        print("Cannot have empty text fields")
        return "Fail"
        
    if file and file.filename != '':
        file_name = f"{user.id}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_PATH'], file_name))
    elif file.filename == "":
        print("no file was uploaded")
        file_name = ""
    else:
        print("Failed to upload file")
        return "Fail"
    
    if not db.create_article(username=session["username"], title=title, content=content, file_name=file_name):
        print("Could not create new article")
        return "Fail"
        
    return url_for("articles", username=session["username"])

@app.route("/reupload", methods=["POST"])
def reupload():
    title = request.form.get('title')
    content = request.form.get('content')
    file = request.files.get('file')
    article_id = request.form.get("article_id")

    user = db.get_user(session["username"])

    if (not title and not content) or not article_id:
        return "Fail"
    
    if title == "" or content == "" or article_id == "":
        return "Fail"
        
    if file and file.filename != '':
        file_name = f"{user.id}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_PATH'], file_name))
    elif file.filename == "":
        print("no file was uploaded")
        file_name = ""
    else:
        return "Fail"
    
    success = db.edit_article(article_id=article_id, new_title=title, new_content=content, file_name=file_name)
    if not success:
        return "Fail"
        #return "Could not edit article"
    return success
    

@app.route('/upload/<filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename, as_attachment=True)

@app.route('/users')
def users():
    user = db.get_user(session["username"])
    print(session["username"])
    print(user.username)
    print(user.account)
    if user.account == "staff":
        return render_template("users.jinja", username = session["username"], account=user.account, users=db.get_all_users())

    return "Students are not authorised to this page"

if __name__ == '__main__': 
    socketio.run(app, host="localhost", port=5000 ,debug=False, ssl_context=('localhost.crt', 'localhost.key'))
