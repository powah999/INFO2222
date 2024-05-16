'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, ForeignKey, Integer, Text, UniqueConstraint, DateTime, CheckConstraint, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, List
from datetime import datetime 
import enum


# data models
class Base(DeclarativeBase):
    pass

def mydefault(context):
    return context.get_current_parameters()["account"] 

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    salt: Mapped[str] = mapped_column(String)
    salt2: Mapped[str] = mapped_column(String)

    ALLOWED_ACCOUNTS = ('student', 'staff')
    account: Mapped[str] = mapped_column(String)

    STAFF_ROLES = ('N/A', 'academic', 'administrative staff', 'admin user')
    staff_role: Mapped[str] = mapped_column(String, default='N/A')

    #current user permission to post articles / message people
    can_post: Mapped[bool] = mapped_column(Boolean, default=True)
    can_message: Mapped[bool] = mapped_column(Boolean, default=True)

    friends: Mapped[List["Friend"]] = relationship('Friend', secondary='link')
    
    articles: Mapped[List["Article"]] = relationship("Article", backref='author')
    comment: Mapped[List["Comment"]] = relationship("Comment", backref='author')

    def __repr__(self):
        return f"(Username: {self.username}, Password: {self.password}, Salt: {self.salt})"     

    __table_args__ = (CheckConstraint(account.in_(ALLOWED_ACCOUNTS), name='check_valid_account_type'), 
                      CheckConstraint(staff_role.in_(STAFF_ROLES), name ='check_valid_role'),
                      )


# existing friends
class Friend(Base):
    __tablename__ = "friend"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    
    friend_of: Mapped[List[User]] = relationship(User, secondary='link')

    def __repr__(self):
        return f"{self.username}"
    

class Link(Base):
    __tablename__ = 'link'

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), primary_key=True)
    friend_id: Mapped[int] = mapped_column(Integer, ForeignKey('friend.id'), primary_key=True)
    
class Request(Base):
    __tablename__ = "request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String)
    receiver: Mapped[str] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint('sender', 'receiver', name='_sender_receiver_uc'),
    )



class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String)
    receiver: Mapped[str] = mapped_column(String)
    history: Mapped[str] = mapped_column(String)

"""
class Students(Base):
    __tablename__ = "students"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)

class Staff(Base):
    __tablename__ = "staff"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    role: Mapped[str] = 

"""

class Article(Base):
    __tablename__ = 'article'

    id: Mapped[int] = mapped_column(Integer, primary_key = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    #author = Mapped[str] = mapped_column(, default="Anonymous")
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String, default=datetime.today().strftime("%d %B, %Y"))
    file_name: Mapped[str] = mapped_column(String, default='')
    
    comments: Mapped[List["Comment"]] = relationship("Comment", backref='post')

class Comment(Base):
    __tablename__ = 'comment'

    id: Mapped[int] = mapped_column(Integer, primary_key = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey('article.id'), nullable=False)
    
    #author = Mapped[str] = mapped_column(String, default="Anonymous")
    content: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String, default=datetime.today().strftime("%d %B, %Y"))


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
        self.dict: Dict[int, list[str]] = {}
        self.history = {}

    def create_room(self, sender: str, receiver) -> int:
        room_id = self.counter.get()
        self.dict[room_id] = [(sender, receiver), sender]
        self.history[(room_id,sender)] = []
        print(f'\nCreated room\ndict: {self.dict}')
        print(f'history: {self.history}\n')
        return room_id
    
    def join_room(self,  sender: str, receiver, room_id: int) -> int:
        if room_id not in self.dict.keys():
            return
        
        flag = False
        for key, lst in self.dict.items():
            check = lst[0]
            if sender in check and receiver in check:
                flag = True
                break

        if flag == False:
            return

        if len(self.dict[room_id]) < 3:
            self.dict.get(room_id).append(sender)
            self.history[(room_id,sender)] = []
            print(f'\Joined room\ndict: {self.dict}')
            print(f'history: {self.history}\n')
        else:
            print("\nRoom full!\n")
        print(self.dict)

        num = len(self.dict[room_id])

        return num

    def leave_room(self, user, room_id):
        if room_id not in self.dict.keys():
            return
        if user not in self.dict[room_id]:
            return
        
        self.dict[room_id].remove(user)
        print(self.dict)

        num = len(self.dict[room_id])

        if num <= 1:
            del self.dict[room_id]

    def delete_history(self, room_id, username):
        tuple = (room_id, username)
        print(f' history: {self.history}\n')
        print(tuple)
        print(f'Deleted history: {self.history.get(tuple)}\n')

        if tuple not in self.history.keys():
            return
        
        history = self.history.pop(tuple)

        return history

    # gets the room id from a user
    def room_exists(self, search_str):
        for key, lst in self.dict.items():
            if search_str in lst:
                return key 
        return None
    

    def unique_room_exists(self, sender, receiver):
        print(self.dict)
        for key, lst in self.dict.items():
            check = lst[0]
            if sender in check and receiver in check:
                return key
        return False
    
    def friend_in_room(self, user, friend,room_id):
        room = self.dict.get(room_id)

        if user in room[0] and friend in room[0]:
            if friend in room:
                return True
        return False

    def append_message(self, room_id, message, username):
        tuple = (room_id, username)
        if tuple not in self.history.keys():
            return
        
        self.history[tuple].append(message)
        print(f'\nAppended message\n')
        print(f'history: {self.history}\n')


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
    