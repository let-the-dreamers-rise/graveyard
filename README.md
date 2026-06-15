# GRAVEYARD

**Hunt ghost artifacts in Windows memory — with autonomous self-correction.**

GRAVEYARD is a Protocol SIFT extension for the [FIND EVIL! hackathon](https://findevil.devpost.com/) that detects **ghost processes** (PIDs in `psscan` but not `pslist`), **orphan sockets** (ESTABLISHED connections without live processes), and hollow memory — then forces the AI agent to **prove every claim** against raw Volatility exports before a report ships.

## Why GRAVEYARD?

Memory forensics agents hallucinate attribution. GRAVEYARD stops that with two architectural guardrails:

1. **`graveyard_correlate.py`** — deterministic ghost detection (no LLM guessing)
2. **`verify_findings.py`** — citation verifier that REJECTs overclaims and triggers self-correction
3. **`mcp_graveyard_server.py`** — Pattern #2 lite: two typed MCP tools, read-only, no shell

The tiebreaker metric is **autonomous self-correction**: the agent drafts findings, gets REJECTed, fixes them, and passes — all logged.

## One-command demo (video-ready)

**Windows:**
```powershell
pip install -r requirements.txt
.\run_demo.ps1
```

**Linux / SIFT:**
```bash
pip install -r requirements.txt
bash run_demo.sh
```

Runs: correlate → v1 REJECT → v2 PASS → show report (pauses between steps for recording).

## Quick start (SIFT Workstation)

```bash
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
bash install.sh
```

Offline demo with bundled sample exports:

```bash
python graveyard_correlate.py --exports examples/sample_exports
python verify_findings.py examples/findings_draft_v1_reject.json --exports examples/sample_exports --json-out   # expect exit 1
python verify_findings.py examples/findings_draft_v2_pass.json --exports examples/sample_exports --report reports/report.md  # expect exit 0
```

## MCP server (Pattern #2 lite)

```bash
pip install -r requirements.txt
python mcp_graveyard_server.py   # stdio — add to Claude Desktop / Protocol SIFT
```

| Tool | Purpose |
|------|---------|
| `graveyard_correlate(exports_dir)` | Ghost + orphan JSON from Volatility exports |
| `verify_findings(findings_path, exports_dir)` | Pass/fail + rejection reasons |

See `docs/ARCHITECTURE.md` for security boundaries.

## What it detects

| Artifact | Definition | Source |
|----------|-----------|--------|
| Ghost process | PID in psscan, absent from pslist | `graveyard_correlate.py` |
| Orphan socket | ESTABLISHED netscan PID not in pslist | `graveyard_correlate.py` |
| Hollow memory | PAGE_EXECUTE_READWRITE VAD on ghost PID | `windows.malfind` + verifier |

## Sample case

Bundled `examples/sample_exports/` contains a ghost PID **5678** (`powershell.exe`) visible in psscan but hidden from pslist, plus an orphan ESTABLISHED connection to `198.51.100.42:4444`.

## Project structure

```
graveyard/
├── graveyard_correlate.py     # Core ghost correlator
├── verify_findings.py         # Finding verifier (self-correction gate)
├── mcp_graveyard_server.py    # MCP Pattern #2 lite (2 tools)
├── run_demo.ps1 / run_demo.sh # One-command video demo
├── install.sh                 # SIFT installer
├── requirements.txt           # mcp SDK
├── AGENTS.md                  # Agent triage playbook
├── schema/finding.schema.json
├── examples/
│   ├── sample_exports/        # Demo Volatility output
│   ├── graveyard_report.json  # Correlator output
│   ├── findings_draft_v1_reject.json
│   └── findings_draft_v2_pass.json
└── docs/                      # Hackathon deliverables
```

## Links

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID *(record using `run_demo.ps1`)*
- **Devpost:** Submit using `docs/DEVPOST_SUBMISSION.md`

## Manual steps after clone

1. **Record 5-min demo** — run `.\run_demo.ps1` or follow `docs/DEMO_SCRIPT.md`
2. **Submit to Devpost** — copy narrative from `docs/DEVPOST_SUBMISSION.md`
3. **Live SIFT run** (recommended) — follow `docs/SIFT_SETUP.md` with a real memory image

## License

MIT — see [LICENSE](LICENSE).
