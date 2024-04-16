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
        user = session.get(User, username)
        new = Friend(username=friend_username)
        user.friends.append(new)
        friend = session.get(User, friend_username)
        new = Friend(username=username)
        friend.friends.append(new)
        session.merge(user)
        session.merge(friend)
        session.commit()


#add friend request to user's requests list
def make_request(sender, receiver):
    with Session(engine) as session:
        new_pending = Pending(sender=sender, receiver=receiver)
        new_received = Received(sender=sender, receiver=receiver)
        session.add(new_pending)
        session.add(new_received)
        session.commit()

        return new_pending

#remove friend request from user's requests list
def remove_request(sender_name, receiver_name):
    with Session(engine) as session:
        sender = session.get(User, sender_name)
        to_remove = None
        for request in sender.pending:
            if request.receiver == receiver_name:
                to_remove = request
                break
        if to_remove != None:
            sender.pending.remove(to_remove)
            session.commit()
        
        receiver = session.get(User, receiver_name)
        to_remove = None
        for request in receiver.received:
            if request.sender == sender_name:
                to_remove = request
                break
        
        if to_remove != None:
            receiver.received.remove(to_remove)
            session.commit()
        
        
#get a list of all of user's friends
def get_friends(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.friends

#get a list of all of user's pending friend requests
def get_pending(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.pending

#get a list of all of user's received friend requests
def get_received(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        return user.received