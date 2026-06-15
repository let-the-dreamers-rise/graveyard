# GRAVEYARD Datasets

Documentation for the bundled sample memory case and recommended live datasets.

## Bundled sample case

**Location:** `examples/sample_exports/` (mirrored at `docs/demo/exports/`)

**Scenario:** Simulated Windows 7 SP1 x64 memory snapshot with a terminated/hidden PowerShell ghost process and suspicious network activity.

### Export files

| File | Plugin | Contents |
|------|--------|----------|
| `windows_info_20240315.txt` | `windows.info` | Win7 SP1 x64, 2 CPUs, capture time 2024-03-15 09:45 UTC |
| `pslist_20240315.txt` | `windows.pslist` | Active process list — PIDs 4, 248, 312, 456, 1234 |
| `psscan_20240315.txt` | `windows.psscan` | Pool scan — includes ghost PID **5678** (powershell.exe) |
| `netscan_20240315.txt` | `windows.netscan` | PID 1234 → 203.0.113.5:443 ESTABLISHED; PID 5678 → 198.51.100.42:4444 ESTABLISHED (orphan) |

### Injected artifacts

1. **Ghost process:** PID 5678 (`powershell.exe`, PPID 1234) appears in psscan but not pslist — simulates a process that terminated or was unlinked from the active list.
2. **Orphan socket:** PID 5678 has ESTABLISHED TCP to 198.51.100.42:4444 despite absence from pslist — simulates lingering network artifact.
3. **Suspicious live connection:** PID 1234 (`cmd.exe`) has ESTABLISHED HTTPS to 203.0.113.5 — legitimate or C2, left ambiguous for interpretation testing.

### Expected correlate output

```json
{
  "ghosts": [{"pid": 5678, "image": "powershell.exe", ...}],
  "orphan_sockets": [{"pid": 5678, "foreign_address": "198.51.100.42", "foreign_port": "4444", ...}]
}
```

## Live dataset recommendations

For SIFT live runs, use publicly available DFIR training images:

| Dataset | Source | Notes |
|---------|--------|-------|
| SANS FOR508 memory samples | Course materials / SIFT `/cases/` | Win7/Win10 malware scenarios |
| Magnet Forensics samples | [magnetforensics.com/blog/free-tools](https://www.magnetforensics.com/blog/free-tools/) | Various OS versions |
| NIST CFReDS | [nist.gov/itl/ssd/software-quality-group/computer-forensics-reference-data-sets-cfreds](https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-reference-data-sets-cfreds) | Disk-focused; pair with memory if available |

## Capture procedure (live)

```bash
# On SIFT with memory image at /cases/graveyard/mem.raw
vol.py -f /cases/graveyard/mem.raw windows.info 2>&1 | tee exports/windows_info_$(date +%Y%m%d_%H%M%S).txt
vol.py -f /cases/graveyard/mem.raw windows.pslist 2>&1 | tee exports/pslist_$(date +%Y%m%d_%H%M%S).txt
vol.py -f /cases/graveyard/mem.raw windows.psscan 2>&1 | tee exports/psscan_$(date +%Y%m%d_%H%M%S).txt
python3 graveyard_correlate.py --exports ./exports/ --output analysis/graveyard_report.json
vol.py -f /cases/graveyard/mem.raw windows.netscan 2>&1 | tee exports/netscan_$(date +%Y%m%d_%H%M%S).txt
```

## Data handling

- Original memory images are **read-only** — never modified
- All analysis writes go to `exports/`, `analysis/`, `reports/`, `docs/`
- Sample exports contain synthetic IPs (RFC 5737 documentation ranges)

## File integrity

Sample exports are deterministic text files suitable for citation verification. Hashes can be computed:

```bash
sha256sum examples/sample_exports/*.txt
```
