from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import sqlite3
import os
import base64
import time
import cloudinary
import cloudinary.uploader
from database import init_db, get_db_connection  # Importere funksjonene fra database.py
from dotenv import load_dotenv

# Last inn miljøvariabler fra .env-filen
load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Opprett mappe for bilder hvis den ikke finnes
UPLOAD_FOLDER = "static/bilder"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Lagrer aktive brukere
users = {}

# Konfigurer Cloudinary
cloudinary.config(
  cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
  api_key=os.environ.get('CLOUDINARY_API_KEY'),
  api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

@app.route("/")
def index():
    return render_template("index.html")

# Rute for å hente lagrede bilder
@app.route("/static/bilder/<path:filename>")
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Når en bruker kobler til
@socketio.on("connect")
def handle_connect():
    print(f"Bruker koblet til: {request.sid}")

# Lagrer ID til brukeren permanent
@socketio.on("register")
def register(data):
    username = data["username"]
    
    # Hvis brukeren allerede er registrert, oppdater `sid`
    if username in users:
        print(f"{username} oppdaterte session ID til {request.sid}")
    else:
        print(f"{username} registrert med ID {request.sid}")
    
    users[username] = request.sid  # Oppdater ID-en til brukeren

# Bruker sender melding
@socketio.on("private_message")
def private_message(data):
    sender = data["from"]
    receiver = data["to"]
    message = data["message"]

    if receiver in users:
        receiver_sid = users[receiver]
        print(f"Sender melding fra {sender} til {receiver} (ID: {receiver_sid})")
        emit("message", {"from": sender, "message": message}, to=receiver_sid)
    else:
        print(f"{receiver} ikke funnet!")

    # Lagre meldingen i databasen
    conn = get_db_connection()
    conn.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                 (sender, receiver, message))
    conn.commit()
    conn.close()

# Håndterer sending av bilder
@socketio.on("send_image")
def handle_image(data):
    sender = data["from"]
    receiver = data["to"]
    image_data = data["image"]

    if receiver in users:
        receiver_sid = users[receiver]

        # Last opp bildet til Cloudinary
        try:
            # Dekode base64-bildedata
            image = base64.b64decode(image_data)

            # Lagre bildet midlertidig på serveren for opplasting til Cloudinary
            temp_image_path = os.path.join(UPLOAD_FOLDER, f"{sender}_{receiver}_{int(time.time())}.png")
            with open(temp_image_path, "wb") as f:
                f.write(image)

            # Last opp til Cloudinary
            upload_result = cloudinary.uploader.upload(temp_image_path)

            # Hent URL til det opplastede bildet
            image_url = upload_result['secure_url']

            # Slett midlertidig bilde
            os.remove(temp_image_path)

            # Send bildet til mottakeren via socket.io
            emit("receive_image", {"from": sender, "image_url": image_url}, to=receiver_sid)
            print(f"Bilde sendt fra {sender} til {receiver} ({image_url})")
        except Exception as e:
            print(f"Feil under bildeopplasting til Cloudinary: {e}")
    else:
        print(f"{receiver} ikke funnet!")

# Når en bruker kobler fra
@socketio.on("disconnect")
def handle_disconnect():
    disconnected_user = None
    for username, sid in list(users.items()):
        if sid == request.sid:
            disconnected_user = username
            del users[username]
            break

    if disconnected_user:
        print(f"{disconnected_user} koblet fra")
    else:
        print(f"Ukjent bruker koblet fra: {request.sid}")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
