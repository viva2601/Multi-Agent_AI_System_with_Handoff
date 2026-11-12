import os
import time

from supertonic import TTS  # type: ignore

MODEL_DIR = os.path.join("tts_models", "supertonic3")
TEXT = "I found two flights from Mumbai to Delhi. Flight AI202 costs 412 USD per passenger."
cores = os.cpu_count()
print("logical cores:", cores)

for threads in sorted({0, 2, 4, cores // 2, cores}):
    tts = TTS(model="supertonic-3", model_dir=MODEL_DIR, intra_op_num_threads=threads or None)
    voice = tts.get_voice_style("M1")
    tts.synthesize(TEXT, voice_style=voice, total_steps=2, lang="en")  # warm-up, not timed
    for steps in (2, 5, 8):
        start = time.time()
        wav, _ = tts.synthesize(TEXT, voice_style=voice, total_steps=steps, lang="en")
        took, audio = time.time() - start, wav.shape[1] / tts.sample_rate
        print(f"threads={threads or 'default':>7} steps={steps}  synth={took:5.2f}s  audio={audio:5.2f}s  RTF={took / audio:.2f}")
