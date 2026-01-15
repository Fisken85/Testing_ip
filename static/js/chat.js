var socket = io(); 
var username = localStorage.getItem('username') || '';
if (username) {
    socket.emit('register', { username: username });
    var el = document.getElementById('username');
    if (el) el.value = username;
}

function appendMessage(html) {
    var chat = document.getElementById('chat');
    chat.innerHTML += html;
    chat.scrollTop = chat.scrollHeight;
}

window.registerUser = function() {
    var val = document.getElementById('username').value.trim();
    if (!val) return appendMessage('<p><em>Skriv inn brukernavn</em></p>');
    username = val;
    localStorage.setItem('username', username);
    socket.emit('register', { username: username });
    appendMessage('<p><em>Registrert som ' + username + '</em></p>');
};

window.sendMessage = function() {
    var receiver = document.getElementById('receiver').value.trim();
    var message = document.getElementById('message').value.trim();
    if (!receiver || !message) return appendMessage('<p><em>Fyll ut mottaker og melding</em></p>');
    socket.emit('private_message', { from: username, to: receiver, message: message });
    appendMessage('<p><b>Til ' + receiver + ':</b> ' + message + '</p>');
    document.getElementById('message').value = '';
};

function makeImageId() {
    return Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,9);
}

async function sendChunkedImage(receiver, dataURL, imageId) {
    var chunkSize = 50 * 1024;
    var totalLength = dataURL.length;
    var chunkCount = Math.ceil(totalLength / chunkSize);
    for (let i = 0; i < chunkCount; i++) {
        let start = i * chunkSize;
        let end = Math.min((i + 1) * chunkSize, totalLength);
        let chunk = dataURL.slice(start, end);
        socket.emit('send_image_chunk', {
            from: username,
            to: receiver,
            imageId: imageId,
            chunkIndex: i,
            totalChunks: chunkCount,
            chunk: chunk
        });
        await new Promise(r => setTimeout(r, 5));
    }
}

window.sendImage = function() {
    var receiver = document.getElementById('receiver').value.trim();
    var file = document.getElementById('imageInput').files[0];
    if (!receiver || !file) return appendMessage('<p><em>Velg mottaker og et bilde</em></p>');

    var reader = new FileReader();
    reader.onload = function(evt) {
        var dataURL = evt.target.result;
        var imageId = makeImageId();
        sendChunkedImage(receiver, dataURL, imageId);
        appendMessage('<p><b>Til ' + receiver + ':</b><br><em>Bilde sendt (chunked)</em></p>');
    };
    reader.readAsDataURL(file);
};

var incoming = {};

socket.on('receive_image_chunk', function(data) {
    var id = data.imageId;
    var sender = data.from || 'ukjent';
    var key = sender + '::' + id;
    if (!incoming[key]) incoming[key] = { total: data.totalChunks, parts: [] };
    incoming[key].parts[data.chunkIndex] = data.chunk;
    if (incoming[key].parts.length === incoming[key].total && !incoming[key].parts.includes(undefined)) {
        var full = incoming[key].parts.join('');
        appendMessage('<p><b>Fra ' + sender + ':</b><br><img src="' + full + '" style="max-width:300px;"></p>');
        delete incoming[key];
    }
});

socket.on('message', function(data) {
    appendMessage('<p><b>Fra ' + data.from + ':</b> ' + data.message + '</p>');
});

window.addEventListener('DOMContentLoaded', function() {
    var reg = document.getElementById('registerBtn'); if (reg) reg.addEventListener('click', registerUser);
    var sbtn = document.getElementById('sendMsgBtn'); if (sbtn) sbtn.addEventListener('click', sendMessage);
    var ibtn = document.getElementById('sendImageBtn'); if (ibtn) ibtn.addEventListener('click', sendImage);
});
