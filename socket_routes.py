'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room, SocketIO
from flask import request, session
import bleach


try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room, Public


import db

room = Room()
public_keys = db.Public()
session_ids = {}

# when the client connects to a socket
# this event is emitted when the io() function is called in JS

def cleaner(sender_name = -99, receiver_name =-99, message = -99, room_id=-99, pubkey_client=-99, session_id=-99):
    
    temp = []

    if sender_name != -99:
        if type(sender_name) != str:
            return 'Invalid username/sender name: socket emit'
        sender_name = bleach.clean(sender_name)
        temp.append(sender_name)

    if receiver_name != -99:
        if type(receiver_name) != str:
            return 'Invalid receiver name: socket emit'
        receiver_name = bleach.clean(receiver_name)
        temp.append(receiver_name)

    if message != -99:
        if type(message) != dict:
            return 'Invalid message: socket emit'
        
        for key, value in message.items():
            if type(message[key]) == str:
                message[key] = bleach.clean(value)
        temp.append(message)
        
    if room_id != -99:
        if type(room_id) != int:
            return 'Invalid socket emit'
        temp.append(room_id)

    if pubkey_client != -99:
        if type(pubkey_client) != str:
            return 'Invalid pubkey: socket emit'
        pubkey_client = bleach.clean(pubkey_client)
        temp.append(pubkey_client)

    if session_id != -99:
        val = session_ids.get(sender_name)
        if val != session_id:
            return 'Invalid session id: socket emit'
        temp.append(session_id)

    return temp

@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    session_id = request.cookies.get("session_id")

    print(session.get('id'))

    print('\nvs\n')

    print(session_ids.get(username))

    
    print('\nSESSION IDS:\n')
    print(session_ids)

    print(f"\nusername: {username} CONNECTED")
    print(f"room_id: {room_id}\n")
    print(f'session_id: {session_id}\n')

    if session.get('id') != session_ids.get(username):
        print('SESSION ID IS NOT EQUAL TO YOURS')
        raise ConnectionRefusedError('Connection refused.')
    
    if session_id is None or str(session_id) == 'None':
        print('NO SESSION ID')
        raise ConnectionRefusedError('Connection refused.')
    
    session_ids[username] = session_id

    print('APPENDED:\n')
    print(session_ids)
    print('\n')

    if room_id is None or username is None or session_id is None:
        return







    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (username,f"{username} has connected", "green", "announcement"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():

    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")

    session_ids.pop(username)
    
    print(f"\nusername: {username} DISCONNECTED")
    print(f"room_id: {room_id}\n")
    print(f"{session_ids}\n")

    if room_id is None or username is None:
        return

    emit("incoming", (username, f"{username} has disconnected", "red", "announcement"), to=int(room_id))

# send message event handler --> send to everyone but sender
@socketio.on("send")
def send(username, message, room_id, session_id):

    temp = cleaner(sender_name=username, message=message,room_id=room_id,session_id=session_id)
    if type(temp) != list:
        return temp
    username, message, room_id, session_id = temp

    print(f'\n\n{username} has sent message: {message}\n\n to room_id: {room_id}\n')

    emit("incoming", (username, message, "black", "msg"), to=room_id, include_self=False)


# leave room event handler
@socketio.on("leave")
def leave(username, room_id, session_id):

    # Checks whether the arguments are valid, returns error message if not.
    temp = cleaner(sender_name=username, room_id=room_id, session_id=session_id)
    if type(temp) != list:
        return temp
    username, room_id, session_id = temp
    

    emit("incoming", (username,f"{username} has left the room.", "red", "announcement"), to=room_id, include_self=False)
    leave_room(room_id)
    room.leave_room(username)

    print(f'\n\n {username} has left {room_id}\n')
    print(room.dict)

# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name, pubkey_client, session_id):

    temp = cleaner(sender_name=sender_name, receiver_name=receiver_name, pubkey_client=pubkey_client, session_id=session_id)
    if type(temp) != list:
        return temp
    sender_name, receiver_name, pubkey_client, session_id = temp

    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.get_room_id(receiver_name)
    pubkey = public_keys.get_key(sender_name)

    if pubkey != pubkey_client:
        pubkey = pubkey_client
        public_keys.add_key(sender_name, pubkey_client)

    # if the user is already inside of a room 
    if room_id is not None:
        print(f'\n\n{sender_name} has joined room {room_id}\n')
        print(f'\n\n Sending {receiver_name} the public key of {sender_name}: {pubkey}\n')     

        room.join_room(sender_name, room_id)
        join_room(room_id)

        emit("pubkey_first", {'pubkey': pubkey, 'guy': sender_name}, to=room_id, include_self=False)
        # emit to everyone in the room except the sender
        emit("incoming", (sender_name,f"{sender_name} has joined the room.", "green", "announcement"), to=room_id, include_self=False)
        # emit only to the sender
        emit("incoming", (sender_name,f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green", "announcement"))
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone

    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)

    print(f'\n\n{sender_name} has joined room {room_id}\n')
    emit("incoming", (sender_name,f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green", "announcement"), to=room_id)
    return room_id

@socketio.on("exchange")
def exchage(sender_name, receiver_name, pubkey_client, session_id):

    temp = cleaner(sender_name=sender_name, receiver_name=receiver_name, pubkey_client=pubkey_client, session_id=session_id)
    if type(temp) != list:
        return temp
    sender_name, receiver_name, pubkey_client, session_id = temp

    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.get_room_id(receiver_name)
    pubkey = public_keys.get_key(sender_name)

    if pubkey != pubkey_client:
        pubkey = pubkey_client
        public_keys.add_key(sender_name, pubkey_client)

    print(f'\n\n Sending {receiver_name} the public key of {sender_name}: {pubkey_client}\n')

    emit("pubkey_second", {'pubkey': pubkey, 'guy': sender_name}, to=room_id,include_self=False)


@socketio.on("send_request")
def send_request(sender_name, receiver_name, session_id):

    temp = cleaner(sender_name=sender_name, receiver_name=receiver_name, session_id=session_id)
    if type(temp) != list:
        return temp
    sender_name, receiver_name, session_id = temp

    #check if new friend already exists
    sender_friends = db.get_friends(sender_name)
    if sender_friends != -1:
        for friend in sender_friends:
            if friend.username == receiver_name:
                return "This person is already your friend!"
    else:
        return "This person does not exist"
    
    flag = db.add_request(sender_name, receiver_name)

    return flag
    
@socketio.on("accept")
def accept(sender_name, receiver_name, session_id):

    temp = cleaner(sender_name=sender_name, receiver_name=receiver_name, session_id=session_id)
    if type(temp) != list:
        return temp
    sender_name, receiver_name, session_id = temp

    flag = db.accept_request(sender_name, receiver_name)

    return flag


#decline friend request
@socketio.on("decline")
def decline(sender_name, receiver_name, session_id):

    temp = cleaner(sender_name=sender_name, receiver_name=receiver_name, session_id=session_id)
    if type(temp) != list:
        return temp
    sender_name, receiver_name, session_id = temp

    flag = db.decline_request(sender_name, receiver_name)

    return flag

# # add message to message history
# @socketio.on("history")
# def history(username, message, room_id):
#     room.add_message(message, username, room.get_receiver(username, room_id))

#join room event handler
#sent when the user joins a room
# @socketio.on("join")
# def join(sender_name, receiver_name):
#     sender = db.get_user(sender_name)
#     if sender == -1:
#         return "Unknown sender!"

#     receiver = db.get_user(receiver_name)
#     if receiver == -1:
#         return "Unknown receiver!"
    
#     #check if person you're chatting with is your friend
#     sender_friends = db.get_friends(sender_name)

#     exists = False
#     if sender_friends != -1:
#         for friend in sender_friends:
#             if friend.username == receiver_name:
#                 exists = True
#     else:
#         return f"{ receiver_name } does not exist!"
    
#     if not exists:
#         return f"{ receiver_name } is not your friend!"


    
    #emit public key of receiver to sender
    # emit("receiver key", keys.get_key(receiver_name))
    
    #if friend is online, join room to allow them to send messages
    #else just create room for the sender and receiver and sender joins room
        
    # room_id = room.get_room_id(sender_name, receiver_name)
    # pubkey = public_keys.get_key(sender_name)

    # # if the user is already inside of a room and wants to chat with the sender (friend is online)
    # if room_id is not None:
    #     room.join_room(sender_name, room_id)
    #     pubkey = public_keys.get_key(sender_name)

    #     join_room(room_id)

    #     emit("pubkey", {'pubkey': pubkey}, to=room_id, include_self=False)
    #     emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}", "green"), to=room_id)
    #     return room_id
    
    # # if the user isn't inside of any room (friend is not online)
    # else:
    #     room_id = room.create_room(sender_name, receiver_name)

    #     join_room(room_id)
    #     emit("pubkey", {'pubkey': pubkey}, to=room_id, include_self=False)
    #     emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id)
    #     return room_id