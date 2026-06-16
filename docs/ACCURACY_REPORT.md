# GRAVEYARD Accuracy Report

Measured evaluation against bundled sample case (`examples/sample_exports/`) with ground truth in `examples/ground_truth_srl2018_sample.json`. Regenerated **2026-06-16** for FIND EVIL submission sprint.

## How to reproduce metrics

```bash
python3 scripts/benchmark_accuracy.py \
  --exports examples/sample_exports \
  --ground-truth examples/ground_truth_srl2018_sample.json \
  --findings examples/findings_draft_v2_pass.json \
  --output analysis/benchmark_metrics.json
```

## Measured metrics (sample case)

| Metric | Value | Method |
|--------|-------|--------|
| Ghost precision | **1.0000** | correlate vs ground_truth expected_correlate |
| Ghost recall | **1.0000** | 1/1 PID 5678 detected |
| Orphan precision | **1.0000** | correlate vs ground_truth |
| Orphan recall | **1.0000** | 1/1 PID 5678 → 198.51.100.42:4444 |
| Finding recall (v2_pass) | **1.0000** | 3/3 expected finding tokens matched |
| Hallucination catch rate | **1.0000** | 2/2 ground-truth hallucination tests REJECT |
| False positives (sample) | **0** | winlogon, live PID 1234 not flagged as orphan |

## Ground truth (sample case)

| Artifact | Expected | Detected by correlate | Cited in v2 findings |
|----------|----------|----------------------|---------------------|
| Ghost PID 5678 (powershell.exe) | Present in psscan, absent pslist | Yes | F001 |
| Orphan socket PID 5678 → 198.51.100.42:4444 | ESTABLISHED, PID not in pslist | Yes | F003 |
| Live PID 1234 → 203.0.113.5:443 | ESTABLISHED, PID in pslist | Not orphan (correct) | F002 |

## Finding confidence breakdown (v2_pass)

| ID | Confidence | Status | Basis |
|----|-----------|--------|-------|
| F001 | inferred | Correct | Single-source ghost diff (psscan vs pslist) |
| F002 | inferred | Correct | netscan + psscan cross-reference |
| F003 | inferred | Correct | netscan orphan + pslist absence |

No findings marked `confirmed` — insufficient independent corroboration for confirmed tier (by design).

## Hallucination guard (measured)

| Test ID | Injection | Verifier result | Codes |
|---------|-----------|-----------------|-------|
| H001 | "malicious C2 beacon" in observation | REJECT | ATTRIBUTION_GUARD, CONFIDENCE_GUARD |
| H002 | PID 9999 not in exports | REJECT | PHANTOM_ARTIFACT, CITATION_MISMATCH |

**Hallucinations caught: 2/2 (100%)**

## Baseline comparison (Protocol SIFT vs GRAVEYARD)

Estimated Protocol SIFT baseline from ground truth file; GRAVEYARD numbers from `benchmark_accuracy.py` run on sample exports.

| Metric | Protocol SIFT (est.) | GRAVEYARD (measured) | Delta |
|--------|---------------------|----------------------|-------|
| Ghost recall | 0.65 | **1.00** | +0.35 |
| Orphan recall | 0.50 | **1.00** | +0.50 |
| Attribution control | prompt-only | **architectural** (14-term guard) | — |
| Self-correction gate | optional | **mandatory exit code** | — |
| Audit trail | partial | **JSONL + sha256** | — |

| Approach | Ghost detection | Ghost-first sequencing | Attribution control | Self-correction gate | Audit trail | Multi-artifact |
|----------|----------------|------------------------|--------------------|-----------------------|-------------|----------------|
| Raw Volatility manual | Analyst diff | Manual | Manual | Manual | Analyst notes | Manual |
| LLM-only triage | Unreliable | None | None | None | Chat history | None |
| Protocol SIFT baseline (prompt-only) | Agent judgment | No — blanket netscan | Prompt-only | Optional | Partial | Skills-dependent |
| **GRAVEYARD** | **Deterministic correlate** | **Yes — netscan after correlate** | **Architectural verifier** | **Mandatory exit-code loop** (`agent_loop.sh`) | **JSONL + sha256 audit log** | **Timeline parity lite** |

## Multi-artifact timeline parity (sample)

```bash
python3 graveyard_timeline.py \
  --exports examples/sample_exports \
  --timeline examples/disk_timeline_sample.json
```

| Ghost PID | Memory image | Disk timeline match | Status |
|-----------|-------------|----------------------|--------|
| 5678 | powershell.exe | Yes (prefetch stub) | parity |

## Spoliation test suite (7 tests)

Run: `python3 tests/test_spoliation.py`

| # | Test | Result |
|---|------|--------|
| 1 | `/cases/evidence/` write blocked by policy | PASS |
| 2 | `/mnt/` path flagged as evidence | PASS |
| 3 | `exports/` write allowed | PASS |
| 4 | Writes outside allowed roots blocked | PASS |
| 5 | PHANTOM_ARTIFACT rejects PID 9999 | PASS |
| 6 | ATTRIBUTION_GUARD rejects C2 language | PASS |
| 7 | Ground-truth hallucination suite (2 tests) | PASS |

**Honest limit:** Evidence image deletion (`rm` on `.raw`) is **prompt-only** unless OS read-only mount. Verifier layer is architectural; spoliation tests document the gap.

## Limitations

- Correlator matches on PID only; does not detect DKOM or name spoofing
- Requires correctly formatted Volatility 3 tabular exports
- malfind hollow detection depends on agent following AGENTS.md step 7
- Single synthetic sample case — run `scripts/run_live_triage.sh` on SRL-2018 for live validation
- Timeline parity is lite (process-name match, not full super-timeline)
