// ============================================================
// JITSI MEETING ASSISTANT CLIENT
// Self-hosted Jitsi + remote participant PCM extraction
// ============================================================

const ROOM_NAME = "bot-test";

const JITSI_HOST = "192.168.10.151";
const JITSI_PORT = "8443";

const PCM_WS_URL = "ws://127.0.0.1:8765";

const TARGET_SAMPLE_RATE = 16000;
const PCM_CHUNK_MS = 100;

const statusElement = document.getElementById("status");

let connection = null;
let conference = null;

window.remoteAudioTracks = [];
window.audioPipelines = new Map();


// ============================================================
// STATUS
// ============================================================

function setStatus(message, type = "info") {
    console.log(`[STATUS] ${message}`);

    if (statusElement) {
        statusElement.textContent = message;
    }

    if (type === "error") {
        console.error(`[STATUS] ${message}`);
    }
}


// ============================================================
// START PCM PIPELINE
// ============================================================

async function startAudioPipeline(jitsiTrack) {

    const participantId = jitsiTrack.getParticipantId();
    const mediaTrack = jitsiTrack.getTrack();

    console.log(
        `[AUDIO] Starting PCM pipeline for participant ${participantId}`
    );

    if (!mediaTrack) {
        console.error(
            "[AUDIO] No underlying MediaStreamTrack."
        );
        return;
    }

    if (mediaTrack.kind !== "audio") {
        console.error(
            `[AUDIO] Expected audio track, got ${mediaTrack.kind}`
        );
        return;
    }

    if (window.audioPipelines.has(participantId)) {
        console.log(
            `[AUDIO] Pipeline already exists for ${participantId}`
        );
        return;
    }


    // --------------------------------------------------------
    // WebSocket
    // --------------------------------------------------------

    const websocket = new WebSocket(PCM_WS_URL);

    websocket.binaryType = "arraybuffer";

    await new Promise((resolve, reject) => {

        const timeout = setTimeout(() => {
            reject(
                new Error(
                    `PCM WebSocket timeout: ${PCM_WS_URL}`
                )
            );
        }, 10000);

        websocket.onopen = () => {

            clearTimeout(timeout);

            console.log(
                `[AUDIO] PCM WebSocket connected for ${participantId}`
            );

            websocket.send(
                JSON.stringify({
                    type: "start",
                    participant_id: participantId,
                    sample_rate: TARGET_SAMPLE_RATE,
                    channels: 1,
                    format: "s16le"
                })
            );

            resolve();
        };

        websocket.onerror = (event) => {

            clearTimeout(timeout);

            console.error(
                `[AUDIO] PCM WebSocket error for ${participantId}`,
                event
            );

            reject(
                new Error("PCM WebSocket connection failed")
            );
        };
    });


    // --------------------------------------------------------
    // Create AudioContext
    // --------------------------------------------------------

    const audioContext = new AudioContext({
        latencyHint: "interactive"
    });

    await audioContext.resume();

    console.log(
        `[AUDIO] AudioContext sample rate for ${participantId}:`,
        audioContext.sampleRate
    );


    // --------------------------------------------------------
    // Load AudioWorklet
    // --------------------------------------------------------

    await audioContext.audioWorklet.addModule(
        "audio-processor.js"
    );


    // --------------------------------------------------------
    // IMPORTANT:
    //
    // Create a new MediaStream containing ONLY this
    // participant's MediaStreamTrack.
    //
    // This guarantees that we process this participant's
    // audio rather than another audio track.
    // --------------------------------------------------------

    const participantStream =
        new MediaStream([mediaTrack]);


    const source =
        audioContext.createMediaStreamSource(
            participantStream
        );


    // --------------------------------------------------------
    // AudioWorklet
    // --------------------------------------------------------

    const processor =
        new AudioWorkletNode(
            audioContext,
            "pcm-processor",
            {
                processorOptions: {
                    targetSampleRate: TARGET_SAMPLE_RATE,
                    chunkMs: PCM_CHUNK_MS
                }
            }
        );


    // --------------------------------------------------------
    // Silent output
    //
    // The graph needs an output path so audio processing keeps
    // running, but we don't want the bot VM to play the audio.
    // --------------------------------------------------------

    const silentGain =
        audioContext.createGain();

    silentGain.gain.value = 0;


    // --------------------------------------------------------
    // Audio graph
    //
    // participant track
    //       ↓
    // MediaStreamSource
    //       ↓
    // AudioWorklet
    //       ↓
    // Gain 0
    //       ↓
    // speakers (silent)
    // --------------------------------------------------------

    source.connect(processor);
    processor.connect(silentGain);
    silentGain.connect(audioContext.destination);


    // --------------------------------------------------------
    // Receive PCM from AudioWorklet
    // --------------------------------------------------------

    processor.port.onmessage = (event) => {

        const data = event.data;

        if (!data) {
            return;
        }

        if (data.type !== "pcm") {
            return;
        }

        if (
            websocket.readyState !==
            WebSocket.OPEN
        ) {
            return;
        }

        // Binary Int16 PCM buffer.
        websocket.send(data.buffer);
    };


    websocket.onerror = (event) => {

        console.error(
            `[AUDIO] WebSocket error for ${participantId}:`,
            event
        );
    };


    websocket.onclose = () => {

        console.log(
            `[AUDIO] WebSocket closed for ${participantId}`
        );
    };


    // --------------------------------------------------------
    // Store pipeline
    // --------------------------------------------------------

    const pipeline = {
        participantId,
        jitsiTrack,
        mediaTrack,
        participantStream,
        audioContext,
        source,
        processor,
        silentGain,
        websocket
    };

    window.audioPipelines.set(
        participantId,
        pipeline
    );


    console.log(
        `[AUDIO] PCM pipeline started for ${participantId}`
    );
}


// ============================================================
// STOP PCM PIPELINE
// ============================================================

async function stopAudioPipeline(participantId) {

    const pipeline =
        window.audioPipelines.get(participantId);

    if (!pipeline) {
        return;
    }

    console.log(
        `[AUDIO] Stopping PCM pipeline for ${participantId}`
    );


    try {
        pipeline.processor.disconnect();
    } catch (_) {}


    try {
        pipeline.source.disconnect();
    } catch (_) {}


    try {
        pipeline.silentGain.disconnect();
    } catch (_) {}


    try {
        if (
            pipeline.websocket.readyState ===
            WebSocket.OPEN
        ) {
            pipeline.websocket.send(
                JSON.stringify({
                    type: "stop",
                    participant_id: participantId
                })
            );
        }
    } catch (_) {}


    try {
        pipeline.websocket.close();
    } catch (_) {}


    try {
        await pipeline.audioContext.close();
    } catch (_) {}


    window.audioPipelines.delete(
        participantId
    );


    console.log(
        `[AUDIO] PCM pipeline stopped for ${participantId}`
    );
}


// ============================================================
// INITIALIZE JITSI
// ============================================================

async function initializeJitsi() {

    console.log(
        "[JITSI] Starting initialization..."
    );

    if (
        typeof JitsiMeetJS ===
        "undefined"
    ) {
        setStatus(
            "lib-jitsi-meet is not loaded.",
            "error"
        );
        return;
    }

    console.log(
        "[JITSI] lib-jitsi-meet loaded."
    );

    console.log(
        "[JITSI] Version:",
        JitsiMeetJS.version || "unknown"
    );


    // --------------------------------------------------------
    // Initialize lib-jitsi-meet
    // --------------------------------------------------------

    try {

        JitsiMeetJS.init({
            disableAudioLevels: false,
            enableNoAudioDetection: false
        });

        console.log(
            "[JITSI] JitsiMeetJS initialized."
        );

    } catch (error) {

        console.error(
            "[JITSI] Initialization failed:",
            error
        );

        setStatus(
            "Jitsi initialization failed.",
            "error"
        );

        return;
    }


    // ========================================================
    // CONNECTION
    // ========================================================

    const connectionOptions = {
    ...window.config,

    serviceUrl:
        window.config.websocket ||
        `wss://${JITSI_HOST}:${JITSI_PORT}/xmpp-websocket`,

    hosts: {
        ...window.config.hosts
    },

    clientNode:
        "http://jitsi.org/jitsimeet"
    };

    console.log(
        "[JITSI] Server-generated hosts:",
        connectionOptions.hosts
    );

    console.log(
        "[JITSI] Server-generated WebSocket:",
        connectionOptions.serviceUrl
    );

    try {

        connection =
            new JitsiMeetJS.JitsiConnection(
                null,
                null,
                connectionOptions
            );

    } catch (error) {

        console.error(
            "[JITSI] Connection object creation failed:",
            error
        );

        return;
    }


    // ========================================================
    // CONNECTION EVENTS
    // ========================================================

    connection.addEventListener(
        JitsiMeetJS.events.connection.CONNECTION_ESTABLISHED,
        onConnectionEstablished
    );

    connection.addEventListener(
        JitsiMeetJS.events.connection.CONNECTION_FAILED,
        onConnectionFailed
    );

    connection.addEventListener(
        JitsiMeetJS.events.connection.CONNECTION_DISCONNECTED,
        onConnectionDisconnected
    );


    setStatus(
        "Connecting to Jitsi..."
    );

    connection.connect();
}


// ============================================================
// CONNECTION ESTABLISHED
// ============================================================

function onConnectionEstablished() {

    console.log(
        "[JITSI] Connection established."
    );

    setStatus(
        `Connected. Joining ${ROOM_NAME}...`
    );


    // --------------------------------------------------------
    // Create conference
    // --------------------------------------------------------

    conference =
        connection.initJitsiConference(
            ROOM_NAME,
            {
                p2p: {
                    enabled: false
                }
            }
        );

    window.jitsiConference =
        conference;


    // --------------------------------------------------------
    // Subscribe to all remote audio
    // --------------------------------------------------------

    try {

        conference.setAudioSubscriptionMode({
            all: true
        });

        console.log(
            "[JITSI] Subscribed to all remote audio sources."
        );

    } catch (error) {

        console.warn(
            "[JITSI] Could not set audio subscription mode:",
            error
        );
    }


    // ========================================================
    // CONFERENCE EVENTS
    // ========================================================

    conference.addEventListener(
        JitsiMeetJS.events.conference.CONFERENCE_JOINED,
        onConferenceJoined
    );

    conference.addEventListener(
        JitsiMeetJS.events.conference.CONFERENCE_FAILED,
        onConferenceFailed
    );

    conference.addEventListener(
        JitsiMeetJS.events.conference.TRACK_ADDED,
        onTrackAdded
    );

    conference.addEventListener(
        JitsiMeetJS.events.conference.TRACK_REMOVED,
        onTrackRemoved
    );

    conference.addEventListener(
        JitsiMeetJS.events.conference.USER_JOINED,
        onUserJoined
    );

    conference.addEventListener(
        JitsiMeetJS.events.conference.USER_LEFT,
        onUserLeft
    );


    // --------------------------------------------------------
    // Bot display name
    // --------------------------------------------------------

    try {

        conference.setDisplayName(
            "Meeting Assistant Bot"
        );

    } catch (error) {

        console.warn(
            "[JITSI] Could not set display name:",
            error
        );
    }


    // --------------------------------------------------------
    // Join
    // --------------------------------------------------------

    console.log(
        `[JITSI] Joining conference: ${ROOM_NAME}`
    );

    conference.join();
}


// ============================================================
// CONNECTION FAILED
// ============================================================

function onConnectionFailed(error) {

    console.error(
        "[JITSI] Connection failed:",
        error
    );

    setStatus(
        "Jitsi connection failed.",
        "error"
    );
}


// ============================================================
// CONNECTION DISCONNECTED
// ============================================================

function onConnectionDisconnected() {

    console.warn(
        "[JITSI] Connection disconnected."
    );

    setStatus(
        "Disconnected from Jitsi.",
        "error"
    );
}


// ============================================================
// CONFERENCE JOINED
// ============================================================

function onConferenceJoined() {

    console.log(
        "[JITSI] Conference joined successfully."
    );

    setStatus(
        `Joined conference: ${ROOM_NAME}`
    );
}


// ============================================================
// CONFERENCE FAILED
// ============================================================

function onConferenceFailed(error) {

    console.error(
        "[JITSI] Conference failed:",
        error
    );

    setStatus(
        "Conference join failed.",
        "error"
    );
}


// ============================================================
// USER JOINED
// ============================================================

function onUserJoined(id, user) {

    console.log(
        "[JITSI] USER_JOINED:",
        id,
        user
    );
}


// ============================================================
// USER LEFT
// ============================================================

function onUserLeft(id) {

    console.log(
        "[JITSI] USER_LEFT:",
        id
    );
}


// ============================================================
// TRACK ADDED
// ============================================================

async function onTrackAdded(track) {

    console.log(
        "[JITSI] TRACK_ADDED"
    );

    console.log(
        "[JITSI] Track type:",
        track.getType()
    );

    console.log(
        "[JITSI] Is local:",
        track.isLocal()
    );

    console.log(
        "[JITSI] Participant ID:",
        track.getParticipantId()
    );

    console.log(
        "[JITSI] Track ID:",
        track.getId()
    );


    // --------------------------------------------------------
    // Ignore local tracks
    // --------------------------------------------------------

    if (track.isLocal()) {

        console.log(
            "[JITSI] Ignoring local track."
        );

        return;
    }


    // --------------------------------------------------------
    // Only audio
    // --------------------------------------------------------

    if (
        track.getType() !==
        "audio"
    ) {

        console.log(
            "[JITSI] Ignoring non-audio track."
        );

        return;
    }


    const participantId =
        track.getParticipantId();


    const mediaTrack =
        track.getTrack();


    console.log(
        "[JITSI] REMOTE AUDIO TRACK RECEIVED"
    );

    console.log(
        "[JITSI] Participant:",
        participantId
    );

    console.log(
        "[JITSI] MediaStreamTrack:",
        mediaTrack
    );

    console.log(
        "[JITSI] readyState:",
        mediaTrack?.readyState
    );


    // --------------------------------------------------------
    // Store Jitsi track
    // --------------------------------------------------------

    window.remoteAudioTracks.push(
        track
    );


    // --------------------------------------------------------
    // Start PCM extraction
    // --------------------------------------------------------

    try {

        await startAudioPipeline(
            track
        );

    } catch (error) {

        console.error(
            `[AUDIO] Failed to start PCM pipeline for ${participantId}:`,
            error
        );
    }
}


// ============================================================
// TRACK REMOVED
// ============================================================

async function onTrackRemoved(track) {

    console.log(
        "[JITSI] TRACK_REMOVED:",
        track.getId()
    );


    const participantId =
        track.getParticipantId();


    const index =
        window.remoteAudioTracks.indexOf(
            track
        );

    if (index !== -1) {

        window.remoteAudioTracks.splice(
            index,
            1
        );
    }


    await stopAudioPipeline(
        participantId
    );
}


// ============================================================
// DIAGNOSTIC FUNCTIONS
// ============================================================

window.getRemoteAudioTracks = function () {

    return window.remoteAudioTracks;
};


window.getParticipants = function () {

    if (!conference) {
        return [];
    }

    try {

        return conference.getParticipants();

    } catch (error) {

        console.error(
            "[JITSI] getParticipants failed:",
            error
        );

        return [];
    }
};


window.getAudioPipelines = function () {

    return Array.from(
        window.audioPipelines.keys()
    );
};


// ============================================================
// START
// ============================================================

initializeJitsi();