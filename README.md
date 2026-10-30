# Schema-Validated YANG-Push Telemetry Pipeline

An enterprise-grade, Cisco/Grafana-inspired network telemetry observability platform that monitors, validates, and visualizes real-time YANG-Push telemetry streams (RFC 8639 / RFC 8641).

## Architecture Highlights
- **Zero-Setup Real-Time Dashboard**: Runs completely in modern browsers with React 18, Tailwind CSS, Lucide Icons, and animated charting engines.
- **Strict In-Line Schema Validation Engine**: Evaluates incoming telemetry against authoritative YANG RFC 7951 JSON models.
- **Dual-Path Ingestion & DLQ**: Clean streams route to time-series analytics, malformed or drifted packets route to the Quarantine Dead-Letter Queue.
- **AI Anomaly Detection**: Real-time heuristic anomaly detection flagging CPU surges, BGP flapping, memory leaks, and interface saturation with natural-language diagnoses.
- **Monochrome Enterprise Visual Theme**: Pitch-black canvas (`#000000`), deep dark cards, and high-contrast solid white buttons (`bg-white text-black font-extrabold`) across all 9 pages, header, sidebar, and modals.
- **NOC Operator Authentication Gateway**: Enterprise login page featuring LDAP/SSO simulation, role selector (Admin, Engineer, Viewer), password eye toggle, and 1-click demo profiles.
- **Role-Based Access Control (RBAC)**: Dynamic permission gating across **Admin** (full injection & DLQ control), **Network Engineer** (triage & alarms), and **Viewer** (read-only audit).
- **Continuous Stream Simulator**: Integrated live packet generator (adjustable 1s - 5s interval, manual fault injection, drift simulation).

## Quick Start

### 1. Direct Browser Launch (Recommended)
Simply open `index.html` in Google Chrome, Microsoft Edge, or Firefox.

### 2. Run with Python Local Server
```bash
python -m http.server 8080
```
Then navigate to: `http://localhost:8080`

### 3. Optional Backend Simulation Server
```bash
python server.py
```
Provides a live REST API at `http://localhost:5000` with endpoints for `/api/telemetry/stream`, `/api/telemetry/validate`, and `/api/devices`.
