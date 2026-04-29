import argparse
from aiops.cli import run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m aiops",
        description="AIOps — Log Anomaly Detector",
    )
    parser.add_argument(
        "log_file",
        nargs="?",
        help="Path to log file (default: logs.txt in project root)",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Use Claude AI to explain root causes and suggest fixes",
    )
    parser.add_argument(
        "--model",
        default="gemma:2b",
        help="Ollama model to use for --explain (default: gemma:2b)",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save AI analysis to docs/report.md (requires --explain)",
    )
    args = parser.parse_args()
    run(log_file=args.log_file, explain=args.explain, model=args.model, save_report=args.save_report)


main()
