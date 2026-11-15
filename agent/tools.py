"""Plain Python tools, shared by the LangGraph agent and the MCP server."""

import json

from . import jd_match, retrieval


def search_portfolio(query: str) -> str:
    """Search Nhi's portfolio (projects, jobs, skills, FAQ). Returns the top matching excerpts with their source ids."""
    chunks = retrieval.search(query)
    if not chunks:
        return "No matching excerpts."
    return "\n\n".join(f"[{c.source}#{c.heading}] (score {c.score:.2f})\n{c.text}" for c in chunks)


def match_job_description(job_description: str) -> str:
    """Compare a pasted job description with Nhi's experience. Returns JSON: matched skills with evidence, missing skills, and a summary."""
    return jd_match.match_jd(job_description).model_dump_json(indent=2)


ALL_TOOLS = [search_portfolio, match_job_description]


def describe() -> str:
    return json.dumps([t.__name__ for t in ALL_TOOLS])
