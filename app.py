'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for
from flask_socketio import SocketIO
import db
import secrets

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
   # status = request.json.get("status")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if user.password != password :
        return "Error: Password does not match!"

    return url_for('home', username=request.json.get("username"), friends=request.json.get("friends"))


#handles a post request when the user sends friend
def accept_friend():
    if not request.is_json:
        abort(404)
    
    username = request.json.get("username")
    user =  db.get_user(username)
    


'''
@app.route("/login/user", methods=["POST"])
def dislay_friends():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    #user =  db.get_user(username)
    
    #friend_list = request.json.get(username + "friends")
    #friends = db.get_friend_list(user)

    return url_for('home', friend_list=request.json.get(username + "friends"))
'''

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
    
    #add username and password security requirements here

    if db.get_user(username) is None:
        db.insert_user(username, password)
        return url_for('home', username=username, friends=request.json.get("friends"))
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

    return render_template("home.jinja", username=request.args.get("username"), friends=request.args.get("friends"))



if __name__ == '__main__':
    app.debug=True
    socketio.run(app)

