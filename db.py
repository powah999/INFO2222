'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, hashed_password: str, salt: str, public: str):
    with Session(engine) as session:
        user = User(username=username, password=hashed_password, salt=salt, public=public) ####
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

#add friends to user's friendlist
def add_friend(username, friend_username):
    with Session(engine) as session:
        #user = session.get(User, username)
        new_friend = Friend(username=friend_username, user_username=username)
        session.add(new_friend)
        session.commit()

#add friend request to user's requests list
def add_request(username, friend_username, is_received: bool):
    with Session(engine) as session:
        #user = session.get(User, username)
        new_request = Request(username=username, friend_username=friend_username, is_received=is_received)
        session.add(new_request)
        session.commit()

#remove friend request from user's requests list
def remove_request(username, friend_username):
    with Session(engine) as session:
        user = session.get(User, username)
        to_remove = None
        for request in user.requests:
            if request.friend_username == friend_username:
                to_remove = request
                break
        
        if to_remove != None:
            user.requests.remove(to_remove)
            session.commit()

#get a list of all of user's friends
def get_friends(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.friends

#get a list of all of user's pending or received friend requests
def get_friend_requests(username: str, received: bool):
    with Session(engine) as session:
        requests = []
        user = session.get(User, username)
        for request in user.requests:
            if received and request.is_received: #want all received requests
                requests.append(request)
            elif (not received) and (not request.is_received): #want all pending request
                requests.append(request)
        
        return user.requests
