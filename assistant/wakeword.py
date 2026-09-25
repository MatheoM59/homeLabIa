import sounddevice as sd
from openwakeword.model import Model

WAKEWORD = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
FREQUENCE = 16000
BLOC_SIZE = 1280
DETECT_SEUIL = 0.2


def wait_for_wake_word():
    with sd.InputStream(
        samplerate=FREQUENCE, channels=1, dtype="int16", blocksize=BLOC_SIZE
    ) as stream:
        while True:
            bloc, _ = stream.read(BLOC_SIZE)
            predictions = WAKEWORD.predict(bloc.flatten())
            score = predictions["hey_jarvis"]  # type: ignore
            if score >= DETECT_SEUIL:
                WAKEWORD.reset()
                return
