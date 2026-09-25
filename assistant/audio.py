import numpy as np
import sounddevice as sd

FREQUENCE = 16000
TAILLE_BLOC = 480
SEUIL_VOLUME = 0.01
SILENCE_FIN = 1.5
ATTENTE_MAX = 5
DUREE_MAX = 30
PAROLE_MIN = 0.3

DUREE_BLOC = TAILLE_BLOC / FREQUENCE


def record_until_silence():
    with sd.InputStream(
        samplerate=FREQUENCE, channels=1, dtype="float32", blocksize=TAILLE_BLOC
    ) as stream:
        audio = []
        silence_bloc = 0
        parole_bloc = 0
        parole_detectee = False
        while True:
            bloc, _ = stream.read(TAILLE_BLOC)
            audio.append(bloc.flatten())
            volume = np.sqrt(np.mean(bloc**2))
            if volume > SEUIL_VOLUME:
                parole_detectee = True
                silence_bloc = 0
                parole_bloc += 1
            elif parole_detectee:
                silence_bloc += 1
            if silence_bloc > SILENCE_FIN / DUREE_BLOC:
                break

            if not parole_detectee and len(audio) >= ATTENTE_MAX / DUREE_BLOC:
                return np.array([], dtype="float32")
            if len(audio) >= DUREE_MAX / DUREE_BLOC:
                break
        if parole_bloc < PAROLE_MIN / DUREE_BLOC:
            return np.array([], dtype="float32")
        return np.concatenate(audio)
