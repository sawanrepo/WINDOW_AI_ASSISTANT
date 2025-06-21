import boto3
import os
import simpleaudio as sa
import wave
import tempfile
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
        # Get raw PCM/WAV from AWS Polly. 
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="pcm",
            VoiceId=voice_id,
            Engine=engine
        )
        pcm_data = response["AudioStream"].read()
        #keeping wav file (pcm) in temp filw which gets deleetd after playing.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            with wave.open(temp_wav.name, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(pcm_data)
            wave_obj = sa.WaveObject.from_wave_file(temp_wav.name)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        os.remove(temp_wav.name)

    except Exception as e:
        print(f"[TTS Error] {e}")

#checking is tts is working or not. 
if __name__ == "__main__":
    speak("Hello, this is a test of the AWS Polly text-to-speech service.")