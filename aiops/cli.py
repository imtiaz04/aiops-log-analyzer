import sys
from datetime import datetime
from pathlib import Path

from aiops.tools import read_log_file, format_alert
from aiops.agent import detect_anomalies, summarize, explain_anomalies

DEFAULT_LOG = Path(__file__).resolve().parent.parent / "logs.txt"
REPORT_PATH = Path(__file__).resolve().parent.parent / "docs" / "report.md"


def run(log_file: str | None = None, explain: bool = False, model: str = "gemma:2b", save_report: bool = False) -> None:
    path = log_file or str(DEFAULT_LOG)

    title = "AIOps — Log Anomaly Detector"
    if explain:
        title += "  [AI Explain Mode]"

    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print(f"  Scanning: {path}\n")

    try:
        lines = read_log_file(path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    alerts = detect_anomalies(lines)

    if not alerts:
        print("  No anomalies detected. All clear.")
    elif not explain:
        for level, line_num, line in alerts:
            print(format_alert(level, line_num, line))
    else:
        top_alerts = sorted(
            alerts,
            key=lambda a: ("CRITICAL", "ERROR", "WARNING").index(a[0])
        )[:3]

        print("  Querying local Ollama model for root-cause analysis...\n")
        try:
            used_model, fields_list = explain_anomalies(top_alerts, model=model)
        except ConnectionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: AI analysis failed — {e}", file=sys.stderr)
            sys.exit(1)

        print(f"  Model: {used_model}\n")
        for (level, line_num, line), fields in zip(top_alerts, fields_list):
            print(format_alert(level, line_num, line))
            print(f"      Root cause      : {fields['root_cause']}")
            print(f"      Impact          : {fields['impact']}")
            print(f"      Recommended fix : {fields['fix']}")
            print(f"      Prevention      : {fields['prevention']}")
            print()

        if save_report:
            _write_report(path, used_model, top_alerts, fields_list)

    counts = summarize(alerts)
    print("-" * 60)
    print(f"  Scanned {len(lines)} lines  |  "
          f"CRITICAL: {counts['CRITICAL']}  "
          f"ERROR: {counts['ERROR']}  "
          f"WARNING: {counts['WARNING']}")
    print("=" * 60)


def _write_report(
    log_path: str,
    model: str,
    alerts: list[tuple[str, int, str]],
    fields_list: list[dict],
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# AIOps Anomaly Report\n\n",
        f"**Generated:** {timestamp}  \n",
        f"**Log file:** `{log_path}`  \n",
        f"**Model:** `{model}`\n",
    ]
    for (level, line_num, log_line), fields in zip(alerts, fields_list):
        lines.append(f"\n---\n\n### `[{level}]` line {line_num}\n\n")
        lines.append(f"```\n{log_line.strip()}\n```\n\n")
        lines.append(f"**Root cause:** {fields['root_cause']}\n\n")
        lines.append(f"**Impact:** {fields['impact']}\n\n")
        lines.append(f"**Recommended fix:** {fields['fix']}\n\n")
        lines.append(f"**Prevention:** {fields['prevention']}\n")
    REPORT_PATH.write_text("".join(lines))
    print(f"  Report saved to {REPORT_PATH}")
