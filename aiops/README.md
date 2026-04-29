# AIOps — Log Anomaly Detector

A Python package that scans log files and prints clean alerts for `ERROR`, `WARNING`, and `CRITICAL` entries — with an optional AI layer powered by a local Ollama model that explains root causes and suggests fixes.

## Structure

```
aiops/
  __main__.py   — entry point, argument parsing (python -m aiops)
  cli.py        — CLI logic and output formatting
  agent.py      — anomaly detection + Ollama AI explanation
  tools.py      — helper functions (file reading, alert formatting)
logs.txt        — sample log file
```

## How to run

From the `demo/` directory:

```bash
# Basic scan — no dependencies required
python -m aiops

# Scan a custom log file
python -m aiops /path/to/your/app.log

# AI explain mode — uses local Ollama to add root cause + fix for every anomaly
python -m aiops --explain

# Both together
python -m aiops /path/to/your/app.log --explain
```

## Prerequisites for --explain

Ollama must be running locally with at least one model pulled:

```bash
# Start Ollama (if not already running)
ollama serve

# Pull a model (llama3 recommended, gemma also works)
ollama pull llama3
```

No API key or internet connection required — everything runs locally.

## Model selection

`--explain` automatically picks the best available model in this order:
`llama3` → `llama3.1` → `llama3.2` → `gemma` → `gemma2` → `mistral` → first available

## Example output

**Basic mode** (`python -m aiops`):
```
============================================================
  AIOps — Log Anomaly Detector
============================================================
  Scanning: /path/to/demo/logs.txt

[!!!] [CRITICAL] line   12: 2026-04-28 08:08:01 CRITICAL  Out of memory ...
[ X ] [ERROR   ] line    5: 2026-04-28 08:04:10 ERROR  Failed to connect to cache ...
[ ! ] [WARNING ] line    3: 2026-04-28 08:02:30 WARNING  Disk usage at 85% ...
...
------------------------------------------------------------
  Scanned 20 lines  |  CRITICAL: 2  ERROR: 6  WARNING: 4
============================================================
```

**AI explain mode** (`python -m aiops --explain`):
```
============================================================
  AIOps — Log Anomaly Detector  [AI Explain Mode]
============================================================
  Scanning: /path/to/demo/logs.txt

  Querying local Ollama model for root-cause analysis...

  Model: llama3:latest

[!!!] [CRITICAL] line   12: 2026-04-28 08:08:01 CRITICAL  Out of memory ...
      Root cause : The worker process exceeded available memory, triggering an OOM kill by the kernel.
      Fix        : Increase container memory limits or add swap; profile heap usage to find the leak.

[ X ] [ERROR   ] line    5: 2026-04-28 08:04:10 ERROR  Failed to connect to cache service ...
      Root cause : The cache service (Redis/Memcached) is down or unreachable on its configured port.
      Fix        : Run `systemctl status redis`; verify the port is open and restart the service if needed.
...
------------------------------------------------------------
  Scanned 20 lines  |  CRITICAL: 2  ERROR: 6  WARNING: 4
============================================================
```

**If Ollama is not running:**
```
ERROR: Ollama is not running. Start it with:

    ollama serve
```
