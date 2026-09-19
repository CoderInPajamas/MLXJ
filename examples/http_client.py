"""Run the server first, then: python examples/http_client.py"""

import json
from pathlib import Path
from urllib.request import Request, urlopen

payload = Path(__file__).with_name("decision.json").read_bytes()
request = Request(
    "http://127.0.0.1:8765/v1/decide", data=payload, headers={"Content-Type": "application/json"}
)
with urlopen(request, timeout=120) as response:
    print(json.dumps(json.load(response), indent=2))
