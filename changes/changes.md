1. DB.PY AND MODELS.PY

COMPLETE OVERHAUL of tables and functions

for every get function, returns -1 as an ERROR, anythign else is SUCCESS

for every other function, returns 0 as SUCCESS, returns string is ERROR 



2. APP.PY, LOGIN.JINJA, SIGNUP.JINJA

signup and login process works different now.

client sends post request -> check if username and password valid

if not valid:

    reject

if valid :

    client sends ANOTHER post request, this time with a newly generated private-public key pair



3. SOCKET_ROUTES.PY

only changed send_request, accept, decline functions



4. HOME.JINJA

minor changes to sync with all the other files


WHAT HAS NOT BEEN TESTED:

any form of creating,joining, and leaving a room
any form of messaging and chatting

WHAT HAS NOT BEEN IMPLEMENTED:

encrypting and decrypting messages
storing message history




