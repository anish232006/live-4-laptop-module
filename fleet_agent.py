"""
LIVE 4-LAPTOP AGENT
Run this on each physical laptop. It sends only telemetry/heartbeat data
to the fleet server. It does not execute attacks or modify files.

Install:
    python -m pip install -r requirements.txt

Run:
    python fleet_agent.py --server http://192.168.1.100:8000 --id LAPTOP-1
"""
import argparse, getpass, json, os, platform, socket, time, urllib.request

def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"

def send(server, payload):
    url = server.rstrip("/") + "/api/heartbeat"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--id", required=True, choices=["LAPTOP-1","LAPTOP-2","LAPTOP-3","LAPTOP-4"])
    args = ap.parse_args()

    user = getpass.getuser()
    os_name = platform.system() + " " + platform.release()
    ip = local_ip()
    print(f"{args.id} -> {args.server}")
    print(f"user={user} | os={os_name} | ip={ip}")

    while True:
        try:
            send(args.server, {
                "id": args.id,
                "user": user,
                "os": os_name,
                "ip": ip,
                "status": "normal"
            })
            print(f"[{args.id}] heartbeat sent")
        except Exception as exc:
            print(f"[{args.id}] server unreachable: {exc}")
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAgent stopped.")
