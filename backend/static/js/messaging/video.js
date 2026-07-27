// Video call — WebRTC

// Global variables we need throughout the call
let localStream = null        // our camera/mic feed
let peerConnection = null     // the WebRTC connection
let isCaller = false          // did we start the call?
let screenSharing = false
// ICE servers — help browsers find each other across networks
const iceServers = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }
    ]
}
async function startVideoCall() {
        isCaller = true

    // Step 1 — open camera and mic
    localStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
    })

    // Step 2 — show our own video on screen
    document.getElementById('local-video').srcObject = localStream

    // Step 3 — show the video panel
    document.getElementById('video-panel').style.display = 'flex'

    // Step 4 — notify the other person via WebSocket
    window.ws.send(JSON.stringify({
        signal: 'call_started',
        sender_id: currentUserId
    }))

}

function toggleMic() {
    const audioTrack = localStream.getAudioTracks()[0]
    if (audioTrack.enabled) {
        // currently on → turn off
        audioTrack.enabled = false
        document.getElementById('btn-mic').innerHTML =
            '<i class="fas fa-microphone-slash"></i>';

        document.getElementById('btn-mic').classList.add('danger');
    } else {
        // currently off → turn on
        audioTrack.enabled = true
        document.getElementById('btn-mic').innerHTML =
            '<i class="fas fa-microphone"></i>';

        document.getElementById('btn-mic').classList.remove('danger');
    
    }
}

function toggleCam() {
    const videoTrack = localStream.getVideoTracks()[0]

    if (videoTrack.enabled) {
        // currently on → turn off
        videoTrack.enabled = false
        document.getElementById('btn-cam').innerHTML =
            '<i class="fas fa-video-slash"></i>';

        document.getElementById('btn-cam').classList.add('danger');
    } else {
        // currently off → turn on
        videoTrack.enabled = true
        document.getElementById('btn-cam').innerHTML =
            '<i class="fas fa-video"></i>';

        document.getElementById('btn-cam').classList.remove('danger');
            }
}

async function toggleScreen() {
        if (!screenSharing) {
        // start screen share
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true })
        const screenTrack = screenStream.getVideoTracks()[0]

        // replace camera track with screen track in WebRTC connection
        const sender = peerConnection.getSenders().find(s => s.track.kind === 'video')
        sender.replaceTrack(screenTrack)

        // show screen in local video
        document.getElementById('local-video').srcObject = screenStream
        document.getElementById('btn-screen').innerHTML =
            '<i class="fas fa-display"></i>';

        document.getElementById('btn-screen').classList.add('active');
        screenSharing = true

        // when user stops sharing from browser UI
        screenTrack.onended = () => toggleScreen()

    } else {
        // stop screen share → go back to camera
        const cameraTrack = localStream.getVideoTracks()[0]
        const sender = peerConnection.getSenders().find(s => s.track.kind === 'video')
        sender.replaceTrack(cameraTrack)

        document.getElementById('local-video').srcObject = localStream
        document.getElementById('btn-screen').innerHTML =
            '<i class="fas fa-desktop"></i>';

        document.getElementById('btn-screen').classList.remove('active');
        screenSharing = false
    }
}

async function handleVideoSignal(data) {
    let signal = data.signal
    if (signal === 'call_started') {
        // other person started a call — show popup
        showIncomingCallPopup(data.sender_id)

    } else if (signal === 'call_joined') {
        // other person joined — we are caller, start WebRTC
        await startWebRTC()

    } else if (signal === 'offer') {
        // we are receiver — create answer
        await handleOffer(data.offer)

    } else if (signal === 'answer') {
        // we are caller — set remote description
        await handleAnswer(data.answer)

    } else if (signal === 'ice_candidate') {
        // network path info — add to connection
        await handleIceCandidate(data.candidate)

    } else if (signal === 'call_ended') {
        // other person ended call
        endCall()
    }
}    


function showIncomingCallPopup(callerId) {
    // Create popup div
    const popup = document.createElement('div')
    popup.id = 'incoming-call-popup'
    popup.innerHTML = `
        <div class="call-popup-box">
            <p>📹 Incoming Session Request</p>
            <div class="call-popup-actions">
                <button class="btn-accept" onclick="joinCall()">Join</button>
                <button class="btn-reject" onclick="rejectCall()">Decline</button>
            </div>
        </div>
    `
    document.body.appendChild(popup)
}

function rejectCall() {
    // Remove popup
    const popup = document.getElementById('incoming-call-popup')
    if (popup) popup.remove()
}

async function joinCall() {
    isCaller = false

    // Step 1 — open camera and mic
    localStream = await navigator.mediaDevices.getUserMedia({
        video : true,
        audio : true
    })

    // Step 2 - show our own video
    document.getElementById('local-video').srcObject = localStream

    // Step 3 - show video panel
    document.getElementById('video-panel').style.display = 'flex'

    //Step 4 - remove popup
    const popup = document.getElementById('incoming-call-popup')
    if (popup) popup.remove()

     // Step 5 — tell caller I joined
    window.ws.send(JSON.stringify({
        signal: 'call_joined'
    }))    
}

async function startWebRTC() {
    // Step 1 — create the WebRTC connection object
    peerConnection = new RTCPeerConnection(iceServers)

    // Step 2 — add our camera/mic stream to the connection
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream)
    })

    // Step 3 — when other person's video arrives, show it
    peerConnection.ontrack = (event) => {
        document.getElementById('remote-video').srcObject = event.streams[0]
    }

    // Step 4 — when ICE candidate is generated, send it to other person
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            window.ws.send(JSON.stringify({
                signal: 'ice_candidate',
                candidate: event.candidate
            }))
        }
    }

    // Step 5 — create offer and send it
    const offer = await peerConnection.createOffer()
    await peerConnection.setLocalDescription(offer)

    window.ws.send(JSON.stringify({
        signal: 'offer',
        offer: offer
    }))
}


async function handleOffer(offer) {
    // Step 1 — create the WebRTC connection object (same as caller did)
    peerConnection = new RTCPeerConnection(iceServers)

    // Step 2 — add our camera/mic stream to the connection
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream)
    })

    // Step 3 — when caller's video arrives, show it
    peerConnection.ontrack = (event) => {
        document.getElementById('remote-video').srcObject = event.streams[0]
    }

    // Step 4 — when ICE candidate generated, send to caller
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            window.ws.send(JSON.stringify({
                signal: 'ice_candidate',
                candidate: event.candidate
            }))
        }
    }

    // Step 5 — read caller's offer ("these are caller's requirements")
    await peerConnection.setRemoteDescription(offer)

    // Step 6 — create answer ("these are my requirements")
    const answer = await peerConnection.createAnswer()
    await peerConnection.setLocalDescription(answer)

    // Step 7 — send answer back to caller
    window.ws.send(JSON.stringify({
        signal: 'answer',
        answer: answer
    }))
}


async function handleAnswer(answer) {
    // Caller reads receiver's requirements
    // Now both sides know each other — video starts
    await peerConnection.setRemoteDescription(answer)
}


async function handleIceCandidate(candidate) {
    // Add network path sent by other person
    if (candidate) {
        await peerConnection.addIceCandidate(candidate)
    }
}

function endCall() {
    // Step 1 — stop camera and mic
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop())
        localStream = null
    }

    // Step 2 — close WebRTC connection
    if (peerConnection) {
        peerConnection.close()
        peerConnection = null
    }

    // Step 3 — clear both video screens
    document.getElementById('local-video').srcObject = null
    document.getElementById('remote-video').srcObject = null

    // Step 4 — hide video panel
    document.getElementById('video-panel').style.display = 'none'

// Step 5 — tell other person call ended (safely)
    try {
       window.ws.send(JSON.stringify({
            signal: 'call_ended'
        }))
    } catch(e) {
        console.log('Could not send call_ended signal:', e)
    }
}
