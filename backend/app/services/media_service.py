import os
import yt_dlp
import subprocess
import logging
import requests
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class MediaService:
    def download_social_video(self, url: str, output_dir: str) -> str:
        """
        The 3-Layer Waterfall Downloader.
        Layer 1: RapidAPI Instagram (if applicable & key present)
        Layer 2: Cobalt API (co.wuk.sh)
        Layer 3: yt-dlp fallback
        Returns the path to the downloaded .mp4 file.
        """
        os.makedirs(output_dir, exist_ok=True)
        video_path = os.path.join(output_dir, 'video.mp4')
        
        # Layer 1: Dedicated API (Instagram)
        if "instagram.com" in url and os.getenv("RAPIDAPI_KEY"):
            logger.info("Layer 1: Trying RapidAPI for Instagram")
            try:
                headers = {
                    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
                    "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"
                }
                # Example request, we fall through if it fails since actual endpoint may vary
                raise Exception("RapidAPI Layer not fully implemented - falling back")
            except Exception as e:
                logger.warning(f"Layer 1 failed: {e}")

        # Layer 2: Cobalt API (co.wuk.sh)
        logger.info("Layer 2: Trying Cobalt API")
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            payload = {
                "url": url,
                "videoQuality": "1080"
            }
            cobalt_url = "https://co.wuk.sh/api/json"
            response = requests.post(cobalt_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "url" in data:
                    direct_url = data["url"]
                    logger.info("Cobalt API returned direct URL. Downloading stream...")
                    video_resp = requests.get(direct_url, stream=True)
                    video_resp.raise_for_status()
                    with open(video_path, 'wb') as f:
                        for chunk in video_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return video_path
            logger.warning(f"Layer 2 failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Layer 2 failed: {e}")

        # Layer 3: yt-dlp - The Ultimate Net
        logger.info("Layer 3: Falling back to yt-dlp")
        meta = self.download_video(url, output_dir)
        return meta['video_path']

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
            'merge_output_format': 'mp4',
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
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
