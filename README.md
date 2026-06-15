# GRAVEYARD

**Hunt ghost artifacts in Windows memory — with autonomous self-correction.**

GRAVEYARD is a Protocol SIFT extension for the [FIND EVIL! hackathon](https://find-evil.devpost.com/) that detects **ghost processes** (PIDs in `psscan` but not `pslist`), **orphan sockets** (ESTABLISHED connections without live processes), and hollow memory — then forces the AI agent to **prove every claim** against raw Volatility exports before a report ships.

## Why GRAVEYARD?

Memory forensics agents hallucinate attribution. GRAVEYARD stops that with two architectural guardrails:

1. **`graveyard_correlate.py`** — deterministic ghost detection (no LLM guessing)
2. **`verify_findings.py`** — citation verifier that REJECTs overclaims and triggers self-correction

The tiebreaker metric is **autonomous self-correction**: the agent drafts findings, gets REJECTed, fixes them, and passes — all logged.

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
├── graveyard_correlate.py   # Core ghost correlator
├── verify_findings.py       # Finding verifier (self-correction gate)
├── install.sh                 # SIFT installer
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

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard *(push required — see below)*
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID *(record using docs/DEMO_SCRIPT.md)*
- **Devpost:** Submit using docs/DEVPOST_SUBMISSION.md

## Manual steps after clone

1. **Push to GitHub** — `git remote add origin ... && git push -u origin main`
2. **Record 5-min demo** — follow `docs/DEMO_SCRIPT.md`
3. **Submit to Devpost** — copy narrative from `docs/DEVPOST_SUBMISSION.md`
4. **Live SIFT run** (optional) — follow `docs/SIFT_SETUP.md` with a real memory image

## License

MIT — see [LICENSE](LICENSE).
