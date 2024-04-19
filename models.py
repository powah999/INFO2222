'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, ForeignKey, Integer, Boolean, Column, MetaData, Table, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, List


# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    salt = Column(String)

    friends = relationship('Friend', secondary='link')

    def __repr__(self):
        return f"(Username: {self.username}, Password: {self.password}, Salt: {self.salt})"     



# existing friends
class Friend(Base):
    __tablename__ = "friend"

    id = Column(Integer, primary_key=True)
    username = Column(String,unique=True)
    
    friend_of = relationship(User, secondary='link')

    def __repr__(self):
        return f"{self.username}"
    

class Link(Base):
    __tablename__ = 'link'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('friend.id'), primary_key=True)
    
class Request(Base):
    __tablename__ = "request"

    id = Column(Integer, primary_key=True)
    sender = Column(String)
    receiver = Column(String)

    __table_args__ = (
        UniqueConstraint('sender', 'receiver', name='_sender_receiver_uc'),
    )

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
#number of failed login attempts for a user
class Attempts():
    def __init__(self):
        #dictionary keeps track of each user's current failed attempts
        #key = username
        #value = number of failed attempts since last successful login
        self.dict: Dict[str, int] = {}
        
    def set_failed(self, user: str):
        if user in self.dict:

            self.dict[user] += 1
        else: 

            self.dict[user] = 0
    
    def reset(self, user: str):
        self.dict[user] = 0
    
    def get_attempts(self, user: str):
        if user not in self.dict:
            return
        return self.dict[user]
    
    def is_blocked(self, user: str):
        if user not in self.dict:
            return False
        return (self.dict[user] > 3)
    
#dictionary to store public keys for all users
class Public():
    def __init__(self):
        self.keys: Dict[str, str] = {}

    def add_key(self, username, key):
        self.keys[username] = key

    def get_key(self, username):
        if username not in self.keys.keys():
            return
        
        return self.keys[username]
    



# class Pending(Base):
#     __tablename__ = "pending"

#     id = Column(Integer, primary_key=True)
#     sender: Mapped[str] = mapped_column(ForeignKey("user.username"), primary_key=True)
#     receiver: Mapped[str] = mapped_column(String)

#     user: Mapped["User"] = relationship(back_populates="pending")

# #every user and friend has a corresponding message history / room id
# #every room id has 2 users associated with it + their chat history
# #when 2 users first start chatting, chat history is empty. Append/log every message to chat history as they are sent
# #when user clicks chat button next to friend name, join room checks if online to allow them to send messages, else just view chat history




# """
# class Request():
#     def __init__(self):
#         self.received: Dict[str, list] = {}
#         self.sent: Dict[str, list] = {}
    
#     def send_request(self, user: str, receiver: str):
#         self.sent[user].append(receiver)
#         self.received[receiver].append(user)
    
#     def accept_request(self, user: str, receiver: str):

#     def decline_request(self, user: str, receiver: str):
# """

    

# # stateful counter used to generate the room id
# class Counter():
#     def __init__(self):
#         self.counter = 0
    
#     def get(self):
#         self.counter += 1
#         return self.counter


  

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps an online user to a room_id to join a room 
        #key = user name
        #value room_id
        self.dict: Dict[str, int] = {}
        # dictionary that maps the 2 users/friends to the room id
        # for example self.dict[{"John", "Bob"}] -> gives you the room id of 
        # the room where John/Bob will chat
        self.room_id: Dict[set, int] = {}
        
        #every chat session (room id) between 2 users has a chat history
        self.history: Dict[set, list] = {} #key = 2 users #value = message history

    #create room id when friend is not online
    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.room_id[{sender, receiver}] = room_id
        return room_id
    
    def join_room(self,  user: str, room_id: int) -> int:
        self.dict[user] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        
        room_id = self.dict[user]
        del self.dict[user]

        if room_id not in self.dict.values():
            #both users left room, remove session id
            for pair, id in self.room_id.items():
                if id == room_id:
                    del self.room_id[pair]
                    break

    # gets the room id from 2 users/friends
    def get_room_id(self, sender: str, receiver: str):
        if {sender, receiver} not in self.room_id.keys():
            return None
        return self.room_id[{sender, receiver}]
    
    def get_receiver(self, username, room_id):
         for pair, id in self.room_id.items():
                if id == room_id:
                    for user in pair:
                        if username != user:
                            return user

    # get message history between 2 users
    def get_history(self, sender: str, receiver: str):
        if {sender, receiver} not in self.history.keys():
            return None
        return self.history[{sender, receiver}]
    
    # add new message to history
    def add_message(self, message: str, sender: str, receiver: str):
        if {sender, receiver} not in self.history.keys():
            return None
        self.history[{sender, receiver}].append(message)

    # delete history between 2 users
    def del_history(self, sender: str, receiver: str): 
        if {sender, receiver} not in self.history.keys():
            return None
        del self.history[{sender, receiver}]

    def create_history(self, sender: str, receiver: str):
        self.dict[{sender, receiver}] = [] #make room_id first element?