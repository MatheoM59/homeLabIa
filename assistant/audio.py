import sounddevice as sd

FREQUENCE = 16000
DUREE = 5


def record():
    audio = sd.rec(FREQUENCE * DUREE, samplerate=FREQUENCE, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()
