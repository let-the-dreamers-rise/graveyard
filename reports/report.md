# Incident Response Report — CASE-001

Generated: 2026-06-15 23:54:48 UTC

All findings below passed GRAVEYARD verification.

## F001 [INFERRED]

**Observation (tool-grounded):**
PID 5678 (powershell.exe) appears in psscan output but is absent from pslist active process listing.

**Interpretation (analyst inference):**
Possible hidden or terminated process artifact — requires corroboration with malfind and network analysis before concluding malicious activity.

**Evidence citations:**
- `psscan_20240315.txt` → "5678	1234	powershell.exe"
- `pslist_20240315.txt` → "1234	456	cmd.exe"

**Tool:** `vol.py -f mem.raw windows.psscan; vol.py -f mem.raw windows.pslist; python3 graveyard_correlate.py --exports ./exports/` @ 2024-03-15T09:50:00Z

---

## F002 [INFERRED]

**Observation (tool-grounded):**
PID 1234 (cmd.exe) has an ESTABLISHED TCP connection to 203.0.113.5 on port 443.

**Interpretation (analyst inference):**
External connection on HTTPS port may indicate C2 or legitimate web traffic — requires corroboration with threat intel and disk artifacts.

**Evidence citations:**
- `netscan_20240315.txt` → "1234	192.168.1.105	203.0.113.5	443	ESTABLISHED"
- `psscan_20240315.txt` → "1234	456	cmd.exe"

**Tool:** `vol.py -f mem.raw windows.netscan` @ 2024-03-15T09:55:00Z

---

## F003 [INFERRED]

**Observation (tool-grounded):**
PID 5678 has an ESTABLISHED TCP connection to 198.51.100.42 on port 4444 but PID 5678 is absent from pslist.

**Interpretation (analyst inference):**
Orphan socket — network connection without active process listing; may indicate process hollowing or recently terminated ghost process.

**Evidence citations:**
- `netscan_20240315.txt` → "5678	192.168.1.105	198.51.100.42	4444	ESTABLISHED"
- `pslist_20240315.txt` → "1234	456	cmd.exe"

**Tool:** `vol.py -f mem.raw windows.netscan; python3 graveyard_correlate.py --exports ./exports/` @ 2024-03-15T09:56:00Z

---
