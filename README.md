# GRAVEYARD

**Hunt ghost artifacts in Windows memory — with deterministic autonomous self-correction.**

GRAVEYARD is a Protocol SIFT extension for the [FIND EVIL! hackathon](https://findevil.devpost.com/) that detects **ghost processes**, **orphan sockets**, **timeline contradictions**, and hollow memory — then forces every finding through a **machine verifier** before a report ships.

## Competitive metrics (reproducible)

| Metric | GRAVEYARD | Prompt-only baseline |
|--------|-----------|----------------------|
| Ghost recall | **1.00** | 0.65 (est.) |
| Orphan recall | **1.00** | 0.50 (est.) |
| Combined F1 | **1.00** | ~0.58 (est.) |
| Hallucination catch | **100%** (2/2) | 0% |
| Self-correction | **Architectural** | None |
| MCP tools | **8** read-only | varies |
| Spoliation tests | **22** | varies |
| Multi-artifact | Engine + timeline + contradictions | ghost-only |

Run: `python scripts/benchmark_accuracy.py --exports examples/sample_exports --ground-truth examples/ground_truth_srl2018_sample.json --findings examples/findings_draft_v2_pass.json`

## Why GRAVEYARD?

Memory forensics agents hallucinate attribution. GRAVEYARD stops that with architectural guardrails:

1. **`graveyard_engine.py`** — Unified correlate: ghosts, orphans, timeline parity, contradictions, severity scores
2. **`verify_findings.py`** — Citation verifier REJECTs overclaims (exit code 1 → deterministic auto-correct)
3. **`scripts/benchmark_accuracy.py`** — F1, FPR, hallucination catch vs baseline JSON
4. **`scripts/agent_loop.sh`** — Autonomous loop: correlate → verify → auto-correct → verify (no LLM)
5. **`mcp_graveyard_server.py`** — 8 typed MCP tools, read-only, no shell

## One-command demos

**Windows:**
```powershell
pip install -r requirements.txt
.\run_demo.ps1
bash scripts/agent_loop.sh examples/sample_exports   # Git Bash / WSL
python scripts\benchmark_accuracy.py --exports examples\sample_exports --ground-truth examples\ground_truth_srl2018_sample.json --findings examples\findings_draft_v2_pass.json
python tests\test_spoliation.py
```

**Linux / SIFT:**
```bash
pip install -r requirements.txt
bash run_demo.sh
bash scripts/agent_loop.sh examples/sample_exports
bash scripts/spoliation_test.sh
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

## Quick start (SIFT Workstation)

```bash
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
bash install.sh
bash scripts/download_sample.sh   # tries Egnyte; prints manual steps if auth required
```

Offline demo with bundled sample exports:

```bash
python3 graveyard_engine.py --exports examples/sample_exports --output analysis/graveyard_engine_report.json
python3 verify_findings.py examples/findings_draft_v1_reject.json --exports examples/sample_exports --json-out   # exit 1
python3 verify_findings.py examples/findings_draft_v2_pass.json --exports examples/sample_exports --report reports/report.md  # exit 0
```

## MCP server (8 tools)

```bash
pip install -r requirements.txt
python mcp_graveyard_server.py   # stdio
```

See `mcp/README.md` for Claude/Cursor config JSON.

| Tool | Purpose |
|------|---------|
| `graveyard_correlate` | Ghost + orphan JSON |
| `graveyard_engine` | Unified scored report |
| `verify_findings` | Pass/fail + rejection reasons |
| `benchmark_accuracy` | Precision/recall/F1/FPR |
| `run_timeline_parity` | Memory vs disk + contradictions |
| `generate_audit_log` | sha256 audit events |
| `get_finding_schema` | Finding JSON schema |
| `spoliation_check` | Evidence path policy |

## What it detects

| Artifact | Definition | Source |
|----------|-----------|--------|
| Ghost process | PID in psscan, absent from pslist | `graveyard_engine.py` |
| Orphan socket | ESTABLISHED netscan PID not in pslist | `graveyard_engine.py` |
| Timeline contradiction | pslist running, disk timeline deleted | `graveyard_engine.py` |
| Hollow memory | PAGE_EXECUTE_READWRITE VAD on ghost PID | `windows.malfind` + verifier |
| Elevated priority | Ghost PID + orphan socket same PID | severity score 90 |

## Sample case

Bundled `examples/sample_exports/` — ghost PID **5678** (`powershell.exe`) + orphan ESTABLISHED to `198.51.100.42:4444`.

## Project structure

```
graveyard/
├── graveyard_engine.py        # Unified correlation engine
├── graveyard_correlate.py     # CLI wrapper (backward compatible)
├── graveyard_timeline.py      # Timeline parity CLI
├── verify_findings.py         # Finding verifier (self-correction gate)
├── spoliation_guard.py        # Evidence path policy
├── mcp_graveyard_server.py    # MCP (8 tools)
├── scripts/
│   ├── agent_loop.sh          # Deterministic autonomous self-correction
│   ├── run_live_triage.sh     # Full SIFT pipeline
│   ├── download_sample.sh     # Memory sample fetch / manual steps
│   ├── benchmark_accuracy.py  # Measured metrics vs ground truth
│   ├── auto_correct_findings.py
│   └── spoliation_test.sh     # PASS/FAIL demo runner
├── tests/test_spoliation.py   # 22 spoliation tests
├── mcp/README.md              # MCP config for SIFT
└── docs/
    ├── BENCHMARK_RESULTS.md   # Judge tables
    ├── DATASETS.md            # Public memory sample URLs
    ├── DEVPOST_SUBMISSION.md
    └── DEMO_SCRIPT.md
```

## Links

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID
- **Devpost:** `docs/DEVPOST_SUBMISSION.md`

## Manual steps after clone

1. **Record 5-min demo** — `run_demo.ps1` + `bash scripts/agent_loop.sh examples/sample_exports`
2. **Submit Devpost** — `docs/DEVPOST_SUBMISSION.md`
3. **Live SIFT run** — `docs/SIFT_SETUP.md` + real memory image

## License

MIT — see [LICENSE](LICENSE).
