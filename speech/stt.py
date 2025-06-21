import speech_recognition as sr
from vosk import Model, KaldiRecognizer
import os
import sys
import json

model_path = os.path.join(os.path.dirname(__file__), "vosk-model-small-en-us-0.15")
if not os.path.exists(model_path):
    print("❌ Vosk model not found! Download and extract to:", model_path)
    sys.exit(1)

model = Model(model_path)

def listen():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone(sample_rate=16000) as source:
            print("🎤 Listening... (speak anytime)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source)
    except Exception as e:
        print(f"❌ Mic error: {e}")
        return "Mic error."

    try:
        rec = KaldiRecognizer(model, 16000)
        rec.AcceptWaveform(audio.get_raw_data())
        result = rec.Result()
        text = json.loads(result).get("text", "").strip()
        return text if text else "Didn't catch that clearly."
    except Exception as e:
        print(f"[STT Error] {e}")
        return "Error recognizing speech."