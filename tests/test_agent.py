"""Offline tests: a scripted fake model and a fake search index, so CI needs no API keys."""

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent import retrieval, tools
from agent.graph import ask, build_graph
from agent.retrieval import Chunk

FAKE_INDEX = [
    Chunk("jobcompass#results", "jobcompass", "Results", "75% overall accuracy on 20 unseen job ads.", 0.82),
]


class ScriptedModel(GenericFakeChatModel):
    """Returns pre-written messages in order; ignores bound tools."""

    def bind_tools(self, tools, **kwargs):
        return self


def scripted(*messages):
    return ScriptedModel(messages=iter(messages))


def test_agent_calls_search_then_answers(monkeypatch):
    seen = []

    def fake_search(query, k=5):
        seen.append(query)
        return FAKE_INDEX

    monkeypatch.setattr(retrieval, "search", fake_search)
    llm = scripted(
        AIMessage("", tool_calls=[{"name": "search_portfolio", "args": {"query": "JobCompass accuracy"}, "id": "t1"}]),
        AIMessage("JobCompass reached 75% accuracy [jobcompass]."),
    )
    result = ask("How accurate was JobCompass?", build_graph(llm))

    assert seen == ["JobCompass accuracy"]
    assert result["tool_calls"] == ["search_portfolio"]
    assert "[jobcompass]" in result["answer"]


def test_agent_can_answer_without_tools():
    llm = scripted(AIMessage("I can only answer questions about Nhi's work."))
    result = ask("Write me a poem about cats.", build_graph(llm))
    assert result["tool_calls"] == []


def test_search_tool_formats_sources(monkeypatch):
    monkeypatch.setattr(retrieval, "search", lambda q, k=5: FAKE_INDEX)
    out = tools.search_portfolio("accuracy")
    assert out.startswith("[jobcompass#Results]")


def test_search_tool_handles_empty(monkeypatch):
    monkeypatch.setattr(retrieval, "search", lambda q, k=5: [])
    assert tools.search_portfolio("kubernetes") == "No matching excerpts."


def test_tool_error_reaches_model_instead_of_crashing(monkeypatch):
    def broken_search(query, k=5):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(retrieval, "search", broken_search)
    llm = scripted(
        AIMessage("", tool_calls=[{"name": "search_portfolio", "args": {"query": "postgres"}, "id": "t1"}]),
        AIMessage("Search is unavailable right now."),
    )
    result = ask("Has Nhi used PostgreSQL?", build_graph(llm))
    assert result["answer"] == "Search is unavailable right now."


def test_search_retries_then_succeeds(monkeypatch):
    calls = []

    def flaky(query, k):
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("connection reset")
        return FAKE_INDEX

    monkeypatch.setattr(retrieval, "_search_once", flaky)
    monkeypatch.setattr(retrieval.time, "sleep", lambda s: None)
    assert retrieval.search("postgres") == FAKE_INDEX
    assert len(calls) == 3


def test_search_gives_up_after_attempts(monkeypatch):
    import pytest

    monkeypatch.setattr(retrieval, "_search_once", lambda q, k: (_ for _ in ()).throw(ConnectionError("down")))
    monkeypatch.setattr(retrieval.time, "sleep", lambda s: None)
    with pytest.raises(ConnectionError):
        retrieval.search("postgres")
