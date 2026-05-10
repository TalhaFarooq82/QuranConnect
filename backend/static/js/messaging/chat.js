// WebSocket connection
const ws = new WebSocket(`ws://${window.location.host}/ws/chat/${conversationId}/`);

let selectedFile = null;

// Scroll to bottom on load
window.addEventListener('load', () => scrollToBottom());

function scrollToBottom() {
    const area = document.getElementById('messages-area');
    area.scrollTop = area.scrollHeight;
}

// Receive message from server
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'file') {
        appendFileMessage(data);
    } else if (data.signal) {
        handleVideoSignal(data);
    } else {
        appendMessage(data);
    }
};

ws.onclose = function() {
    console.log('WebSocket closed');
};

// Send text message
function sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();

    // If file selected, upload it first
    if (selectedFile) {
        uploadFile();
        return;
    }

    if (!text) return;

    ws.send(JSON.stringify({ message: text }));
    input.value = '';
}

// Append message bubble to UI
function appendMessage(data) {
    const area = document.getElementById('messages-area');
    const isMine = String(data.sender_id) === String(currentUserId);

    // Remove empty chat message if present
    const empty = area.querySelector('.empty-chat');
    if (empty) empty.remove();

    const row = document.createElement('div');
    row.className = `message-row ${isMine ? 'mine' : 'theirs'}`;
    row.id = `msg-${data.message_id}`;

    row.innerHTML = `
        ${!isMine ? `<div class="msg-avatar">${data.sender_name[0].toUpperCase()}</div>` : ''}
        <div class="message-bubble">
            <p>${escapeHtml(data.message)}</p>
            <span class="msg-time">${data.timestamp}</span>
        </div>
    `;

    area.appendChild(row);
    scrollToBottom();
}

// File handling
function handleFileSelect(input) {
    const file = input.files[0];
    if (!file) return;
    selectedFile = file;
    document.getElementById('file-preview-name').textContent = file.name;
    document.getElementById('file-preview-bar').style.display = 'flex';
}

function cancelFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-preview-bar').style.display = 'none';
}

function uploadFile() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(uploadUrl, {
        method: 'POST',
        body: formData,
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Send via WebSocket so BOTH users see it
            ws.send(JSON.stringify({
                type: 'file',
                file_url: data.file_url,
                file_type: data.file_type,
                original_name: data.original_name,
                timestamp: new Date().toLocaleString('en-GB', {
                    day: '2-digit', month: 'short',
                    hour: '2-digit', minute: '2-digit'
                }),
            }));
            cancelFile();
        } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
        }
    });
}

function appendFileMessage(data) {
    const area = document.getElementById('messages-area');
    const row = document.createElement('div');
    row.className = 'message-row mine';

    let fileHtml = '';
    if (data.file_type === 'image') {
        fileHtml = `<img src="${data.file_url}" class="msg-image" onclick="window.open('${data.file_url}')">`;
    } else if (data.file_type === 'audio') {
        fileHtml = `<audio controls src="${data.file_url}" class="msg-audio"></audio>`;
    } else {
        fileHtml = `<a href="${data.file_url}" target="_blank" class="msg-file">
                        📄 ${data.original_name}
                    </a>`;
    }

    row.innerHTML = `
        <div class="message-bubble">
            ${fileHtml}
            <span class="msg-time">Just now</span>
        </div>
    `;

    area.appendChild(row);
    scrollToBottom();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}