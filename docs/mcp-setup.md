# MCP Server Setup — Data Tools

Orbital agents can use these data tools when connected. They degrade gracefully when unavailable — agents note data gaps in their contributions rather than failing.

---

## BigQuery

**What agents use it for:** Custom cohort queries, raw event data, segment analysis (Data, Data-Science, Analyst agents).

**Setup:**

1. Install a BigQuery MCP server (e.g., `@anthropic/bigquery-mcp` or community alternatives)
2. Configure in Claude Code settings (`~/.claude/settings.json`):
   ```json
   {
     "mcpServers": {
       "bigquery": {
         "command": "npx",
         "args": ["-y", "@anthropic/bigquery-mcp"],
         "env": {
           "GOOGLE_CLOUD_PROJECT": "your-project-id",
           "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account.json"
         }
       }
     }
   }
   ```
3. Required permissions: `bigquery.jobs.create`, `bigquery.tables.getData` on relevant datasets
4. Verify: Run a test query through Claude Code to confirm connectivity

**Datasets typically needed:**
- User events / clickstream
- Order history
- Subscription lifecycle (Pro)
- Experiment results (Eppo/internal)

**Graceful degradation:** When BigQuery is not connected, Data and Analyst agents should note "BigQuery not available — findings based on available Google Sheets data and context documents" in their contribution and reduce confidence scores for findings that would normally require raw data queries.

---

## Tableau

**What agents use it for:** Dashboard access, visualization review, executive reporting data (Data, Analyst, Financial agents).

**Setup:**

1. Install a Tableau MCP server
2. Configure with Tableau Online/Server credentials:
   ```json
   {
     "mcpServers": {
       "tableau": {
         "command": "npx",
         "args": ["-y", "tableau-mcp-server"],
         "env": {
           "TABLEAU_SERVER_URL": "https://your-org.online.tableau.com",
           "TABLEAU_SITE_ID": "your-site",
           "TABLEAU_TOKEN_NAME": "mcp-token",
           "TABLEAU_TOKEN_VALUE": "your-personal-access-token"
         }
       }
     }
   }
   ```
3. Generate a Personal Access Token in Tableau: Settings > Personal Access Tokens
4. Verify: List available workbooks through Claude Code

**Graceful degradation:** When Tableau is not connected, agents should note the gap and rely on Google Sheets exports or screenshot references from context documents.

---

## Looker

**What agents use it for:** Product metrics, segment data, funnel analysis (Data, Analyst agents).

**Setup:**

1. Install a Looker MCP server
2. Configure with Looker API credentials:
   ```json
   {
     "mcpServers": {
       "looker": {
         "command": "npx",
         "args": ["-y", "looker-mcp-server"],
         "env": {
           "LOOKER_BASE_URL": "https://your-org.cloud.looker.com",
           "LOOKER_CLIENT_ID": "your-client-id",
           "LOOKER_CLIENT_SECRET": "your-client-secret"
         }
       }
     }
   }
   ```
3. Create API credentials in Looker: Admin > Users > API Keys
4. Verify: List available looks/dashboards through Claude Code

**Graceful degradation:** When Looker is not connected, agents should use Google Sheets data or context documents. Note reduced data coverage in findings.

---

## Anthropic API (Quality Gates Layer 2)

**What it's used for:** Layer 2 LLM-as-Judge evaluation — each finding is scored against 5 binary rubrics via Claude Haiku API calls. Not an MCP server, but a direct API dependency for the quality gate system.

**Setup:**

1. Set the `ANTHROPIC_API_KEY` environment variable before starting the server:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
2. Verify: `POST /api/workspaces/{id}/quality/evaluate` should return rubric scores

**Graceful degradation:** When `ANTHROPIC_API_KEY` is not set, Layer 2 returns a degraded report (`"degraded": true`, `"degraded_reason": "No API key configured"`). Layer 1 deterministic gates and Layer 3 judge agent continue to function independently.

See `docs/quality-gates.md` for the full quality evaluation system documentation.

---

## Already Connected (no setup needed)

These MCP servers are available in the current Claude Code environment:

| Tool | MCP Server | Status |
|------|-----------|--------|
| Figma | plugin:figma:figma | Available (may need OAuth) |
| GitHub | github | Available |
| Google Workspace (Drive, Sheets, Gmail) | google-workspace | Available |
| Linear | claude.ai Linear | Available |
| Slack | slack | Available (may need OAuth) |
| Jira/Confluence | atlassian | Available (may need OAuth) |
| Miro | claude.ai Miro | Available (may need OAuth) |
