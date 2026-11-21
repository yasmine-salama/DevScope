from typing import Any, Dict, Optional


def ok(data: Any = None, meta: Optional[Dict[str, Any]] = None):
    payload: Dict[str, Any] = {"status": "ok", "data": data if data is not None else {}}
    if meta is not None:
        payload["meta"] = meta
    return payload


def err(message: str, code: str = "error"):
    return {"status": "error", "error": {"code": code, "message": message}}
