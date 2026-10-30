import socket

def get_local_ip():
    """Detect the machine's local IPv4 network address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.60"

"""
Schema-Validated YANG-Push Telemetry Pipeline
Backend Simulation Server (Python 3.11)
Provides REST API, Server-Sent Events (SSE), and Static Web Hosting.
"""

import http.server
import socketserver
import json
import time
import random
import datetime
import urllib.parse
import os
import threading

PORT = int(os.environ.get("PORT", 8080))
HOST = "0.0.0.0"

# Sample Devices
DEVICES = [
    {
        "device_id": "Router-01",
        "type": "Cisco ASR 9904",
        "ip": "10.100.1.1",
        "role": "Core Router",
        "status": "Online",
        "health": 98,
        "uptime": "142d 18h",
        "subscription_type": "Periodic (1s)",
        "sub_id": "SUB-YANG-8641-001",
        "interface": "GigabitEthernet0/0/0/1"
    },
    {
        "device_id": "Router-02",
        "type": "Juniper MX480",
        "ip": "10.100.1.2",
        "role": "Edge Gateway",
        "status": "Online",
        "health": 94,
        "uptime": "89d 04h",
        "subscription_type": "On-Change",
        "sub_id": "SUB-YANG-8641-002",
        "interface": "xe-0/1/0"
    },
    {
        "device_id": "Switch-01",
        "type": "Arista 7280R3",
        "ip": "10.200.2.1",
        "role": "Spine Switch",
        "status": "Online",
        "health": 99,
        "uptime": "210d 12h",
        "subscription_type": "Periodic (2s)",
        "sub_id": "SUB-YANG-8641-003",
        "interface": "Ethernet1/1"
    },
    {
        "device_id": "Switch-02",
        "type": "Cisco Nexus 9300",
        "ip": "10.200.2.2",
        "role": "Leaf Switch",
        "status": "Degraded",
        "health": 76,
        "uptime": "34d 06h",
        "subscription_type": "Periodic (2s)",
        "sub_id": "SUB-YANG-8641-004",
        "interface": "Ethernet1/2"
    }
]

# In-memory storage
VALID_TELEMETRY = []
INVALID_TELEMETRY = []
ACTIVE_ALERTS = []

# Schema specification
SCHEMA_SPEC = {
    "device_id": {"type": "string", "required": True},
    "cpu": {"type": "number", "min": 0, "max": 100, "required": True},
    "memory": {"type": "number", "min": 0, "max": 100, "required": True},
    "bandwidth": {"type": "number", "min": 0, "required": True},
    "packet_loss": {"type": "number", "min": 0, "max": 100, "required": False},
    "latency": {"type": "number", "min": 0, "required": False},
    "interface": {"type": "string", "required": False},
    "timestamp": {"type": "datetime", "required": True}
}

def validate_telemetry(payload):
    """Strict schema validator for incoming telemetry packet."""
    errors = []
    
    if not isinstance(payload, dict):
        return False, ["Payload must be a JSON object"]

    # Check required fields and types
    for field, rule in SCHEMA_SPEC.items():
        if rule.get("required") and field not in payload:
            errors.append(f"Missing required field: '{field}'")
            continue
            
        if field in payload:
            val = payload[field]
            expected_type = rule["type"]
            
            if expected_type == "string":
                if not isinstance(val, str):
                    errors.append(f"Wrong data type for '{field}': expected string, received {type(val).__name__}")
            elif expected_type == "number":
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    errors.append(f"Wrong data type for '{field}': expected number, received {type(val).__name__}")
                else:
                    if "min" in rule and val < rule["min"]:
                        errors.append(f"Value out of bounds for '{field}': minimum is {rule['min']}, got {val}")
                    if "max" in rule and val > rule["max"]:
                        errors.append(f"Value out of bounds for '{field}': maximum is {rule['max']}, got {val}")
            elif expected_type == "datetime":
                if not isinstance(val, str):
                    errors.append(f"Wrong data type for '{field}': expected ISO 8601 string")
                else:
                    # Validate ISO format
                    try:
                        datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
                    except Exception:
                        errors.append(f"Timestamp Error: '{val}' is not a valid ISO 8601 datetime")

    # Detect schema drift: check for unmapped leaves
    unrecognized = [k for k in payload.keys() if k not in SCHEMA_SPEC]
    if unrecognized:
        errors.append(f"Schema Drift Detected: Unknown leaves {unrecognized} not found in YANG model")

    return (len(errors) == 0), errors


def generate_packet(force_invalid=False, error_kind=None):
    """Generates synthetic valid or invalid YANG telemetry packet."""
    dev = random.choice(DEVICES)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Base packet
    cpu = round(random.uniform(22, 75), 1)
    mem = round(random.uniform(40, 82), 1)
    bw = round(random.uniform(120, 850), 1)
    loss = round(random.uniform(0.01, 1.2), 2)
    lat = round(random.uniform(4.5, 38.0), 1)

    # Induce occasional spikes
    if random.random() < 0.15:
        cpu = round(random.uniform(82, 97), 1) # Trigger alert
    if random.random() < 0.1:
        lat = round(random.uniform(105, 180), 1) # Latency spike

    packet = {
        "device_id": dev["device_id"],
        "cpu": cpu,
        "memory": mem,
        "bandwidth": bw,
        "packet_loss": loss,
        "latency": lat,
        "interface": dev["interface"],
        "timestamp": now_iso
    }

    # Decide if invalid
    if force_invalid or (random.random() < 0.22): # ~22% invalid packets
        kind = error_kind or random.choice(["wrong_type", "missing_field", "schema_drift", "bad_timestamp"])
        if kind == "wrong_type":
            packet["cpu"] = random.choice(["OVERFLOW", "critical_high", True, None])
        elif kind == "missing_field":
            packet.pop("device_id", None)
        elif kind == "schema_drift":
            packet["vendor_unauthorized_custom_attribute"] = "FW-v9.4-BETA"
        elif kind == "bad_timestamp":
            packet["timestamp"] = "INVALID_TIMESTAMP_FORMAT_2026"

    # Evaluate validation
    is_valid, errors = validate_telemetry(packet)
    
    record = {
        "id": f"PKT-{int(time.time() * 1000)}-{random.randint(100, 999)}",
        "payload": packet,
        "is_valid": is_valid,
        "errors": errors,
        "received_at": now_iso
    }

    if is_valid:
        VALID_TELEMETRY.insert(0, record)
        if len(VALID_TELEMETRY) > 200:
            VALID_TELEMETRY.pop()
        check_alerts(packet)
    else:
        INVALID_TELEMETRY.insert(0, record)
        if len(INVALID_TELEMETRY) > 200:
            INVALID_TELEMETRY.pop()

    return record


def check_alerts(packet):
    """Check metrics against SLA thresholds and generate alerts."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    dev = packet.get("device_id", "Unknown")

    if packet.get("cpu", 0) > 80:
        ACTIVE_ALERTS.insert(0, {
            "id": f"ALT-{int(time.time()*1000)}",
            "device_id": dev,
            "metric": "CPU Usage",
            "value": f"{packet['cpu']}%",
            "threshold": "80%",
            "severity": "Critical" if packet["cpu"] > 90 else "Warning",
            "timestamp": now_iso,
            "message": f"High CPU utilization threshold exceeded ({packet['cpu']}%)"
        })
    if packet.get("memory", 0) > 90:
        ACTIVE_ALERTS.insert(0, {
            "id": f"ALT-{int(time.time()*1000)+1}",
            "device_id": dev,
            "metric": "Memory Usage",
            "value": f"{packet['memory']}%",
            "threshold": "90%",
            "severity": "Critical",
            "timestamp": now_iso,
            "message": f"Memory buffer starvation danger on device ({packet['memory']}%)"
        })
    if packet.get("latency", 0) > 100:
        ACTIVE_ALERTS.insert(0, {
            "id": f"ALT-{int(time.time()*1000)+2}",
            "device_id": dev,
            "metric": "RTT Latency",
            "value": f"{packet['latency']}ms",
            "threshold": "100ms",
            "severity": "Warning",
            "timestamp": now_iso,
            "message": f"Elevated transmission latency across spine fabric ({packet['latency']}ms)"
        })
    if packet.get("packet_loss", 0) > 5:
        ACTIVE_ALERTS.insert(0, {
            "id": f"ALT-{int(time.time()*1000)+3}",
            "device_id": dev,
            "metric": "Packet Loss",
            "value": f"{packet['packet_loss']}%",
            "threshold": "5%",
            "severity": "Critical",
            "timestamp": now_iso,
            "message": f"High packet drop rate detected on interface ({packet['packet_loss']}%)"
        })

    # Keep latest 50 alerts
    if len(ACTIVE_ALERTS) > 50:
        del ACTIVE_ALERTS[50:]


# Background generator thread
def telemetry_generator_loop():
    while True:
        try:
            generate_packet()
        except Exception as e:
            print("Generator error:", e)
        time.sleep(2.0)


class PipelineHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/devices":
            self.send_json_response(DEVICES)
        elif path == "/api/telemetry/stream":
            self.send_json_response({
                "valid": VALID_TELEMETRY[:30],
                "invalid": INVALID_TELEMETRY[:30]
            })
        elif path == "/api/telemetry/stats":
            total_v = len(VALID_TELEMETRY)
            total_inv = len(INVALID_TELEMETRY)
            pass_rate = round((total_v / max(1, total_v + total_inv)) * 100, 1)
            self.send_json_response({
                "valid_count": total_v,
                "invalid_count": total_inv,
                "total_count": total_v + total_inv,
                "pass_rate": pass_rate,
                "active_alerts_count": len(ACTIVE_ALERTS)
            })
        elif path == "/api/alerts":
            self.send_json_response(ACTIVE_ALERTS)
        elif path == "/api/export/csv":
            self.send_csv_export()
        else:
            # Serve static files (index.html, etc.)
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if path == "/api/telemetry/validate":
            is_valid, errors = validate_telemetry(data)
            self.send_json_response({
                "is_valid": is_valid,
                "errors": errors,
                "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
        elif path == "/api/telemetry/inject":
            error_kind = data.get("error_kind", "wrong_type")
            pkt = generate_packet(force_invalid=True, error_kind=error_kind)
            self.send_json_response(pkt)
        elif path == "/api/alerts/clear":
            ACTIVE_ALERTS.clear()
            self.send_json_response({"status": "cleared"})
        else:
            self.send_error(404, "Endpoint not found")

    def send_json_response(self, obj):
        content = json.dumps(obj).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_csv_export(self):
        lines = ["id,device_id,cpu,memory,bandwidth,packet_loss,latency,interface,timestamp,status"]
        for item in VALID_TELEMETRY:
            p = item["payload"]
            lines.append(f"{item['id']},{p.get('device_id','')},{p.get('cpu','')},{p.get('memory','')},{p.get('bandwidth','')},{p.get('packet_loss','')},{p.get('latency','')},{p.get('interface','')},{p.get('timestamp','')},VALID")
        csv_data = "\n".join(lines).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/csv')
        self.send_header('Content-Disposition', 'attachment; filename="telemetry_export.csv"')
        self.send_header('Content-Length', str(len(csv_data)))
        self.end_headers()
        self.wfile.write(csv_data)


def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Seed initial telemetry
    for _ in range(15):
        generate_packet()

    # Start background generator
    gen_thread = threading.Thread(target=telemetry_generator_loop, daemon=True)
    gen_thread.start()

    local_ip = get_local_ip()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), PipelineHTTPRequestHandler) as httpd:
        print("=" * 72)
        print("  SCHEMA-VALIDATED YANG-PUSH TELEMETRY PIPELINE")
        print("=" * 72)
        print(f"  [+] Local Machine:     http://localhost:{PORT}")
        print(f"  [+] Same Wi-Fi / Phone: http://{local_ip}:{PORT}")
        print("=" * 72)
        print("  To open on ANY network worldwide (Cellular 4G/5G, Remote Devices):")
        print("  Run 'share_online.bat' or deploy to Netlify / Vercel.")
        print("=" * 72)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
