# GRAVEYARD Demo Video Script (~5 minutes)

Record on SIFT live or locally with bundled sample exports. Terminal + Cursor side by side.

---

## [0:00–0:25] Hook — "The Graveyard Problem"

**Screen:** Title slide or README

**Narration (word-for-word):**
> "Memory forensics agents find evil — but they also hallucinate it. GRAVEYARD hunts ghost artifacts: processes that exist in memory pool scans but not in active process lists, and network sockets with no live process. When the AI overclaims, our verifier forces autonomous self-correction — with measured precision and recall for the judges."

**Action:** Show README tagline and `docs/ARCHITECTURE.md` diagram.

---

## [0:25–1:00] Measured accuracy — benchmark

**Screen:** Terminal

**Narration:**
> "Before the demo, here are real numbers. Our benchmark script scores correlate output and findings against ground truth JSON."

**Commands:**
```bash
cd graveyard
python3 scripts/benchmark_accuracy.py \
  --exports examples/sample_exports \
  --ground-truth examples/ground_truth_srl2018_sample.json \
  --findings examples/findings_draft_v2_pass.json \
  --output analysis/benchmark_metrics.json
```

**Highlight:** `"ghost_recall": 1.0`, `"hallucination_catch_rate": 1.0` in output.

**Narration:**
> "One hundred percent ghost recall, one hundred percent hallucination catch rate on the sample case. Judges can reproduce this in ten seconds."

---

## [1:00–1:45] Sample case — ghost PID 5678

**Screen:** Terminal

**Narration:**
> "Our bundled case mirrors SRL-2018 ghost patterns. PID 5678 is PowerShell in psscan but absent from pslist."

**Commands:**
```bash
grep 5678 examples/sample_exports/psscan_20240315.txt
grep 5678 examples/sample_exports/pslist_20240315.txt || echo "NOT in pslist — ghost!"
python3 graveyard_correlate.py --exports examples/sample_exports
```

**Highlight:** `"ghost_count": 1`, orphan socket to 198.51.100.42:4444.

---

## [1:45–2:15] Multi-artifact timeline parity

**Screen:** Terminal

**Narration:**
> "GRAVEYARD also cross-checks memory ghosts against disk timeline exports — lightweight multi-source correlation."

**Commands:**
```bash
python3 graveyard_timeline.py \
  --exports examples/sample_exports \
  --timeline examples/disk_timeline_sample.json
```

**Highlight:** `"parity_matches": 1` — powershell.exe on disk and in memory ghost.

---

## [2:15–3:15] Self-correction — verifier REJECT

**Screen:** Terminal

**Narration:**
> "The agent drafts findings. Version one overclaims — it calls cmd.exe a malicious C2 beacon in the observation field. The verifier rejects it. The agent must self-correct. No arguing with the verifier."

**Commands:**
```bash
python3 verify_findings.py examples/findings_draft_v1_reject.json \
  --exports examples/sample_exports --json-out
echo "Exit code: $?"
```

**Highlight:** ATTRIBUTION_GUARD, CONFIDENCE_GUARD. Pause 3 seconds.

---

## [3:15–4:15] Self-correction — verifier PASS + audit trail

**Screen:** Terminal

**Narration:**
> "Version two moves attribution to interpretation, cites exact export substrings, and uses inferred confidence. Report only generates after verification passes."

**Commands:**
```bash
python3 verify_findings.py examples/findings_draft_v2_pass.json \
  --exports examples/sample_exports --report reports/report.md
python3 scripts/generate_audit_log.py --exports examples/sample_exports
head -5 docs/execution_logs/execution_log.jsonl
```

**Highlight:** PASSED, sha256 hashes in audit log.

---

## [4:15–4:45] SIFT live triage (optional — record on VM)

**Screen:** SIFT terminal

**Narration:**
> "On SANS SIFT, one script runs the full pipeline: Volatility, correlate, netscan, malfind, audit log, and findings template."

**Commands:**
```bash
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

**Narration:**
> "Copy your SRL-2018 or FOR508 memory image to evidence first. See docs/DATASETS.md for paths."

---

## [4:45–5:00] Close

**Narration (word-for-word):**
> "GRAVEYARD wins on the tiebreaker: autonomous self-correction with a full audit trail, measured accuracy metrics, and deterministic ghost detection — not just prompt engineering. Three MCP tools, seven spoliation tests, one-command demo. GitHub link in description. Built for FIND EVIL on Protocol SIFT."

**End card:** https://github.com/let-the-dreamers-rise/graveyard

---

## Windows offline recording

```powershell
.\run_demo.ps1
python scripts\benchmark_accuracy.py --exports examples\sample_exports --ground-truth examples\ground_truth_srl2018_sample.json --findings examples\findings_draft_v2_pass.json
python tests\test_spoliation.py
```

## Recording tips

- 1080p, terminal font 14+
- Pause on REJECT output 3 seconds
- Show benchmark JSON metrics — judges love numbers
- Keep under 5:00 — cut SIFT live section if running long
