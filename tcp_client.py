from __future__ import annotations

import socket

from generated_models import Command, SensorReading

HOST = "127.0.0.1"
PORT = 9000
RESPONSE_SIZE = len(SensorReading(device_id="", timestamp=0, humidity=0.0, active=False, history={"1": "49", "2": "50", "3": "51", "4": "52"}).serialize())


def recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = conn.recv(size - len(chunks))
        if not part:
            raise ConnectionError("Socket closed before full payload")
        chunks.extend(part)
    return bytes(chunks)


def run_client(host: str, port: int, command_id: int = 101, limit: int = 1) -> None:
    command = Command(command_id=command_id, name="subscribe", retry=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        client.sendall(command.serialize())
        print(f"Sent command: {command}")

        for index in range(limit):
            upload = SensorReading(
                device_id=f"client-{index}",
                timestamp=command_id + index,
                humidity=30.0 + index,
                history={"batch": str(index), "source": "client"},
                active=True,
            )
            client.sendall(upload.serialize())
            print(f"Sent client packet: {upload}")

        client.shutdown(socket.SHUT_WR)

        received = 0
        while received < limit:
            payload = recv_exact(client, RESPONSE_SIZE)
            response = SensorReading.deserialize(payload)
            print(f"Received response: {response}")
            received += 1


if __name__ == "__main__":
    raise SystemExit("Run main.py instead")
