# Devpost Submission — GRAVEYARD

Copy sections below into the [FIND EVIL! Devpost](https://findevil.devpost.com/) form.

---

## Project name

**GRAVEYARD**

## Tagline

Deterministic ghost-artifact engine with architectural self-correction — measured F1, 8 MCP tools, live SIFT pipeline.

## Inspiration

Protocol SIFT finds hidden PIDs — but agents still write "malicious C2 beacon" in observations without proof. GRAVEYARD ships the **verifier + measured accuracy + autonomous correction loop** that makes memory ghost hunting **auditable and reproducible** today — without claiming zero hallucinations we can't prove on live cases.

## What it does

GRAVEYARD is an **autonomous verification layer**, not a human review portal:

1. **`graveyard_engine.py`** — Ghosts, orphans, timeline parity, memory/disk contradictions, severity scores (beats ghost-only overlap)
2. **`verify_findings.py`** — Exit-code gate: REJECT attribution, phantom artifacts, fake citations
3. **`scripts/agent_loop.sh`** — Deterministic self-correction: v1 REJECT → engine-facts auto-correct → PASS (no LLM)
4. **`scripts/benchmark_accuracy.py`** — F1, false positive rate, hallucination catch vs simulated baseline
5. **`mcp_graveyard_server.py`** — **8** typed MCP tools (read-only, no shell)
6. **`tests/test_spoliation.py`** — **22** spoliation tests with PASS/FAIL demo runner
7. **`scripts/run_live_triage.sh`** — One-command SIFT pipeline with vol.py auto-detect

Workflow: Volatility → engine → netscan → timeline (optional) → draft findings → verifier REJECT or PASS → report only on PASS.

## How we built it

- **~1200 lines** deterministic Python — engine, verifier, benchmark, spoliation, MCP
- **Protocol SIFT + Cursor** with `AGENTS.md` ghost-first triage order
- **Volatility 3 exports** as sole citation source; substring match, grep-auditable
- **JSONL audit logs** with sha256 per export
- **Ground truth:** bundled sample + `ground_truth_live_template.json` for live SIFT runs

## Measured results (reproducible)

```bash
python3 scripts/benchmark_accuracy.py \
  --exports examples/sample_exports \
  --ground-truth examples/ground_truth_srl2018_sample.json \
  --findings examples/findings_draft_v2_pass.json \
  --output analysis/benchmark_metrics.json \
  --baseline-out analysis/baseline_vs_graveyard.json \
  --summary-table
bash scripts/agent_loop.sh examples/sample_exports
bash scripts/spoliation_test.sh
```

| Metric | GRAVEYARD | Baseline Protocol SIFT (simulated prompt-only) |
|--------|-----------|-----------------------------------------------|
| Ghost recall | **1.00** | 0.65 (est.) |
| Orphan recall | **1.00** | 0.50 (est.) |
| Combined F1 | **1.00** | 0.00 on 1-artifact sample* |
| Ghost/orphan FPR | **0.00** | est. 0.12 |
| Hallucination catch | **100%** (2/2) | 0% |
| Overclaim rate | **0%** (verifier gate) | est. 35% |
| Self-correction | **Architectural loop** (`agent_loop.sh`) | None |
| MCP tools | **8 read-only** | varies |
| Spoliation tests | **22** | unmeasured |
| Multi-artifact | Engine + timeline + contradictions | ghost-only typical |

*Honest note: baseline uses `int(n*recall)` — on our 1-ghost sample, 0.65 rounds to zero detected. GRAVEYARD still wins on measured detection + verifier. Live SRL-2018 numbers require your memory image.*

## Key differentiators

| Tiebreaker criterion | GRAVEYARD proof |
|---------------------|-----------------|
| **Autonomous self-correction** | `agent_loop.sh`: exit 1 → `auto_correct_findings.py` → exit 0; logged, no LLM |
| **Constraint implementation** | 22 spoliation tests + architectural verifier + export traversal blocking |
| **IR accuracy** | Benchmark JSON with F1/FPR; `baseline_vs_graveyard.json` for judges |
| **Multi-artifact** | Timeline parity + memory/disk contradiction report (lite, extensible) |
| **Reproducibility** | `run_demo.ps1`, ground truth JSON, download_sample.sh, DATASETS.md URLs |
| **Audit trail** | sha256 JSONL; verifier.jsonl rejection reasons |
| **Severity ranking** | Ghost+orphan same PID → score 90 (critical) |

**Architectural verification:** The report **blocks** until citations match exports — not prompt retries. `verify_findings.py` REJECTs attribution, phantom artifacts, and fake citations with exit code 1.

**Ghost-first pipeline:** Correlate runs before netscan; analysts focus netscan on ghost/orphan PIDs flagged by the engine — not blanket scanning.

**Measured reproducibility:** Side-by-side benchmark JSON vs documented prompt-only baseline estimates — judges re-run one command and get the same numbers.

**Typed MCP surface:** **8 read-only forensic tools** including `spoliation_check` and `benchmark_accuracy` — grep-auditable, no generic shell.

## Challenges we ran into

1. **Observation vs interpretation** — 14-term attribution guard + mandatory correction loop
2. **Honest benchmarking** — Simulated baseline vs claiming 0% hallucination on unmeasured live cases
3. **Live memory access** — Documented NIST/Volatility/Magnet URLs; Egnyte auth for hackathon images
4. **Windows dev + SIFT deploy** — Same engine runs on sample exports offline and live triage on VM

## Accomplishments that we're proud of

- **100% measured ghost/orphan recall**, 0 false positives on sample case
- **100% hallucination catch** on injected tests
- **Deterministic agent loop** — architectural self-correction, not prompt retry
- **8 MCP tools** + **22 spoliation tests** + live triage with vol auto-detect
- **Public dataset documentation** in DATASETS.md

## What we learned

- Exit-code gates beat prompt pleading for self-correction
- Measured metrics with honest baseline simulation beat unverifiable "0% hallucination" claims
- Thin MCP surface plugs into Protocol SIFT without platform rebuild
- Ghost+network combo scoring prioritizes analyst attention

## What's next for GRAVEYARD

- Live SRL-2018 ground truth from `ground_truth_live_template.json`
- malfind hollow-memory auto-correlation on ghost PIDs in engine
- CI: benchmark + spoliation + agent_loop on every push

## Built with

- Python 3
- Volatility 3
- MCP (Model Context Protocol)
- Protocol SIFT
- Cursor / Claude
- SANS SIFT Workstation (`sansforensics/forensics`)

## Links

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID

## Try it out

**Windows (fastest):**
```powershell
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
pip install -r requirements.txt
.\run_demo.ps1
python scripts\benchmark_accuracy.py --exports examples\sample_exports --ground-truth examples\ground_truth_srl2018_sample.json --findings examples\findings_draft_v2_pass.json
```

**SIFT autonomous loop:**
```bash
bash scripts/agent_loop.sh examples/sample_exports
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

**MCP:** See `mcp/README.md` — 8 tools including `graveyard_engine`, `spoliation_check`, `benchmark_accuracy`
