# GRAVEYARD Accuracy Report

Evaluation against bundled sample case (`examples/sample_exports/`) and verifier self-correction demo.

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

## False positives

| Check | Result |
|-------|--------|
| PID 456 (winlogon.exe) in pslist only | Not flagged as ghost — correct |
| PID 1234 ESTABLISHED connection | Not flagged as orphan (in pslist) — correct |
| System PID 4 | Present in both lists — not flagged |

**False positive rate on sample case: 0/3 detections**

## False negatives

| Potential miss | Status | Notes |
|---------------|--------|-------|
| Hollow memory (malfind) | Not in sample exports | Requires live malfind run; AGENTS.md step 7 covers this |
| UDP orphan sockets | Not tested | Correlator filters ESTABLISHED only (by design) |
| Ghost PPID chain analysis | Not implemented | Future enhancement |

## Overclaim caught (self-correction demo)

`findings_draft_v1_reject.json` F002 observation:

> "Process 1234 is malicious C2 beacon communicating with attacker infrastructure"

Verifier rejections:
- **ATTRIBUTION_GUARD** — "malicious", "C2", "attacker" in observation
- **CONFIDENCE_GUARD** — "confirmed" with only 1 citation

Corrected in v2:

> observation: "PID 1234 (cmd.exe) has an ESTABLISHED TCP connection to 203.0.113.5 on port 443."

Attribution moved to interpretation with `inferred` confidence.

## Spoliation test

The verifier reads exports as read-only. Attempting to cite a PID not present in any export triggers **PHANTOM_ARTIFACT**. The agent cannot fabricate evidence without a matching export substring — exports directory is the sole source of truth.

Test: Adding `"PID 9999 (evil.exe) in psscan"` to an observation without export backing → REJECT.

## Baseline comparison

| Approach | Ghost detection | Attribution control | Self-correction | Audit trail |
|----------|----------------|--------------------|--------------------|-------------|
| Raw Volatility manual | Analyst diff | Manual | Manual | Analyst notes |
| LLM-only triage | Unreliable | None | None | Chat history |
| Protocol SIFT alone | Agent judgment | Prompt-only | Optional | Partial |
| **GRAVEYARD** | Deterministic correlate | Architectural verifier | Mandatory loop | JSONL logs |

## Metrics summary

| Metric | Value |
|--------|-------|
| Ghost recall (sample) | 1/1 (100%) |
| Orphan recall (sample) | 1/1 (100%) |
| False positives (sample) | 0 |
| Overclaim blocked | 1/1 (100%) |
| Self-correction success | v1 REJECT → v2 PASS |

## Limitations

- Correlator matches on PID only; does not detect DKOM or name spoofing
- Requires correctly formatted Volatility 3 tabular exports
- malfind hollow detection depends on agent following AGENTS.md step 7
- Single sample case — live SIFT validation recommended for production claims
