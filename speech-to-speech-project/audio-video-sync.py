from moviepy import *

# Load the video and audio files
video = VideoFileClip("video2.mp4")
audio = AudioFileClip("hindi_audio2.mp3")

# Replace the audio of the video with the new audio
video_with_new_audio = video.with_audio(audio)

# Save the video with the new audio
video_with_new_audio.write_videofile("synchronized_video.mp4")