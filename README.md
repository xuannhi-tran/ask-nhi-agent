# Ask Nhi Agent

An agentic version of the "Ask Nhi" chatbot on [xuannhi.me](https://xuannhi.me), in Python.

- **LangGraph agent** on Claude that decides when to call tools and loops until it can answer with citations.
- **Two tools**: `search_portfolio` (Voyage embeddings + Supabase pgvector, the same index the website uses) and `match_job_description` (compares a job ad with Nhi's experience and returns schema-validated JSON through Claude structured outputs).
- **MCP server** exposing the same two tools, so Claude Desktop or any MCP client can use them.
- **FastAPI** service, **Docker**, **GitHub Actions** CI, deployed on **Azure Container Apps**.
- **Eval**: the website's 12-question eval set, graded on citations, required facts and refusals.

```
question ──► [model] ──tool call?──► [tools: search_portfolio | match_job_description] ──┐
                ▲                                                                       │
                └───────────────────────────── results ◄────────────────────────────────┘
             no tool call ──► answer with [source] citations
```

## Run locally

```bash
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env                               # then fill in the keys
python -m pytest -q                                  # offline tests, no keys needed
uvicorn agent.api:app --reload                       # http://localhost:8000/docs
python -m eval.run_eval                              # real eval, uses the API (add --delay 25 on a free Voyage account)
```

## Use it from Claude Desktop (MCP)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ask-nhi": {
      "command": "C:\\path\\to\\ask-nhi-agent\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\ask-nhi-agent\\mcp_server.py"]
    }
  }
}
```

## Deploy to Azure Container Apps (PowerShell)

Uses the Azure for Students subscription. The app scales to zero when idle, and `/ask` and `/match` are rate limited (10 per visitor per hour, 200 per day) so the public URL can't burn the API credit.

```powershell
az login
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az group create --name ask-nhi-rg --location australiaeast

# GitHub Actions builds the image and pushes it to ghcr.io on every push to main
# (make the package public once: GitHub profile -> Packages -> ask-nhi-agent -> Package settings).
az containerapp up --name ask-nhi-agent --resource-group ask-nhi-rg --location australiaeast `
  --image ghcr.io/xuannhi-tran/ask-nhi-agent:latest --ingress external --target-port 8080

# Keys go in as Container Apps secrets, never in the code (paste each value when asked)
$anthropic = Read-Host "ANTHROPIC_API_KEY"
$voyage = Read-Host "VOYAGE_API_KEY"
$supabase = Read-Host "SUPABASE_SECRET_KEY"
az containerapp secret set --name ask-nhi-agent --resource-group ask-nhi-rg `
  --secrets anthropic-key=$anthropic voyage-key=$voyage supabase-key=$supabase

az containerapp update --name ask-nhi-agent --resource-group ask-nhi-rg `
  --min-replicas 0 --max-replicas 1 `
  --set-env-vars ANTHROPIC_MODEL=claude-haiku-5-5 SUPABASE_URL=https://YOUR-PROJECT.supabase.co `
    ANTHROPIC_API_KEY=secretref:anthropic-key VOYAGE_API_KEY=secretref:voyage-key SUPABASE_SECRET_KEY=secretref:supabase-key

# The public URL
az containerapp show --name ask-nhi-agent --resource-group ask-nhi-rg --query properties.configuration.ingress.fqdn -o tsv
```

If `australiaeast` is refused (some student subscriptions limit regions), use `eastus` instead. To redeploy after a code change: push to main, wait for CI, then `az containerapp update --name ask-nhi-agent --resource-group ask-nhi-rg --image ghcr.io/xuannhi-tran/ask-nhi-agent:<commit sha>`. To remove everything: `az group delete --name ask-nhi-rg`.

## Results

<!-- TODO(Nhi): after running the eval, e.g. "11/12 eval cases pass; the agent cites a source in every answer." -->
