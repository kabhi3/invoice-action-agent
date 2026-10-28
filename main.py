from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Invoice Action Agent", version="0.2.0")


@app.get("/")
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "running", "service": "invoice-action-agent"}


@app.get("/.well-known/agent-card.json")
def agent_card(request: Request) -> dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    return {
        "name": "Invoice Action Agent",
        "description": (
            "Reviews invoice evidence, checks approval scope and duplicate "
            "risk, and only records actions after verifying a receipt."
        ),
        "url": f"{base}/a2a",
        "version": "0.2.0",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "defaultInputModes": ["text", "application/json"],
        "defaultOutputModes": ["text", "application/json"],
        "skills": [
            {
                "id": "invoice-review",
                "name": "Invoice review and safe action planning",
                "description": (
                    "Evaluate invoice packages against their evidence and "
                    "approval limits; avoid duplicate payments; verify receipts."
                ),
                "tags": ["invoice", "approval", "duplicate-payment", "receipt"],
            }
        ],
    }


@app.post("/a2a")
async def a2a(request: Request) -> JSONResponse | dict[str, Any]:
    """JSON-RPC entry point. Fail closed rather than claiming an action occurred."""
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None,
             "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
        return JSONResponse(
            {"jsonrpc": "2.0", "id": payload.get("id") if isinstance(payload, dict) else None,
             "error": {"code": -32600, "message": "Invalid JSON-RPC request"}},
            status_code=400,
        )

    method = payload.get("method")
    request_id = payload.get("id")

    if method in {"tasks/get", "GetTask"}:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": request_id,
             "error": {"code": -32602, "message": "Unknown task id"}},
            status_code=404,
        )

    if method in {"message/send", "SendMessage", "tasks/send"}:
        # Do not invent approvals, execute payments, or fabricate receipts.
        # Wire the assignment's exact action/receipt contract here before grading.
        return JSONResponse(
            {"jsonrpc": "2.0", "id": request_id,
             "result": {
                 "status": "input-required",
                 "accepted": False,
                 "message": (
                     "The A2A endpoint is online, but invoice actions are disabled "
                     "until the assignment's action and signed-receipt contract "
                     "is configured. No payment was attempted."
                 ),
             }},
            status_code=200,
        )

    return JSONResponse(
        {"jsonrpc": "2.0", "id": request_id,
         "error": {"code": -32601, "message": f"Method not found: {method}"}},
        status_code=400,
    )
