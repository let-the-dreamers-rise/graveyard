# GRAVEYARD MCP Server

Read-only MCP tools for Protocol SIFT / Claude Desktop / Cursor on SANS SIFT Workstation.

## Tools (8)

| Tool | Purpose |
|------|---------|
| `graveyard_correlate` | Ghost processes + orphan sockets from Volatility exports |
| `graveyard_engine` | Unified report with severity scores, timeline, contradictions |
| `verify_findings` | Citation verifier — pass/fail + rejection reasons |
| `benchmark_accuracy` | Precision/recall/F1/FPR vs ground truth JSON |
| `run_timeline_parity` | Memory ghosts vs disk timeline + contradiction report |
| `generate_audit_log` | sha256 audit events (returned in response, no disk write) |
| `get_finding_schema` | JSON schema for finding drafts |
| `spoliation_check` | Evidence path / export traversal policy check |

All tools are **read-only** — no shell execution, no writes to evidence paths.

## Install on SIFT

```bash
cd /path/to/graveyard
pip install -r requirements.txt
python3 mcp_graveyard_server.py   # stdio — test manually
```

## Claude Desktop config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:

```json
{
  "mcpServers": {
    "graveyard": {
      "command": "python3",
      "args": ["/path/to/graveyard/mcp_graveyard_server.py"],
      "cwd": "/path/to/graveyard"
    }
  }
}
```

## Cursor MCP config

Add to Cursor MCP settings (`.cursor/mcp.json` or Settings → MCP):

```json
{
  "mcpServers": {
    "graveyard": {
      "command": "python3",
      "args": ["mcp_graveyard_server.py"],
      "cwd": "/cases/graveyard"
    }
  }
}
```

On Windows (dev / offline demo):

```json
{
  "mcpServers": {
    "graveyard": {
      "command": "python",
      "args": ["C:\\path\\to\\graveyard\\mcp_graveyard_server.py"],
      "cwd": "C:\\path\\to\\graveyard"
    }
  }
}
```

## Example agent prompts

- "Run `graveyard_engine` on `examples/sample_exports` and summarize ranked artifacts."
- "Verify `examples/findings_draft_v2_pass.json` against `examples/sample_exports`."
- "Benchmark accuracy with ground truth `examples/ground_truth_srl2018_sample.json`."
- "Check spoliation policy for write to `/cases/graveyard/evidence/mem.raw`."

## Security boundaries

- MCP server never invokes `vol.py` or shell
- `spoliation_check` documents policy; OS-level read-only mounts still recommended for evidence images
- Verifier is architectural; agents must still tee Volatility output to `exports/`

See `docs/ARCHITECTURE.md` for full design.
