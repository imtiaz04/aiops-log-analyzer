from pathlib import Path


def read_log_file(path: str) -> list[str]:
    log_path = Path(path)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")
    return log_path.read_text().splitlines()


def format_alert(level: str, line_num: int, line: str) -> str:
    icons = {"CRITICAL": "!!!", "ERROR": " X ", "WARNING": " ! "}
    icon = icons.get(level, "   ")
    return f"[{icon}] [{level:<8}] line {line_num:>4}: {line.strip()}"
