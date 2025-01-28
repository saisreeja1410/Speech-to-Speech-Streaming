from flask import Flask, render_template, request, send_from_directory, url_for
import os
import ffmpeg
import speech_recognition as sr
from gtts import gTTS
from langdetect import detect
from pydub import AudioSegment
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from googletrans import Translator
from dotenv import load_dotenv
import logging
from werkzeug.utils import secure_filename
import shutil
from typing import Optional, Tuple
import yt_dlp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from the .env file
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    logger.warning("YouTube API key not found in environment variables")

# Flask app setup
app = Flask(__name__)

# Configuration
class Config:
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'output'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

app.config.from_object(Config)

def setup_folders():
    """Create necessary folders if they don't exist and clean old files."""
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        os.makedirs(folder, exist_ok=True)
        # Clean old files
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f'Failed to delete {file_path}. Reason: {e}')

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters."""
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def download_youtube_video(url: str, output_path: str) -> str:
    """Download a YouTube video using yt-dlp."""
    try:
        ydl_opts = {
            'format': 'mp4',
            # Use sanitized filename template
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            video_title = info['title']
            
            # Sanitize the filename before download
            safe_title = sanitize_filename(video_title)
            ydl_opts['outtmpl'] = os.path.join(output_path, f"{safe_title}.%(ext)s")
            
            # Download with sanitized filename
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([url])
            
            video_path = os.path.join(output_path, f"{safe_title}.mp4")
            return video_path
            
    except Exception as e:
        logger.error(f"YouTube download error: {str(e)}")
        raise ValueError(f"Failed to download video: {str(e)}")

def extract_audio(input_video_path: str, output_audio_path: str) -> None:
    """Extract audio from a video file and save it as a WAV file."""
    try:
        ffmpeg.input(input_video_path).output(
            output_audio_path,
            acodec="pcm_s16le",
            ac=1,
            ar="16000"
        ).run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        raise ValueError("Failed to extract audio from video")

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using SpeechRecognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        raise ValueError("Speech recognition could not understand the audio")
    except sr.RequestError as e:
        logger.error(f"Speech recognition error: {str(e)}")
        raise ValueError("Speech recognition service failed")

def translate_text(input_text: str, target_language: str) -> str:
    """Translate text to the target language."""
    try:
        translator = Translator()
        translated = translator.translate(input_text, dest=target_language)
        return translated.text
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise ValueError("Failed to translate text")

def text_to_speech(text: str, output_audio_path: str, target_language: str) -> None:
    """Convert text to speech and save it as a WAV file."""
    try:
        tts = gTTS(text=text, lang=target_language)
        tts.save(output_audio_path)
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        raise ValueError("Failed to convert text to speech")

def synchronize_audio_with_video(
    video_path: str,
    audio_path: str,
    output_path: str
) -> None:
    """Synchronize the translated audio with the video."""
    video_clip = None
    translated_audio = None
    adjusted_audio_clip = None
    
    try:
        video_clip = VideoFileClip(video_path)
        translated_audio = AudioFileClip(audio_path)

        # Adjust audio duration
        translated_duration = translated_audio.duration
        original_duration = video_clip.duration

        if translated_duration < original_duration:
            silence = AudioSegment.silent(
                duration=int((original_duration - translated_duration) * 1000)
            )
            adjusted_audio = AudioSegment.from_file(audio_path) + silence
        else:
            adjusted_audio = AudioSegment.from_file(audio_path)[
                :int(original_duration * 1000)
            ]

        adjusted_audio_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            "adjusted_audio.wav"
        )
        adjusted_audio.export(adjusted_audio_path, format="wav")

        adjusted_audio_clip = AudioFileClip(adjusted_audio_path)
        final_audio = CompositeAudioClip([adjusted_audio_clip])
        video_clip.audio = final_audio

        video_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True
        )

    except Exception as e:
        logger.error(f"Video processing error: {str(e)}")
        raise ValueError("Failed to synchronize audio with video")
    
    finally:
        # Clean up resources
        if video_clip:
            video_clip.close()
        if translated_audio:
            translated_audio.close()
        if adjusted_audio_clip:
            adjusted_audio_clip.close()

def process_video(
    video_path: str,
    target_language: str,
    source_language: Optional[str] = None
) -> str:
    """Process the video through the translation pipeline."""
    try:
        # Extract audio
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_audio.wav')
        extract_audio(video_path, audio_path)

        # Transcribe audio
        transcribed_text = transcribe_audio(audio_path)
        
        # Detect source language if not provided
        if not source_language:
            source_language = detect(transcribed_text)

        # Translate text
        translated_text = translate_text(transcribed_text, target_language)

        # Convert to speech
        translated_audio_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            'translated_audio.wav'
        )
        text_to_speech(translated_text, translated_audio_path, target_language)

        # Create final video
        translated_video_path = os.path.join(
            app.config['OUTPUT_FOLDER'],
            'translated_video.mp4'
        )
        synchronize_audio_with_video(
            video_path,
            translated_audio_path,
            translated_video_path
        )

        return translated_video_path

    except Exception as e:
        logger.error(f"Video processing pipeline error: {str(e)}")
        raise ValueError(f"Failed to process video: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def index():
    """Handle the main page and form submission."""
    error = None
    video_path = None
    translated_video_path = None

    if request.method == "POST":
        try:
            # Clean previous files
            setup_folders()

            video_file = request.files.get("video")
            video_url = request.form.get("video_url")
            source_language = request.form.get("source_language")
            target_language = request.form.get("target_language")

            if not target_language:
                raise ValueError("Target language is required")

            if video_file:
                if not video_file.filename:
                    raise ValueError("No file selected")
                if not allowed_file(video_file.filename):
                    raise ValueError("File type not allowed")
                    
                filename = secure_filename(video_file.filename)
                video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                video_file.save(video_path)
                
            elif video_url:
                if not video_url.strip():
                    raise ValueError("Please provide a valid YouTube URL")
                video_path = download_youtube_video(
                    video_url,
                    app.config['UPLOAD_FOLDER']
                )
            else:
                raise ValueError(
                    "Please upload a video file or provide a YouTube URL"
                )

            translated_video_path = process_video(
                video_path,
                target_language,
                source_language
            )

        except Exception as e:
            error = str(e)
            logger.error(f"Request processing error: {str(e)}")

    return render_template(
        "index.html",
        error=error,
        video_path=url_for(
            'uploaded_file',
            filename=os.path.basename(video_path)
        ) if video_path else None,
        translated_video_path=url_for(
            'output_file',
            filename='translated_video.mp4'
        ) if translated_video_path else None
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/output/<filename>')
def output_file(filename):
    """Serve output files."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == "__main__":
    setup_folders()
    app.run(debug=True)
