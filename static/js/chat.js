var socket = io.connect(window.location.origin);

// Send bilde
function sendImage() {
    var receiver = document.getElementById("receiver").value.trim(); // Hent mottakernavn
    var file = document.getElementById("imageInput").files[0]; // Hent valgt fil

    if (!file || receiver === "") {
        alert("Velg en mottaker og et bilde.");
        return;
    }

    var formData = new FormData(); // Lag et FormData-objekt for å sende filen
    formData.append('file', file); // Legg til filen i FormData

    // API-håndtering for bildeopplasting
    fetch('/upload', {
        method: 'POST',  // Metoden er POST
        body: formData   // Innholdet er FormData (filen)
    })
    .then(response => response.json())  // Når serveren svarer, leser vi svaret som JSON
    .then(data => {
        if (data.image_url) {
            // Hvis opplastingen er vellykket, får vi en URL tilbake
            socket.emit("send_image", {
                "to": receiver,  // Mottakeren
                "image_url": data.image_url  // URL til bildet som ble opplastet
            });
        } else {
            alert("Opplasting feilet: " + (data.error || "Ukjent feil")); // Feil ved opplasting
        }
    })
    .catch(error => {
        alert("Feil under opplasting: " + error.message); // Feil som oppstår i nettverksforespørselen
    });
}

// Mottar bilde
socket.on("receive_image", function(data) {

    document.getElementById("chat").innerHTML += 
        `<p><b>Fra ${data.from}:</b><br><img src="${data.image_url}" style="max-width: 200px;"></p>`;
});
