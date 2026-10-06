from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core.agent.workflow import ToolCallResult
from llama_index.core.workflow import Context
from pydantic import BaseModel, Field

from .rag import build_agent

# session_id -> agent Context (holds conversation memory). In-memory: lost on restart.
sessions: dict[str, Context] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = build_agent()  # load index + models once at startup
    yield


app = FastAPI(title="RAG Support API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class Source(BaseModel):
    file: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[Source]


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    agent = app.state.agent
    session_id = req.session_id or str(uuid4())

    ctx = sessions.get(session_id)
    if ctx is None:
        ctx = Context(agent)
        sessions[session_id] = ctx

    found: dict[str, float] = {}
    try:
        handler = agent.run(req.message, ctx=ctx)
        async for event in handler.stream_events():
            if isinstance(event, ToolCallResult):
                raw = getattr(event.tool_output, "raw_output", None)
                for node in getattr(raw, "source_nodes", None) or []:
                    name = node.node.metadata.get("file_name", "unknown")
                    found[name] = max(found.get(name, 0.0), float(node.score or 0.0))
        result = await handler
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc

    sources = [Source(file=f, score=round(s, 3)) for f, s in sorted(found.items(), key=lambda x: -x[1])]
    return ChatResponse(session_id=session_id, answer=str(result), sources=sources)


@app.delete("/api/sessions/{session_id}")
async def reset_session(session_id: str):
    sessions.pop(session_id, None)
    return {"ok": True}