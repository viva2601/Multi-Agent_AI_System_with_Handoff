import logging

from fastapi import FastAPI, Request # type: ignore
from fastapi.exceptions import RequestValidationError # type: ignore
from fastapi.responses import PlainTextResponse, StreamingResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore

from config import GENERIC_ERROR
from memory import load_turns
from orchestrator import orchestrator
from tts import synthesize_stream

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Booking Orchestrator")


class QueryRequest(BaseModel):
    session_id: str = "default"
    query: str = Field(min_length=1)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    logger.warning("Invalid request: %s", exc.errors())
    return PlainTextResponse(GENERIC_ERROR, status_code=400)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(req: QueryRequest):
    return PlainTextResponse(orchestrator.handle(req.session_id, req.query))


@app.post("/query/audio")
def query_audio(req: QueryRequest):
    reply = orchestrator.handle(req.session_id, req.query)
    return StreamingResponse(synthesize_stream(reply), media_type="audio/wav")


@app.get("/history/{session_id}")
def history(session_id: str):
    return {"session_id": session_id, "turns": load_turns(session_id)}