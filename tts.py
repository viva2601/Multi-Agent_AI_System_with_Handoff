import logging
import re
import struct

import numpy as np  # type: ignore
from supertonic import TTS  # type: ignore

from config import TTS_DIR, TTS_LANG, TTS_MODEL, TTS_SPEED, TTS_STEPS, TTS_THREADS, TTS_VOICE

logger = logging.getLogger("uvicorn.error")
DOWNSAMPLE = 2  # 44.1 kHz -> 22.05 kHz: halves the audio size, like the Kokoro version; 1 = off
tts = TTS(model=TTS_MODEL, model_dir=TTS_DIR, intra_op_num_threads=TTS_THREADS or None)
voice = tts.get_voice_style(TTS_VOICE)


def _wav_header(rate):
    # WAV header with unknown length (0xFFFFFFFF), so players start before the audio ends
    return (b"RIFF" + struct.pack("<I", 0xFFFFFFFF) + b"WAVEfmt "
            + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
            + b"data" + struct.pack("<I", 0xFFFFFFFF))


def _pcm(wav):
    samples = np.clip(wav[0], -1, 1)
    if DOWNSAMPLE > 1:  # average neighbouring samples, then keep one per group
        samples = samples[: len(samples) // DOWNSAMPLE * DOWNSAMPLE].reshape(-1, DOWNSAMPLE).mean(axis=1)
    return (samples * 32767).astype(np.int16).tobytes()


def synthesize_stream(text):
    started = False
    for sentence in (s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if re.search(r"\w", s)):
        try:
            wav, _ = tts.synthesize(sentence, voice_style=voice, total_steps=TTS_STEPS, speed=TTS_SPEED, lang=TTS_LANG)
        except ValueError:  # e.g. unsupported characters: skip the sentence instead of cutting the stream
            logger.warning("TTS skipped a sentence it could not synthesize")
            continue
        if not started:
            yield _wav_header(tts.sample_rate // DOWNSAMPLE)
            started = True
        yield _pcm(wav)

