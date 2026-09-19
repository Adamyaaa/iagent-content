import os
import logging
import json
from typing import Dict, Any
from .media_service import media_service
from .transcription_service import transcription_service
from .gemini_service import gemini_service
from .generation_service import generation_service
from ..database.supabase_client import supabase_db

logger = logging.getLogger(__name__)

class IngestionService:
    def process_video_pipeline(self, queue_id: str, video_path: str, filename: str, platform: str = "youtube") -> Dict[str, Any]:
        """
        Unified ingestion pipeline that takes a local .mp4 file (downloaded or uploaded) 
        and orchestrates the AI analysis and generation process.
        """
        temp_dir = os.path.dirname(video_path)
        client = supabase_db.get_client()

        try:
            if client:
                # check if exists
                res = client.table("trend_queue").select("id").eq("id", queue_id).execute()
                if not res.data:
                    client.table("trend_queue").insert({"id": queue_id, "source_url": filename, "status": "analyzing"}).execute()
                else:
                    client.table("trend_queue").update({"status": "analyzing"}).eq("id", queue_id).execute()

            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            duration = clip.duration
            clip.close()

            video_meta = {
                "title": filename,
                "duration": duration,
                "resolution": "Unknown",
                "frame_rate": 30,
                "video_path": video_path
            }

            # Extract audio and frames
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            audio_path = media_service.extract_audio(video_path, audio_path)
            frames_dir = os.path.join(temp_dir, 'frames')
            frame_paths = media_service.extract_frames(
                video_path=video_path, output_dir=frames_dir, duration=duration
            )

            transcript = transcription_service.transcribe_audio(audio_path)
            analysis = gemini_service.analyze_content(frame_paths, transcript, video_meta, platform)
            
            pattern = analysis.get("core_message", "") or analysis.get("hook", "")
            
            if client:
                # Save analysis to DB
                client.table("content_analysis").insert({
                    "queue_id": queue_id,
                    "transcript": transcript.transcript if hasattr(transcript, 'transcript') else transcript,
                    "viral_pattern": pattern,
                    "hook": analysis.get("hook", ""),
                    "emotional_trigger": analysis.get("emotional_trigger", ""),
                    "narrative_structure": analysis.get("narrative_structure", {}),
                    "pacing": analysis.get("pacing", {}),
                    "visual_analysis": analysis.get("visual_storytelling", {}),
                    "cta_analysis": analysis.get("cta_analysis", {})
                }).execute()
                
                client.table("trend_queue").update({
                    "status": "generating",
                    "topic": filename,
                    "content_pattern": pattern
                }).eq("id", queue_id).execute()

            generation = gemini_service.generate_content(pattern, platform)
            concept = generation.get("concept")
            qa_score = generation.get("qa_score")
            
            ideations = gemini_service.generate_platform_ideations(concept)

            if client and concept:
                client.table("content_concepts").insert({
                    "queue_id": queue_id,
                    "title": concept.title,
                    "generated_concept": concept.model_dump() if hasattr(concept, 'model_dump') else concept,
                    "scene_breakdowns": [s.model_dump() if hasattr(s, 'model_dump') else s for s in concept.scene_breakdown] if hasattr(concept, 'scene_breakdown') else [],
                    "linkedin_ideation": ideations.get("linkedin", {}),
                    "instagram_ideation": ideations.get("instagram", {}),
                    "whatsapp_ideation": ideations.get("whatsapp", {}),
                    "qa_scores": qa_score.model_dump() if hasattr(qa_score, 'model_dump') else {} if qa_score else {},
                    "approval_status": qa_score.approved if hasattr(qa_score, 'approved') else False if qa_score else False
                }).execute()
                
                client.table("trend_queue").update({"status": "generated"}).eq("id", queue_id).execute()

            return {"queue_id": queue_id, "status": "success", "metadata": video_meta, "pattern": pattern}

        except Exception as e:
            logger.error(f"Error during video processing for {filename}: {e}")
            if client:
                error_msg = f"FAILED: ERROR: {str(e)}"[:200]
                client.table("trend_queue").update({"status": "rejected", "source_url": error_msg}).eq("id", queue_id).execute()
            raise e

ingestion_service = IngestionService()
