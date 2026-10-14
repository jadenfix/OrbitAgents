"""Bounded same-origin transport to explicitly configured real services."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from flask import jsonify, request


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def forward(setting, endpoint):
    base = os.getenv(setting, "").rstrip("/")
    parts = urlsplit(base)
    loopback = parts.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or not (parts.scheme == "https" or (parts.scheme == "http" and loopback))
    ):
        return (
            jsonify(
                {
                    "detail": "Required service is not configured. No operation was performed."
                }
            ),
            503,
        )
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if request.headers.get("Authorization"):
        headers["Authorization"] = request.headers["Authorization"]
    payload = request.get_data() if request.method == "POST" else None
    if payload and len(payload) > 65536:
        return jsonify({"detail": "Request too large"}), 413
    upstream = Request(
        f"{base}/{endpoint}", data=payload, headers=headers, method=request.method
    )
    try:
        response = build_opener(NoRedirect).open(upstream, timeout=15)
    except HTTPError as error:
        if error.code in {400, 401, 403, 404, 409, 422, 429, 503}:
            # Preserve service error status without leaking provider internals or submitted secrets.
            return (
                jsonify(
                    {"detail": f"Service rejected the request (HTTP {error.code})."}
                ),
                error.code,
            )
        return jsonify({"detail": "Service request failed."}), 502
    except (URLError, TimeoutError, OSError):
        return (
            jsonify({"detail": "Service is unavailable. No result was received."}),
            503,
        )
    with response:
        raw = response.read(1048577)
        if len(raw) > 1048576:
            return jsonify({"detail": "Service response exceeded limit."}), 502
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError):
            return jsonify({"detail": "Service returned an invalid response."}), 502
        if not isinstance(data, dict):
            return jsonify({"detail": "Service returned an invalid response."}), 502
        return jsonify(data), response.status
