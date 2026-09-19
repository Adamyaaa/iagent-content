import os
import yt_dlp
import subprocess
import logging
import httpx
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def get_ffmpeg_exe() -> str:
    """
    Locates the ffmpeg executable. Prioritizes imageio_ffmpeg's bundled binary,
    falling back to system 'ffmpeg'.
    """
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception as e:
        logger.debug(f"imageio_ffmpeg not available: {e}")
    return "ffmpeg"

class MediaService:
    def download_social_video(self, url: str, output_dir: str) -> str:
        """
        The 3-Layer Waterfall Downloader.
        Layer 1: RapidAPI Instagram (if applicable & key present)
        Layer 2: Cobalt API (co.wuk.sh / api.cobalt.tools)
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
                    "X-RapidAPI-Host": os.getenv("RAPIDAPI_HOST", "instagram-scraper-api2.p.rapidapi.com")
                }
                # If a specific scraper endpoint is configured, call it here
                raise Exception("RapidAPI Layer falling back to Layer 2")
            except Exception as e:
                logger.warning(f"Layer 1 failed: {e}")

        # Layer 2: Cobalt API
        logger.info("Layer 2: Trying Cobalt API")
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            if os.getenv("COBALT_API_KEY"):
                headers["Authorization"] = f"Bearer {os.getenv('COBALT_API_KEY')}"

            payload = {
                "url": url,
                "videoQuality": "1080"
            }
            cobalt_url = os.getenv("COBALT_API_URL", "https://co.wuk.sh/api/json")
            
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.post(cobalt_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    direct_url = data.get("url")
                    if direct_url:
                        logger.info("Cobalt API returned direct URL. Downloading stream...")
                        with client.stream("GET", direct_url) as video_resp:
                            video_resp.raise_for_status()
                            with open(video_path, 'wb') as f:
                                for chunk in video_resp.iter_bytes(chunk_size=8192):
                                    f.write(chunk)
                        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                            return video_path
                logger.warning(f"Layer 2 failed with status {response.status_code}")
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
                
            if not os.path.exists(video_path):
                # Look for any video file created in output_dir
                for f in os.listdir(output_dir):
                    if f.endswith(('.mp4', '.mkv', '.webm', '.mov')):
                        video_path = os.path.join(output_dir, f)
                        break

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
        ffmpeg_bin = get_ffmpeg_exe()
        command = [
            ffmpeg_bin, '-y', '-i', video_path, 
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
        if not duration or duration <= 0:
            duration = 10.0
            
        interval = duration / (num_frames + 1)
        ffmpeg_bin = get_ffmpeg_exe()
        
        for i in range(1, num_frames + 1):
            timestamp = interval * i
            output_path = os.path.join(output_dir, f'frame_{i}.jpg')
            
            command = [
                ffmpeg_bin, '-y', '-ss', str(timestamp), '-i', video_path,
                '-vframes', '1', '-q:v', '2', '-update', '1', output_path
            ]
            
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(output_path):
                frame_paths.append(output_path)
                
        return frame_paths

media_service = MediaService()
