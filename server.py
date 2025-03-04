from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*") 

import sqlite3

# Lag database hvis den ikke eksisterer
def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT,
                        receiver TEXT,
                        message TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()  # Kjører denne ved oppstart


# Lagrer aktive brukere
users = {}

# Database tilkobling
def get_db_connection():
    conn = sqlite3.connect("chat.db")
    conn.row_factory = sqlite3.Row
    return conn

# 🎨Serve html
@app.route("/")
def index():
    return render_template("index.html")

# Når en bruker kobler til
@socketio.on("connect")
def handle_connect():
    print(f"🔗 Bruker koblet til: {request.sid}")

# Når en bruker registrerer seg
@socketio.on("register")
def register(data):
    username = data["username"]
    users[username] = request.sid
    print(f"✅ {username} registrert med ID {request.sid}")

# Når en melding sendes
@socketio.on("private_message")
def private_message(data):
    sender = data["from"]
    receiver = data["to"]
    message = data["message"]

    if receiver in users:  
        receiver_sid = users[receiver]
        emit("message", {"from": sender, "message": message}, to=receiver_sid)

    # Lagre meldingen i SQL
    conn = get_db_connection()
    conn.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", 
                 (sender, receiver, message))
    conn.commit()
    conn.close()

# Når en bruker kobler fra
@socketio.on("disconnect")
def handle_disconnect():
    for username, sid in list(users.items()):
        if sid == request.sid:
            del users[username]
            print(f"❌ {username} koblet fra")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
