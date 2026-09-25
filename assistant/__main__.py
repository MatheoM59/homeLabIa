from assistant.audio import record_until_silence
from assistant.llm import SYSTEM_PROMPT, ask_llm
from assistant.stt import transcribe_audio

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]
while True:
    print("🎙️Je t'écoute...")
    question = transcribe_audio(record_until_silence())
    if not question:
        break
    messages.append({"role": "user", "content": question})
    print("Toi : ", question)
    answer = ask_llm(messages)
    print("IA : ", answer)
    messages.append({"role": "assistant", "content": answer})
