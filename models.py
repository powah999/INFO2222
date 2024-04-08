'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, ForeignKey, INTEGER, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, List

# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base): 
    __tablename__ = "user"
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String(60)) #hash (kdf) of password
    salt: Mapped[str] = mapped_column(String)
    #attempts: Mapped[int] = mapped_column(INTEGER, default=0) #number of failed login attempts

    #status: Mapped[bool] = mapped_column(Boolean) #Online if True

    friends: Mapped[List["Friend"]] = relationship(back_populates="user") #list of friends
    requests: Mapped[List["Request"]] = relationship(back_populates="user") #received friend requests

    #def __init__(self):
        #self.attempts = 0

# existing friends
class Friend(Base):
    __tablename__ = "friend"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    #status: Mapped[bool] = mapped_column(Boolean)
    user_username: Mapped[str] = mapped_column(ForeignKey("user.username"))

    user: Mapped["User"] = relationship(back_populates="friends")

    def __str__(self):
        return f'{self.username}'

# friend requests
class Request(Base):
    __tablename__ = "request"

    username: Mapped[str] = mapped_column(ForeignKey("user.username"))
    #sent: Mapped[str] = mapped_column(String)
    friend_username: Mapped[str] = mapped_column(String, primary_key=True) #name of friend who sent/received request
    is_received: Mapped[bool] = mapped_column(Boolean) #if true: received, if false: sent/pending

    user: Mapped["User"] = relationship(back_populates="requests")

"""
class Request():
    def __init__(self):
        self.received: Dict[str, list] = {}
        self.sent: Dict[str, list] = {}
    
    def send_request(self, user: str, receiver: str):
        self.sent[user].append(receiver)
        self.received[receiver].append(user)
    
    def accept_request(self, user: str, receiver: str):

    def decline_request(self, user: str, receiver: str):
"""

#number of failed login attempts for a user
class Attempts():
    def __init__(self):
        #dictionary keeps track of each user's current failed attempts
        #key = username
        #value = number of failed attempts since last successful login
        self.dict: Dict[str, int] = {}

    def set_failed(self, user: str):
        self.dict[user] += 1
    
    def reset(self, user: str):
        self.dict[user] = 0
    
    def get_attempts(self, user: str):
        if user not in self.user.keys():
            return
        return self.dict[user]
    
    def is_blocked(self, user: str):
        if user not in self.attempts.keys():
            return
        return self.dict[user] > 3
    

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
    
