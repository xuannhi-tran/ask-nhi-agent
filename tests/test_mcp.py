import asyncio

from mcp_server import server


def test_mcp_exposes_both_tools():
    names = {t.name for t in asyncio.run(server.list_tools())}
    assert names == {"search_portfolio", "match_job_description"}
