from __future__ import annotations

import socket
import threading
import time

from generated_models import Command, SensorReading

HOST = "127.0.0.1"
PORT = 9000
COMMAND_SIZE = len(Command(command_id=0, name="", retry=False).serialize())
PUBLISH_INTERVAL_SEC = 2.0


def recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = conn.recv(size - len(chunks))
        if not part:
            raise ConnectionError("Socket closed before full payload")
        chunks.extend(part)
    return bytes(chunks)


def build_response(cmd: Command) -> SensorReading:
    temp = 20.5 if cmd.retry else 22.0
    return SensorReading(
        device_id=f"srv-{cmd.command_id}",
        timestamp=int(time.time()),
        temperature=temp,
        active=True,
    )


class Publisher:
    def __init__(self) -> None:
        self._subscribers: set[socket.socket] = set()
        self._lock = threading.Lock()

    def subscribe(self, conn: socket.socket) -> None:
        with self._lock:
            self._subscribers.add(conn)

    def unsubscribe(self, conn: socket.socket) -> None:
        with self._lock:
            self._subscribers.discard(conn)

    def publish(self, reading: SensorReading) -> None:
        payload = reading.serialize()
        dead_connections: list[socket.socket] = []

        with self._lock:
            subscribers = list(self._subscribers)

        for conn in subscribers:
            try:
                conn.sendall(payload)
            except OSError:
                dead_connections.append(conn)

        if dead_connections:
            with self._lock:
                for conn in dead_connections:
                    self._subscribers.discard(conn)


def publish_loop(publisher: Publisher) -> None:
    counter = 0
    while True:
        reading = SensorReading(
            device_id="sensor-main",
            timestamp=int(time.time()),
            temperature=21.0 + (counter % 5) * 0.3,
            active=True,
        )
        publisher.publish(reading)
        counter += 1
        time.sleep(PUBLISH_INTERVAL_SEC)


def handle_client(conn: socket.socket, addr: tuple[str, int], publisher: Publisher) -> None:
    with conn:
        print(f"Connected: {addr}")
        payload = recv_exact(conn, COMMAND_SIZE)
        command = Command.deserialize(payload)
        print(f"Received command: {command}")

        if command.name != "subscribe":
            response = build_response(command)
            conn.sendall(response.serialize())
            print(f"Sent one-shot response: {response}")
            return

        publisher.subscribe(conn)
        print(f"Subscriber registered: {addr}")
        try:
            while conn.recv(1):
                pass
        finally:
            publisher.unsubscribe(conn)
            print(f"Subscriber disconnected: {addr}")


def main() -> None:
    publisher = Publisher()
    threading.Thread(target=publish_loop, args=(publisher,), daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server listening on {HOST}:{PORT}")
        print("Mode: publisher-subscriber")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr, publisher), daemon=True).start()


if __name__ == "__main__":
    main()
