# Speech-to-Speech Streaming 🎙️🔄🌍

This project enables real-time **speech-to-speech translation** for videos, allowing users to convert spoken language in videos into another language with synchronized audio output. It supports both **file uploads and YouTube videos** for translation.  

## 🚀 Features
- 🎥 **Video Upload or YouTube URL Support**  
- 🎤 **Automatic Speech Recognition (ASR)**  
- 🌐 **Language Detection & Translation**  
- 🗣️ **Text-to-Speech (TTS) with Google TTS**  
- 🎼 **Audio Synchronization with Video**  
- 🛠 **Flask-based Web Application**  

## 🛠️ Tech Stack
- **Python**, **Flask**
- **SpeechRecognition**, **gTTS**
- **Google Translate API**
- **FFmpeg**, **MoviePy**, **Pydub**
- **yt-dlp** for YouTube video downloads

## 📦 Installation
Clone the repository:
```bash
git clone https://github.com/saisreeja1410/Speech-to-Speech-Streaming.git
cd Speech-to-Speech-Streaming
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Set up the required directories:
```bash
mkdir uploads output
```

## 🔑 Environment Variables
Create a `.env` file and add:
```env
YOUTUBE_API_KEY=your_api_key_here
```

## ▶️ Usage
Run the Flask app:
```bash
python app.py
```
Access the web UI at: **http://127.0.0.1:5000/**

## 🖼️ Web Interface
Upload a video or provide a YouTube link, choose the target language, and get the translated speech output.

## 📜 License
This project is licensed under the **MIT License**.
