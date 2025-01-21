import subprocess

def extract_audio(video_file, output_file):
    command = [
        "C:\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe",
        "-i",
        video_file,
        "-vn",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-ab",
        "192k",
        "-f",
        "wav",
        output_file
    ]
    subprocess.run(command)

# Example usage:
video_file = "video2.mp4"
output_file = "audio2_output.mp3"
#save in mp3 format

extract_audio(video_file, output_file)