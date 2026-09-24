import os
import sys
import json

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QHeaderView,
    QGroupBox,
    QSizePolicy,
)

from meeting_controller import MeetingController


class MeetingAssistantGUI(QWidget):

    def __init__(self):

        super().__init__()

        self.controller = MeetingController()

        self.setWindowTitle(
            "AI Meeting Assistant"
        )

        self.resize(
            1100,
            850
        )

        self.setup_ui()
        self.setup_timer()




    # ============================================================
    # UI SETUP
    # ============================================================

    def setup_ui(self):

        # --------------------------------------------------------
        # Main scroll area
        # --------------------------------------------------------

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()

        self.main_layout = QVBoxLayout(
            content
        )

        scroll.setWidget(
            content
        )

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.addWidget(
            scroll
        )

        # ========================================================
        # TITLE
        # ========================================================

        title = QLabel(
            "AI Meeting Assistant"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: bold;
                padding: 15px;
            }
        """)

        self.main_layout.addWidget(
            title
        )

        # ========================================================
        # MEETING INFORMATION
        # ========================================================

        meeting_group = QGroupBox(
            "Meeting Information"
        )

        meeting_layout = QFormLayout()

        self.meeting_name_input = QLineEdit()

        self.meeting_name_input.setPlaceholderText(
            "Enter meeting name"
        )

        self.room_input = QLineEdit()

        self.room_input.setPlaceholderText(
            "Enter Jitsi room name"
        )

        meeting_layout.addRow(
            "Meeting Name:",
            self.meeting_name_input
        )

        meeting_layout.addRow(
            "Jitsi Room:",
            self.room_input
        )

        meeting_group.setLayout(
            meeting_layout
        )

        self.main_layout.addWidget(
            meeting_group
        )

        # ========================================================
        # MEETING CONTROLS
        # ========================================================

        controls_group = QGroupBox(
            "Meeting Controls"
        )

        controls_layout = QHBoxLayout()

        self.start_button = QPushButton(
            "Start Bot"
        )

        self.stop_button = QPushButton(
            "Stop Bot"
        )

        self.stop_button.setEnabled(
            False
        )

        self.start_button.clicked.connect(
            self.start_meeting
        )

        self.stop_button.clicked.connect(
            self.stop_meeting
        )

        controls_layout.addWidget(
            self.start_button
        )

        controls_layout.addWidget(
            self.stop_button
        )

        controls_group.setLayout(
            controls_layout
        )

        self.main_layout.addWidget(
            controls_group
        )

        # ========================================================
        # STATUS
        # ========================================================

        status_group = QGroupBox(
            "Status"
        )

        status_layout = QVBoxLayout()

        self.status_label = QLabel(
            "Status: Ready"
        )

        self.status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        status_layout.addWidget(
            self.status_label
        )

        status_group.setLayout(
            status_layout
        )

        self.main_layout.addWidget(
            status_group
        )

        # ========================================================
        # PARTICIPANTS
        # ========================================================

        participants_group = QGroupBox(
            "Participants"
        )

        participants_layout = QVBoxLayout()

        self.participant_table = QTableWidget()


        self.participant_table.setMinimumHeight(180)
        self.participant_table.setMaximumHeight(250)

        # Only two columns now.
        self.participant_table.setColumnCount(
            2
        )

        self.participant_table.setHorizontalHeaderLabels([
            "Participant ID",
            "Jitsi Name",
        ])

        # --------------------------------------------------------
        # IMPORTANT:
        # Select individual cells instead of entire rows.
        # --------------------------------------------------------

        self.participant_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectItems
        )

        # --------------------------------------------------------
        # Editing is disabled.
        #
        # Participant ID and Jitsi Name are both read-only.
        # --------------------------------------------------------

        self.participant_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # --------------------------------------------------------
        # Column sizes
        # --------------------------------------------------------

        header = (
            self.participant_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch
        )

        participants_layout.addWidget(
            self.participant_table
        )

        participants_group.setLayout(
            participants_layout
        )

        self.main_layout.addWidget(
            participants_group
        )

        # ========================================================
        # LIVE TRANSCRIPT
        # ========================================================

        transcript_group = QGroupBox(
            "Live Transcript"
        )

        transcript_layout = QVBoxLayout()

        self.transcript_text = QTextEdit()

        self.transcript_text.setReadOnly(
            True
        )

        self.transcript_text.setMinimumHeight(
            250
        )

        transcript_layout.addWidget(
            self.transcript_text
        )

        transcript_group.setLayout(
            transcript_layout
        )

        self.main_layout.addWidget(
            transcript_group
        )

        # ========================================================
        # FINAL OUTPUT
        # ========================================================

        output_group = QGroupBox(
            "Final Meeting Output"
        )

        output_layout = QVBoxLayout()

        # --------------------------------------------------------
        # Summary
        # --------------------------------------------------------

        output_layout.addWidget(
            QLabel("Summary")
        )

        self.summary_edit = QTextEdit()

        self.summary_edit.setMinimumHeight(
            120
        )

        output_layout.addWidget(
            self.summary_edit
        )

        # --------------------------------------------------------
        # Topics
        # --------------------------------------------------------

        output_layout.addWidget(
            QLabel("Topics")
        )

        self.topics_edit = QTextEdit()

        self.topics_edit.setMinimumHeight(
            100
        )

        output_layout.addWidget(
            self.topics_edit
        )

        # --------------------------------------------------------
        # Decisions
        # --------------------------------------------------------

        output_layout.addWidget(
            QLabel("Decisions")
        )

        self.decisions_edit = QTextEdit()

        self.decisions_edit.setMinimumHeight(
            100
        )

        output_layout.addWidget(
            self.decisions_edit
        )

        # --------------------------------------------------------
        # Action Items
        # --------------------------------------------------------

        output_layout.addWidget(
            QLabel("Action Items")
        )

        self.action_items_edit = QTextEdit()

        self.action_items_edit.setMinimumHeight(
            100
        )

        output_layout.addWidget(
            self.action_items_edit
        )

        # --------------------------------------------------------
        # Open Questions
        # --------------------------------------------------------

        output_layout.addWidget(
            QLabel("Open Questions")
        )

        self.open_questions_edit = QTextEdit()

        self.open_questions_edit.setMinimumHeight(
            100
        )

        output_layout.addWidget(
            self.open_questions_edit
        )

        output_group.setLayout(
            output_layout
        )

        self.main_layout.addWidget(
            output_group
        )

        # ========================================================
        # OUTPUT BUTTONS
        # ========================================================

        buttons_group = QGroupBox(
            "Output"
        )

        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton(
            "Save Output"
        )

        self.pdf_button = QPushButton(
            "Export PDF"
        )

        self.docx_button = QPushButton(
            "Export DOCX"
        )

        self.save_button.clicked.connect(
            self.save_output
        )

        self.pdf_button.clicked.connect(
            self.export_pdf
        )

        self.docx_button.clicked.connect(
            self.export_docx
        )

        buttons_layout.addWidget(
            self.save_button
        )

        buttons_layout.addWidget(
            self.pdf_button
        )

        buttons_layout.addWidget(
            self.docx_button
        )

        buttons_group.setLayout(
            buttons_layout
        )

        self.main_layout.addWidget(
            buttons_group
        )

        # ========================================================
        # SPACING
        # ========================================================

        self.main_layout.addStretch()

    # ============================================================
    # TIMER
    # ============================================================

    def setup_timer(self):

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.refresh_live_data
        )

        # Refresh every second.
        self.timer.start(
            1000
        )



    # ============================================================
    # START MEETING
    # ============================================================

    def start_meeting(self):

        meeting_name = (
            self.meeting_name_input
            .text()
            .strip()
        )

        room_name = (
            self.room_input
            .text()
            .strip()
        )

        if not meeting_name:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a meeting name."
            )
            return

        if not room_name:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter the Jitsi room name."
            )
            return

        try:
            # ============================================================
            # START NEW MEETING
            # ============================================================

            success = self.controller.start_meeting(
                meeting_name,
                room_name
            )

            if not success:
                QMessageBox.warning(
                    self,
                    "Error",
                    "The meeting could not be started."
                )
                return

            # ============================================================
            # UPDATE GUI STATE
            # ============================================================

            self.start_button.setEnabled(False)

            self.stop_button.setEnabled(True)

            self.meeting_name_input.setEnabled(False)

            self.room_input.setEnabled(False)

            self.status_label.setText(
                "Status: Meeting running"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Could not start meeting:\n\n{e}"
            )

    # ============================================================
    # STOP MEETING
    # ============================================================

    def stop_meeting(self):

        try:

            self.controller.stop_meeting()

            self.start_button.setEnabled(
                True
            )

            self.stop_button.setEnabled(
                False
            )

            self.meeting_name_input.setEnabled(
                True
            )

            self.room_input.setEnabled(
                True
            )

            self.status_label.setText(
                "Status: Meeting stopped"
            )

            # Load final generated state.
            self.load_final_output()

            # Refresh transcript and participants.
            self.refresh_live_data()


        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Could not stop meeting:\n\n{e}"
            )

    # ============================================================
    # REFRESH LIVE DATA
    # ============================================================

    def refresh_live_data(self):

        # --------------------------------------------------------
        # TRANSCRIPT
        # --------------------------------------------------------

        try:

            transcript = (
                self.controller.get_transcript()
            )

            if (
                transcript
                != self.transcript_text.toPlainText()
            ):

                self.transcript_text.setPlainText(
                    transcript
                )

                cursor = (
                    self.transcript_text.textCursor()
                )

                cursor.movePosition(
                    cursor.MoveOperation.End
                )

                self.transcript_text.setTextCursor(
                    cursor
                )

        except Exception as e:

            print(
                f"[GUI] Transcript refresh error: {e}"
            )

        # --------------------------------------------------------
        # PARTICIPANTS
        # --------------------------------------------------------

        try:

            self.refresh_participants()

        except Exception as e:

            print(
                f"[GUI] Participant refresh error: {e}"
            )

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        try:

            if self.controller.running:

                self.status_label.setText(
                    "Status: Meeting running"
                )

        except Exception as e:

            print(
                f"[GUI] Status refresh error: {e}"
            )

    # ============================================================
    # PARTICIPANT TABLE
    # ============================================================

    def refresh_participants(self):

        participants = (
            self.controller.get_participants()
        )

        print(
            "[GUI] Participants received:",
            participants
        )

        # --------------------------------------------------------
        # Block signals while modifying the table.
        # --------------------------------------------------------

        self.participant_table.blockSignals(
            True
        )

        try:

            self.participant_table.setRowCount(
                0
            )

            for (
                participant_id,
                participant_data
            ) in participants.items():

                row = (
                    self.participant_table.rowCount()
                )

                self.participant_table.insertRow(
                    row
                )

                # =================================================
                # PARTICIPANT ID
                # =================================================

                id_item = QTableWidgetItem(
                    str(participant_id)
                )

                # Store ID internally.
                id_item.setData(
                    Qt.ItemDataRole.UserRole,
                    participant_id
                )

                # ID is read-only.
                id_item.setFlags(
                    id_item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                )

                self.participant_table.setItem(
                    row,
                    0,
                    id_item
                )

                # =================================================
                # JITSI NAME
                # =================================================

                if isinstance(
                    participant_data,
                    dict
                ):

                    jitsi_name = str(
                        participant_data.get(
                            "jitsi_name",
                            ""
                        )
                    )

                else:

                    jitsi_name = str(
                        participant_data
                    )

                jitsi_item = QTableWidgetItem(
                    jitsi_name
                )

                # Jitsi name is read-only.
                jitsi_item.setFlags(
                    jitsi_item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                )

                self.participant_table.setItem(
                    row,
                    1,
                    jitsi_item
                )

        finally:

            self.participant_table.blockSignals(
                False
            )

    # ============================================================
    # CLEAR FINAL OUTPUT
    # ============================================================

    def clear_final_output(self):

        self.summary_edit.clear()

        self.topics_edit.clear()

        self.decisions_edit.clear()

        self.action_items_edit.clear()

        self.open_questions_edit.clear()

    # ============================================================
    # LOAD FINAL OUTPUT
    # ============================================================

    def load_final_output(self):

        try:

            state = (
                self.controller.get_meeting_state()
            )

            if not state:

                return

            # ----------------------------------------------------
            # Handle both a MeetingState object and a dictionary.
            # ----------------------------------------------------

            if isinstance(
                state,
                dict
            ):

                summary = state.get(
                    "summary",
                    ""
                )

                topics = state.get(
                    "topics",
                    []
                )

                decisions = state.get(
                    "decisions",
                    []
                )

                action_items = state.get(
                    "action_items",
                    []
                )

                open_questions = state.get(
                    "open_questions",
                    []
                )

            else:

                summary = getattr(
                    state,
                    "summary",
                    ""
                )

                topics = getattr(
                    state,
                    "topics",
                    []
                )

                decisions = getattr(
                    state,
                    "decisions",
                    []
                )

                action_items = getattr(
                    state,
                    "action_items",
                    []
                )

                open_questions = getattr(
                    state,
                    "open_questions",
                    []
                )

            # ----------------------------------------------------
            # Display
            # ----------------------------------------------------

            self.summary_edit.setPlainText(
                summary or ""
            )

            self.topics_edit.setPlainText(
                self.format_list(
                    topics
                )
            )

            self.decisions_edit.setPlainText(
                self.format_list(
                    decisions
                )
            )

            self.action_items_edit.setPlainText(
                self.format_list(
                    action_items
                )
            )

            self.open_questions_edit.setPlainText(
                self.format_list(
                    open_questions
                )
            )

        except Exception as e:

            print(
                f"[GUI] Could not load final output: {e}"
            )

    # ============================================================
    # FORMAT LIST
    # ============================================================

    @staticmethod
    def format_list(value):

        if value is None:

            return ""

        if isinstance(
            value,
            list
        ):

            return "\n".join(
                f"• {str(item)}"
                for item in value
            )

        return str(value)

    # ============================================================
    # READ FINAL OUTPUT FROM GUI
    # ============================================================

    def get_final_output(self):

        summary = (
            self.summary_edit
            .toPlainText()
            .strip()
        )

        topics = self.text_to_list(
            self.topics_edit.toPlainText()
        )

        decisions = self.text_to_list(
            self.decisions_edit.toPlainText()
        )

        action_items = self.text_to_list(
            self.action_items_edit.toPlainText()
        )

        open_questions = self.text_to_list(
            self.open_questions_edit.toPlainText()
        )

        return (
            summary,
            topics,
            decisions,
            action_items,
            open_questions
        )

    # ============================================================
    # TEXT → LIST
    # ============================================================

    @staticmethod
    def text_to_list(text):

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:

                continue

            # Remove display bullet.
            if line.startswith("•"):

                line = line[1:].strip()

            elif line.startswith("-"):

                line = line[1:].strip()

            lines.append(
                line
            )

        return lines

    # ============================================================
    # SAVE OUTPUT
    # ============================================================

    def save_output(self):

        try:

            (
                summary,
                topics,
                decisions,
                action_items,
                open_questions
            ) = self.get_final_output()

            self.controller.update_final_output(
                summary,
                topics,
                decisions,
                action_items,
                open_questions
            )

            QMessageBox.information(
                self,
                "Saved",
                "Meeting output saved successfully."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Could not save meeting output:\n\n{e}"
            )

    # ============================================================
    # EXPORT PDF
    # ============================================================

    def export_pdf(self):

        try:

            (
                summary,
                topics,
                decisions,
                action_items,
                open_questions
            ) = self.get_final_output()

            self.controller.update_final_output(
                summary,
                topics,
                decisions,
                action_items,
                open_questions
            )

            default_name = (
                self.meeting_name_input
                .text()
                .strip()
                or "meeting"
            )

            default_name += ".pdf"

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export PDF",
                default_name,
                "PDF Files (*.pdf)"
            )

            if not path:

                return

            self.controller.export_pdf(
                path
            )

            QMessageBox.information(
                self,
                "Export Complete",
                f"PDF exported successfully:\n\n{path}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Export Error",
                f"Could not export PDF:\n\n{e}"
            )

    # ============================================================
    # EXPORT DOCX
    # ============================================================

    def export_docx(self):

        try:

            (
                summary,
                topics,
                decisions,
                action_items,
                open_questions
            ) = self.get_final_output()

            self.controller.update_final_output(
                summary,
                topics,
                decisions,
                action_items,
                open_questions
            )

            default_name = (
                self.meeting_name_input
                .text()
                .strip()
                or "meeting"
            )

            default_name += ".docx"

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export DOCX",
                default_name,
                "Word Documents (*.docx)"
            )

            if not path:

                return

            self.controller.export_docx(
                path
            )

            QMessageBox.information(
                self,
                "Export Complete",
                f"DOCX exported successfully:\n\n{path}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Export Error",
                f"Could not export DOCX:\n\n{e}"
            )

    # ============================================================
    # CLOSE EVENT
    # ============================================================

    def closeEvent(
        self,
        event
    ):

        try:

            if self.controller.running:

                reply = QMessageBox.question(
                    self,
                    "Meeting Running",
                    "A meeting is currently running. "
                    "Do you want to stop it and close the application?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                )

                if (
                    reply
                    == QMessageBox.StandardButton.No
                ):

                    event.ignore()

                    return

                self.controller.stop_meeting()

        except Exception as e:

            print(
                f"[GUI] Error while closing: {e}"
            )

        event.accept()


# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

def run():


    app = QApplication.instance()

    if app is None:

        app = QApplication(
            sys.argv
        )

    window = MeetingAssistantGUI()

    window.show()

    return app.exec()


# ================================================================
# DIRECT EXECUTION
# ================================================================

if __name__ == "__main__":

    sys.exit(
        run()
    )