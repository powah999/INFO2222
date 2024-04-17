'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room, Public


import db

room = Room()
keys = Public()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler --> send to everyone but sender
@socketio.on("send")
def send(username, message, room_id):
    emit("incoming", (f"{username}: {message}"), to=room_id, include_self=False)

# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    #check if person you're chatting with is your friend
    sender_friends = db.get_friends(sender_name)

    exists = False
    for friend in sender_friends:
        if friend.username == receiver_name:
            exists = True
            break

    if not exists:
        return f"{ receiver_name } is not your friend!"
    
    #emit public key of receiver to sender
    emit("receiver key", keys.get_key(receiver_name))
    
    #if friend is online, join room to allow them to send messages
    #else just create room for the sender and receiver and sender joins room
        
    room_id = room.get_room_id({sender_name, receiver_name})

    # if the user is already inside of a room and wants to chat with the sender (friend is online)
    if room_id is not None:
        room.join_room(sender_name, room_id)
        join_room(room_id)
        emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}", "green"), to=room_id)
        return room_id

    # if the user isn't inside of any room (friend is not online)
    room_id = room.create_room({sender_name, receiver_name})
    join_room(room_id)
    emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
    return room_id

#add message to message history
@socketio.on("history")
def history(username, message, room_id):
    room.add_message(message, username, room.get_receiver(username, room_id))

# leave room event handler
@socketio.on("leave")
def leave(username, friend, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username, friend)

#create pending and received request for sender and receiver respectively
@socketio.on("send_request")
def send_request(sender_name, receiver_name):
    print("TESTING")
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"
    
    #check if new friend already exists
    sender_friends = db.get_friends(sender_name)
    for friend in sender_friends:
        if friend.username == receiver_name:
            return "This person is already your friend!"
    
    #check if friend request has already been sent
    sender_requests = db.get_pending(sender_name)
    for pending in sender_requests:
        if pending.receiver == receiver_name:
            return "You've already sent this person a request!"
    
    db.make_request(sender=sender_name, receiver=receiver_name)

    

#accept friend request
@socketio.on("accept")
def accept(sender_name, receiver_name):
    #add to friend list in both users
    db.add_friend(sender_name, receiver_name)

    #remove sent and received requests from sender and receiver respectively
    db.remove_request(sender_name, receiver_name)

    #create empty chat history
    room.create_history(sender_name, receiver_name)

    #return db.get_friends(receiver_name)

#decline friend request
@socketio.on("decline")
def decline(sender_name, receiver_name):
    db.remove_request(sender_name, receiver_name)

