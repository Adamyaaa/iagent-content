import os
import yt_dlp
import subprocess
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class MediaService:
    def download_video(self, url: str, output_dir: str) -> Dict[str, Any]:
        """
        Downloads a video using yt-dlp and extracts metadata.
        """
        os.makedirs(output_dir, exist_ok=True)
        output_template = os.path.join(output_dir, 'video.%(ext)s')
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading video from {url}")
            info_dict = ydl.extract_info(url, download=True)
            
            video_path = ydl.prepare_filename(info_dict)
            if not os.path.exists(video_path):
                # Sometimes yt-dlp renames the file if merging happens
                video_path = video_path.rsplit('.', 1)[0] + '.mp4'
                
            metadata = {
                'duration': info_dict.get('duration', 0.0),
                'resolution': f"{info_dict.get('width', 0)}x{info_dict.get('height', 0)}",
                'frame_rate': info_dict.get('fps', 0.0),
                'title': info_dict.get('title', ''),
                'video_path': video_path
            }
            logger.info(f"Downloaded video metadata: {metadata}")
            return metadata

    def extract_audio(self, video_path: str, output_path: str) -> str:
        """
        Extracts audio from video and converts it to .mp3 using FFmpeg to stay under Groq's 25MB limit.
        """
        output_path = output_path.replace('.wav', '.mp3')
        logger.info(f"Extracting audio to {output_path}")
        command = [
            'ffmpeg', '-y', '-i', video_path, 
            '-vn', '-acodec', 'libmp3lame', '-q:a', '4', 
            output_path
        ]
        
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path

    def extract_frames(self, video_path: str, output_dir: str, duration: float, num_frames: int = 7) -> List[str]:
        """
        Extracts representative frames from the video.
        Instead of consecutive frames, we distribute them evenly across the video duration.
        """
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Extracting {num_frames} frames from video")
        
        frame_paths = []
        
        # Calculate evenly spaced intervals, avoiding the very beginning and very end (often black screens)
        interval = duration / (num_frames + 1)
        
        for i in range(1, num_frames + 1):
            timestamp = interval * i
            output_path = os.path.join(output_dir, f'frame_{i}.jpg')
            
            # Extract a single frame at the specific timestamp
            command = [
                'ffmpeg', '-y', '-ss', str(timestamp), '-i', video_path,
                '-vframes', '1', '-q:v', '2', output_path
            ]
            
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(output_path):
                frame_paths.append(output_path)
                
        return frame_paths

media_service = MediaService()
