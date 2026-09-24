import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

FREQUENCE = 16000
DUREE = 5


def record():
    audio = sd.rec(FREQUENCE * DUREE, samplerate=FREQUENCE, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def transcribe_audio(audio):
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio, language="fr")
    for segment in segments:
        print(segment.text)


if __name__ == "__main__":
    audio = record()
    print(audio.shape, ",", audio.max())
    transcribe_audio(audio)
