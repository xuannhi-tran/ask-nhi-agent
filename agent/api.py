"""HTTP API, served by uvicorn inside the Docker image."""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from . import jd_match, limits
from .graph import ask, build_graph

app = FastAPI(title="Ask Nhi Agent")
_graph = None


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=300)


class MatchIn(BaseModel):
    job_description: str = Field(min_length=50, max_length=8000)


def _check_limit(request: Request):
    # The last X-Forwarded-For entry is the one our own proxy (Nginx / Azure ingress) added;
    # earlier entries can be faked by the client.
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[-1].strip() or (request.client.host if request.client else "unknown")
    verdict = limits.allow(ip)
    if verdict != "ok":
        raise HTTPException(429, "Too many questions right now. Please try again later.")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ask")
def ask_endpoint(body: AskIn, request: Request):
    _check_limit(request)
    global _graph
    _graph = _graph or build_graph()
    return ask(body.question, _graph)


@app.post("/match")
def match_endpoint(body: MatchIn, request: Request):
    _check_limit(request)
    try:
        return jd_match.match_jd(body.job_description)
    except RuntimeError as e:
        raise HTTPException(502, str(e))
