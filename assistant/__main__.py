import time

from assistant.audio import record_until_silence
from assistant.historique import preparer_historique, reinitialiser_si_inactif
from assistant.llm import SYSTEM_PROMPT, ask_llm, prepare_search
from assistant.stt import transcribe_audio
from assistant.text import clean_for_speech
from assistant.tts import speak
from assistant.wakeword import wait_for_wake_word

MESSAGE_ERROR = "Système actuellement indisponible, règle le problème."

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]
derniere_activite = time.monotonic()
while True:
    print("👂 En veille...")
    wait_for_wake_word()
    reinitialiser_si_inactif(messages, derniere_activite)
    speak("Je t'écoute")
    try:
        while True:
            print("🎙️ Je t'écoute...")
            question = transcribe_audio(record_until_silence())
            if not question:
                break
            messages.append({"role": "user", "content": prepare_search(question)})
            print("Toi : ", question)
            preparer_historique(messages)
            answer = clean_for_speech(ask_llm(messages))
            print("IA : ", answer)
            speak(answer)
            messages.append({"role": "assistant", "content": answer})
            derniere_activite = time.monotonic()
    except ConnectionError:
        messages.pop()
        speak(MESSAGE_ERROR)
