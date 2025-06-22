import boto3
import os
import pyaudio
from dotenv import load_dotenv

load_dotenv()

polly = boto3.client(
    "polly",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-south-1")
)

def speak(text, voice_id="Joanna", engine="neural"):
    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="pcm",
            VoiceId=voice_id,
            Engine=engine
        )
        pcm_data = response['AudioStream'].read()

        rate = 16000
        channels = 1
        width = 2

        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(width),
                        channels=channels,
                        rate=rate,
                        output=True)

        stream.write(pcm_data)
        stream.stop_stream()
        stream.close()
        p.terminate()

    except Exception as e:
        print(f"[TTS Error] {e}")
if __name__ == "__main__":
    speak("Hello, this is a test of the text-to-speech system using AWS Polly.")