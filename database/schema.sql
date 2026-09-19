-- PostgreSQL Schema for iAgent Solutions Content OS

CREATE TYPE content_status AS ENUM (
    'pending', 
    'analyzing', 
    'analyzed', 
    'pitched', 
    'approved', 
    'generating', 
    'generated', 
    'published', 
    'rejected'
);

CREATE TABLE trend_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    source_platform TEXT,
    source_title TEXT,
    source_creator TEXT,
    source_date TIMESTAMP WITH TIME ZONE,
    topic TEXT,
    raw_content JSONB,
    content_pattern TEXT,
    industry TEXT,
    status content_status DEFAULT 'pending',
    priority INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE content_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID REFERENCES trend_queue(id) ON DELETE CASCADE,
    transcript TEXT,
    viral_pattern TEXT,
    hook TEXT,
    emotional_trigger TEXT,
    narrative_structure JSONB,
    pacing JSONB,
    visual_analysis JSONB,
    cta_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE content_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID REFERENCES trend_queue(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    generated_concept JSONB,
    script TEXT,
    scene_breakdowns JSONB,
    qa_scores JSONB,
    revision_history JSONB[],
    approval_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE content_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID REFERENCES content_concepts(id) ON DELETE CASCADE,
    voiceover_url TEXT,
    images_urls TEXT[],
    video_url TEXT,
    captions_url TEXT,
    final_render_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
