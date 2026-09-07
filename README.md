# Heera Edge-TTS Backend

Free backend for Heera Intelligence Android TTS fallback.

## Deploy on Render
1. Push this folder to GitHub.
2. Render → New Web Service → connect repo.
3. Runtime: Python
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. Health path: `/health`
7. Copy the public URL, e.g. `https://heera-edge-tts.onrender.com`.
8. Paste it in app Settings → `Edge-TTS backend URL`.

## API
`POST /tts`

```json
{
  "text": "नमस्ते bhai, voice ready hai",
  "languageCode": "hi-IN",
  "voice": "hi-IN-SwaraNeural"
}
```

Returns: `audio/mpeg` MP3.

Default voices:
- Hindi female: `hi-IN-SwaraNeural`
- Hindi male: `hi-IN-MadhurNeural`
- English: `en-US-AriaNeural`

## Local test
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
curl -X POST http://localhost:8000/tts \
  -H 'Content-Type: application/json' \
  -o test.mp3 \
  -d '{"text":"नमस्ते bhai, Edge TTS chal raha hai","languageCode":"hi-IN"}'
```

## If you see Edge TTS 403
Redeploy this updated backend with `edge-tts==7.2.8` and clear Render build cache. Test:

```bash
curl https://YOUR-RENDER-URL.onrender.com/diag
```

If `/diag` still returns 403, that Render region/IP is blocked by Microsoft Edge speech. Redeploy on another provider/region; Android app will still fallback to Android TTS.
