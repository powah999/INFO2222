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

engine = create_engine("sqlite:///database/main.db", echo=True)
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, hashed_password: str, salt: str):
    with Session(engine) as session:
        user = User(username=username, password=hashed_password, salt=salt)
        session.add(user)
        session.commit()
        return 0

#add friends to user's friendlist
def add_friend(name_a: str, name_b: str):
    with Session(engine) as session:
        user_a = session.query(User).filter_by(username=name_a).first()
        user_b = session.query(User).filter_by(username=name_b).first()

        if not (user_a and user_b):
            return 'Users does not exist.'

        temp_b = session.query(Friend).filter_by(username=name_b).first()
        if temp_b is not None:
            friendship_exists = session.query(Link).filter_by(user_id = user_a.id, friend_id = temp_b.id).first()
            if friendship_exists:
                return 'Friendship already exists.'

        friend_a = session.query(Friend).filter_by(username=name_a).first()
        friend_b = session.query(Friend).filter_by(username=name_b).first()

        if not friend_a:
            friend_a = Friend(username=name_a)
            user_b.friends.append(friend_a)
        else:
            user_b.friends.append(friend_a)

        if not friend_b:
            friend_b = Friend(username=name_b)
            user_a.friends.append(friend_b)
        else:
            user_a.friends.append(friend_b)

        session.commit()
        
        return 0

#remove friend
def remove_friend(name_a: str, name_b: str):
    with Session(engine) as session:
        user_a = session.query(User).filter_by(username=name_a).first()
        user_b = session.query(User).filter_by(username=name_b).first()

        if not (user_a and user_b):
            return 'One or both users does not exist'

        temp_a = session.query(Friend).filter_by(username=name_a).first()
        temp_b = session.query(Friend).filter_by(username=name_b).first()

        friendship_exists_a = session.query(Link).filter_by(user_id = user_a.id, friend_id = temp_b.id).first()
        friendship_exists_b = session.query(Link).filter_by(user_id = user_b.id, friend_id = temp_a.id).first()

        if (not friendship_exists_a) or (not friendship_exists_b):
            return 'Friendship does not exist.'

        session.delete(friendship_exists_a)
        session.delete(friendship_exists_b)

        session.commit()
        return 0

#adds request
def add_request(sender_name: str, receiver_name:str):
    with Session(engine) as session:
        sender = session.query(User).filter_by(username=sender_name).first()
        receiver = session.query(User).filter_by(username=receiver_name).first()

        if not (sender and receiver):
            return 'One or both users do not exist.'
        
        check_request = session.query(Request).filter_by(sender=receiver_name,receiver=sender_name).first()
        if check_request:
            return 'The receiver has already sent a request to the user.'


        request = session.query(Request).filter_by(sender=sender_name,receiver=receiver_name).first()

        if not request:
            request = Request(sender=sender_name, receiver=receiver_name)
            session.add(request)
        else:
            return 'Request already exists.'

        session.commit()

        return 0

# Method: Calls add_friend(), if successful, deletes the request
def accept_request(sender_name: str, receiver_name: str):
    with Session(engine) as session:
        print("TESTING?????")
        request = session.query(Request).filter_by(sender=sender_name,receiver=receiver_name).first()

        if not request:
            return 'Request does not exist'
        
        session.commit()
        
        flag = add_friend(sender_name, receiver_name)

        if flag != 0:
            return flag
        else:
            session.delete(request)
            session.commit()
            return 0

# Deletes the request
def decline_request(sender_name: str, receiver_name: str):
    with Session(engine) as session:
        
        request = session.query(Request).filter_by(sender=sender_name,receiver=receiver_name).first()

        if not request:
            return 'Request does not exist'
        
        session.delete(request)

        session.commit()

        return 0
        
# Returns a list of sent requests (list[str], each element is a friendname)
def get_sent(username: str):
    with Session(engine) as session:
        users = session.query(Request).filter_by(sender = username).all()

        if not users:
            print("\n User or request does not exist \n")
            return -1
        
        return users
    
# Returns a list of received requests (list[str], each element is a friendname)
def get_received(username: str):
    with Session(engine) as session:
        users = session.query(Request).filter_by(receiver = username).all()

        if not users:
            print("\n User or request does not exist \n")
            return -1
        
        return users

# Returns a list of friend names (list[str])
def get_friends(username):
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username).first()

        if not user:
            print("\n User or friend list does not exist \n")
            return -1
        
        return user.friends
    

        
# Gets a user's username from the database
def get_user(username: str):
    with Session(engine) as session:

        user = session.query(User).filter_by(username=username).first()
        if not user:
            print("\n User does not exist \n")
            return -1

        return user
