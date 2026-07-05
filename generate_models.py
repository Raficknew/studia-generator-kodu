from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


TYPE_MAP = {
    "int32": ("i", "int"),
    "int64": ("q", "int"),
    "float32": ("f", "float"),
    "float64": ("d", "float"),
    "bool": ("?", "bool"),
    "str": (None, "str"),
}


def load_interface(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_and_prepare(data: dict) -> dict:
    if "types" not in data or not isinstance(data["types"], list) or not data["types"]:
        raise ValueError("Interface must contain non-empty 'types' list")

    endianness = data.get("endianness", "<")
    if endianness not in ("<", ">"):
        raise ValueError("'endianness' must be '<' (little) or '>' (big)")

    for type_def in data["types"]:
        if "name" not in type_def or "fields" not in type_def:
            raise ValueError("Each type must contain 'name' and 'fields'")

        prepared_fields = []
        for field in type_def["fields"]:
            field_name = field.get("name")
            if not isinstance(field_name, str) or not field_name:
                raise ValueError(f"Type '{type_def['name']}' has field without valid 'name'")

            field_type = field.get("type")
            if field_type not in TYPE_MAP:
                raise ValueError(f"Unsupported field type: {field_type}")

            fmt, py_type = TYPE_MAP[field_type]
            prepared = {
                "name": field_name,
                "type": field_type,
                "fmt": fmt,
                "py_type": py_type,
            }

            if field_type == "str":
                length = field.get("length")
                if not isinstance(length, int) or length <= 0:
                    raise ValueError(f"Field '{field_name}' requires positive 'length'")
                prepared["length"] = length

            prepared_fields.append(prepared)

        type_def["fields"] = prepared_fields

    data["endianness"] = endianness
    return data


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
