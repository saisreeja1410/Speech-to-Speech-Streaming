import soundfile as sf
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import os

def text_to_audio(text, audio_file):
    tts = gTTS(text=text, lang='en')
    tts.save(audio_file)

def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    text = recognizer.recognize_google(audio)
    return text

def translate_text(text, dest_language='hi'):
    translator = Translator()
    translated = translator.translate(text, dest=dest_language)
    return translated.text

def synchronize_audio(text, audio_file, output_file):
    audio_clip, samplerate = sf.read(audio_file)
    text_to_audio(text, output_file)
    synchronized_audio, _ = sf.read(output_file)
    synchronized_audio = synchronized_audio[:len(audio_clip)]
    sf.write(output_file, synchronized_audio, samplerate)

if __name__ == "__main__":
    # Read text from the file
    with open("transcription2.txt", "r") as file:
        text = file.read()

    audio_file = "audio2_output.wav"
    output_file = "hindi_sync.wav"

    # Translate text
    translated_text = translate_text(text, dest_language='hi')

    # Synchronize audio
    synchronize_audio(translated_text, audio_file, output_file)