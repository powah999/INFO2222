from db import *
from models import *
from sqlalchemy.orm import Session


# I used this file to test db.py functions

session = Session(bind=engine)


insert_user('b', '1', '1', '1', 'student')
insert_user('c', '1', '1', '1', 'staff', 'admin user')
insert_user('d', '1', '1', '1', 'staff','administrative staff')
insert_user('e', '1', '1', '1', 'staff', 'academic')

'''
create_article('hello', 'First post', 'blah')
create_article('b', 'Second post', 'blah')
create_article('c', 'Third post', 'blah')
'''
