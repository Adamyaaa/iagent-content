-- Run this to update your existing Supabase database for the new Omnichannel features
ALTER TABLE content_concepts 
ADD COLUMN IF NOT EXISTS linkedin_ideation JSONB,
ADD COLUMN IF NOT EXISTS instagram_ideation JSONB,
ADD COLUMN IF NOT EXISTS whatsapp_ideation JSONB;
