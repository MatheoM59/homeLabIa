import sounddevice as sd
from piper import PiperVoice

VOICE = PiperVoice.load("models/fr_FR-siwis-medium.onnx")


def speak(text):
    chunks = VOICE.synthesize(text)

    for chunk in chunks:
        sd.play(chunk.audio_float_array, samplerate=chunk.sample_rate)
        sd.wait()
