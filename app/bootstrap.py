from app.core.ffmpeg.manager import ffmpeg_manager

def initialize():
    path = ffmpeg_manager.get()
    print("FFmpeg ready:", path)