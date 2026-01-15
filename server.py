from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def handle_register(data):
    username = data.get('username')
    if username:
        users[username] = request.sid
        print(f"{username} registered -> {request.sid}")

@socketio.on('private_message')
def handle_private_message(data):
    sender = data.get('from')
    receiver = data.get('to')
    message = data.get('message')
    if not receiver or not message:
        return
    if receiver in users:
        emit('message', {'from': sender, 'message': message}, to=users[receiver])
    else:
        emit('message', {'from': 'system', 'message': f'User {receiver} is offline or not found.'}, to=request.sid)

@socketio.on('send_image_chunk')
def handle_image_chunk(data):
    receiver = data.get('to')
    if not receiver:
        return
    if receiver in users:
        emit('receive_image_chunk', data, to=users[receiver])
    else:
        emit('message', {'from': 'system', 'message': f'User {receiver} is offline or not found.'}, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    disconnected = None
    for user, sid in list(users.items()):
        if sid == request.sid:
            disconnected = user
            del users[user]
            break
    if disconnected:
        print(f"{disconnected} disconnected")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
