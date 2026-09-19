# iAgent's Content OS

## Architecture Overview
The Content OS is designed as a modular, asynchronous system focused on scalability, data integrity, and strict separation of concerns.

### 1. FastAPI (Backend Layer)
**Why it exists**: Serves as the high-performance orchestration layer. FastAPI's native `asyncio` support is crucial because video downloading, API calls to AI models, and database operations are heavily I/O bound. Pydantic models enforce strict data schemas across all microservices, ensuring the AI responses are structured and predictable.

### 2. PostgreSQL / Supabase (Data Layer)
**Why it exists**: Acts as the central nervous system. It stores the content discovery queue, extracted patterns, QA results, and asset metadata. Supabase allows us to eventually trigger webhooks or realtime UI updates as content moves through the pipeline statuses (e.g., `pending` -> `analyzed` -> `generated`).

### 3. AI Service Layer (Groq + Gemini + ElevenLabs)
**Why it exists**: Separates inference from orchestration.
- **Groq Whisper**: For extremely fast audio transcription.
- **Google Gemini**: Selected for its multimodal reasoning capabilities (analyzing 7 frames + transcript together) and its ability to output strict JSON schemas for pattern extraction and concept generation.
- **ElevenLabs/OpenAI TTS**: For high-quality, professional voice generation suited for LinkedIn and business audiences.

### 4. FFmpeg / MoviePy (Media Processing)
**Why it exists**: Handles raw pixel and audio manipulation. FFmpeg efficiently extracts audio and representative frames from source URLs without loading massive videos into memory.

### 5. n8n (Proactive Discovery)
**Why it exists**: A visual automation tool that continuously monitors RSS feeds, YouTube channels, and industry publications, pushing new URLs to our Supabase `trend_queue`. This automates the top of the funnel.

### 6. Telegram Agent (Interaction Layer)
**Why it exists**: Provides an immediate, low-friction interface for the core team to review content pitches, approve generations, and drop URLs manually without needing to log into the main dashboard.

### 7. React/Vite Dashboard (Visualization Layer)
**Why it exists**: A premium, internal product-studio dashboard to review the pattern library, check QA scores, and view the overall health of the content pipeline. 

---

## Setup Instructions

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and docker-compose
- FFmpeg installed and available in system PATH

### 2. Environment Variables
Copy `.env.example` to `.env` in the `backend/` directory and populate your API keys:
```bash
cp backend/.env.example backend/.env
```

### 3. Database Setup (Supabase)
Execute `database/schema.sql` against your Supabase PostgreSQL instance to create the required tables and enums.

### 4. Running the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to see the generated OpenAPI documentation.

### 5. Running the Frontend (Coming soon in Phase 7)
```bash
cd frontend
npm install
npm run dev
```
