# Devpost Submission — GRAVEYARD

Copy sections below into the [FIND EVIL! Devpost](https://findevil.devpost.com/) form.

---

## Project name

**GRAVEYARD**

## Tagline

Autonomous ghost-artifact verifier for memory triage — deterministic detection, exit-code self-correction.

## Inspiration

Protocol SIFT can spot hidden PIDs — but agents still write "malicious C2 beacon" in the observation field without proof. Rob Lee's own demo starts with psscan−pslist ghost detection. We built GRAVEYARD to make that step **deterministic** and every finding **machine-verifiable** before a human ever reviews it.

## What it does

GRAVEYARD is an **autonomous verification layer**, not a human review portal. It extends Protocol SIFT with:

1. **`graveyard_correlate.py`** — Ghost-first detection: psscan − pslist diff + orphan ESTABLISHED sockets (no LLM)
2. **`verify_findings.py`** — Exit-code gate: REJECT on attribution, phantom artifacts, or citation mismatch → agent self-corrects
3. **`mcp_graveyard_server.py`** — Pattern #2 lite: two typed MCP tools, read-only, no shell
4. **`run_demo.ps1` / `run_demo.sh`** — One command reproduces the full self-correction loop for judges

Workflow: Volatility → correlate ghosts → **then** netscan on flagged PIDs only → draft findings → verifier REJECT or PASS → report only on PASS.

## How we built it

- **~300 lines** of deterministic Python (correlate + verifier) — reproducible offline, no API keys
- **Protocol SIFT + Cursor** for agent orchestration; `AGENTS.md` mandates ghost-first triage order
- **Volatility 3 exports** as sole citation source; substring match, grep-auditable
- **MCP stdio server** exposing correlate + verify as typed tools (FIND EVIL architectural pattern #2, lightweight)
- **JSONL execution logs** with 2026-06-16 demo trace; `token_usage` field reserved for live agent runs

Architecture: prompt guardrails (soft) + correlator/verifier exit codes (hard). The agent cannot ship a report while the verifier returns exit 1.

## Challenges we ran into

1. **Observation vs interpretation** — 14-term attribution guard + mandatory self-correction loop
2. **Competitive scope** — Top submissions (Council-SIFT, EvidenceChain) cover disk+timeline+MCP suites; we chose depth on memory ghosts + verifiable minimalism
3. **Honest spoliation docs** — Verifier is architectural; evidence-image protection is prompt-only until OS read-only mounts
4. **Offline judges** — Bundled synthetic exports with known ghost PID 5678; `run_demo.ps1` pauses between steps for video

## Accomplishments that we're proud of

- **100% ghost/orphan recall**, 0 false positives on sample case
- **Autonomous self-correction**: v1 REJECT → v2 PASS, logged with rejection reasons
- **Ghost-first sequencing** — netscan only after correlate flags PIDs (noise + token reduction)
- **One-command demo** + MCP integration — judges run the full loop in under 2 minutes

## What we learned

- Exit-code gates beat prompt pleading for self-correction
- Substring citations are simple, auditable, and judge-friendly
- A thin MCP surface (2 tools) plugs into Protocol SIFT without rebuilding a platform
- Honest constraint documentation (what's architectural vs prompt-only) is signal, not weakness

## What's next for GRAVEYARD

- Live SRL-2018 memory run on SIFT Workstation
- malfind hollow-memory auto-correlation on ghost PIDs
- Append-only export hashing at capture time
- CI workflow running `run_demo.ps1` on every push

## Built for FIND EVIL — competitive positioning

| Dimension | GRAVEYARD focus |
|-----------|-----------------|
| Tiebreaker (self-correction) | v1 REJECT → v2 PASS with logged ATTRIBUTION_GUARD |
| Constraint implementation | Verifier exit-code gate + read-only MCP (2 tools, no shell) |
| IR accuracy | Observation/interpretation split enforced programmatically |
| Breadth | Memory-deep; disk/timeline left to Protocol SIFT skills |
| Reproducibility | Offline demo, ~300 LOC, one-command `run_demo` |

We complement broader submissions (multi-artifact MCP platforms, council verifiers) by shipping a **focused, auditable memory ghost hunter** any Protocol SIFT agent can call today.

## Built with

- Python 3
- Volatility 3
- MCP (Model Context Protocol)
- Protocol SIFT
- Cursor / Claude
- SANS SIFT Workstation

## Links

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID *(record with `run_demo.ps1`)*

## Try it out

**Windows (fastest):**
```powershell
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
pip install -r requirements.txt
.\run_demo.ps1
```

**Linux / SIFT:**
```bash
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
pip install -r requirements.txt
bash run_demo.sh
```

**MCP server (add to Claude Desktop / Protocol SIFT):**
```json
{
  "mcpServers": {
    "graveyard": {
      "command": "python",
      "args": ["mcp_graveyard_server.py"],
      "cwd": "/path/to/graveyard"
    }
  }
}
```

Or on SIFT: `bash install.sh` then follow `docs/SIFT_SETUP.md`.
