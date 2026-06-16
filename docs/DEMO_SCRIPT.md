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
  --output analysis/benchmark_metrics.json \
  --baseline-out analysis/baseline_vs_graveyard.json \
  --summary-table
```

**Narration:**
> "One command prints measured F1, false positive rate, and hallucination catch. GRAVEYARD hits one-point-oh on ghost and orphan recall with zero false positives on the sample case. The prompt-only baseline misses artifacts and catches zero hallucinations."

**Highlight on screen:** ghost_recall 1.0, combined_f1 1.0, hallucination_catch_rate 1.0

### [0:50–1:30] Unified engine

```bash
python3 graveyard_engine.py --exports examples/sample_exports
```

**Narration:**
> "The unified engine correlates ghosts, orphans, timeline parity, and contradictions — with severity scoring. PID fifty-six seventy-eight scores ninety — critical — because it's both a ghost process and an orphan socket."

**Highlight:** PID 5678 severity_score 90, priority critical (ghost + orphan)

### [1:30–2:00] Timeline + contradictions

```bash
python3 graveyard_engine.py \
  --exports examples/sample_exports \
  --timeline examples/disk_timeline_sample.json \
  --output analysis/graveyard_engine_report.json
```

**Narration:**
> "EvidenceChain-style memory-versus-disk contradictions — in a hundred lines you run today on SIFT."

### [2:00–2:45] Verifier REJECT

```bash
python3 verify_findings.py examples/findings_draft_v1_reject.json \
  --exports examples/sample_exports --json-out
```

**Narration:**
> "The verifier is the gate. Attribution in the observation field — REJECT. Exit code one. No report ships."

**Highlight:** ATTRIBUTION_GUARD — pause 3 seconds

### [2:45–3:30] Verifier PASS

```bash
python3 verify_findings.py examples/findings_draft_v2_pass.json \
  --exports examples/sample_exports --report reports/report.md
```

**Narration:**
> "Facts-only observations with exact export citations — PASS. Exit code zero. Report generated."

---

## Path B — Autonomous agent loop (3:30–4:30) ⭐ tiebreaker

**Narration (before command):**
> "This is deterministic self-correction — not prompt engineering. Watch the loop: engine facts, intentional bad finding, verifier rejects, auto-correct rebuilds from engine only, verifier passes. No LLM in the loop."

```bash
bash scripts/agent_loop.sh examples/sample_exports
```

**Word-for-word narration (sync to terminal output):**

> "Step one — graveyard engine builds the scored correlation report."
>
> "Step two — generate findings from engine facts. Demo mode injects an attribution violation — the kind of overclaim agents make every day."
>
> "Verify iteration one — exit code one. REJECT. The architectural gate caught it."
>
> "Auto-correct iteration one — rebuild from engine facts only. No LLM."
>
> "Verify iteration two — exit code zero. PASS."
>
> "Agent Loop Complete — PASS on iteration two."
>
> "RESULT: PASS — deterministic self-correction demonstrated."

**Highlight on screen:**
- `v1 exit code: 1` (or `exit code: 1` on verify 1)
- `[auto-correct 1/3] rebuild from engine facts (no LLM)`
- `RESULT: PASS — deterministic self-correction demonstrated`

Optional Windows (Git Bash or PowerShell):

```powershell
bash scripts/agent_loop.sh examples/sample_exports
# or
powershell -File scripts/agent_loop.ps1
```

---

## Path C — SIFT live (4:30–5:00, optional)

```bash
bash scripts/download_sample.sh
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

**Narration:**
> "Same pipeline on live Volatility exports. Fill ground truth template for your memory image."

Fill `examples/ground_truth_live_template.json` → `analysis/ground_truth_live.json`

---

## Spoliation + MCP (B-roll)

```bash
bash scripts/spoliation_test.sh
python3 mcp_graveyard_server.py   # show 8 tools in mcp/README.md
```

**Narration:**
> "Twenty-two spoliation tests block evidence tampering. Eight typed MCP tools — read-only, no shell."

---

## Close

> "GRAVEYARD: measured F1, eight MCP tools, twenty-two spoliation tests, and an agent loop that proves autonomous self-correction. GitHub in description."

**End card:** https://github.com/let-the-dreamers-rise/graveyard

---

## Windows one-liner

```powershell
$env:PAUSE=0; .\run_demo.ps1
python scripts\benchmark_accuracy.py --exports examples\sample_exports --ground-truth examples\ground_truth_srl2018_sample.json --findings examples\findings_draft_v2_pass.json --summary-table
python tests\test_spoliation.py
bash scripts/agent_loop.sh examples/sample_exports
```

## Recording tips

- Show `agent_loop.sh` PASS banner — judges care about tiebreaker
- Show benchmark `--summary-table` output, not slides
- Keep under 5:00 — cut SIFT live if long
