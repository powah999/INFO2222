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

from models import Room
import db

room = Room()
public_keys = db.Public()
session_ids = {}
session_tokens = {}

@socketio.on('connect')
def connect():
    username_session = session.get('username')

    #uncomment once final
    # if 'username' not in session:
    #     print('\nNo session\n')
    #     raise ConnectionRefusedError('Connection refused.')
    
    # if session_tokens.get(username_session) == None:
    #     raise ConnectionRefusedError('Connection refused.')

    # if session_tokens.get(username_session) != session['token']:
    #     print('\nUser has not logged/signup yet\n')
    #     session_ids.pop(username_session, None)
    #     public_keys.keys.pop(username_session, None)
    #     session_tokens.pop(username_session, None)
    #     session.clear()
    #     raise ConnectionRefusedError('Connection refused.')

    session_ids[username_session] = request.sid

    #updates online/offline status of friend
    emit('status_update', {'username': username_session, 'status': 'online'}, broadcast=True)

    print(f"\nusername: {username_session} CONNECTED")

    print('\nSession ids: \n')

    print(session_ids)

    
    print('\nPublic keys:\n')
    print(public_keys.keys)

#gets online/offlien status of friend
@socketio.on("get_status")
def get_status(username):
    print("HEY IS THIS WORKING")
    if session_ids.get(username) != None:
        print("HEY IS THIS ONLINE?")
        return 'online'
    return 'offline'

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")

    session_ids.pop(username, None)
    public_keys.keys.pop(username, None)
    session_tokens.pop(username, None)
    session.clear()

    print('\nSession ids: \n')

    print(session_ids)

    
    print('\nPublic keys:\n')
    print(public_keys.keys)

    #updates online/offlien status of friend
    emit('status_update', {'username': username, 'status': 'offline'}, broadcast=True)

    room_id = room.room_exists(username)
    if room_id is None:
        return
    
    friendname = request.cookies.get("friendname")
    
    message = [f"{username} has disconnected", "red", 'a']
    room.append_message(room_id, message, username)
    room.append_message(room_id, message, friendname)

    room.leave_room(username, room_id)
    history = room.delete_history(room_id, username)
    print(db.append_history(username, friendname, history))

    emit("incoming", (message[0], message[1], "a"), to=int(room_id))

# send message event handler --> send to everyone but sender
@socketio.on("send")
def send(friendname, friendmessage, ourmessage, room_id):

    username = request.cookies.get("username")

    if session_ids.get(username) != request.sid:
        return 'Your SID does not match the one stored in server'
    
    if session['username'] != username:
        return 'invalid session'

    if room.friend_in_room(username, friendname, room_id) == False:
        return "Can't send a message because friend is not in room!"

    friendmessage = [friendmessage, 'black', 'msg']
    ourmessage = [ourmessage, 'black', 'msg']

    room.append_message(room_id, ourmessage, username)

    emit("incoming", (friendmessage[0], friendmessage[1], friendmessage[2]), to=room_id, include_self=False)

@socketio.on("receiver_encrypt")
def receiver_encrypt(message, room_id):

    username = request.cookies.get("username")

    if session_ids.get(username) != request.sid:
        return 'Your SID does not match the one stored in server'
    
    storedmessage = [message, 'black', 'msg']
    room.append_message(room_id, storedmessage, username)

# leave room event handler
@socketio.on("leave")
def leave(friendname, room_id):

    username = request.cookies.get("username")

    print(room_id)
    print(username)

    if session_ids.get(username) != request.sid:
        return 'Your SID does not match the one stored in server'

    #friendname = request.cookies.get('friendname')
    print(f'friend leave: {friendname}')
    
    message = [f"{username} has left the room.", "red", 'a']
    room.append_message(room_id, message, username)
    room.append_message(room_id, message, friendname)

    room.leave_room(username, room_id)
    history = room.delete_history(room_id, username)
    a = db.append_history(username, friendname, history)
    if a == -1:
        return 'FAILED TO DELETE HISTORY'

    print(f'\n\n DELETED HISTORY: {history}')
    
    print(f'\n\n {username} has left {room_id}\n')
    leave_room(room_id)

    emit("incoming", (message[0], message[1], "a"), to=room_id, include_self=False)


# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(receiver_name, pubkey):

    sender_name = request.cookies.get("username")

    if session_ids.get(sender_name) != request.sid:
        return 'Your SID does not match the one stored in server'

    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    # Checks if someone sends a request to masquarade a user
    pubkey_client = public_keys.get_key(sender_name)

    #uncomment once final
    # if pubkey_client == None:
    #     return 'User is not in session'

    # if pubkey != pubkey_client:
    #     return 'Your pubkey does not match user"s pubkey'
    
    if receiver_name == sender_name:
        return 'Cant talk to yourself'
    
    if room.room_exists(sender_name) is not None:
        return 'You are already in a room, leave the room first'
    
    room_id = room.unique_room_exists(sender_name, receiver_name)


    # if the user is already inside of a room 
    if room_id != False:

        history = db.get_history(sender_name, receiver_name)
        if history == -1:
            history = []
            db.insert_history(sender_name,receiver_name, history)

        message1 = [f"{sender_name} has joined the room.", 'green', 'a']
        message2 = [f"{sender_name} has joined the room. Now talking to {receiver_name}.", 'green', 'a']\
        
        history.append(message1)
        history.append(message2)

        room.join_room(sender_name, receiver_name, room_id)

        room.append_message(room_id, message1, sender_name)
        room.append_message(room_id, message2, sender_name)
        room.append_message(room_id, message1, receiver_name)
        room.append_message(room_id, message2, receiver_name)

        join_room(room_id)

        #initiate key exchange
        emit("pubkey_first", {'pubkey': pubkey, 'guy': sender_name}, to=room_id, include_self=False)
        # emit to everyone in the room except the sender
        emit("incoming", (message1[0], message1[1], "a"), to=room_id, include_self=False)
        # emit only to the sender
        emit("historydump", (history), room=request.sid)
        #emit("incoming", (message2[0], message2[1], "a"))
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone

    history = db.get_history(sender_name, receiver_name)
    if history == -1:
        history = []
        db.insert_history(sender_name,receiver_name, history)

    message = [f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green", "a"]
    history.append(message)

    room_id = room.create_room(sender_name, receiver_name)
    room.append_message(room_id, message, sender_name)
    room.append_message(room_id, message, receiver_name)
    join_room(room_id)

    emit("historydump", (history), to=room_id)
    #emit("incoming", (message[0], message[1], "a"), to=room_id)
    return room_id

@socketio.on("exchange")
def exchage(receiver_name, pubkey):

    sender_name = request.cookies.get("username")

    if session_ids.get(sender_name) != request.sid:
        return 'Your SID does not match the one stored in server'

    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.unique_room_exists(sender_name, receiver_name)
    if room_id == False:
        return 'Room does not exist!'

    pubkey_client = public_keys.get_key(sender_name)

    #uncomment once final
    # if pubkey_client == None:
    #     return 'User not in session'

    # if pubkey != pubkey_client:
    #     return 'Your pubkey does not match user"s pubkey'
    
    print(f'\n\n Sending {receiver_name} the public key of {sender_name}: {pubkey}\n')

    emit("pubkey_second", {'pubkey': pubkey, 'guy': sender_name}, to=room_id,include_self=False)


@socketio.on("send_request")
def send_request(receiver_name):

    sender_name = request.cookies.get("username")

    print(f"\nrequest.sid:   {request.sid}")
    print(session_ids.get(sender_name))
    print(sender_name)

    if session_ids.get(sender_name) != request.sid:
        return 'Your SID does not match the one stored in server'
    
    if sender_name == receiver_name:
        return 'You cant send a friend request to yourself'


    #check if new friend already exists
    sender_friends = db.get_friends(sender_name)
    if sender_friends != -1:
        for friend in sender_friends:
            if friend.username == receiver_name:
                return "This person is already your friend!"
    else:
        return "This person does not exist"
    
    flag = db.add_request(sender_name, receiver_name)

    if flag != 0:
        return flag
    else:
        emit("incoming_request", (sender_name), to=session_ids.get(receiver_name))
        return 0

@socketio.on("remove_friend")
def remove_friend(friendname):

    username = request.cookies.get("username")

    if session_ids.get(username) != request.sid:
        return 'Your SID does not match the one stored in server'

    flag = db.remove_friend(username, friendname)

    if flag != 0:
        return flag
    else: 
        emit("youGotRemoved", (username), to=session_ids.get(friendname))
        return 0
    

@socketio.on("accept")
def accept(sender_name):

    receiver_name = request.cookies.get("username")

    if receiver_name == sender_name:
        return 'Cant accept your own friend request'

    if session_ids.get(receiver_name) != request.sid:
        return 'Your SID does not match the one stored in server'

    flag = db.accept_request(sender_name, receiver_name)

    if flag != 0:
        return flag
    else: 
        emit("check_accepted_requests", (receiver_name), to=session_ids.get(sender_name))
        return 0



#decline friend request
@socketio.on("decline")
def decline(sender_name):

    receiver_name = request.cookies.get("username")

    if session_ids.get(receiver_name) != request.sid:
        return 'Your SID does not match the one stored in server'

    flag = db.decline_request(sender_name, receiver_name)

    if flag != 0:
        return flag
    else: 
        emit("check_declined_requests", (receiver_name), to=session_ids.get(sender_name))
        return 0

@socketio.on("new_post")
def new_post(title, content):
    print(title)
    print(content)
    print(session["username"])

    if not title or not content:
        return False
 
    if not db.create_article(username=session["username"], title=title, content=content):
        return False
    
    return True

@socketio.on("delete_article")
def delete_article(article):
    if not db.delete_article(username=session["username"], article=article):
        return False
    
    return True

@socketio.on("re_post")
def re_post(article, new_title, new_content):
    return db.edit_article(article=article, new_title=new_title, new_content=new_content)

# when the client connects to a socket
# this event is emitted when the io() function is called in JS

# def cmp(string_a, string_b):
#     li = []
#     string_a = set(string_a)

#     for char in string_a:
#         if char not in string_b:
#             li.append(char)
#     if len(li) > 0:
#         return f'Your username should only contain alphanumeric ("a" or "1"), underscore ("_"), period ("."), and space " " characters! '
#     return True

# def cleaner(sender_name = -99, receiver_name =-99, message = -99, room_id=-99, pubkey_client=-99):

#     temp = []

#     if sender_name != -99:
#         if type(sender_name) != str:
#             return 'Invalid username/sender name: socket emit'
#         sender_name = bleach.clean(sender_name)
#         temp.append(sender_name)

#     if receiver_name != -99:
#         if type(receiver_name) != str:
#             return 'Invalid receiver name: socket emit'
#         receiver_name = bleach.clean(receiver_name)
#         temp.append(receiver_name)

#     if message != -99:
#         if type(message) != dict:
#             return 'Invalid message: socket emit'
        
#         for key, value in message.items():
#             if type(message[key]) == str:
#                 message[key] = bleach.clean(value)
#         temp.append(message)
        
#     if room_id != -99:
#         if type(room_id) != int:
#             return 'Invalid socket emit'
#         temp.append(room_id)

#     if pubkey_client != -99:
#         if type(pubkey_client) != str:
#             return 'Invalid pubkey: socket emit'
#         pubkey_client = bleach.clean(pubkey_client)
#         temp.append(pubkey_client)

#     return temp