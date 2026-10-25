"""Send a WAV file to a Wyoming STT server and print the transcript and latency.

Usage: python script/transcribe_wav.py file.wav [--uri tcp://127.0.0.1:10300]
"""

import argparse
import asyncio
import time
import wave

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient

CHUNK_SAMPLES = 1024


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wav")
    parser.add_argument("--uri", default="tcp://127.0.0.1:10300")
    args = parser.parse_args()

    with wave.open(args.wav, "rb") as wav:
        rate, width, channels = wav.getframerate(), wav.getsampwidth(), wav.getnchannels()
        frames = wav.readframes(wav.getnframes())

    async with AsyncClient.from_uri(args.uri) as client:
        await client.write_event(Transcribe(language="sv").event())
        await client.write_event(AudioStart(rate=rate, width=width, channels=channels).event())
        step = CHUNK_SAMPLES * width * channels
        for i in range(0, len(frames), step):
            await client.write_event(
                AudioChunk(rate=rate, width=width, channels=channels, audio=frames[i : i + step]).event()
            )
        start = time.perf_counter()
        await client.write_event(AudioStop().event())

        while True:
            event = await client.read_event()
            if event is None:
                raise SystemExit("Connection closed without a transcript")
            if Transcript.is_type(event.type):
                elapsed = time.perf_counter() - start
                print(f"{Transcript.from_event(event).text}  ({elapsed:.2f}s after audio-stop)")
                break


if __name__ == "__main__":
    asyncio.run(main())
