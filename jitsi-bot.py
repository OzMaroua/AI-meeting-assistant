import json
import os
import sys
import threading
import time

from playwright.sync_api import sync_playwright
from websockets.sync.server import serve

from realtime.jitsi_transcriber import LiveJitsiTranscriber
from meeting_state import MeetingState
from transcription.analyzer import analyze_transcript


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

CLIENT_URL = "http://127.0.0.1:8000"

BOT_NAME = "Meeting-Minute-Bot"

BOT_DURATION_SECONDS = 300

PCM_HOST = "127.0.0.1"
PCM_PORT = 8765


# ============================================================
# RECORDINGS
# ============================================================

RECORDINGS_DIR = os.path.join(
    PROJECT_ROOT,
    "recordings"
)

TRANSCRIPT_PATH = os.path.join(
    RECORDINGS_DIR,
    "live_transcript.txt"
)

STATE_PATH = os.path.join(
    RECORDINGS_DIR,
    "meeting_state.json"
)

PARTICIPANTS_PATH = os.path.join(
    RECORDINGS_DIR,
    "participants.json"
)


# ============================================================
# GLOBAL OBJECTS
# ============================================================

transcriber = None
pcm_server = None


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def ensure_recordings_directory():
    os.makedirs(
        RECORDINGS_DIR,
        exist_ok=True
    )


def reset_recordings():
    ensure_recordings_directory()

    with open(
        TRANSCRIPT_PATH,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("")

    with open(
        PARTICIPANTS_PATH,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            [],
            f,
            indent=2,
            ensure_ascii=False
        )

    print("[BOT] Recording files reset.")


# ============================================================
# PARTICIPANTS
# ============================================================

def save_participants(participants):

    ensure_recordings_directory()

    cleaned = []
    seen_ids = set()

    for participant in participants:

        if not isinstance(
            participant,
            dict
        ):
            continue

        participant_id = (
            participant.get("id")
            or participant.get("participantId")
            or participant.get("jid")
        )

        if not participant_id:
            continue

        participant_id = str(
            participant_id
        )

        if participant_id in seen_ids:
            continue

        seen_ids.add(
            participant_id
        )

        display_name = (
            participant.get("displayName")
            or participant.get("name")
            or ""
        )

        cleaned.append({
            "id": participant_id,
            "jitsi_name": str(display_name),
            "name": str(display_name)
        })

    with open(
        PARTICIPANTS_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            cleaned,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# PCM SERVER
# ============================================================

class PCMServer:

    def __init__(
        self,
        host,
        port,
        transcriber
    ):
        self.host = host
        self.port = port
        self.transcriber = transcriber

        self.server = None
        self.thread = None

    def handle_connection(
        self,
        websocket
    ):

        participant_id = None

        print("[PCM] Client connected.")

        try:

            for message in websocket:

                # ------------------------------------------------
                # JSON CONTROL MESSAGE
                # ------------------------------------------------

                if isinstance(
                    message,
                    str
                ):

                    try:

                        data = json.loads(
                            message
                        )

                    except json.JSONDecodeError:

                        print(
                            "[PCM] Invalid JSON message."
                        )

                        continue

                    message_type = data.get(
                        "type"
                    )

                    # ------------------------------------------------
                    # START PARTICIPANT
                    # ------------------------------------------------

                    if message_type == "start":

                        participant_id = str(
                            data.get(
                                "participant_id",
                                ""
                            )
                        )

                        if not participant_id:

                            print(
                                "[PCM] Missing participant ID."
                            )

                            continue

                        print(
                            f"[PCM] START "
                            f"participant={participant_id}"
                        )

                        self.transcriber.start_participant(
                            participant_id
                        )

                    # ------------------------------------------------
                    # STOP PARTICIPANT
                    # ------------------------------------------------

                    elif message_type == "stop":

                        stop_id = str(
                            data.get(
                                "participant_id",
                                participant_id or ""
                            )
                        )

                        if stop_id:

                            print(
                                f"[PCM] STOP "
                                f"participant={stop_id}"
                            )

                            self.transcriber.stop_participant(
                                stop_id
                            )

                    continue

                # ------------------------------------------------
                # RAW PCM AUDIO
                # ------------------------------------------------

                if isinstance(
                    message,
                    bytes
                ):

                    if not participant_id:

                        print(
                            "[PCM] Audio received "
                            "without participant ID."
                        )

                        continue

                    self.transcriber.add_pcm(
                        participant_id,
                        message
                    )

        except Exception as e:

            print(
                f"[PCM] Connection error: {e}"
            )

        finally:

            if participant_id:

                try:

                    self.transcriber.stop_participant(
                        participant_id
                    )

                except Exception as e:

                    print(
                        f"[PCM] Error stopping "
                        f"{participant_id}: {e}"
                    )

            print(
                "[PCM] Client disconnected."
            )

    def run(self):

        print(
            f"[PCM] Starting server on "
            f"{self.host}:{self.port}"
        )

        self.server = serve(
            self.handle_connection,
            self.host,
            self.port
        )

        print(
            "[PCM] Server ready."
        )

        try:

            self.server.serve_forever()

        except Exception as e:

            print(
                f"[PCM] Server error: {e}"
            )

    def start(self):

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        self.thread.start()

        time.sleep(1)

    def stop(self):

        if self.server:

            try:

                self.server.shutdown()

            except Exception as e:

                print(
                    f"[PCM] Shutdown error: {e}"
                )


# ============================================================
# BROWSER LOGGING
# ============================================================

def setup_browser_logging(page):

    def handle_console(message):

        try:

            print(
                f"[BROWSER:{message.type}] "
                f"{message.text}"
            )

        except Exception:
            pass

    page.on(
        "console",
        handle_console
    )


def handle_page_error(error):

    print(
        f"[BROWSER ERROR] {error}"
    )


# ============================================================
# JITSI API STATE
# ============================================================
def get_client_state(page):

    try:

        state = page.evaluate(
            """
            () => {

                if (!window.jitsiApi) {

                    return {
                        api: false,
                        participant_count: 0,
                        participants: []
                    };
                }

                const participantMap =
                    window.jitsiApi._participants || {};

                const participants =
                    Object.entries(
                        participantMap
                    ).map(
                        ([participantId, participant]) => {

                            return {
                                id: participantId,

                                displayName:
                                    participant.displayName ||
                                    participant.name ||
                                    ""
                            };
                        }
                    );

                return {
                    api: true,

                    participant_count:
                        window.jitsiApi._numberOfParticipants || 0,

                    participants:
                        participants
                };
            }
            """
        )

        return state

    except Exception as e:

        print(
            f"[BOT] Error reading Jitsi state: {e}"
        )

        return {
            "api": False,
            "participant_count": 0,
            "participants": []
        }

# ============================================================
# WAIT FOR JITSI API
# ============================================================

def wait_for_jitsi_api(page):

    print(
        "[BOT] Waiting for Jitsi IFrame API..."
    )

    try:

        page.wait_for_function(
            """
            () => (
                window.jitsiApi !== undefined &&
                window.jitsiApi !== null
            )
            """,
            timeout=30000
        )

        print(
            "[BOT] Jitsi IFrame API detected."
        )

        return True

    except Exception as e:

        print(
            f"[BOT] Jitsi API was not detected: {e}"
        )

        return False


# ============================================================
# PARTICIPANT MONITORING
# ============================================================

def monitor_participants(
    page,
    duration_seconds
):

    start_time = time.time()

    last_count = -1
    last_participants = None

    print(
        "[BOT] Starting participant monitoring."
    )

    while (
        time.time() - start_time
        < duration_seconds
    ):

        try:

            state = get_client_state(
                page
            )

            if not state.get("api"):

                time.sleep(1)

                continue

            participant_count = state.get(
                "participant_count",
                0
            )

            participants = state.get(
                "participants",
                []
            )

            # ------------------------------------------------
            # SAVE PARTICIPANTS
            # ------------------------------------------------

            save_participants(
                participants
            )

            # ------------------------------------------------
            # CREATE DISPLAY SNAPSHOT
            # ------------------------------------------------

            participant_snapshot = []

            for participant in participants:

                if not isinstance(
                    participant,
                    dict
                ):
                    continue

                participant_id = (
                    participant.get("id")
                    or participant.get("participantId")
                    or participant.get("jid")
                )

                display_name = (
                    participant.get("displayName")
                    or participant.get("name")
                    or ""
                )

                if participant_id:

                    participant_snapshot.append(
                        (
                            str(participant_id),
                            str(display_name)
                        )
                    )

            participant_snapshot = sorted(
                participant_snapshot
            )

            # ------------------------------------------------
            # PRINT ONLY WHEN SOMETHING CHANGES
            # ------------------------------------------------

            if (
                participant_count != last_count
                or participant_snapshot
                != last_participants
            ):

                print(
                    f"[BOT] Participants: "
                    f"{participant_count}"
                )

                for (
                    participant_id,
                    display_name
                ) in participant_snapshot:

                    print(
                        f"[BOT]   "
                        f"{participant_id} "
                        f"-> "
                        f"{display_name}"
                    )

                last_count = participant_count

                last_participants = (
                    participant_snapshot
                )

        except Exception as e:

            print(
                f"[BOT] Participant monitoring "
                f"error: {e}"
            )

        time.sleep(2)


# ============================================================
# FINAL ANALYSIS
# ============================================================

def run_final_analysis():

    print(
        "[BOT] Starting final transcript analysis..."
    )

    if not os.path.exists(
        TRANSCRIPT_PATH
    ):

        print(
            "[BOT] Transcript file does not exist."
        )

        return

    try:

        with open(
            TRANSCRIPT_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            transcript = f.read()

    except Exception as e:

        print(
            f"[BOT] Could not read transcript: {e}"
        )

        return

    if not transcript.strip():

        print(
            "[BOT] Transcript is empty."
        )

        return

    try:

        analysis = analyze_transcript(
            transcript
        )

        if not isinstance(
            analysis,
            dict
        ):

            print(
                "[BOT] Analyzer did not return "
                "a JSON object."
            )

            return

        meeting_state = MeetingState()

        meeting_state.update(
            analysis
        )

        with open(
            STATE_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                meeting_state.__dict__,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(
            f"[BOT] Meeting state saved to: "
            f"{STATE_PATH}"
        )

    except Exception as e:

        print(
            f"[BOT] Final analysis failed: {e}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    global transcriber
    global pcm_server

    # --------------------------------------------------------
    # ROOM ARGUMENT
    # --------------------------------------------------------

    if len(sys.argv) < 2:

        print(
            "Usage: python jitsi-bot.py ROOM_NAME"
        )

        print(
            "Example: "
            "python jitsi-bot.py TEST1234"
        )

        sys.exit(1)

    room_name = sys.argv[1]

    print(
        "=================================================="
    )

    print(
        " Meeting Minute Bot"
    )

    print(
        f" Room: {room_name}"
    )

    print(
        "=================================================="
    )

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------

    ensure_recordings_directory()

    reset_recordings()

    # --------------------------------------------------------
    # TRANSCRIBER
    # --------------------------------------------------------

    print(
        "[BOT] Starting transcriber..."
    )

    transcriber = LiveJitsiTranscriber()

    # --------------------------------------------------------
    # PCM SERVER
    # --------------------------------------------------------

    pcm_server = PCMServer(
        PCM_HOST,
        PCM_PORT,
        transcriber
    )

    pcm_server.start()

    # --------------------------------------------------------
    # PLAYWRIGHT
    # --------------------------------------------------------

    with sync_playwright() as p:

        browser = None

        try:

            print(
                "[BOT] Launching Chromium..."
            )

            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--autoplay-policy=no-user-gesture-required",
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-sandbox"
                ]
            )

            context = browser.new_context(
                ignore_https_errors=True
            )

            context.grant_permissions(
                [
                    "microphone",
                    "camera"
                ],
                origin=CLIENT_URL
            )

            page = context.new_page()

            setup_browser_logging(
                page
            )

            page.on(
                "pageerror",
                handle_page_error
            )

            # ------------------------------------------------
            # OPEN LOCAL JITSI WRAPPER
            # ------------------------------------------------

            room_url = (
                f"{CLIENT_URL.rstrip('/')}"
                f"/?room={room_name}"
            )

            print(
                f"[BOT] Opening: {room_url}"
            )

            page.goto(
                room_url,
                wait_until="domcontentloaded"
            )

            print(
                "[BOT] Wrapper page loaded."
            )

            # ------------------------------------------------
            # WAIT FOR JITSI API
            # ------------------------------------------------

            if not wait_for_jitsi_api(
                page
            ):

                print(
                    "[BOT] Cannot continue "
                    "without Jitsi API."
                )

                return

            # ------------------------------------------------
            # GIVE JITSI TIME TO JOIN
            # ------------------------------------------------

            print(
                "[BOT] Waiting for conference..."
            )

            page.wait_for_timeout(
                5000
            )

            # ------------------------------------------------
            # INITIAL STATE
            # ------------------------------------------------

            initial_state = get_client_state(
                page
            )

            print(
                "[BOT] Initial Jitsi state:"
            )

            print(
                json.dumps(
                    initial_state,
                    indent=2,
                    ensure_ascii=False
                )
            )

            save_participants(
                initial_state.get(
                    "participants",
                    []
                )
            )

            # ------------------------------------------------
            # MONITOR PARTICIPANTS
            # ------------------------------------------------

            monitor_participants(
                page,
                BOT_DURATION_SECONDS
            )

        except KeyboardInterrupt:

            print(
                "[BOT] Interrupted by user."
            )

        except Exception as e:

            print(
                f"[BOT] Fatal error: {e}"
            )

        finally:

            print(
                "[BOT] Cleaning up..."
            )

            # ------------------------------------------------
            # BROWSER
            # ------------------------------------------------

            if browser:

                try:

                    browser.close()

                except Exception as e:

                    print(
                        f"[BOT] Browser cleanup "
                        f"error: {e}"
                    )

            # ------------------------------------------------
            # PCM SERVER
            # ------------------------------------------------

            if pcm_server:

                try:

                    pcm_server.stop()

                except Exception as e:

                    print(
                        f"[BOT] PCM cleanup "
                        f"error: {e}"
                    )

            # ------------------------------------------------
            # TRANSCRIBER
            # ------------------------------------------------

            if transcriber:

                try:

                    transcriber.stop()

                except Exception as e:

                    print(
                        f"[BOT] Transcriber cleanup "
                        f"error: {e}"
                    )

    # --------------------------------------------------------
    # FINAL ANALYSIS
    # --------------------------------------------------------

    run_final_analysis()

    print(
        "[BOT] Meeting bot finished."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()