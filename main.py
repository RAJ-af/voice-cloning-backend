from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from supabase import create_client
import uuid
from datetime import datetime
import io

load_dotenv()

app = FastAPI(title="Voice Cloning API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Password check
def verify_password(password: str):
    return password == os.getenv("API_PASSWORD")

@app.get("/")
async def root():
    return {"status": "Voice Cloning API Running", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/clone-voice")
async def clone_voice(
    audio: UploadFile = File(...),
    voice_name: str = Form(...),
    voice_description: str = Form(""),
    x_api_password: str = Header(None)
):
    # Password check
    if not verify_password(x_api_password):
        raise HTTPException(401, "Invalid password")
    
    try:
        voice_id = str(uuid.uuid4())
        audio_bytes = await audio.read()
        
        # Upload to Supabase
        filename = f"{voice_id}_reference.wav"
        storage_resp = supabase.storage.from_("reference-voices").upload(
            filename,
            audio_bytes,
            {"content-type": "audio/wav"}
        )
        
        # Get URL
        audio_url = supabase.storage.from_("reference-voices").get_public_url(filename)
        
        # For now, dummy embeddings (F5-TTS integration later)
        voice_embeddings = {"placeholder": "will_add_f5tts_later"}
        
        # Save to DB
        supabase.table("cloned_voices").insert({
            "id": voice_id,
            "voice_name": voice_name,
            "voice_description": voice_description,
            "reference_audio_url": audio_url,
            "voice_embeddings": voice_embeddings,
            "audio_duration": len(audio_bytes) // 44100,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "voice_id": voice_id,
            "message": "Voice cloned successfully"
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/test-voice/{voice_id}")
async def test_voice(
    voice_id: str,
    test_text: str = Form(...),
    x_api_password: str = Header(None)
):
    if not verify_password(x_api_password):
        raise HTTPException(401, "Invalid password")
    
    try:
        # Get voice
        resp = supabase.table("cloned_voices").select("*").eq("id", voice_id).execute()
        if not resp.data:
            raise HTTPException(404, "Voice not found")
        
        # For now, return dummy audio URL (F5-TTS integration later)
        # In production, yahan F5-TTS se audio generate hoga
        
        return {
            "success": True,
            "audio_url": "https://example.com/test.wav",
            "message": "Test audio generated (F5-TTS integration pending)"
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/generate-speech")
async def generate_speech(
    voice_id: str = Form(...),
    text: str = Form(...),
    x_api_password: str = Header(None)
):
    if not verify_password(x_api_password):
        raise HTTPException(401, "Invalid password")
    
    # Similar to test_voice
    return {"success": True, "message": "Speech generation (F5-TTS pending)"}

@app.get("/api/voices")
async def get_voices(x_api_password: str = Header(None)):
    if not verify_password(x_api_password):
        raise HTTPException(401, "Invalid password")
    
    resp = supabase.table("cloned_voices").select("*").order("created_at", desc=True).execute()
    return {"success": True, "voices": resp.data}

@app.delete("/api/voices/{voice_id}")
async def delete_voice(voice_id: str, x_api_password: str = Header(None)):
    if not verify_password(x_api_password):
        raise HTTPException(401, "Invalid password")
    
    supabase.table("cloned_voices").delete().eq("id", voice_id).execute()
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

