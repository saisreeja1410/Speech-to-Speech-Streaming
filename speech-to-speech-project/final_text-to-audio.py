from gtts import gTTS
import pygame
from pydub import AudioSegment
import os
import pyaudio

# Path to your text file
text_file_path = "hindi-translation.txt"

# Read the text from the file
with open(text_file_path, "r", encoding="utf-8") as file:
    mytext = file.read()

# Language in which you want to convert (Hindi)
language = 'hi'

# Passing the text and language to the engine
# Set slow=False for normal speed audio
myobj = gTTS(text=mytext, lang=language, slow=False)

# Save the converted audio in an mp3 file
audio_file = "hindi_audio2.mp3"
myobj.save(audio_file)

# Play the audio using pyaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=44100,  # default frame rate
                output=True)

# Load the audio file
hindi_audio = AudioSegment.from_mp3(audio_file)

stream.write(hindi_audio.raw_data)

stream.stop_stream()
stream.close()
p.terminate()