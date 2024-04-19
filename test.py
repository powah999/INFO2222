from db import *
from models import *
from sqlalchemy.orm import Session


# I used this file to test db.py functions

session = Session(bind=engine)


insert_user('a', '1', '1')
insert_user('b', '1', '1')
insert_user('c', '1', '1')
insert_user('d', '1', '1')

add_request(sender_name='a', receiver_name='b')
accept_request(sender_name='a', receiver_name='b')

add_request(sender_name='a', receiver_name='d')
decline_request(sender_name='a', receiver_name='d')