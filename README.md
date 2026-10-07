# Live 4-Laptop Module

This package contains ONLY the reusable live 4-laptop fleet feature.

## What it provides

- Exactly 4 laptop slots: LAPTOP-1 to LAPTOP-4
- Real laptop heartbeat/telemetry
- Online/offline detection
- User, OS and IP display
- Event/signal/risk fields ready for your threat-detection engine
- REST API for your teammate's frontend
- Server-Sent Events (SSE) for live updates
- Standalone test dashboard
- No database required
- No external backend framework required

## 1. Test it standalone

On the server laptop:

```powershell
python fleet_server.py
```

Open:

`http://localhost:8000`

## 2. Connect physical laptops

All laptops must be on the same LAN/Wi-Fi.

Find the server laptop IPv4 address:

```powershell
ipconfig
```

Example server IP:

`192.168.1.100`

On each client laptop:

```powershell
python -m pip install -r requirements.txt
python fleet_agent.py --server http://192.168.1.100:8000 --id LAPTOP-1
```

Use LAPTOP-2, LAPTOP-3 and LAPTOP-4 on the other machines.

If Windows Firewall blocks it, allow Python/port 8000 on the server laptop.

## 3. Merge into your teammate's project

The backend exposes:

### GET /api/fleet

Returns all four laptop records.

### GET /api/stream

SSE stream. The browser receives a new JSON state whenever a laptop heartbeat arrives.

### POST /api/heartbeat

Example:

```json
{
  "id": "LAPTOP-2",
  "user": "alice",
  "os": "Windows 11",
  "ip": "192.168.1.101",
  "status": "normal",
  "events": 15,
  "signals": 2,
  "risk": 10,
  "last_event": "login"
}
```

### GET /api/state

Same state structure as `/api/fleet`.

## 4. Frontend merge

Your teammate does NOT need to use the included HTML.

In React/Vite/Next/etc., consume:

```js
fetch("http://SERVER-IP:8000/api/fleet")
```

For live updates:

```js
const source = new EventSource("http://SERVER-IP:8000/api/stream");
source.onmessage = (event) => {
  const state = JSON.parse(event.data);
  console.log(state.laptops);
};
```

Each item has:

```text
id
online
status
user
os
ip
events
signals
risk
last_seen
last_event
age
```

Use these fields to populate the four laptop cards in your teammate's existing dashboard.

## Important

This module is deliberately separated from the attack-detection engine. Your teammate can merge the telemetry fields into his existing incident/risk engine later.

The included agent is intentionally safe: it sends heartbeat/system metadata only and does not run attacks, read sensitive files, or modify the laptop.
