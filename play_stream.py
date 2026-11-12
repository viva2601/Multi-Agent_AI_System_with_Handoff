import struct
import sys
import time

import requests  # type: ignore
import sounddevice as sd  # type: ignore

URL = "http://localhost:8010/query/audio"
query = sys.argv[1] if len(sys.argv) > 1 else "Find flights from Mumbai to Delhi tomorrow for 2"

start = time.time()
response = requests.post(URL, json={"session_id": "play1", "query": query}, stream=True)
buffer, speaker = b"", None

try:
    for chunk in response.iter_content(4096):
        buffer += chunk
        if speaker is None:
            if len(buffer) < 44:
                continue
            rate = struct.unpack("<I", buffer[24:28])[0]  # sample rate is stored in the WAV header
            speaker = sd.RawOutputStream(samplerate=rate, channels=1, dtype="int16")
            speaker.start()
            buffer = buffer[44:]
            print(f"first audio after {time.time() - start:.1f}s")
        usable = len(buffer) - len(buffer) % 2  # int16 samples are 2 bytes each
        if usable:
            speaker.write(buffer[:usable])
            buffer = buffer[usable:]
finally:
    if speaker:
        speaker.stop()
        speaker.close()
print(f"finished after {time.time() - start:.1f}s")
