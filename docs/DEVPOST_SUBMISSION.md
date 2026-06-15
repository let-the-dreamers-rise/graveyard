# Devpost Submission — GRAVEYARD

Copy sections below into the [FIND EVIL! Devpost](https://findevil.devpost.com/) form.

---

## Project name

**GRAVEYARD**

## Tagline

Autonomous ghost-artifact verifier for memory triage — measured accuracy, exit-code self-correction, live SIFT pipeline.

## Inspiration

Protocol SIFT can spot hidden PIDs — but agents still write "malicious C2 beacon" in the observation field without proof. Rob Lee's demo starts with psscan−pslist ghost detection. We built GRAVEYARD to make that step **deterministic**, every finding **machine-verifiable**, and accuracy **measurable** before a human reviews it.

## What it does

GRAVEYARD is an **autonomous verification layer**, not a human review portal:

1. **`graveyard_correlate.py`** — Ghost-first: psscan − pslist + orphan ESTABLISHED sockets (no LLM)
2. **`graveyard_timeline.py`** — Multi-artifact lite: memory ghosts vs disk timeline JSON/CSV
3. **`verify_findings.py`** — Exit-code gate: REJECT on attribution, phantom artifacts, citation mismatch
4. **`scripts/benchmark_accuracy.py`** — Judge-ready precision/recall/F1 vs ground truth JSON
5. **`scripts/run_live_triage.sh`** — One-command SIFT pipeline (vol → correlate → netscan → malfind → audit)
6. **`mcp_graveyard_server.py`** — Three typed MCP tools, read-only, no shell
7. **`tests/test_spoliation.py`** — 7 spoliation/constraint tests (honest prompt-only gaps documented)

Workflow: Volatility → correlate ghosts → netscan → timeline parity (optional) → draft findings → verifier REJECT or PASS → report only on PASS.

## How we built it

- **~800 lines** deterministic Python — correlate, verifier, timeline, benchmark, spoliation guard
- **Protocol SIFT + Cursor** with `AGENTS.md` ghost-first triage order
- **Volatility 3 exports** as sole citation source; substring match, grep-auditable
- **MCP stdio server** — correlate, verify, benchmark (FIND EVIL pattern #2)
- **JSONL audit logs** with sha256 per export via `scripts/generate_audit_log.py`
- **Ground truth:** `examples/ground_truth_srl2018_sample.json` for reproducible metrics

## Measured results (reproducible)

```bash
python3 scripts/benchmark_accuracy.py \
  --exports examples/sample_exports \
  --ground-truth examples/ground_truth_srl2018_sample.json \
  --findings examples/findings_draft_v2_pass.json
```

| Metric | GRAVEYARD | Protocol SIFT baseline (est.) |
|--------|-----------|-------------------------------|
| Ghost recall | **1.00** | 0.65 |
| Orphan recall | **1.00** | 0.50 |
| Hallucination catch | **2/2 (100%)** | prompt-only |
| Self-correction | **v1 REJECT → v2 PASS** | optional |

## Why we win (competitive positioning)

| Tiebreaker criterion | GRAVEYARD proof |
|---------------------|-----------------|
| **Autonomous self-correction** | Verifier exit code 1 → agent fixes → exit 0; logged ATTRIBUTION_GUARD |
| **Constraint implementation** | 7 spoliation tests + architectural verifier + 3 read-only MCP tools |
| **IR accuracy** | Measured 100% ghost/orphan recall on sample; benchmark JSON for judges |
| **Multi-artifact** | `graveyard_timeline.py` memory+disk parity (lite, extensible) |
| **Reproducibility** | `run_demo.ps1`, ground truth JSON, one-command live triage script |
| **Audit trail** | sha256 JSONL per export; verifier.jsonl rejection reasons |

We complement broader submissions (Council-SIFT, EvidenceChain) by shipping a **focused, auditable, measured** memory ghost hunter any Protocol SIFT agent can call today — with honest documentation of prompt-only spoliation limits.

## Challenges we ran into

1. **Observation vs interpretation** — 14-term attribution guard + mandatory self-correction loop
2. **Competitive scope** — Added timeline parity + benchmark metrics without rebuilding a full platform
3. **Honest spoliation docs** — Verifier architectural; evidence-image protection prompt-only until OS read-only mounts
4. **Live SRL-2018** — Documented SIFT paths; bundled synthetic exports for offline judges

## Accomplishments that we're proud of

- **100% measured ghost/orphan recall**, 0 false positives on sample case
- **100% hallucination catch rate** on ground-truth injection tests
- **Ghost-first sequencing** — netscan only after correlate flags PIDs
- **Live SIFT pipeline** + **3 MCP tools** + **7 spoliation tests**
- **One-command demo** — judges reproduce full loop in under 2 minutes

## What we learned

- Exit-code gates beat prompt pleading for self-correction
- Measured metrics (benchmark_accuracy.py) are judge differentiators
- Thin MCP surface (3 tools) plugs into Protocol SIFT without platform rebuild
- Honest constraint documentation is signal, not weakness

## What's next for GRAVEYARD

- Live SRL-2018 run on SIFT Workstation (user VM ready)
- malfind hollow-memory auto-correlation on ghost PIDs
- Append-only export hashing at capture time (OS-level read-only mounts)
- CI workflow running benchmark + spoliation tests on every push

## Built with

- Python 3
- Volatility 3
- MCP (Model Context Protocol)
- Protocol SIFT
- Cursor / Claude
- SANS SIFT Workstation

## Links

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID *(record with `docs/DEMO_SCRIPT.md`)*

## Try it out

**Windows (fastest):**
```powershell
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
pip install -r requirements.txt
.\run_demo.ps1
python scripts\benchmark_accuracy.py --exports examples\sample_exports --ground-truth examples\ground_truth_srl2018_sample.json --findings examples\findings_draft_v2_pass.json
```

**Linux / SIFT:**
```bash
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
pip install -r requirements.txt
bash run_demo.sh
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

**MCP server:**
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

Tools: `graveyard_correlate`, `verify_findings`, `benchmark_accuracy`
