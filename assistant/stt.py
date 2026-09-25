from faster_whisper import WhisperModel

MODEL = WhisperModel("small", device="cpu", compute_type="int8")


def transcribe_audio(audio):
    segments, _ = MODEL.transcribe(audio, language="fr", vad_filter=True)
    text = "".join(segment.text for segment in segments).strip()
    return text
