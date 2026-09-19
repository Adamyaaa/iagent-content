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

def get_video_duration(video_path: str) -> float:
    """
    Safely extracts video duration supporting MoviePy 2.x, 1.x, and fallback.
    """
    try:
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip
            
        clip = VideoFileClip(video_path)
        dur = float(clip.duration) if clip.duration else 0.0
        clip.close()
        if dur > 0:
            return dur
    except Exception as e:
        logger.warning(f"MoviePy duration extraction error: {e}")

    return 30.0

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
                try:
                    res = client.table("trend_queue").select("id").eq("id", queue_id).execute()
                    if not res.data:
                        client.table("trend_queue").insert({"id": queue_id, "source_url": filename, "status": "analyzing"}).execute()
                    else:
                        client.table("trend_queue").update({"status": "analyzing"}).eq("id", queue_id).execute()
                except Exception as e:
                    logger.warning(f"Could not update status in Supabase: {e}")

            # 1. Determine video metadata
            duration = get_video_duration(video_path)
            video_meta = {
                "title": filename,
                "duration": duration,
                "resolution": "Unknown",
                "frame_rate": 30,
                "video_path": video_path
            }

            # 2. Extract audio and frames
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            audio_path = media_service.extract_audio(video_path, audio_path)
            frames_dir = os.path.join(temp_dir, 'frames')
            frame_paths = media_service.extract_frames(
                video_path=video_path, output_dir=frames_dir, duration=duration
            )

            # 3. Transcribe audio — or use text override (e.g. LinkedIn photo post body)
            transcript_override_path = os.path.join(temp_dir, 'transcript_override.txt')
            if os.path.exists(transcript_override_path):
                with open(transcript_override_path, 'r', encoding='utf-8') as _f:
                    transcript = _f.read().strip()
                logger.info(f"Using transcript override ({len(transcript)} chars) — skipping audio transcription")
            else:
                transcript = transcription_service.transcribe_audio(audio_path)
            
            # 4. Reverse-engineer video structure with Gemini
            analysis = gemini_service.analyze_content(frame_paths, transcript, video_meta, platform)
            
            # 5. Extract underlying psychological and structural pattern
            pattern = gemini_service.extract_pattern(analysis)
            
            logger.info(f"Successfully analyzed {filename}. Extracted Pattern: {pattern}")
            
            if client:
                try:
                    # Save analysis to DB
                    client.table("content_analysis").insert({
                        "queue_id": queue_id,
                        "transcript": transcript.transcript if hasattr(transcript, 'transcript') else str(transcript),
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
                except Exception as e:
                    logger.warning(f"Could not persist analysis to DB: {e}")

            # 6. Generate Concept with Brand QA revisions
            source_problem = analysis.get("narrative_structure", {}).get("problem", "")
            source_insight = analysis.get("narrative_structure", {}).get("insight", "")
            source_hook = analysis.get("hook", "")
            raw_transcript_text = transcript.transcript if hasattr(transcript, 'transcript') else str(transcript)
            source_snippet = raw_transcript_text[:300].strip() if raw_transcript_text else ""
            
            dynamic_context = (
                f"Source Content Reference: '{filename}'. "
                f"Source Problem: '{source_problem}'. "
                f"Source Core Insight: '{source_insight}'. "
                f"Source Hook Angle: '{source_hook}'. "
                f"Transcript Excerpt: '{source_snippet}'. "
                f"Mission: Pivot and adapt this insight into a high-ROI AI agent, automation system, or chatbot solution specifically for Indian businesses and founders."
            )
            
            generation_result = generation_service.generate_with_revisions(
                extracted_pattern=pattern,
                topic_context=dynamic_context
            )
            
            if client:
                try:
                    concept = generation_result.get("final_concept")
                    qa_score = generation_result.get("final_score")
                    ideations = generation_result.get("ideations", {})

                    if concept:
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
                except Exception as e:
                    logger.warning(f"Could not persist generated concept to DB: {e}")

            return {
                "queue_id": queue_id,
                "status": "success",
                "metadata": video_meta,
                "pattern": pattern,
                "generation": generation_result
            }

        except Exception as e:
            logger.error(f"Error during video processing for {filename}: {e}")
            if client:
                try:
                    error_msg = f"FAILED: ERROR: {str(e)}"[:200]
                    client.table("trend_queue").update({"status": "rejected", "source_url": error_msg}).eq("id", queue_id).execute()
                except Exception:
                    pass
            raise e

ingestion_service = IngestionService()
