from assistant.audio import record_until_silence
from assistant.llm import SYSTEM_PROMPT, ask_llm
from assistant.stt import transcribe_audio
from assistant.tts import speak
from assistant.wakeword import wait_for_wake_word

MESSAGE_ERROR = "Système actuellement indisponible, règle le problème."

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]
while True:
    print("👂 En veille...")
    wait_for_wake_word()
    speak("Je t'écoute")
    try:
        while True:
            print("🎙️ Je t'écoute...")
            question = transcribe_audio(record_until_silence())
            if not question:
                break
            messages.append({"role": "user", "content": question})
            print("Toi : ", question)
            answer = ask_llm(messages)
            print("IA : ", answer)
            speak(answer)
            messages.append({"role": "assistant", "content": answer})
    except ConnectionError:
        messages.pop()
        speak(MESSAGE_ERROR)
