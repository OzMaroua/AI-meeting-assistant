import os
import sys
import json
import subprocess

from meeting_state import MeetingState
from exporter import MeetingExporter
from config import MEETING_STATE_FILE, TRANSCRIPT_FILE


class MeetingController:

    def __init__(self):

        self.state = MeetingState()
        self.running = False

        # participant_id -> Jitsi name
        self.participants = {}

        # participant_id -> user-defined display name
        self.participant_names = {}

        self.meeting_name = ""
        self.room_name = ""

        self.transcript_file = TRANSCRIPT_FILE
        self.state_file = MEETING_STATE_FILE

        # --------------------------------------------------------
        # Make sure recordings directory exists
        # --------------------------------------------------------

        base_dir = os.path.dirname(
            os.path.abspath(
                self.transcript_file
            )
        )

        os.makedirs(
            base_dir,
            exist_ok=True
        )

        state_dir = os.path.dirname(
            os.path.abspath(
                self.state_file
            )
        )

        os.makedirs(
            state_dir,
            exist_ok=True
        )

        # --------------------------------------------------------
        # Participants file
        # --------------------------------------------------------

        self.participants_file = os.path.join(
            os.path.dirname(
                os.path.abspath(
                    self.transcript_file
                )
            ),
            "participants.json"
        )

        # --------------------------------------------------------
        # Jitsi bot process
        # --------------------------------------------------------

        self.bot_process = None

        self.project_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.bot_script = os.path.join(
            self.project_dir,
            "jitsi-bot.py"
        )

        self.bot_log_file = None



    # ============================================================
    # START MEETING
    # ============================================================

    def start_meeting(
        self,
        meeting_name,
        room_name
    ):

        if self.running:

            raise RuntimeError(
                "A meeting is already running."
            )

        room_name = room_name.strip()

        if not room_name:

            raise ValueError(
                "Jitsi room name cannot be empty."
            )

        if not os.path.exists(
            self.bot_script
        ):

            raise FileNotFoundError(
                f"Could not find jitsi-bot.py:\n"
                f"{self.bot_script}"
            )

        self.meeting_name = (
            meeting_name.strip()
            or "Untitled Meeting"
        )

        self.room_name = room_name

        # --------------------------------------------------------
        # Reset meeting state
        # --------------------------------------------------------

        self.state = MeetingState()

        self.state.meeting_name = (
            self.meeting_name
        )

        # --------------------------------------------------------
        # Reset participants
        # --------------------------------------------------------

        self.participants = {}

        self.participant_names = {}

        # --------------------------------------------------------
        # Clear previous transcript
        # --------------------------------------------------------

        with open(
            self.transcript_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write("")

        # --------------------------------------------------------
        # Clear previous participants
        # --------------------------------------------------------

        with open(
            self.participants_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                [],
                f,
                indent=2,
                ensure_ascii=False
            )

        # --------------------------------------------------------
        # Remove previous meeting state
        # --------------------------------------------------------

        if os.path.exists(
            self.state_file
        ):

            try:

                os.remove(
                    self.state_file
                )

            except OSError:

                pass

        # ========================================================
        # BOT LOG
        # ========================================================

        log_path = os.path.join(
            os.path.dirname(
                os.path.abspath(
                    self.transcript_file
                )
            ),
            "bot.log"
        )

        self.bot_log_file = open(
            log_path,
            "w",
            encoding="utf-8"
        )

        # ========================================================
        # START JITSI BOT
        # ========================================================

        command = [
            sys.executable,
            self.bot_script,
            self.room_name
        ]

        try:

            self.bot_process = subprocess.Popen(
                command,
                cwd=self.project_dir,
                stdout=self.bot_log_file,
                stderr=subprocess.STDOUT
            )

        except Exception as e:

            self.bot_log_file.close()

            self.bot_log_file = None

            raise RuntimeError(
                f"Could not start Jitsi bot: {e}"
            )

        self.running = True

        print(
            f"[CONTROLLER] Meeting started: "
            f"{self.meeting_name}"
        )

        print(
            f"[CONTROLLER] Jitsi room: "
            f"{self.room_name}"
        )

        print(
            f"[CONTROLLER] Bot PID: "
            f"{self.bot_process.pid}"
        )


        return True

    # ============================================================
    # STOP MEETING
    # ============================================================

    def stop_meeting(self):

        if not self.running:

            return

        print(
            "[CONTROLLER] Stopping meeting..."
        )

        self.running = False

        # ========================================================
        # STOP BOT PROCESS
        # ========================================================

        if self.bot_process is not None:

            if self.bot_process.poll() is None:

                try:

                    self.bot_process.terminate()

                    self.bot_process.wait(
                        timeout=15
                    )

                except subprocess.TimeoutExpired:

                    print(
                        "[CONTROLLER] Bot did not "
                        "terminate gracefully. Killing it."
                    )

                    try:

                        self.bot_process.kill()

                        self.bot_process.wait()

                    except Exception:

                        pass

                except Exception as e:

                    print(
                        "[CONTROLLER] Error stopping bot: "
                        f"{e}"
                    )

            self.bot_process = None

        # ========================================================
        # CLOSE BOT LOG
        # ========================================================

        if self.bot_log_file is not None:

            try:

                self.bot_log_file.close()

            except Exception:

                pass

            self.bot_log_file = None

        # ========================================================
        # LOAD FINAL PARTICIPANT INFORMATION
        # ========================================================

        self.update_participants()

        # ========================================================
        # LOAD FINAL MEETING STATE
        # ========================================================

        self.load_meeting_state()

        # --------------------------------------------------------
        # Make sure manually assigned names are preserved
        # --------------------------------------------------------

        self.state.participants = dict(
            self.participant_names
        )

        self.save_state()

        print(
            "[CONTROLLER] Meeting stopped."
        )

    # ============================================================
    # BOT STATUS
    # ============================================================

    def is_bot_running(self):

        if self.bot_process is None:

            return False

        return (
            self.bot_process.poll() is None
        )

    # ============================================================
    # PARTICIPANTS
    # ============================================================

    def update_participants(self):

        if not os.path.exists(
            self.participants_file
        ):

            return []

        try:

            with open(
                self.participants_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except json.JSONDecodeError:

            print(
                "[CONTROLLER] participants.json "
                "is not valid JSON yet."
            )

            return []

        except OSError as e:

            print(
                "[CONTROLLER] Error reading "
                f"participants.json: {e}"
            )

            return []

        # --------------------------------------------------------
        # Expected format:
        #
        # [
        #     {
        #         "id": "062bb62f",
        #         "displayName": "Alice"
        #     }
        # ]
        # --------------------------------------------------------

        if not isinstance(
            data,
            list
        ):

            return []

        new_participants = {}

        for participant in data:

            if not isinstance(
                participant,
                dict
            ):

                continue

            # ----------------------------------------------------
            # Participant ID
            # ----------------------------------------------------

            participant_id = str(
                participant.get(
                    "id",
                    ""
                )
            ).strip()

            if not participant_id:

                continue

            # ----------------------------------------------------
            # Jitsi display name
            # ----------------------------------------------------

            jitsi_name = str(
                participant.get(
                    "displayName",
                    participant.get(
                        "jitsi_name",
                        participant.get(
                            "name",
                            ""
                        )
                    )
                )
            ).strip()

            # ----------------------------------------------------
            # Store participant
            # ----------------------------------------------------

            new_participants[
                participant_id
            ] = jitsi_name

            # ----------------------------------------------------
            # Only create a default user name if this participant
            # has never been manually renamed.
            # ----------------------------------------------------

            if participant_id not in (
                self.participant_names
            ):

                self.participant_names[
                    participant_id
                ] = (
                    jitsi_name
                    or participant_id
                )

        # --------------------------------------------------------
        # Replace currently detected participants.
        # --------------------------------------------------------

        self.participants = (
            new_participants
        )

        # --------------------------------------------------------
        # Update MeetingState participant mapping.
        # --------------------------------------------------------

        self.state.participants = dict(
            self.participant_names
        )

        return data

    # ============================================================
    # GET PARTICIPANTS
    # ============================================================

    def get_participants(self):

        self.update_participants()

        result = {}

        for (
            participant_id,
            jitsi_name
        ) in self.participants.items():

            result[
                participant_id
            ] = {

                "id":
                    participant_id,

                "jitsi_name":
                    jitsi_name,

                "display_name":
                    self.participant_names.get(
                        participant_id,
                        jitsi_name
                        or participant_id
                    )
            }

        print(
            "[CONTROLLER] Participants:",
            result
        )

        return result

    # ============================================================
    # SET PARTICIPANT NAME
    # ============================================================

    def set_participant_name(
        self,
        participant_id,
        name
    ):

        participant_id = str(
            participant_id
        ).strip()

        name = str(
            name
        ).strip()

        if not participant_id:

            return

        # --------------------------------------------------------
        # If user clears the field, fall back to Jitsi name
        # or participant ID.
        # --------------------------------------------------------

        if not name:

            name = self.participants.get(
                participant_id,
                participant_id
            )

        self.participant_names[
            participant_id
        ] = name

        self.state.participants = dict(
            self.participant_names
        )

        self.save_state()

        print(
            f"[CONTROLLER] Participant "
            f"{participant_id} -> {name}"
        )

    # ============================================================
    # REMOVE PARTICIPANT
    # ============================================================

    def remove_participant(
        self,
        participant_id
    ):

        participant_id = str(
            participant_id
        ).strip()

        self.participants.pop(
            participant_id,
            None
        )

        self.participant_names.pop(
            participant_id,
            None
        )

        self.state.participants = dict(
            self.participant_names
        )

        self.save_state()

    # ============================================================
    # TRANSCRIPT
    # ============================================================

    def get_transcript(self):

        if not os.path.exists(
            self.transcript_file
        ):

            return ""

        try:

            with open(
                self.transcript_file,
                "r",
                encoding="utf-8"
            ) as f:

                return f.read()

        except OSError:

            return ""

    # ============================================================
    # ANALYSIS
    # ============================================================

    def update_analysis(
        self,
        analysis
    ):

        self.state.update(
            analysis
        )

        self.state.participants = dict(
            self.participant_names
        )

        self.save_state()

    # ============================================================
    # LOAD MEETING STATE
    # ============================================================

    def load_meeting_state(self):

        if not os.path.exists(
            self.state_file
        ):

            return False

        try:

            with open(
                self.state_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except (
            json.JSONDecodeError,
            OSError
        ):

            return False

        # --------------------------------------------------------
        # Meeting name
        # --------------------------------------------------------

        if "meeting_name" in data:

            self.state.meeting_name = (
                data["meeting_name"]
            )

        # --------------------------------------------------------
        # Summary
        # --------------------------------------------------------

        if "summary" in data:

            self.state.summary = (
                data["summary"]
            )

        # --------------------------------------------------------
        # Topics
        # --------------------------------------------------------

        if "topics" in data:

            self.state.topics = (
                data["topics"]
            )

        # --------------------------------------------------------
        # Decisions
        # --------------------------------------------------------

        if "decisions" in data:

            self.state.decisions = (
                data["decisions"]
            )

        # --------------------------------------------------------
        # Action items
        # --------------------------------------------------------

        if "action_items" in data:

            self.state.action_items = (
                data["action_items"]
            )

        # --------------------------------------------------------
        # Open questions
        # --------------------------------------------------------

        if "open_questions" in data:

            self.state.open_questions = (
                data["open_questions"]
            )

        # --------------------------------------------------------
        # Participants
        # --------------------------------------------------------

        if "participants" in data:

            saved_participants = (
                data["participants"]
            )

            if isinstance(
                saved_participants,
                dict
            ):

                for (
                    participant_id,
                    name
                ) in saved_participants.items():

                    self.participant_names[
                        str(participant_id)
                    ] = str(name)

        return True

    # ============================================================
    # GET MEETING STATE
    # ============================================================

    def get_meeting_state(self):

        if os.path.exists(
            self.state_file
        ):

            self.load_meeting_state()

        return {

            "meeting_name":
                self.state.meeting_name,

            "summary":
                self.state.summary,

            "topics":
                self.state.topics,

            "decisions":
                self.state.decisions,

            "action_items":
                self.state.action_items,

            "open_questions":
                self.state.open_questions,

            "participants":
                dict(
                    self.participant_names
                )
        }

    # ============================================================
    # UPDATE FINAL OUTPUT
    # ============================================================

    def update_final_output(
        self,
        summary,
        topics,
        decisions,
        action_items,
        open_questions
    ):

        self.state.summary = summary

        self.state.topics = topics

        self.state.decisions = decisions

        self.state.action_items = (
            action_items
        )

        self.state.open_questions = (
            open_questions
        )

        self.state.participants = dict(
            self.participant_names
        )

        self.save_state()

    # ============================================================
    # SAVE STATE
    # ============================================================

    def save_state(self):

        self.state.save(
            self.state_file
        )

    # ============================================================
    # EXPORT PDF
    # ============================================================

    def export_pdf(
        self,
        path
    ):

        self.save_state()

        MeetingExporter.export_pdf(
            self.state,
            path
        )

    # ============================================================
    # EXPORT DOCX
    # ============================================================

    def export_docx(
        self,
        path
    ):

        self.save_state()

        MeetingExporter.export_docx(
            self.state,
            path
        )