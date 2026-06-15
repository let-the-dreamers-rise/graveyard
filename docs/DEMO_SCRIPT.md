# GRAVEYARD Demo Video Script (~5 minutes)

Two paths: **offline sample** (Windows/SIFT) and **autonomous agent loop** (tiebreaker).

---

## Path A — Offline sample (0:00–3:30)

### [0:00–0:20] Hook

**Narration:**
> "Memory forensics agents find evil — and hallucinate it. GRAVEYARD hunts ghost artifacts with a deterministic engine, architectural verifier, and measured accuracy. When the AI overclaims, our agent loop self-corrects without a human — and without another LLM call."

### [0:20–0:50] Benchmark

```bash
python3 scripts/benchmark_accuracy.py \
  --exports examples/sample_exports \
  --ground-truth examples/ground_truth_srl2018_sample.json \
  --findings examples/findings_draft_v2_pass.json \
  --output analysis/benchmark_metrics.json
```

**Highlight:** ghost_recall 1.0, combined_f1 1.0, hallucination_catch_rate 1.0

### [0:50–1:30] Unified engine

```bash
python3 graveyard_engine.py --exports examples/sample_exports
```

**Highlight:** PID 5678 severity_score 90, priority critical (ghost + orphan)

### [1:30–2:00] Timeline + contradictions

```bash
python3 graveyard_engine.py \
  --exports examples/sample_exports \
  --timeline examples/disk_timeline_sample.json \
  --output analysis/graveyard_engine_report.json
```

### [2:00–2:45] Verifier REJECT

```bash
python3 verify_findings.py examples/findings_draft_v1_reject.json \
  --exports examples/sample_exports --json-out
```

**Highlight:** ATTRIBUTION_GUARD — pause 3 seconds

### [2:45–3:30] Verifier PASS

```bash
python3 verify_findings.py examples/findings_draft_v2_pass.json \
  --exports examples/sample_exports --report reports/report.md
```

---

## Path B — Autonomous agent loop (3:30–4:30) ⭐ tiebreaker

**Narration:**
> "This is deterministic self-correction — not prompt engineering. The loop injects a bad finding, verifier rejects, engine rebuilds facts-only findings, verifier passes."

```bash
bash scripts/agent_loop.sh examples/sample_exports
```

**Highlight:**
- `v1 exit code: 1`
- `auto_correct_findings (engine facts only, no LLM)`
- `RESULT: PASS — deterministic self-correction demonstrated`

Optional Windows (Git Bash):
```powershell
bash scripts/agent_loop.sh examples/sample_exports
```

---

## Path C — SIFT live (4:30–5:00, optional)

```bash
bash scripts/download_sample.sh
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

Fill `examples/ground_truth_live_template.json` → `analysis/ground_truth_live.json`

---

## Spoliation + MCP (B-roll)

```bash
bash scripts/spoliation_test.sh
python3 mcp_graveyard_server.py   # show 8 tools in mcp/README.md
```

---

## Close

> "GRAVEYARD: 8 MCP tools, 17 spoliation tests, measured F1, and an agent loop that proves autonomous self-correction. GitHub in description."

**End card:** https://github.com/let-the-dreamers-rise/graveyard

---

## Windows one-liner

```powershell
.\run_demo.ps1
python scripts\benchmark_accuracy.py --exports examples\sample_exports --ground-truth examples\ground_truth_srl2018_sample.json --findings examples\findings_draft_v2_pass.json
python tests\test_spoliation.py
```

## Recording tips

- Show `agent_loop.sh` PASS banner — judges care about tiebreaker
- Show benchmark JSON numbers, not slides
- Keep under 5:00 — cut SIFT live if long
