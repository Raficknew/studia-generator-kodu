from __future__ import annotations

import socket
import threading
import time

from generated_models import Command, SensorReading

HOST = "127.0.0.1"
PORT = 9000
COMMAND_SIZE = len(Command(command_id=0, name="", retry=False).serialize())
CLIENT_PACKET_SIZE = len(SensorReading(device_id="", timestamp=0, humidity=0.0, active=False, history={"1": "49", "2": "50", "3": "51", "4": "52"}).serialize())
PUBLISH_INTERVAL_SEC = 2.0


def recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = conn.recv(size - len(chunks))
        if not part:
            raise ConnectionError("Socket closed before full payload")
        chunks.extend(part)
    return bytes(chunks)


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
            humidity=45.0 + (counter % 5) * 1.5,
            history={"batch": str(counter), "source": "server"},
            active=True,
        )
        publisher.publish(reading)
        counter += 1
        time.sleep(PUBLISH_INTERVAL_SEC)


def handle_client(conn: socket.socket, addr: tuple[str, int], publisher: Publisher) -> None:
    with conn:
        print(f"(server): Connected: {addr}")
        payload = recv_exact(conn, COMMAND_SIZE)
        command = Command.deserialize(payload)
        print(f"(server): Received command: {command}")

        if command.name != "subscribe":
            print(f"(server): Rejected command: {command.name}")
            return

        publisher.subscribe(conn)
        print(f"(server): Subscriber registered: {addr}")
        try:
            while True:
                try:
                    payload = recv_exact(conn, CLIENT_PACKET_SIZE)
                except ConnectionError:
                    print(f"(server): Client upload closed: {addr}")
                    break

                client_packet = SensorReading.deserialize(payload)
                print(f"(server): Received client packet: {client_packet}")

            while True:
                time.sleep(1)
        finally:
            publisher.unsubscribe(conn)
            print(f"(server): Subscriber disconnected: {addr}")


def main(host: str = HOST, port: int = PORT, ready_event: threading.Event | None = None) -> None:
    publisher = Publisher()
    threading.Thread(target=publish_loop, args=(publisher,), daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        if ready_event is not None:
            ready_event.set()
        print(f"(server): Listening on {host}:{port}")
        print("(server): Mode: publisher-subscriber")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr, publisher), daemon=True).start()


def run_server(host: str = HOST, port: int = PORT, ready_event: threading.Event | None = None) -> None:
    main(host, port, ready_event)


if __name__ == "__main__":
    raise SystemExit("There is no connection right now, run main.py instead")
