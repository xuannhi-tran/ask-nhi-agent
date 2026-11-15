"""MCP server exposing Nhi's portfolio tools, e.g. to Claude Desktop.

Run locally:  python mcp_server.py   (stdio transport)
"""

from mcp.server.mcpserver import MCPServer

from agent.tools import match_job_description, search_portfolio

server = MCPServer(
    name="ask-nhi",
    instructions="Tools to look up Nhi's projects and experience, and to compare a job description with them.",
)
server.add_tool(search_portfolio)
server.add_tool(match_job_description)

if __name__ == "__main__":
    server.run()
