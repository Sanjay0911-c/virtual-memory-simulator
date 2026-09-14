"""
Standardized API response envelope.

Every endpoint returns EXACTLY one of these two shapes, so the frontend
never has to special-case a particular endpoint's response format:

    success_response(data)        -> {"success": true,  "data": {...}, "error": null}
    error_response(code, message) -> {"success": false, "data": null,  "error": {"code": ..., "message": ...}}
"""

from typing import Any, Dict


def success_response(data: Any) -> Dict:
    return {"success": True, "data": data, "error": None}


def error_response(code: str, message: str) -> Dict:
    return {"success": False, "data": None, "error": {"code": code, "message": message}}
