from __future__ import annotations

import argparse
import socket
from dataclasses import dataclass

from generated_models import Command, SensorReading


def recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = conn.recv(size - len(chunks))
        if not part:
            raise ConnectionError("Socket closed before full payload")
        chunks.extend(part)
    return bytes(chunks)


@dataclass
class ReadingStats:
    count: int = 0
    min_temp: float | None = None
    max_temp: float | None = None
    sum_temp: float = 0.0

    def update(self, reading: SensorReading) -> None:
        temp = reading.temperature
        self.count += 1
        self.sum_temp += temp
        self.min_temp = temp if self.min_temp is None else min(self.min_temp, temp)
        self.max_temp = temp if self.max_temp is None else max(self.max_temp, temp)

    @property
    def avg_temp(self) -> float:
        if self.count == 0:
            return 0.0
        return self.sum_temp / self.count


def run_subscriber(host: str, port: int, limit: int, threshold: float) -> None:
    response_size = len(SensorReading(device_id="", timestamp=0, temperature=0.0, active=False).serialize())
    command = Command(command_id=1, name="subscribe", retry=True)
    stats = ReadingStats()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        client.sendall(command.serialize())
        print(f"Subscribed to {host}:{port}")

        while stats.count < limit:
            payload = recv_exact(client, response_size)
            reading = SensorReading.deserialize(payload)
            stats.update(reading)

            print(
                f"[{stats.count}/{limit}] device={reading.device_id} "
                f"temp={reading.temperature:.2f}C ts={reading.timestamp}"
            )

            if reading.temperature >= threshold:
                print(
                    f"ACTION: high temperature alert "
                    f"({reading.temperature:.2f}C >= {threshold:.2f}C)"
                )

    print(
        "Summary: "
        f"count={stats.count}, min={stats.min_temp:.2f}C, "
        f"max={stats.max_temp:.2f}C, avg={stats.avg_temp:.2f}C"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TCP subscriber app for SensorReading stream")
    parser.add_argument("--host", default="127.0.0.1", help="TCP server host")
    parser.add_argument("--port", type=int, default=9000, help="TCP server port")
    parser.add_argument("--limit", type=int, default=10, help="Number of readings to process")
    parser.add_argument("--threshold", type=float, default=22.0, help="Temperature alert threshold")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit <= 0:
        raise ValueError("--limit must be > 0")
    run_subscriber(args.host, args.port, args.limit, args.threshold)


if __name__ == "__main__":
    main()