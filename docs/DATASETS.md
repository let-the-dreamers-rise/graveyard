# GRAVEYARD Datasets

Documentation for bundled sample cases, public memory datasets, SRL-2018 live paths, and benchmark ground truth.

## Bundled sample case

**Location:** `examples/sample_exports/` (mirrored at `docs/demo/exports/`)

**Scenario:** Simulated Windows 7 SP1 x64 memory snapshot with a terminated/hidden PowerShell ghost process and suspicious network activity — patterned after **SRL-2018** ghost PID hunting exercises.

### Export files

| File | Plugin | Contents |
|------|--------|----------|
| `windows_info_20240315.txt` | `windows.info` | Win7 SP1 x64, 2 CPUs, capture time 2024-03-15 09:45 UTC |
| `pslist_20240315.txt` | `windows.pslist` | Active process list — PIDs 4, 248, 312, 456, 1234 |
| `psscan_20240315.txt` | `windows.psscan` | Pool scan — includes ghost PID **5678** (powershell.exe) |
| `netscan_20240315.txt` | `windows.netscan` | PID 1234 → 203.0.113.5:443 ESTABLISHED; PID 5678 → 198.51.100.42:4444 ESTABLISHED (orphan) |

### Ground truth benchmark

**File:** `examples/ground_truth_srl2018_sample.json`

**Live template (fill after triage):** `examples/ground_truth_live_template.json`

Run measured accuracy:

```bash
python3 scripts/benchmark_accuracy.py \
  --exports examples/sample_exports \
  --ground-truth examples/ground_truth_srl2018_sample.json \
  --findings examples/findings_draft_v2_pass.json \
  --output analysis/benchmark_metrics.json \
  --baseline-out analysis/baseline_vs_graveyard.json
```

### Disk timeline stub (multi-artifact demo)

**File:** `examples/disk_timeline_sample.json`

```bash
python3 graveyard_engine.py \
  --exports examples/sample_exports \
  --timeline examples/disk_timeline_sample.json \
  --output analysis/graveyard_engine_report.json
```

## Public Windows memory samples (reference URLs)

| Dataset | URL | Notes |
|---------|-----|-------|
| **NIST CFReDS** | https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-reference-data-sets-cfreds | Reference data sets; mostly disk — pair with memory when available |
| **NIST Hacking Case (2012)** | https://www.cfreds.nist.gov/Hacking_Case.html | Classic disk image; use for timeline parity layer |
| **NIST Mobile Device Images** | https://www.cfreds.nist.gov/mobile_devices.html | Mobile-focused |
| **Volatility 3 samples** | https://github.com/volatilityfoundation/volatility3/tree/develop/doc/sample | Official Volatility test images/docs |
| **Volatility 2 sample docs** | https://github.com/volatilityfoundation/volatility/wiki/Memory-Samples | Legacy sample list (Win XP/7 era) |
| **Magnet Forensics free tools** | https://www.magnetforensics.com/blog/free-tools/ | Free forensic resources and sample references |
| **Magnet AXIOM free tier** | https://www.magnetforensics.com/products/magnet-axiom/ | Sample case references in product docs |
| **SANS SIFT `/cases/`** | *(on VM)* | SRL-2018, FOR508 scenarios when course materials installed |
| **FIND EVIL hackathon Egnyte** | *(requires auth)* | Set `GRAVEYARD_EGNYTE_URL` and run `bash scripts/download_sample.sh` |

### Download helper

```bash
bash scripts/download_sample.sh /cases/graveyard/evidence
# Or with custom URL:
export GRAVEYARD_EGNYTE_URL='https://your-share/mem.raw'
bash scripts/download_sample.sh
```

If download fails (auth required), the script prints manual steps.

## SRL-2018 / SIFT live memory paths

SRL-2018 (Security Response Lab) memory images are used in FOR508/FOR610 training. On a standard SANS SIFT Workstation:

| Path | Status | Notes |
|------|--------|-------|
| `/cases/` | **Check on your VM** | SIFT OVA may ship with sample cases — `ls -la /cases/` |
| `/cases/SRL-2018/` | Common training layout | Memory + disk artifacts when course materials installed |
| `/cases/graveyard/evidence/` | **GRAVEYARD install target** | Created by `install.sh` — copy your `.raw` here |
| `/home/sans/sans-sift/` | Alternate SIFT layout | Some OVAs use `$HOME` case directories |

### If `/cases/` is empty

1. Log in to [SANS MySANS](https://www.sans.org/my-account/) or course Egnyte share
2. Navigate to **FOR508** or **SRL-2018** → Memory images
3. Copy to SIFT:

```bash
sudo mkdir -p /cases/graveyard/evidence
sudo cp ~/Downloads/SRL*.raw /cases/graveyard/evidence/mem.raw
sudo chown -R $(whoami) /cases/graveyard
```

**Never modify the original evidence file** — all writes go to `exports/`, `analysis/`, `reports/`, `docs/`.

## Live triage (one command)

```bash
cd /path/to/graveyard
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

Optional disk timeline parity:

```bash
export DISK_TIMELINE=/cases/graveyard/analysis/bodyfile_timeline.json
bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

After live run, fill ground truth:

```bash
cp examples/ground_truth_live_template.json analysis/ground_truth_live.json
# Edit PIDs from analysis/graveyard_engine_*.json
```

## Autonomous agent loop (deterministic self-correction)

```bash
bash scripts/agent_loop.sh examples/sample_exports
# With timeline:
bash scripts/agent_loop.sh examples/sample_exports examples/disk_timeline_sample.json
```

## Data handling

- Original memory images are **read-only** — never modified
- All analysis writes go to `exports/`, `analysis/`, `reports/`, `docs/`
- Sample exports contain synthetic IPs (RFC 5737 documentation ranges)
- Run spoliation tests: `python3 tests/test_spoliation.py` or `bash scripts/spoliation_test.sh`

## File integrity

```bash
python3 scripts/generate_audit_log.py --exports examples/sample_exports
sha256sum examples/sample_exports/*.txt
```
