"""JSON 스키마 검증 — 필요한 부분집합만 (설계 §3.5).

jsonschema 라이브러리를 쓰지 않는다. 스키마가 type·enum·required·properties·
minimum·maximum·items 로 끝나서 의존성 하나를 더 얹을 만큼 복잡하지 않다.
오류 메시지는 모델에게 되돌려 보내므로 사람이 읽는 문장으로 쓴다.
"""

from typing import Any

_TYPES: dict[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "null": (type(None),),
}


def _type_ok(value: Any, t: str) -> bool:
    if t in ("number", "integer") and isinstance(value, bool):
        return False
    return isinstance(value, _TYPES[t])


def validate(data: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(data, x) for x in types):
            errors.append(f"{path}: {'|'.join(types)} 이어야 하는데 {type(data).__name__} 이다")
            return errors
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: {schema['enum']} 중 하나여야 하는데 {data!r} 이다")
    if isinstance(data, int | float) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: {schema['minimum']} 이상이어야 하는데 {data} 이다")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: {schema['maximum']} 이하여야 하는데 {data} 이다")
    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}: 필수 필드 {key} 가 없다")
        for key, sub in schema.get("properties", {}).items():
            if key in data:
                errors.extend(validate(data[key], sub, f"{path}.{key}"))
    if isinstance(data, list) and "items" in schema:
        for i, item in enumerate(data):
            errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
    return errors
