from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import ffmpeg
import speech_recognition as sr
from gtts import gTTS
from langdetect import detect
from pydub import AudioSegment
from moviepy import *
from dotenv import load_dotenv
from googletrans import Translator

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load environment variables
load_dotenv()

def extract_audio(input_video_path, output_audio_path):
    """Extract audio from a video file and save it as a WAV file."""
    ffmpeg.input(input_video_path).output(
        output_audio_path, acodec="pcm_s16le", ac=1, ar="16000"
    ).run(overwrite_output=True)

def transcribe_audio(audio_path):
    """Transcribe audio using SpeechRecognition."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio)

def translate_text(input_text, target_language):
    """Translate text to the target language."""
    translator = Translator()
    translated = translator.translate(input_text, dest=target_language)
    return translated.text

def text_to_speech(text, output_audio_path, target_language):
    """Convert text to speech and save it as a WAV file."""
    tts = gTTS(text=text, lang=target_language)
    tts.save(output_audio_path)

def synchronize_audio_with_video(video_path, audio_path, output_path):
    """Synchronize the translated audio with the video."""
    video_clip = VideoFileClip(video_path)
    translated_audio = AudioFileClip(audio_path)

    # Adjust audio duration
    translated_duration = translated_audio.duration
    original_duration = video_clip.duration

    if translated_duration < original_duration:
        # Extend audio with silence
        silence = AudioSegment.silent(duration=(original_duration - translated_duration) * 1000)
        adjusted_audio = AudioSegment.from_file(audio_path) + silence
    else:
        # Trim audio to match video duration
        adjusted_audio = AudioSegment.from_file(audio_path)[:int(original_duration * 1000)]

    # Save the adjusted audio to a new file
    adjusted_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], "adjusted_audio.wav")
    adjusted_audio.export(adjusted_audio_path, format="wav")

    # Use CompositeAudioClip to set audio
    adjusted_audio_clip = AudioFileClip(adjusted_audio_path)
    final_audio = CompositeAudioClip([adjusted_audio_clip])
    video_clip.audio = final_audio

    # Write the final video to disk
    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # Close resources
    video_clip.close()
    adjusted_audio_clip.close()


@app.route("/", methods=["GET", "POST"])
def index():
    """Handle the main page and form submission."""
    try:
        if request.method == "POST":
            video_file = request.files['video']
            target_language = request.form['target_language']

            # Save the uploaded video
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
            video_file.save(video_path)

            # Step 1: Extract audio
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_audio.wav')
            extract_audio(video_path, audio_path)

            # Step 2: Transcribe audio
            transcribed_text = transcribe_audio(audio_path)
            print("Transcribed Text:", transcribed_text)

            # Step 3: Translate text
            translated_text = translate_text(transcribed_text, target_language)
            print("Translated Text:", translated_text)

            # Step 4: Text-to-speech
            translated_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'translated_audio.wav')
            text_to_speech(translated_text, translated_audio_path, target_language)

            # Step 5: Synchronize audio and video
            translated_video_path = os.path.join(app.config['OUTPUT_FOLDER'], 'translated_video.mp4')
            synchronize_audio_with_video(video_path, translated_audio_path, translated_video_path)

            # Return paths to display in the front end
            return render_template(
                'index.html',
                video_path=url_for('uploaded_file', filename=video_file.filename),
                translated_video_path=url_for('output_file', filename='translated_video.mp4')
            )
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', error=str(e))

    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/output/<filename>')
def output_file(filename):
    """Serve output files."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
