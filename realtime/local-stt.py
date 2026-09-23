import numpy as np
from faster_whisper import WhisperModel


class LocalWhisperSTT:

    def __init__(
        self,
        model_size="small",
        device="cpu",
        compute_type="int8",
        language="en"
    ):
        print("\n🧠 Loading local Whisper model...")
        print(f"Model: {model_size}")
        print(f"Device: {device}")
        print(f"Compute type: {compute_type}")
        print(f"Language: {language if language else 'auto'}\n")

        self.language = language

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

        print("✓ Local Whisper model loaded\n")

    # ============================================================
    # BASIC TRANSCRIPTION
    # ============================================================

    def transcribe(
        self,
        audio_bytes,
        sample_rate=16000
    ):
        """
        Transcribe raw PCM int16 audio.

        Returns:
            str: Transcribed text
        """

        audio = np.frombuffer(
            audio_bytes,
            dtype=np.int16
        ).astype(np.float32)

        # Convert int16 audio to float32 [-1, 1]
        audio /= 32768.0

        segments, info = self.model.transcribe(
            audio,
            beam_size=5,
            vad_filter=True,
            language=self.language
        )

        text_parts = []

        for segment in segments:

            text = segment.text.strip()

            if text:
                text_parts.append(text)

        return " ".join(text_parts)

    # ============================================================
    # TRANSCRIPTION WITH TIMESTAMPS
    # ============================================================

    def transcribe_with_timestamps(
        self,
        audio_bytes,
        sample_rate=16000
    ):
        """
        Transcribe raw PCM int16 audio and return
        Whisper segments with timestamps.

        Returns:

            [
                {
                    "start": float,
                    "end": float,
                    "text": str
                },
                ...
            ]
        """

        audio = np.frombuffer(
            audio_bytes,
            dtype=np.int16
        ).astype(np.float32)

        # Convert int16 audio to float32 [-1, 1]
        audio /= 32768.0

        segments, info = self.model.transcribe(
            audio,
            beam_size=5,
            vad_filter=True,
            language=self.language
        )

        results = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            results.append(
                {
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": text
                }
            )

        return results