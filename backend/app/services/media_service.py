import os
import re
import html as html_module
import yt_dlp
import subprocess
import logging
import httpx
from typing import Dict, List, Any, Optional, Tuple

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

        # Layer 0: LinkedIn photo/text post fallback (yt-dlp can only handle video posts)
        if "linkedin.com" in url:
            logger.info("Layer 0: Trying LinkedIn photo fallback (Twitterbot OG scrape)")
            try:
                lk_video_path, og_description = self._try_linkedin_photo_fallback(url, output_dir)
                if og_description:
                    override_path = os.path.join(output_dir, 'transcript_override.txt')
                    with open(override_path, 'w', encoding='utf-8') as f:
                        f.write(og_description)
                    logger.info(f"Wrote {len(og_description)} chars to transcript_override.txt")
                return lk_video_path
            except Exception as e:
                logger.warning(f"Layer 0 (LinkedIn photo) failed: {e} — falling through to video layers")

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

    def _try_linkedin_photo_fallback(self, url: str, output_dir: str) -> Tuple[str, str]:
        """
        For LinkedIn photo/text posts that yt-dlp cannot handle.
        1. Fetches page with Twitterbot/1.0 UA to bypass login wall.
        2. Parses og:image and og:description meta tags.
        3. Downloads the photo and converts it to a 5-second silent MP4.
        Returns (video_path, og_description). Raises Exception if not a photo post.
        """
        headers = {
            "User-Agent": "Twitterbot/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"LinkedIn page returned HTTP {resp.status_code}")
            html_text = resp.text

        def _parse_og(prop: str) -> Optional[str]:
            # Try property-first attribute order
            m = re.search(
                rf'<meta[^>]+property=["\']og:{prop}["\'][^>]+content=["\']([^"\']+)["\']',
                html_text, re.IGNORECASE
            )
            if not m:
                # Try content-first attribute order
                m = re.search(
                    rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:{prop}["\']',
                    html_text, re.IGNORECASE
                )
            return html_module.unescape(m.group(1)) if m else None

        og_image = _parse_og("image")
        og_description = _parse_og("description") or ""

        if not og_image:
            raise Exception("No og:image tag found — post may be a video or requires login")

        # Download the image
        photo_path = os.path.join(output_dir, 'linkedin_photo.jpg')
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            img_resp = client.get(og_image, headers={"User-Agent": "Twitterbot/1.0"})
            img_resp.raise_for_status()
            with open(photo_path, 'wb') as f:
                f.write(img_resp.content)

        if not os.path.exists(photo_path) or os.path.getsize(photo_path) == 0:
            raise Exception("Downloaded LinkedIn photo is empty or missing")

        # Convert static image to 5-second silent MP4
        video_path = os.path.join(output_dir, 'video.mp4')
        ffmpeg_bin = get_ffmpeg_exe()
        command = [
            ffmpeg_bin, '-y',
            '-loop', '1', '-i', photo_path,
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-c:v', 'libx264', '-t', '5',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-c:a', 'aac', '-shortest',
            video_path
        ]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise Exception(f"FFmpeg photo-to-video failed: {result.stderr.decode()[:200]}")

        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            raise Exception("FFmpeg produced an empty video file")

        logger.info(
            f"LinkedIn photo -> video OK ({os.path.getsize(video_path)} bytes). "
            f"Description: {og_description[:80]}..."
        )
        return video_path, og_description

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
