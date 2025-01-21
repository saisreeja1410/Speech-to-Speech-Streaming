from gtts import gTTS
import pygame
from pydub import AudioSegment
import os
import pyaudio

# Path to your text file
text_file_path = "hindi-translation.txt"
# Get the path to the desktop
desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

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

# Load the English audio and Hindi audio using pydub
english_audio_file = "audio2_output.mp3"  # Provide the path to the English audio file
english_audio = AudioSegment.from_mp3(english_audio_file)
hindi_audio = AudioSegment.from_mp3(audio_file)

# Calculate playback speed ratio
english_duration = len(english_audio)  # Duration in milliseconds
hindi_duration = len(hindi_audio)  # Duration in milliseconds
playback_speed = english_duration / hindi_duration

# Adjust the speed of the Hindi audio
hindi_audio_synchronized = hindi_audio._spawn(
    hindi_audio.raw_data,
    overrides={"frame_rate": int(hindi_audio.frame_rate * playback_speed)}
).set_frame_rate(hindi_audio.frame_rate)

# Save the synchronized Hindi audio
synchronized_audio_file = os.path.join(desktop_path, "hindi_audio_synchronized.mp3")
hindi_audio_synchronized.export(synchronized_audio_file, format="mp3")

# Play the synchronized audio using pyaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=hindi_audio_synchronized.frame_rate,
                output=True)

stream.write(hindi_audio_synchronized.raw_data)

stream.stop_stream()
stream.close()
p.terminate()