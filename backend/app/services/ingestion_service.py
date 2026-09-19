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
    def process_url(self, url: str, queue_id: str, platform: str = "youtube") -> Dict[str, Any]:
        """
        Orchestrates the ingestion pipeline for a given URL and persists to Supabase.
        """
        logger.info(f"Starting ingestion process for URL: {url} (Queue ID: {queue_id})")
        
        temp_dir = os.path.join(os.getcwd(), 'app', 'temp', queue_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        client = supabase_db.get_client()
        
        try:
            # Update status in DB (if the row exists from n8n. If not, we create it)
            if client:
                try:
                    # check if exists
                    res = client.table("trend_queue").select("id").eq("id", queue_id).execute()
                    if not res.data:
                        client.table("trend_queue").insert({"id": queue_id, "source_url": url, "status": "analyzing"}).execute()
                    else:
                        client.table("trend_queue").update({"status": "analyzing"}).eq("id", queue_id).execute()
                except Exception as e:
                    logger.warning(f"Could not update status in Supabase: {e}")

            # 1-3. Media processing
            video_meta = media_service.download_video(url, temp_dir)
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            audio_path = media_service.extract_audio(video_meta['video_path'], audio_path)
            frames_dir = os.path.join(temp_dir, 'frames')
            frame_paths = media_service.extract_frames(
                video_path=video_meta['video_path'], output_dir=frames_dir, duration=video_meta['duration']
            )
            
            # 4-6. AI Analysis
            transcript = transcription_service.transcribe_audio(audio_path)
            analysis = gemini_service.analyze_content(frame_paths, transcript, video_meta, platform)
            pattern = gemini_service.extract_pattern(analysis)
            
            logger.info(f"Successfully processed {url}. Extracted Pattern: {pattern}")
            
            if client:
                # Save analysis to DB
                client.table("content_analysis").insert({
                    "queue_id": queue_id,
                    "transcript": transcript.transcript,
                    "viral_pattern": pattern,
                    "hook": analysis.get("hook", ""),
                    "emotional_trigger": analysis.get("emotional_trigger", ""),
                    "narrative_structure": analysis.get("narrative_structure", {}),
                    "pacing": analysis.get("pacing", {}),
                    "visual_analysis": analysis.get("visual_storytelling", {}),
                    "cta_analysis": analysis.get("cta_analysis", {})
                }).execute()
                # Update queue status
                client.table("trend_queue").update({"status": "generating", "topic": video_meta.get("title", ""), "content_pattern": pattern}).eq("id", queue_id).execute()

            # 7. Generate Concept
            generation_result = generation_service.generate_with_revisions(
                extracted_pattern=pattern,
                topic_context="Enterprise AI Automation for Indian Businesses"
            )
            
            if client:
                # Save Concept to DB
                concept = generation_result.get("final_concept")
                qa_score = generation_result.get("final_score")
                ideations = generation_result.get("ideations", {})
                
                if concept:
                    client.table("content_concepts").insert({
                        "queue_id": queue_id,
                        "title": concept.title,
                        "generated_concept": concept.model_dump(),
                        "scene_breakdowns": [s.model_dump() for s in concept.scene_breakdown],
                        "linkedin_ideation": ideations.get("linkedin", {}),
                        "instagram_ideation": ideations.get("instagram", {}),
                        "whatsapp_ideation": ideations.get("whatsapp", {}),
                        "qa_scores": qa_score.model_dump() if qa_score else {},
                        "approval_status": qa_score.approved if qa_score else False
                    }).execute()
                # Mark as generated
                client.table("trend_queue").update({"status": "generated"}).eq("id", queue_id).execute()

            return {
                "queue_id": queue_id,
                "status": "success",
                "metadata": video_meta,
                "pattern": pattern,
                "generation": generation_result
            }
            
        except Exception as e:
            logger.error(f"Error during ingestion for {url}: {e}")
            if client:
                error_msg = f"FAILED: {str(e)}"[:200]
                client.table("trend_queue").update({"status": "rejected", "source_url": error_msg}).eq("id", queue_id).execute()
            raise e

ingestion_service = IngestionService()
