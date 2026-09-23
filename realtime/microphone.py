import asyncio
import pyaudio


async def microphone_stream(
    sample_rate=16000,
    chunk_duration_ms=480
):
    """
    Capture microphone audio and yield PCM chunks.
    """

    p = pyaudio.PyAudio()

    chunk_samples = int(
        sample_rate * chunk_duration_ms / 1000
    )

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_samples,
    )

    loop = asyncio.get_running_loop()

    try:
        while True:

            data = await loop.run_in_executor(
                None,
                stream.read,
                chunk_samples,
                False
            )

            yield data

    finally:

        stream.stop_stream()
        stream.close()
        p.terminate()