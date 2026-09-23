#!/usr/bin/env python3

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty
from typing import Callable

import numpy as np
from faster_whisper import WhisperModel


# ============================================================
# CONFIGURATION
# ============================================================

SAMPLE_RATE = 16_000
CHANNELS = 1
BYTES_PER_SAMPLE = 2

# Transcribe every 4 seconds initially.
WINDOW_SECONDS = 4
WINDOW_SAMPLES = SAMPLE_RATE * WINDOW_SECONDS
WINDOW_BYTES = WINDOW_SAMPLES * BYTES_PER_SAMPLE

MODEL_SIZE = "small"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Your meetings are expected to be French.
# Set to None for automatic language detection.
LANGUAGE = "fr"

# Ignore very quiet audio.
RMS_THRESHOLD = 0.003

PROJECT_DIR = Path.home() / "meeting-assistant"
RECORDINGS_DIR = PROJECT_DIR / "recordings"
TRANSCRIPT_FILE = RECORDINGS_DIR / "live_transcript.txt"


# ============================================================
# PARTICIPANT STATE
# ============================================================

@dataclass
class ParticipantState:
    participant_id: str

    buffer: bytearray = field(
        default_factory=bytearray
    )

    buffer_start_time: float | None = None

    total_audio_seconds: float = 0.0


# ============================================================
# TRANSCRIPTION JOB
# ============================================================

@dataclass
class TranscriptionJob:
    participant_id: str
    pcm_bytes: bytes
    start_time: float


# ============================================================
# LIVE TRANSCRIBER
# ============================================================

class LiveJitsiTranscriber:

    def __init__(
        self,
        on_transcript: Callable[
            [str, float, float, str],
            None
        ] | None = None,
    ):

        self.on_transcript = (
            on_transcript
        )

        self.meeting_start = (
            time.monotonic()
        )

        self.participants: dict[
            str,
            ParticipantState
        ] = {}

        self.lock = threading.Lock()

        self.jobs: Queue[
            TranscriptionJob
        ] = Queue(
            maxsize=20
        )

        self.stop_event = threading.Event()

        self.worker = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="whisper-worker",
        )

        RECORDINGS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Start fresh for this meeting.
        TRANSCRIPT_FILE.write_text(
            "",
            encoding="utf-8",
        )

        print(
            "[WHISPER] Loading model..."
        )

        self.model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )

        print(
            "[WHISPER] Model loaded:"
            f" {MODEL_SIZE}"
            f" / {DEVICE}"
            f" / {COMPUTE_TYPE}"
        )

        self.worker.start()

    # ========================================================
    # PARTICIPANT START
    # ========================================================

    def start_participant(
        self,
        participant_id: str,
    ):

        with self.lock:

            if participant_id not in self.participants:

                self.participants[
                    participant_id
                ] = ParticipantState(
                    participant_id=participant_id
                )

                print(
                    "[WHISPER] New participant:",
                    participant_id,
                )

    # ========================================================
    # ADD PCM
    # ========================================================

    def add_pcm(
        self,
        participant_id: str,
        pcm_bytes: bytes,
    ):

        if not pcm_bytes:
            return

        self.start_participant(
            participant_id
        )

        jobs_to_enqueue = []

        with self.lock:

            state = self.participants[
                participant_id
            ]

            # Record when the current
            # transcription window began.
            if (
                state.buffer_start_time
                is None
            ):

                state.buffer_start_time = (
                    time.monotonic()
                    - self.meeting_start
                )

            state.buffer.extend(
                pcm_bytes
            )

            # ------------------------------------------------
            # Extract complete 4-second windows
            # ------------------------------------------------

            while (
                len(state.buffer)
                >= WINDOW_BYTES
            ):

                chunk = bytes(
                    state.buffer[
                        :WINDOW_BYTES
                    ]
                )

                del state.buffer[
                    :WINDOW_BYTES
                ]

                start_time = (
                    state.buffer_start_time
                )

                state.total_audio_seconds += (
                    WINDOW_SECONDS
                )

                state.buffer_start_time = (
                    start_time
                    + WINDOW_SECONDS
                )

                jobs_to_enqueue.append(
                    TranscriptionJob(
                        participant_id=participant_id,
                        pcm_bytes=chunk,
                        start_time=start_time,
                    )
                )

        # Queue jobs outside the state lock.
        for job in jobs_to_enqueue:

            try:

                self.jobs.put_nowait(
                    job
                )

            except Exception:

                print(
                    "[WHISPER] WARNING: "
                    "transcription queue full; "
                    "dropping audio window for",
                    participant_id,
                )

    # ========================================================
    # FLUSH PARTICIPANT
    # ========================================================

    def flush_participant(
        self,
        participant_id: str,
    ):

        with self.lock:

            state = self.participants.get(
                participant_id
            )

            if state is None:
                return

            if len(state.buffer) == 0:
                return

            # Don't transcribe extremely tiny fragments.
            if (
                len(state.buffer)
                < SAMPLE_RATE
                * BYTES_PER_SAMPLE
                // 2
            ):
                state.buffer.clear()
                state.buffer_start_time = None
                return

            chunk = bytes(
                state.buffer
            )

            start_time = (
                state.buffer_start_time
                if state.buffer_start_time
                is not None
                else (
                    time.monotonic()
                    - self.meeting_start
                )
            )

            state.buffer.clear()
            state.buffer_start_time = None

        try:

            self.jobs.put_nowait(
                TranscriptionJob(
                    participant_id=participant_id,
                    pcm_bytes=chunk,
                    start_time=start_time,
                )
            )

        except Exception:

            print(
                "[WHISPER] Could not queue "
                "final audio window for",
                participant_id,
            )

    # ========================================================
    # FLUSH ALL
    # ========================================================

    def flush_all(self):

        with self.lock:

            participant_ids = list(
                self.participants.keys()
            )

        for participant_id in participant_ids:

            self.flush_participant(
                participant_id
            )

    # ========================================================
    # WORKER
    # ========================================================

    def _worker_loop(self):

        print(
            "[WHISPER] Worker started."
        )

        while not self.stop_event.is_set():

            try:

                job = self.jobs.get(
                    timeout=0.5
                )

            except Empty:

                continue

            try:

                self._transcribe_job(
                    job
                )

            except Exception as exc:

                print(
                    "[WHISPER] Transcription error:",
                    exc,
                )

            finally:

                self.jobs.task_done()

        print(
            "[WHISPER] Worker stopped."
        )

    # ========================================================
    # TRANSCRIBE
    # ========================================================

    def _transcribe_job(
        self,
        job: TranscriptionJob,
    ):

        audio = np.frombuffer(
            job.pcm_bytes,
            dtype=np.int16,
        ).astype(
            np.float32
        ) / 32768.0

        if audio.size == 0:
            return

        # ----------------------------------------------------
        # Simple silence / very-low-energy filter
        # ----------------------------------------------------

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

        if rms < RMS_THRESHOLD:

            print(
                f"[WHISPER] Silence for "
                f"{job.participant_id} "
                f"(RMS={rms:.5f})"
            )

            return

        # ----------------------------------------------------
        # Run Faster-Whisper
        #
        # transcribe() accepts a NumPy audio array.
        # ----------------------------------------------------

        inference_start = (
            time.perf_counter()
        )

        segments, info = (
            self.model.transcribe(
                audio,
                language=LANGUAGE,
                task="transcribe",
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=False,
            )
        )

        # The segments object is a generator,
        # so force evaluation here.
        segments = list(segments)

        inference_time = (
            time.perf_counter()
            - inference_start
        )

        audio_duration = (
            len(audio)
            / SAMPLE_RATE
        )

        print(
            f"[WHISPER] "
            f"participant={job.participant_id} "
            f"audio={audio_duration:.1f}s "
            f"inference={inference_time:.2f}s"
        )

        # ----------------------------------------------------
        # Emit transcript
        # ----------------------------------------------------

        for segment in segments:

            text = (
                segment.text
                .strip()
            )

            if not text:
                continue

            absolute_start = (
                job.start_time
                + float(segment.start)
            )

            absolute_end = (
                job.start_time
                + float(segment.end)
            )

            self._emit_transcript(
                participant_id=job.participant_id,
                start_time=absolute_start,
                end_time=absolute_end,
                text=text,
            )

    # ========================================================
    # EMIT TRANSCRIPT
    # ========================================================

    def _emit_transcript(
        self,
        participant_id: str,
        start_time: float,
        end_time: float,
        text: str,
    ):

        line = (
            f"[{format_timestamp(start_time)}"
            f" → "
            f"{format_timestamp(end_time)}] "
            f"{participant_id}: "
            f"{text}"
        )

        print(
            f"[TRANSCRIPT] {line}"
        )

        with open(
            TRANSCRIPT_FILE,
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                line + "\n"
            )

        if self.on_transcript:

            self.on_transcript(
                participant_id,
                start_time,
                end_time,
                text,
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        print(
            "[WHISPER] Flushing remaining audio..."
        )

        self.flush_all()

        # Wait for queued jobs.
        self.jobs.join()

        self.stop_event.set()

        self.worker.join(
            timeout=10
        )

        print(
            "[WHISPER] Transcriber stopped."
        )


# ============================================================
# TIMESTAMP
# ============================================================

def format_timestamp(
    seconds: float,
) -> str:

    total_seconds = max(
        0,
        int(seconds)
    )

    hours = (
        total_seconds
        // 3600
    )

    minutes = (
        total_seconds % 3600
        // 60
    )

    secs = (
        total_seconds % 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}"
    )