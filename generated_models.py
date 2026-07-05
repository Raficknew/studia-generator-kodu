from __future__ import annotations

from dataclasses import dataclass
import struct


@dataclass
class SensorReading:
    device_id: str
    timestamp: int
    temperature: float
    active: bool

    def serialize(self) -> bytes:
        return b"".join([
            _encode_str(self.device_id, 24),
            struct.pack("<q", self.timestamp),
            struct.pack("<d", self.temperature),
            struct.pack("<?", self.active),
        ])

    @classmethod
    def deserialize(cls, payload: bytes) -> "SensorReading":
        expected_size = 0
        expected_size += 24
        expected_size += struct.calcsize("<q")
        expected_size += struct.calcsize("<d")
        expected_size += struct.calcsize("<?")
        if len(payload) != expected_size:
            raise ValueError(f"Invalid payload size for SensorReading: expected {expected_size}, got {len(payload)}")

        offset = 0
        device_id = _decode_str(payload[offset:offset + 24])
        offset += 24
        (timestamp,) = struct.unpack_from("<q", payload, offset)
        offset += struct.calcsize("<q")
        (temperature,) = struct.unpack_from("<d", payload, offset)
        offset += struct.calcsize("<d")
        (active,) = struct.unpack_from("<?", payload, offset)
        offset += struct.calcsize("<?")
        return cls(
            device_id=device_id,
            timestamp=timestamp,
            temperature=temperature,
            active=active,
        )


@dataclass
class Command:
    command_id: int
    name: str
    retry: bool

    def serialize(self) -> bytes:
        return b"".join([
            struct.pack("<i", self.command_id),
            _encode_str(self.name, 32),
            struct.pack("<?", self.retry),
        ])

    @classmethod
    def deserialize(cls, payload: bytes) -> "Command":
        expected_size = 0
        expected_size += struct.calcsize("<i")
        expected_size += 32
        expected_size += struct.calcsize("<?")
        if len(payload) != expected_size:
            raise ValueError(f"Invalid payload size for Command: expected {expected_size}, got {len(payload)}")

        offset = 0
        (command_id,) = struct.unpack_from("<i", payload, offset)
        offset += struct.calcsize("<i")
        name = _decode_str(payload[offset:offset + 32])
        offset += 32
        (retry,) = struct.unpack_from("<?", payload, offset)
        offset += struct.calcsize("<?")
        return cls(
            command_id=command_id,
            name=name,
            retry=retry,
        )


def _encode_str(value: str, size: int) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) > size:
        raise ValueError(f"String too long: max {size} bytes")
    return raw.ljust(size, b"\x00")


def _decode_str(value: bytes) -> str:
    return value.split(b"\x00", 1)[0].decode("utf-8")
