var socket = io();
var username = localStorage.getItem('username') || '';
if (username) socket.emit('register', { username: username }), document.getElementById('username').value = username;

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

window.sendImage = function() {
    var receiver = document.getElementById('receiver').value.trim();
    var file = document.getElementById('imageInput').files[0];
    if (!receiver || !file) return appendMessage('<p><em>Velg mottaker og et bilde</em></p>');

    var reader = new FileReader();
    reader.onload = function(evt) {
        var dataURL = evt.target.result;
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
                chunkIndex: i,
                totalChunks: chunkCount,
                chunk: chunk
            });
        }
        appendMessage('<p><b>Til ' + receiver + ':</b><br><em>Bilde sendt</em></p>');
    };
    reader.readAsDataURL(file);
};

var incomingImages = {};
socket.on('receive_image_chunk', function(data) {
    var key = data.from + '_' + username;
    if (!incomingImages[key]) incomingImages[key] = [];
    incomingImages[key][data.chunkIndex] = data.chunk;
    if (incomingImages[key].length === data.totalChunks && !incomingImages[key].includes(undefined)) {
        var fullData = incomingImages[key].join('');
        appendMessage('<p><b>Fra ' + data.from + ':</b><br><img src="' + fullData + '" style="max-width:300px;"></p>');
        delete incomingImages[key];
    }
});

socket.on('message', function(data) {
    appendMessage('<p><b>Fra ' + data.from + ':</b> ' + data.message + '</p>');
});

window.addEventListener('DOMContentLoaded', function() {
    document.getElementById('registerBtn').addEventListener('click', registerUser);
    document.getElementById('sendMsgBtn').addEventListener('click', sendMessage);
    document.getElementById('sendImageBtn').addEventListener('click', sendImage);
});
