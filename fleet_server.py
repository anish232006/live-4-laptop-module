"""
LIVE 4-LAPTOP FLEET MODULE
Standalone backend. No changes to your main project are required.

Run:
    python fleet_server.py

Dashboard:
    http://localhost:8000

Each real laptop runs:
    python fleet_agent.py --server http://<SERVER-IP>:8000 --id LAPTOP-1
    python fleet_agent.py --server http://<SERVER-IP>:8000 --id LAPTOP-2
    python fleet_agent.py --server http://<SERVER-IP>:8000 --id LAPTOP-3
    python fleet_agent.py --server http://<SERVER-IP>:8000 --id LAPTOP-4

API:
    GET  /api/fleet
    GET  /api/state
    GET  /api/stream
    POST /api/heartbeat
    POST /api/reset
"""
import json, time, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8000
LOCK = threading.Lock()
COND = threading.Condition(LOCK)
VERSION = 0
LAST_STATE = "{}"

SLOTS = [f"LAPTOP-{i}" for i in range(1, 5)]
fleet = {
    slot: {
        "id": slot, "online": False, "status": "waiting",
        "user": None, "os": None, "ip": None,
        "events": 0, "signals": 0, "risk": 0,
        "last_seen": 0, "last_event": None
    } for slot in SLOTS
}

def build_state():
    now = time.time()
    rows = []
    for slot in SLOTS:
        f = fleet[slot]
        online = bool(f["last_seen"] and now - f["last_seen"] <= 8)
        if not online:
            status = "offline" if f["last_seen"] else "waiting"
        else:
            status = f["status"] or "online"
        rows.append({
            **f,
            "online": online,
            "status": status,
            "age": round(now - f["last_seen"], 1) if f["last_seen"] else None
        })
    return {"timestamp": now, "laptops": rows}

def publish():
    global VERSION, LAST_STATE
    LAST_STATE = json.dumps(build_state())
    VERSION += 1
    COND.notify_all()

def heartbeat(body):
    global fleet
    laptop_id = str(body.get("id", "")).upper()
    if laptop_id not in fleet:
        return False, "Only LAPTOP-1 through LAPTOP-4 are supported."

    with LOCK:
        f = fleet[laptop_id]
        f["user"] = body.get("user") or f["user"]
        f["os"] = body.get("os") or f["os"]
        f["ip"] = body.get("ip") or f["ip"]
        f["events"] = int(body.get("events", f["events"]) or 0)
        f["signals"] = int(body.get("signals", f["signals"]) or 0)
        f["risk"] = int(body.get("risk", f["risk"]) or 0)
        f["status"] = body.get("status") or "normal"
        f["last_event"] = body.get("last_event") or f["last_event"]
        f["last_seen"] = time.time()
        publish()
    return True, "ok"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, code, data):
        raw = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            try:
                with open("static/fleet.html", "rb") as f:
                    raw = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except OSError:
                self.send_json(500, {"error": "static/fleet.html not found"})
            return

        if path in ("/api/fleet", "/fleet", "/api/state"):
            with LOCK:
                self.send_json(200, build_state())
            return

        if path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            last_version = -1
            try:
                while True:
                    with COND:
                        COND.wait_for(lambda: VERSION != last_version, timeout=15)
                        last_version = VERSION
                        payload = LAST_STATE
                    self.wfile.write(f"data: {payload}\n\n".encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self.send_json(400, {"error": "invalid JSON"})
            return

        if path == "/api/heartbeat":
            ok, message = heartbeat(body)
            self.send_json(200 if ok else 400, {"ok": ok, "message": message})
            return

        if path == "/api/reset":
            with LOCK:
                for slot in SLOTS:
                    fleet[slot].update(
                        online=False, status="waiting", user=None, os=None, ip=None,
                        events=0, signals=0, risk=0, last_seen=0, last_event=None
                    )
                publish()
            self.send_json(200, {"ok": True})
            return

        self.send_json(404, {"error": "not found"})

def main():
    global LAST_STATE
    with LOCK:
        LAST_STATE = json.dumps(build_state())
    print(f"Live 4-Laptop server running on port {PORT}")
    print(f"Dashboard: http://localhost:{PORT}")
    print("Agents should connect to http://<SERVER-LAN-IP>:8000")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
