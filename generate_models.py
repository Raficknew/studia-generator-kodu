from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


TYPE_MAP = {
    "int8": ("b", "int"),
    "uint8": ("B", "int"),
    "int16": ("h", "int"),
    "uint16": ("H", "int"),
    "int32": ("i", "int"),
    "uint32": ("I", "int"),
    "int64": ("q", "int"),
    "uint64": ("Q", "int"),
    "float32": ("f", "float"),
    "float64": ("d", "float"),
    "bool": ("?", "bool"),
    "str": (None, "str"),
    "dict": (None, "dict"),
}


def load_interface(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_struct_format(struct_format: str) -> str:
    if not isinstance(struct_format, str) or not struct_format:
        raise ValueError("'struct_format' must be a non-empty string")

    if struct_format[0] in ("<", ">", "!", "=", "@"):
        return struct_format[1:]

    return struct_format


def infer_py_type(field_type: str, struct_format: str | None = None) -> str:
    if field_type == "bool":
        return "bool"

    if field_type == "str":
        return "str"

    if struct_format is not None and struct_format.endswith(("s", "p")):
        return "bytes"

    if field_type.startswith("float") or (struct_format is not None and struct_format[-1:] in ("f", "d", "e")):
        return "float"

    return "int"


def validate_type_definition(type_def: dict) -> list[dict]:
    if "name" not in type_def or "fields" not in type_def:
        raise ValueError("Each type must contain 'name' and 'fields'")

    prepared_fields = []
    for field in type_def["fields"]:
        field_name = field.get("name")
        if not isinstance(field_name, str) or not field_name:
            raise ValueError(f"Type '{type_def['name']}' has field without valid 'name'")

        field_type = field.get("type")
        struct_format = field.get("struct_format")

        if field_type in TYPE_MAP:
            fmt, py_type = TYPE_MAP[field_type]
        elif struct_format is not None:
            fmt = normalize_struct_format(struct_format)
            py_type = field.get("py_type") or infer_py_type(field_type or "custom", fmt)
        else:
            raise ValueError(
                f"Unsupported field type: {field_type}. Add alias to TYPE_MAP or provide 'struct_format'"
            )

        try:
            if fmt is not None:
                import struct as _struct

                _struct.calcsize(f"<{fmt}")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid struct format for field '{field_name}': {fmt}") from exc

        prepared = {
            "name": field_name,
            "type": field_type or "custom",
            "fmt": fmt,
            "py_type": py_type,
        }

        if field_type == "str":
            length = field.get("length")
            if not isinstance(length, int) or length <= 0:
                raise ValueError(f"Field '{field_name}' requires positive 'length'")
            prepared["length"] = length

        prepared_fields.append(prepared)

    return prepared_fields


def validate_and_prepare(data: dict) -> dict:
    types = data.get("types")
    if not isinstance(types, list) or not types:
        raise ValueError("Interface must contain non-empty 'types' list")

    endianness = data.get("endianness", "<")
    if endianness not in ("<", ">"):
        raise ValueError("'endianness' must be '<' (little) or '>' (big)")

    prepared_types = []
    for type_def in types:
        if "name" not in type_def:
            raise ValueError("Each type must contain 'name'")

        prepared_type = dict(type_def)
        prepared_type["fields"] = validate_type_definition(type_def)
        prepared_types.append(prepared_type)

    return {"endianness": endianness, "types": prepared_types, "output": data.get("output", "generated_models.py")}


def generate(interface_path: Path, template_path: Path) -> Path:
    payload = validate_and_prepare(load_interface(interface_path))
    output = interface_path.parent / payload.get("output", "generated_models.py")

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_path.name)
    rendered = template.render(types=payload["types"], endianness=payload["endianness"])
    output.write_text(rendered + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    out = generate(root / "interface.json", root / "templates" / "models.py.j2")
    print(f"Generated: {out}")
