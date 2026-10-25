"""Wyoming event handler: collects audio, transcribes it with Pianissimo."""

import asyncio
import logging
import time
from typing import Any, Optional

import numpy as np
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler

_LOGGER = logging.getLogger(__name__)

RATE = 16000
WIDTH = 2  # 16-bit
CHANNELS = 1


class PianissimoEventHandler(AsyncEventHandler):
    """Handles one Wyoming client connection."""

    def __init__(
        self,
        wyoming_info: Info,
        model: Any,
        model_lock: asyncio.Lock,
        pad_seconds: float,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.pad_seconds = pad_seconds
        self.wyoming_info_event = wyoming_info.event()
        self.model = model
        self.model_lock = model_lock
        self.converter = AudioChunkConverter(rate=RATE, width=WIDTH, channels=CHANNELS)
        self.audio = bytearray()
        self.language: Optional[str] = None

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_event)
            return True

        if Transcribe.is_type(event.type):
            self.language = Transcribe.from_event(event).language
            return True

        if AudioStart.is_type(event.type):
            self.audio = bytearray()
            return True

        if AudioChunk.is_type(event.type):
            chunk = self.converter.convert(AudioChunk.from_event(event))
            self.audio.extend(chunk.audio)
            return True

        if AudioStop.is_type(event.type):
            text = await self._transcribe(bytes(self.audio))
            self.audio = bytearray()
            await self.write_event(Transcript(text=text, language="sv").event())
            # One transcription per connection, as Home Assistant expects.
            return False

        return True

    async def _transcribe(self, pcm: bytes) -> str:
        if not pcm:
            return ""

        samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        seconds = len(samples) / RATE

        # The model tends to drop the first word when speech starts at sample 0
        # (tested: "Tänd lampan..." -> "lampan..."). Leading/trailing silence fixes it.
        if self.pad_seconds > 0:
            pad = np.zeros(int(RATE * self.pad_seconds), dtype=np.float32)
            samples = np.concatenate([pad, samples, pad])

        async with self.model_lock:
            start = time.perf_counter()
            text = await asyncio.to_thread(self.model.recognize, samples, sample_rate=RATE)
            elapsed = time.perf_counter() - start

        text = (text or "").strip()
        _LOGGER.info("Transcribed %.1fs audio in %.2fs: %s", seconds, elapsed, text)
        return text
