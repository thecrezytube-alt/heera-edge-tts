import asyncio
import os
import re
import tempfile
from pathlib import Path

import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Heera Edge TTS Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",
    "hi-IN": "hi-IN-SwaraNeural",
    "hi-male": "hi-IN-MadhurNeural",
    "en": "en-US-AriaNeural",
    "en-US": "en-US-AriaNeural",
    "en-IN": "en-IN-NeerjaNeural",
}
ALLOWED = set(VOICE_MAP.values()) | {"hi-IN-SwaraNeural", "hi-IN-MadhurNeural", "en-US-AriaNeural", "en-IN-NeerjaNeural", "en-IN-PrabhatNeural"}

class TtsRequest(BaseModel):
    text: str
    languageCode: str = "hi-IN"
    voice: str | None = None
    rate: str = "+0%"
    pitch: str = "+0Hz"


def clean_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"```.*?```", " ", s, flags=re.S)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"^\s{0,3}#{1,6}\s*", "", s, flags=re.M)
    s = s.replace("**", "").replace("__", "").replace("*", "").replace("_", "").replace("~~", "")
    s = re.sub(r"https?://\S+", "link", s)
    s = re.sub(r"\s+", " ", s).strip()
    return (s or "Haan, bol.")[:1200]


def select_voice(language: str, requested: str | None) -> str:
    if requested in ALLOWED:
        return requested
    lang = (language or "hi-IN").strip()
    if lang in VOICE_MAP:
        return VOICE_MAP[lang]
    return "hi-IN-SwaraNeural" if lang.lower().startswith("hi") else "en-US-AriaNeural"

@app.get("/")
async def root():
    return {"ok": True, "service": "heera-edge-tts", "voices": {"hi": "hi-IN-SwaraNeural", "hiMale": "hi-IN-MadhurNeural", "en": "en-US-AriaNeural"}}

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/tts")
async def tts(req: TtsRequest):
    text = clean_text(req.text)
    voice = select_voice(req.languageCode, req.voice)
    try:
        out = Path(tempfile.gettempdir()) / f"heera_edge_{abs(hash(text + voice))}.mp3"
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=req.rate, pitch=req.pitch)
        await communicate.save(str(out))
        if not out.exists() or out.stat().st_size < 200:
            raise RuntimeError("empty audio")
        return FileResponse(str(out), media_type="audio/mpeg", filename="heera-edge-tts.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edge TTS failed: {e}")

@app.post("/tts_stream")
async def tts_stream(req: TtsRequest):
    text = clean_text(req.text)
    voice = select_voice(req.languageCode, req.voice)
    async def gen():
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=req.rate, pitch=req.pitch)
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio" and chunk.get("data"):
                    yield chunk["data"]
        except Exception as e:
            # StreamingResponse cannot change status after start; raise before first chunk where possible.
            raise e
    return StreamingResponse(gen(), media_type="audio/mpeg", headers={"X-Heera-Voice": voice})

# Vercel/ASGI handler can import this `app`; Render can run uvicorn app:app.
