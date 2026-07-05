from __future__ import annotations

import socket

from generated_models import Command, SensorReading

HOST = "127.0.0.1"
PORT = 9000
RESPONSE_SIZE = len(SensorReading(device_id="", timestamp=0, temperature=0.0, active=False).serialize())


def recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        part = conn.recv(size - len(chunks))
        if not part:
            raise ConnectionError("Socket closed before full payload")
        chunks.extend(part)
    return bytes(chunks)


def main() -> None:
    command = Command(command_id=101, name="subscribe", retry=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall(command.serialize())
        print(f"Sent subscription command: {command}")

        while True:
            payload = recv_exact(client, RESPONSE_SIZE)
            response = SensorReading.deserialize(payload)
            print(f"Received publication: {response}")


if __name__ == "__main__":
    main()
