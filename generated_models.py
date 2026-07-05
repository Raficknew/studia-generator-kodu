from __future__ import annotations

import json
from dataclasses import dataclass
import struct


def _expected_size_for_SensorReading() -> int:
    size = 0
    size += 24
    size += struct.calcsize("<q")
    size += struct.calcsize("<d")
    size += 1024
    size += struct.calcsize("<?")
    return size


@dataclass
class SensorReading:
    device_id: str
    timestamp: int
    humidity: float
    history: dict
    active: bool

    def serialize(self) -> bytes:
        return b"".join([
            _encode_str(self.device_id, 24),
            struct.pack("<q", self.timestamp),
            struct.pack("<d", self.humidity),
            _encode_dict(self.history, 1024),
            struct.pack("<?", self.active),
        ])

    @classmethod
    def deserialize(cls, payload: bytes) -> "SensorReading":
        expected_size = _expected_size_for_SensorReading()
        if len(payload) != expected_size:
            raise ValueError(f"Invalid payload size for SensorReading: expected {expected_size}, got {len(payload)}")

        offset = 0
        device_id = _decode_str(payload[offset:offset + 24])
        offset += 24
        (timestamp,) = struct.unpack_from("<q", payload, offset)
        offset += struct.calcsize("<q")
        (humidity,) = struct.unpack_from("<d", payload, offset)
        offset += struct.calcsize("<d")
        history = _decode_dict(payload[offset:offset + 1024])
        offset += 1024
        (active,) = struct.unpack_from("<?", payload, offset)
        offset += struct.calcsize("<?")
        return cls(
            device_id=device_id,
            timestamp=timestamp,
            humidity=humidity,
            history=history,
            active=active,
        )


def _expected_size_for_Command() -> int:
    size = 0
    size += struct.calcsize("<i")
    size += 32
    size += struct.calcsize("<?")
    return size


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
        expected_size = _expected_size_for_Command()
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


def _encode_dict(value: dict, size: int) -> bytes:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(raw) > size:
        raise ValueError(f"Dictionary too large: max {size} bytes")
    return raw.ljust(size, b"\x00")


def _decode_dict(value: bytes) -> dict:
    decoded = value.split(b"\x00", 1)[0].decode("utf-8")
    return json.loads(decoded) if decoded else {}
