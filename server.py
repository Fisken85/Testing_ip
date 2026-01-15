from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Username og sid
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def register(data):
    username = data.get('username')
    if username:
        users[username] = request.sid
        print(f"{username} registered -> {request.sid}")

@socketio.on('private_message')
def private_message(data):
    sender = data.get('from')
    receiver = data.get('to')
    message = data.get('message')
    if receiver in users:
        emit('message', {'from': sender, 'message': message}, to=users[receiver])

@socketio.on('send_image_chunk')
def handle_image_chunk(data):
    receiver = data.get('to')
    if receiver in users:
        emit('receive_image_chunk', data, to=users[receiver])


@socketio.on('disconnect')
def disconnect():
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
