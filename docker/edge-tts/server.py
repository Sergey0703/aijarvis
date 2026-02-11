from fastapi import FastAPI, Query
from fastapi.responses import Response
import edge_tts
import asyncio
import io

app = FastAPI()

@app.get("/tts")
async def tts(
    text: str = Query(...),
    lang: str = Query(default="en"),
    voice: str = Query(default=None)
):
    if voice is None:
        voice = "ru-RU-SvetlanaNeural" if lang == "ru" else "en-US-JennyNeural"

    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])

    buf.seek(0)
    return Response(content=buf.read(), media_type="audio/mpeg")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "edge-tts"}
