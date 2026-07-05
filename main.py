from __future__ import annotations

import argparse
from pathlib import Path
import threading


def ensure_generated_models() -> None:
    generated_models_path = Path(__file__).resolve().parent / "generated_models.py"
    if not generated_models_path.exists():
        raise FileNotFoundError("Run python3 generate_models.py first; generated_models.py missing")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launcher for TCP publisher and subscriber")
    parser.add_argument("--host", default="127.0.0.1", help="TCP server host")
    parser.add_argument("--port", type=int, default=9000, help="TCP server port")
    parser.add_argument("--limit", type=int, default=5, help="How many published readings to consume")
    parser.add_argument("--command-id", type=int, default=101, help="Command id sent by client")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit <= 0:
        raise ValueError("--limit must be > 0")

    ensure_generated_models()

    from tcp_client import run_client
    from tcp_server import run_server

    ready_event = threading.Event()
    server_thread = threading.Thread(
        target=run_server,
        kwargs={"host": args.host, "port": args.port, "ready_event": ready_event},
        daemon=True,
    )
    server_thread.start()

    if not ready_event.wait(timeout=5.0):
        raise ConnectionError(f"Server not ready on {args.host}:{args.port}")

    run_client(args.host, args.port, command_id=args.command_id, limit=args.limit)


if __name__ == "__main__":
    main()
