#!/usr/bin/env python3
"""
Thalamus OMI Webhook Server

Copyright (C) 2025 Mark "Rizzn" Hopkins, Athena Vernal, John Casaretto

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from flask import Flask, request
from typing import Tuple

app = Flask(__name__)

@app.route("/omi", methods=["POST"])
def omi_webhook() -> Tuple[str, int]:
    print(f"🔎 Incoming POST: {request.method} {request.url}")

    try:
        data = request.get_json(force=True)
        print("\n🔥 Cerebellum Input [UNRESTRICTED]:")
        print(data)
        return "OK", 200
    except Exception as e:
        print(f"💥 Failed to parse incoming data: {e}")
        return "Bad Request", 400

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
